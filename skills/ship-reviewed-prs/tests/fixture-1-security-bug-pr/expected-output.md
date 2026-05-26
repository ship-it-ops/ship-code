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
## PR Review: #5012 — Add tier-upgrade endpoint

### Decision: 🛑 REQUEST_CHANGES

### Confidence
Reviewed 1 file (api/users.ts). No conditional personas activated (no schema, no infra files). No existing review threads. CI is green. The critical security finding is unambiguous: a new state-changing endpoint added without auth.

### 🛑 Critical (must fix before merge) — see inline comments
- **[SC1-AUTH-MISSING]** api/users.ts:14 — *see inline comment* (suggestion attached)

### Important (should fix)

- (none)

### Suggestions (improve when convenient)

- (none)

### Delegations

- (none — no test gap signal because this PR adds < 30 net lines)

### Comment lifecycle
- 0 resolved | 0 outdated | 0 won't-fix | 0 possibly addressed | 0 stale | 0 open
- Suppressed: 0 findings.

### What's Good

- The new endpoint follows the existing route pattern (path style, response shape).
- The endpoint correctly uses the project's `db.users.update` helper rather than rolling its own query — no SQL injection risk on this surface.
```

---

## Submission preview (local mode)

```
Will post 1 review with:
  - 1 inline comment  (1 with a suggestion fence — SC1)
  - Decision: REQUEST_CHANGES

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
