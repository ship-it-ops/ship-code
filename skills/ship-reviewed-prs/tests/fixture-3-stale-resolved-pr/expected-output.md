# Expected Review Output — fixture-3-stale-resolved-pr

```
## PR Review: #4980 — Refactor payment processing for retries

### Decision: COMMENT

### Confidence
Reviewed 1 file (services/payments.ts, 45 net added lines). No conditional personas activated. CI green. Long-lived PR with 6 existing review threads — applied aggressive lifecycle suppression. Three threads resolved (parametrized retry policy, UUID idempotency key, structured logging) and two won't-fix-marked (per-merchant retry policy → tracked in #5001; circuit breaker → discussed offline). One open thread (Grace's retry-exhaustion test request) remains. The skill suppressed 3 candidate findings that would have re-raised resolved/won't-fix concerns. The remaining advisory is the missing test coverage signal.

### Critical (must fix before merge)

- (none)

### Important (should fix)

- (none — all the substantive concerns are either resolved, won't-fix-marked, or already raised by Grace in thread T6)

### Suggestions (improve when convenient)

- (none)

### Delegations

- Run `/ship-tested-code` on this PR — 45 lines of production code added in services/payments.ts with no test files modified. TS1 triggered. The skill should design tests at the right level, including the retry-exhaustion path Grace asks about in T6.

### Comment lifecycle
- 3 resolved (parametrized retry, UUID idempotency key, structured logging) | 0 outdated | 2 won't-fix (per-merchant policy → tracked in #5001; circuit breaker → discussed offline) | 0 possibly addressed | 0 stale | 1 open (Grace: retry-exhaustion test, T6)
- Suppressed: 3 findings already discussed in earlier review (would have re-raised resolved concerns about parametrized policy, UUID generation, retry logging).

### Open threads (still need author response)
- services/payments.ts:38 (Grace, 2026-05-11 14:00 UTC — "Add a test for the retry exhaustion path") — matches the TS1 delegation above. Author should address Grace's specific request or close with a follow-up ticket.

### What's Good

- The author uses the team's `withRetry` helper from `lib/retry` rather than rolling retry logic inline. The reviews preserved across the PR's history show this point was raised early and addressed.
- The won't-fix items are clearly tracked: T4 references issue #5001, T5 documents the offline decision in writing. This is the right etiquette and makes the skill's suppression confident rather than guesswork.
- Idempotency key is now a required parameter — closes an important loophole in the original signature.

### Submission preview (local mode)
  gh api -X POST repos/acme/billing/pulls/4980/reviews (create pending review)
  gh api -X POST .../reviews/{id}/events -f event=COMMENT -f body=<summary>
  (no inline comments — all current findings are advisory/lifecycle and live in the summary body)

Proceed? Type "yes" to submit, "edit" to revise, or "no" to abort.
```

## What this fixture demonstrates

1. **Three RESOLVED threads (T1, T2, T3)** — the skill notes them but doesn't re-raise. The candidate findings that would have matched are dropped into the "Suppressed: 3" counter.
2. **Two WONT_FIX threads (T4, T5)** — T4 uses the `tracked in #5001` marker; T5 uses the `discussed offline ... agreed to skip` marker. Both suppress fresh findings on the same surface.
3. **One OPEN thread (T6)** — Grace's test-coverage concern is acknowledged in the output and routed to the TS1 delegation. The skill doesn't re-frame the concern; it credits Grace and points to where the deeper review should happen.
4. **Decision is COMMENT, not APPROVE** — even though there are no new findings, the open thread T6 prevents APPROVE. The skill is conservative: open threads block approval regardless of new findings.
5. **What's Good acknowledges the *process*** — clear tracking refs, written-down offline decisions — that makes the suppression reliable.
6. **No inline comments are posted** when all findings are advisory/lifecycle. The submission preview reflects this honestly.
