# Expected Review Output — fixture-8-pending-ci-approve

```
Posted by ship-reviewed-prs (bot). Reasoning available in this comment;
ask the author/oncall for human judgment on disputed findings.

---

## PR Review: #2201 — docs(readme): clarify deploy step ordering

### Decision: APPROVE

### Confidence
Reviewed README.md (+2 lines, -2 lines) as a docs-only re-ordering of two deploy steps. SC scanned for secret/URL leakage — clean. SE confirmed the new ordering is technically correct: `PLATFORM_CONFIG_DIR` must be set before `helm install` reads it. IN/DA/FE/TS did not activate. No findings. CI partially pending — Validate Skills jobs green, CodeQL language-analysis jobs still running (irrelevant to a markdown diff). Per the v2.0.0 matrix, pending CI is noted as a caveat rather than blocking APPROVE.

### Critical (must fix before merge)

- (none)

### Important (should fix)

- (none)

### Suggestions (improve when convenient)

- (none)

### Delegations

- (none)

### Awaiting CI

Recommend awaiting CI completion before merge — 3 check(s) still running: `CodeQL / Analyze (python)`, `CodeQL / Analyze (javascript-typescript)`, `CodeQL / Analyze (java-kotlin)`. APPROVE stands; this is advisory.

### Comment lifecycle

- 0 resolved | 0 outdated | 0 won't-fix | 0 possibly addressed | 0 stale | 0 open
- Suppressed: 0 findings already discussed in earlier review.

### What's Good

- Two-line re-ordering with a clear correctness motivation captured in the PR body (env-var-before-consumer). Low risk, immediately reviewable.
- No collateral churn — only the two affected lines touched.
```

## CI mode submission

Exit code: `0` (APPROVE). Because there are no inline comments (zero findings), the simpler submission form is used:

```
gh pr review 2201 --approve --body "<summary with disclosure prefix and Awaiting CI caveat>"

✓ Review submitted: https://github.com/acme/platform/pull/2201#pullrequestreview-<id>
```

## What this fixture demonstrates

1. **Pending CI does not block APPROVE** — the v2.0.0 matrix surfaces it as an "Awaiting CI" caveat rather than degrading to COMMENT.
2. **"Awaiting CI" caveat lists pending check names by name** — even checks that are likely irrelevant to the diff (CodeQL on markdown). The skill defers to the human reviewer to decide what to wait for.
3. **"Suggestions" caveat is absent** because `suggestion_count == 0`; caveat sections are conditional on their predicate.
4. **APPROVE without inline findings uses the simpler `gh pr review --approve --body` form** (reference.md §6 exception).
5. **`--auto-approve` would NOT have been honored here** because pending CI blocks auto-submit; the local user would have been prompted to confirm submit.
6. **Exit code 0** in CI mode — downstream gating sees a clean pass; pending CI is a body-only signal, not a verdict modifier.
