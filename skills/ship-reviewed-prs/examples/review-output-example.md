# Review Output Example

End-to-end demonstration of the structured review output produced by the skill. This example covers a moderately complex PR with findings across multiple personas, lifecycle suppression in action, and a clear REQUEST_CHANGES decision.

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

## Review Output (what the skill produces)

```
## PR Review: #4811 — Add billing-tier feature flag and migration

### Decision: 🛑 REQUEST_CHANGES

### Confidence
Reviewed 4 files: 1 migration, 2 production TypeScript, 1 SDK type. Skipped 0 generated, 0 vendor files. Conditional DA persona activated (schema migration). Conditional IN-deep persona did not activate (no IaC). CI is green. 3 existing review threads classified — 1 won't-fix, 1 outdated, 1 still open. Suppressed 2 candidate findings: a DA5-TYPE-PRECISION concern about the TEXT column matched Thread A (WONT_FIX, tracked in #4820) and was dropped silently; an SC1-AUTH-MISSING concern on the admin endpoint matched Thread C (OPEN) and is surfaced under "Open threads still need author response" rather than re-raised as a fresh finding. The decision is REQUEST_CHANGES because Thread C carries an SC1-priority concern that remains unresolved, plus fresh Critical findings on the timeout and SDK contract.

Findings are tiered by the documented priority rule (1-2 Critical, 3-5 Important, 6-7 Suggestion). Some placements look stricter than feel — IN2 OBSERVABILITY-GAP being Critical, SC7 LOG-LEAKAGE being a Suggestion — but the example follows the rule consistently so reviewers can rely on it.

### 🛑 Critical (must fix before merge)

- **[IN1-PROD-OUTAGE-RISK] services/billing.ts:5**: `fetch("https://billing.internal/users/...")` has no timeout. A slow billing-internal will hang this function indefinitely, blocking the calling request and exhausting connection pool capacity. → Add `signal: AbortSignal.timeout(5000)` and a retry policy: see `lib/http.ts` for the team's `httpWithRetry` helper.

- **[IN2-OBSERVABILITY-GAP] api/admin.ts:42**: New admin endpoint has no metric and no structured log. Admin actions that change user state always warrant audit logging. → Add `logger.info("admin.tier_changed", { actor_id, target_user_id, new_tier })` and increment a counter `admin.actions.tier_change`.

- **[SE2-CONTRACT-DRIFT] sdk/index.ts:7**: `User.tier` is added as `Optional` to the public SDK type. SDK consumers that destructure `{ tier }` will get `undefined` where they didn't before, and JSON parsers without strict typing will not raise on missing `tier`. → If the migration backfills `tier` for all users, mark the field required (`tier: "free" | "pro" | "premium"`). If you want it optional during the rollout window, document the rollout plan in the SDK changelog.

### ⚠️ Important (should fix)

- **[DA3-BACKFILL-MISSING] migrations/0042_add_user_tier.sql:1**: Adding NOT NULL `tier` to an existing populated `users` table. Migration will fail when run against production data. → Three-step migration:
  1. Add column nullable with default: `ALTER TABLE users ADD COLUMN tier TEXT DEFAULT 'free'`.
  2. Backfill in a separate deploy: `UPDATE users SET tier = 'free' WHERE tier IS NULL` (chunked if table is large).
  3. Add NOT NULL constraint in a follow-up migration after backfill completes.
  The PR description mentions `default 'free'` but the SQL does not include `DEFAULT 'free'`.

### Suggestions (improve when convenient)

- **[SC7-LOG-LEAKAGE] services/billing.ts:6**: `console.log("Premium check for user:", user)` writes the full user object (including email) to logs. → Log the user ID only: `logger.info("billing.premium_check", { user_id: userId })`. Use the structured logger, not `console.log`.

### Delegations

- Run `/ship-tested-code` on this PR — production code added in `services/billing.ts` and `api/admin.ts` (52 net added lines) with no test files modified. TS1 triggered.
- Run `/ship-debugged-code` on PR #4811 — description mentions `fixes #4801` but no regression test was added. TS2 triggered. (Once the regression test exists, return here for re-review.)

### Open threads (still need author response)
- `api/admin.ts:42` (Thread C, opened 1 day ago — "Should this require admin auth?") — matches SC1-AUTH-MISSING from this scan. The original framing is correct; the author acknowledged ("Yes, will add.") but the code has not been updated. This thread is what blocks the decision matrix from approving — same severity as SC1 (priority 1) so the unresolved concern drives REQUEST_CHANGES.

### Comment lifecycle
- 1 won't-fix (Thread A: ENUM-vs-TEXT typing, deferred to #4820)
- 1 outdated (Thread B: prior version of services/billing.ts)
- 1 open (Thread C: admin auth — surfaced above, not re-raised as a fresh finding)
- Suppressed: 2 findings already discussed in earlier review (DA5 TYPE-PRECISION → won't-fix Thread A; SC1 AUTH-MISSING → routed to Open threads above instead of re-emitted).

### Stale comments needing reply
- (none)

### What's Good

- The PR description is excellent — clear scope, explicit out-of-scope items with ticket references, and links the bug being fixed. This is what makes Thread A's won't-fix marker reliable and lets the skill suppress a duplicate finding confidently.
- The new feature is structured behind a clear flag gate (the `tier` column is the source of truth), which makes rollout reversible by simply leaving the column nullable until backfill completes.
- The SDK type was updated in the same PR as the underlying schema change — many teams ship these in separate PRs and end up with a window where they're inconsistent.

### Submission preview (local mode only)
  gh api -X POST repos/ship-it-ops/ship-code/pulls/4811/reviews (create pending review)
  gh api -X POST .../reviews/${REVIEW_ID}/comments × 4  (one per Critical/Important finding above — IN1, IN2, SE2, DA3; SC7 is a Suggestion, included in the summary body but not posted inline)
  gh api -X POST .../reviews/${REVIEW_ID}/events -f event=REQUEST_CHANGES -f body="<this entire output as the summary, with the Submission preview block stripped>"

Proceed? Type "yes" to submit, "edit" to revise the body, "no" to abort.
```

---

## What this example demonstrates

1. **Decision is decisive**: REQUEST_CHANGES, with a one-line reason and substantive Confidence section.
2. **Multi-persona findings**: SC (log leakage), DA (migration), IN (timeout, observability), SE (contract drift), TS (delegation only). For a worked example with the FE persona engaged, see `examples/fe-review-example.md`.
3. **Strict priority tiering**: Critical = priority 1-2, Important = 3-5, Suggestions = 6-7. The example follows this rule even where the resulting tier is stricter than gut feel (SC7 LOG-LEAKAGE in Suggestions, IN2 OBSERVABILITY-GAP in Critical). Consistency across reviews matters more than per-finding intuition — if a number feels wrong, the fix is to renumber the persona, not to violate the rule in one example.
4. **Won't-fix suppression**: a candidate DA5-TYPE-PRECISION finding (the TEXT column could be ENUM) is *not* emitted because Thread A already marked the typing concern won't-fix and tracked it in #4820. Dropped silently into the suppressed-finding counter.
5. **Open-thread suppression**: the admin-auth concern (SC1) is *also* not re-raised as a fresh inline finding — Thread C already covers it. Instead, the thread is surfaced under "Open threads (still need author response)" with its original framing, and its priority-1 weight still drives the decision matrix to REQUEST_CHANGES. This is the difference between "duplicate the team's existing work" and "leverage it."
6. **Lifecycle visibility**: every lifecycle state present is named, with counts. Suppression count is explicit (2 here).
7. **Delegations are separate from findings**: TS1 and TS2 are surfaced but don't count toward the decision.
8. **"What's Good" is substantive**: not generic. Names what the author did well that makes the reviewer's job easier.
9. **Submission preview shows the exact `gh` commands** — no opaque "I will submit a review"; the reviewer sees what's about to happen.
