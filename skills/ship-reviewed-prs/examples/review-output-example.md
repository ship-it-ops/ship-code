# Review Output Example

End-to-end demonstration of the inline-first review output produced by the skill. This example covers a moderately complex PR with findings across multiple personas, lifecycle suppression in action, and a clear REQUEST_CHANGES decision.

The skill emits two surfaces — a set of **inline comments** anchored at `file:line` and a single **summary body** — submitted as one atomic review via the GitHub pending-review API.

---

## Source PR (summarized)

**PR #4811: "Add billing-tier feature flag and migration"**

**Body:**
> Adds a new `tier` column to `users` with default `'free'`, a feature flag for premium gating, and a new admin endpoint to update tiers. Fixes #4801.
>
> Out of scope: tier-based pricing logic — tracked in #4815.

**Diff:**
```diff
diff --git a/migrations/0042_add_user_tier.sql b/migrations/0042_add_user_tier.sql
new file mode 100644
+ALTER TABLE users ADD COLUMN tier TEXT NOT NULL;

diff --git a/api/admin.ts b/api/admin.ts
+router.post("/admin/users/:id/tier", async (req, res) => {
+  const user = await db.users.update(req.params.id, { tier: req.body.tier });
+  res.json(user);
+});

diff --git a/services/billing.ts b/services/billing.ts
+export async function checkPremium(userId: string) {
+  const user = await fetch(`https://billing.internal/users/${userId}`).then(r => r.json());
+  console.log("Premium check for user:", user);
+  return user.tier === "premium";
+}

diff --git a/sdk/index.ts b/sdk/index.ts
-export interface User { id: string; email: string; }
+export interface User { id: string; email: string; tier?: "free" | "pro" | "premium"; }
```

**Existing review threads:**
- Thread A on `migrations/0042_add_user_tier.sql:1` — opened 2 days ago by maintainer: "Should this be ENUM instead of TEXT? An open TEXT column lets bad values in." Author replied: "Decided TEXT for flexibility; type-safety is being handled by a Zod schema at the API layer. Tracked in #4820 if we revisit." → **WONT_FIX**
- Thread B on `services/billing.ts:8` (older revision) — opened 5 days ago about a different version of this function. Line no longer exists. → **OUTDATED**
- Thread C on `api/admin.ts:42` — opened 1 day ago: "Should this require admin auth?" Currently has 1 reply from author: "Yes, will add." No commit yet. → **OPEN**

**CI status:** All green.

---

## Inline comments to post

The skill emits four inline comments — three on Critical findings (IN1, IN2, SE2) and one on the DA3 migration. The IN1 timeout fix is mechanical and self-contained, so it gets a `suggestion` fence. The other three keep the fix as prose because each needs an adjacent edit the fence cannot cover.

### Inline comment 1 — IN1-PROD-OUTAGE-RISK

```
path:        services/billing.ts
line:        5
suggestion:  yes
```

````markdown
**[IN1-PROD-OUTAGE-RISK]** `fetch("https://billing.internal/users/...")` has
no timeout. A slow billing-internal will hang `checkPremium` indefinitely,
blocking the calling request and exhausting connection-pool capacity.

```suggestion
  const user = await fetch(`https://billing.internal/users/${userId}`, { signal: AbortSignal.timeout(5000) }).then(r => r.json());
```

The team's `lib/http.ts` exposes a `httpWithRetry` helper — for repeated calls
to `billing.internal` consider migrating to that instead.
````

### Inline comment 2 — IN2-OBSERVABILITY-GAP

```
path:        api/admin.ts
line:        42
suggestion:  no  (needs new import + new metric counter)
```

```markdown
**[IN2-OBSERVABILITY-GAP]** New admin endpoint has no audit log and no
metric. Admin actions that change user state always warrant audit logging.

Add:

    logger.info("admin.tier_changed", { actor_id, target_user_id: req.params.id, new_tier: req.body.tier });
    metrics.counter("admin.actions.tier_change").increment();

Both `logger` and `metrics` need imports from `lib/observability.ts`, so
this isn't a one-line `suggestion` — apply the edit manually.
```

### Inline comment 3 — SE2-CONTRACT-DRIFT

```
path:        sdk/index.ts
line:        7
suggestion:  no  (decision required: required vs optional rollout window)
```

```markdown
**[SE2-CONTRACT-DRIFT]** `User.tier` is added as optional to the public SDK
type. SDK consumers that destructure `{ tier }` will get `undefined` where
they didn't before, and JSON parsers without strict typing will not raise
on missing `tier`.

Two acceptable resolutions — pick one:

- **If the migration backfills `tier` for all users**, mark the field
  required (`tier: "free" | "pro" | "premium"`) and document the SDK
  version bump.
- **If you want it optional during the rollout window**, document the
  rollout plan in the SDK changelog and leave the field optional.

This is a choice, not a mechanical edit — no `suggestion` fence.
```

### Inline comment 4 — DA3-BACKFILL-MISSING

```
path:        migrations/0042_add_user_tier.sql
line:        1
suggestion:  no  (three-step migration spans multiple deploys)
```

```markdown
**[DA3-BACKFILL-MISSING]** Adding `NOT NULL tier` to an existing populated
`users` table. Migration will fail when run against production data.
Three-step migration required:

1. Add column nullable with default: `ALTER TABLE users ADD COLUMN tier TEXT DEFAULT 'free'`.
2. Backfill in a separate deploy: `UPDATE users SET tier = 'free' WHERE tier IS NULL` (chunked if table is large).
3. Add `NOT NULL` constraint in a follow-up migration after backfill completes.

The PR description mentions `default 'free'` but this SQL does not include
`DEFAULT 'free'`. Spans three deploys, so no `suggestion` fence.
```

---

## Summary body (posted as the review body)

```
## PR Review — #4811 `Add billing-tier feature flag and migration`

**Verdict: Changes requested**

### Confidence
Reviewed 4 files: 1 migration, 2 production TypeScript, 1 SDK type. Skipped 0 generated, 0 vendor files. CI is green. 3 existing review threads classified — 1 won't-fix, 1 outdated, 1 still open. Suppressed 2 candidate findings: a DA5-TYPE-PRECISION concern about the TEXT column matched Thread A (WONT_FIX, tracked in #4820) and was dropped silently; an SC1-AUTH-MISSING concern on the admin endpoint matched Thread C (OPEN) and is surfaced under "Open threads still need author response" rather than re-raised as a fresh finding. The verdict is `Changes requested` because Thread C carries an SC1-priority concern that remains unresolved, plus fresh Must-fix findings on the timeout and SDK contract.

### Personas activated

| Persona | Status | Reason |
|---|---|---|
| SE | ✅ active | public SDK type changed |
| SC | ✅ active | new admin endpoint added; structured-log gap |
| IN | ✅ active | IN-light — services/billing.ts hits an internal HTTP without timeout |
| DA | ✅ active | new migration + NOT NULL column |
| FE | ⏭ skip | no TSX/JSX in diff |
| TS | ✅ active | production code added with no test files modified |

### Findings

| Severity   | Count |
|---|---|
| Must-fix   | 3 |
| Should-fix | 1 |
| Nits       | 1 |

**Must-fix anchors:**
- `IN1` services/billing.ts:5 — see inline comment (with `suggestion` fence)
- `IN2` api/admin.ts:42 — see inline comment
- `SE2` sdk/index.ts:7 — see inline comment

**Should-fix anchors:**
- `DA3` migrations/0042_add_user_tier.sql:1 — see inline comment

**Nit anchors:**
- `SC7` services/billing.ts:6 — see inline comment

### Delegations
- Run `/ship-tested-code` on this PR — production code added in `services/billing.ts` and `api/admin.ts` (52 net added lines) with no test files modified. TS1 triggered.
- Run `/ship-debugged-code` on PR #4811 — description mentions `fixes #4801` but no regression test was added. TS2 triggered. (Once the regression test exists, return here for re-review.)

### Open threads (still need author response)
- `api/admin.ts:42` (Thread C, opened 1 day ago — "Should this require admin auth?") — matches SC1-AUTH-MISSING from this scan. The original framing is correct; the author acknowledged ("Yes, will add.") but the code has not been updated. This thread is what blocks the decision matrix from approving — same severity as SC1 (priority 1) so the unresolved concern drives `Changes requested`.

### Comment lifecycle

| State | Count |
|---|---|
| Resolved | 0 |
| Won't-fix | 1 |
| Outdated | 1 |
| Possibly addressed | 0 |
| Stale | 0 |
| Open | 1 |

Suppressed 2 findings already discussed in earlier review (DA5 TYPE-PRECISION → won't-fix Thread A; SC1 AUTH-MISSING → routed to Open threads above instead of re-emitted).

### What's solid

- The PR description is excellent — clear scope, explicit out-of-scope items with ticket references, and links the bug being fixed. This is what makes Thread A's won't-fix marker reliable and lets the skill suppress a duplicate finding confidently.
- The new feature is structured behind a clear flag gate (the `tier` column is the source of truth), which makes rollout reversible by simply leaving the column nullable until backfill completes.
- The SDK type was updated in the same PR as the underlying schema change — many teams ship these in separate PRs and end up with a window where they're inconsistent.
```

---

## Submission preview (local mode only)

```
Will post 1 review with:
  - 4 inline comments  (1 with a suggestion fence — IN1; 3 prose-only)
  - 1 Nit (SC7) inline-anchored in the Findings table (deferred to a follow-up commit, no inline comment yet)
  - Verdict: Changes requested  (decision: REQUEST_CHANGES)

  gh api -X POST repos/ship-it-ops/billing-service/pulls/4811/reviews            (create pending review)
  gh api -X POST .../reviews/${REVIEW_ID}/comments × 4                             (one per Critical/Important finding)
  gh api -X POST .../reviews/${REVIEW_ID}/events -f event=REQUEST_CHANGES ...     (submit verdict + summary body)

Proceed? Type "yes" to submit, "edit" to revise the body, "no" to abort.
```

---

## What this example demonstrates

1. **Inline-first layout**: every Must-fix and Should-fix finding ships as an inline review comment anchored at `file:line`. The summary body's Findings table is a scannable index pointing at the inline comments — never a duplicate of their bodies.
2. **One `suggestion` fence**: IN1 qualifies because the fix is a single, contiguous edit that does not require any other change to compile. The other three Must-fix/Should-fix findings keep the fix as prose because each needs an adjacent edit a `suggestion` fence cannot cover (new import, decision between two valid approaches, multi-step migration spanning deploys).
3. **Verdict is decisive**: `Changes requested`, with a one-line reason and substantive Confidence section. The formal `REQUEST_CHANGES` keyword is preserved in the JSON output and exit code.
4. **Personas-activated table makes scope visible at a glance**: SE, SC, IN, DA, TS all ran; FE skipped because there's no TSX/JSX in the diff. A reviewer can see which lenses were applied before reading any finding.
5. **Multi-persona findings**: SC (log leakage), DA (migration), IN (timeout, observability), SE (contract drift), TS (delegation only). For a worked example with the FE persona engaged, see `examples/fe-review-example.md`.
6. **Strict severity tiering**: Must-fix = priority 1-2, Should-fix = 3-5, Nits = 6-7. The example follows this rule even where the resulting tier is stricter than gut feel (SC7 LOG-LEAKAGE in Nits, IN2 OBSERVABILITY-GAP in Must-fix). Consistency across reviews matters more than per-finding intuition.
7. **Won't-fix suppression**: a candidate DA5-TYPE-PRECISION finding (the TEXT column could be ENUM) is *not* emitted because Thread A already marked the typing concern won't-fix and tracked it in #4820. Dropped silently into the suppressed-finding counter.
8. **Open-thread suppression**: the admin-auth concern (SC1) is *also* not re-raised as a fresh inline finding — Thread C already covers it. Instead, the thread is surfaced under "Open threads (still need author response)" with its original framing, and its priority-1 weight still drives the decision matrix to `Changes requested`. This is the difference between "duplicate the team's existing work" and "leverage it."
9. **Comment-lifecycle table** lives separately from the Findings table — distinct concepts (thread states vs. severity counts), distinct surfaces. Suppression count is explicit (2 here) as a trailing line.
10. **Delegations are separate from findings**: TS1 and TS2 are surfaced but don't count toward the verdict.
11. **"What's solid" is substantive**: not generic. Names what the author did well that makes the reviewer's job easier.
12. **Submission preview shows the exact `gh` commands** — no opaque "I will submit a review"; the reviewer sees what's about to happen, including the inline-comment count and how many `suggestion` fences are included.
