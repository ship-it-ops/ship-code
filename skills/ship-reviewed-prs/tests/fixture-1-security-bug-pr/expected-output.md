# Expected Review Output — fixture-1-security-bug-pr

The skill should produce a review with **one inline comment** on `api/users.ts:14` carrying the SC1-AUTH-MISSING finding (with a `suggestion` fence adding `requireAuth`) and a trimmed summary body. The REQUEST_CHANGES decision and the SC1-AUTH-MISSING fingerprint are non-negotiable; wording details and the exact suggestion contents can vary as long as the fence is syntactically valid TypeScript that adds the middleware in the same spot.

---

## Inline comments to post

### Inline comment 1 — SC1-AUTH-MISSING

```
path:        api/users.ts
line:        14
suggestion:  yes
```

````markdown
**[SC1-AUTH-MISSING]** New `POST /api/users/:id/upgrade-tier` has no auth
middleware. Compare to the adjacent `GET /api/users/:id` on line 10, which
uses `requireAuth`. Without it, any unauthenticated request can change any
user's tier.

```suggestion
router.post("/api/users/:id/upgrade-tier", requireAuth, async (req, res) => {
```

Given the PR description ("so admins can change user tiers"), `requireAdmin`
is likely the right middleware — if you have one, swap `requireAuth` for it.
Verify after applying: `curl -X POST localhost:3000/api/users/123/upgrade-tier -d '{"tier":"premium"}'` should return 401.
````

---

## Summary body (posted as the review body)

```
## PR Review — #5012 `Add tier-upgrade endpoint`

**Verdict: Changes requested**

### Confidence
Reviewed 1 file (api/users.ts). No existing review threads. CI is green. The Must-fix security finding is unambiguous: a new state-changing endpoint added without auth.

### Personas activated

| Persona | Status | Reason |
|---|---|---|
| SE | ✅ pass | new route follows the existing pattern; no contract drift |
| SC | ✅ active | new state-changing endpoint without auth middleware |
| IN | ✅ pass | IN-light — no infra files touched |
| DA | ⏭ skip | no schema/migration touched |
| FE | ⏭ skip | no TSX/JSX in diff |
| TS | ✅ pass | under TS1 threshold (< 30 net lines added) |

### Findings

| Severity   | Count |
|---|---|
| Must-fix   | 1 |
| Should-fix | 0 |
| Nits       | 0 |

**Must-fix anchors:**
- `SC1` api/users.ts:14 — see inline comment (with `suggestion` fence)

### Comment lifecycle

| State | Count |
|---|---|
| Resolved | 0 |
| Won't-fix | 0 |
| Outdated | 0 |
| Possibly addressed | 0 |
| Stale | 0 |
| Open | 0 |

Suppressed 0 findings.

### What's solid

- The new endpoint follows the existing route pattern (path style, response shape).
- The endpoint correctly uses the project's `db.users.update` helper rather than rolling its own query — no SQL injection risk on this surface.
```

---

## Submission preview (local mode)

```
Will post 1 review with:
  - 1 inline comment  (1 with a suggestion fence — SC1)
  - Verdict: Changes requested  (decision: REQUEST_CHANGES)

  gh api -X POST repos/acme/billing/pulls/5012/reviews                    (create pending review)
  gh api -X POST .../reviews/${REVIEW_ID}/comments × 1                      (inline comment on api/users.ts:14)
  gh api -X POST .../reviews/${REVIEW_ID}/events -f event=REQUEST_CHANGES   (submit verdict + summary body)

Proceed? Type "yes" to submit, "edit" to revise, or "no" to abort.
```

---

## CI mode variant

If the skill is invoked with `CI=true GH_TOKEN=...`, the same review is produced but submitted without confirmation. The summary body sent in Step 3 is prefixed with:

```
Posted by ship-reviewed-prs (bot). Reasoning available in this comment;
ask the author/oncall for human judgment on disputed findings.

---
<the actual summary body>
```

The inline comment posted in Step 2 is **not** prefixed — only the summary body carries the bot identity disclosure.

Exit code: `1` (REQUEST_CHANGES).
