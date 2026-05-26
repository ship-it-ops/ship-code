# Expected Review Output — fixture-1-security-bug-pr

The skill should produce a report substantially matching the structure below. The critical SC1-AUTH-MISSING and the REQUEST_CHANGES decision are non-negotiable; wording details can vary.

---

```
## PR Review: #5012 — Add tier-upgrade endpoint

### Decision: 🛑 REQUEST_CHANGES

### Confidence
Reviewed 1 file (api/users.ts). No conditional personas activated (no schema, no infra files). No existing review threads. CI is green. The critical security finding is unambiguous: a new state-changing endpoint added without auth.

### 🛑 Critical (must fix before merge)

- **[SC1-AUTH-MISSING] api/users.ts:14**: New `POST /api/users/:id/upgrade-tier` has no auth middleware. Compare to the adjacent `GET /api/users/:id` on line 10, which uses `requireAuth`. The POST endpoint allows any unauthenticated request to change any user's tier. → Add `requireAuth` (and likely `requireAdmin` given the description says "so admins can change user tiers"). Verify: `curl -X POST localhost:3000/api/users/123/upgrade-tier -d '{"tier":"premium"}'` should return 401.

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

### Submission preview (local mode)
  gh api -X POST repos/acme/billing/pulls/5012/reviews (create pending review)
  gh api -X POST .../reviews/{id}/comments × 1 (one inline comment on api/users.ts:14)
  gh api -X POST .../reviews/{id}/events -f event=REQUEST_CHANGES -f body=<summary>

Proceed? Type "yes" to submit, "edit" to revise, or "no" to abort.
```

## CI mode variant

If the skill is invoked with `CI=true GH_TOKEN=...`, the same review is produced but submitted without confirmation. The body of the GitHub review is prefixed with:

```
Posted by ship-reviewed-prs (bot). Reasoning available in this comment;
ask the author/oncall for human judgment on disputed findings.

---
<the actual review>
```

Exit code: `1` (REQUEST_CHANGES).

If `ci_max_decision: COMMENT` is set in `overrides.md`, the submission downgrades to COMMENT with an `[advisory — bot policy: COMMENT-only]` prefix, and the exit code stays at `1`.

## What this fixture demonstrates

1. **SC1 catches the auth-missing finding** without the skill needing to be told what to look for.
2. **The adjacent line (line 10's `requireAuth`)** is used as evidence — the skill compares to surrounding code to make findings concrete.
3. **The PR description is read** — "so admins can change user tiers" informs the recommendation to use `requireAdmin`.
4. **Zero false-positives**: no spurious findings on the small diff. "What's Good" is substantive, not boilerplate.
5. **Decision is REQUEST_CHANGES** based on SC1 alone (any *1 finding).
