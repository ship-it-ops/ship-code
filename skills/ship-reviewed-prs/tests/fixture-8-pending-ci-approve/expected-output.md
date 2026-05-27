# Expected Review Output — fixture-8-pending-ci-approve

```
Posted by ship-reviewed-prs (bot). Reasoning available in this comment;
ask the author/oncall for human judgment on disputed findings.

---

## PR Review — #2201 `docs(readme): clarify deploy step ordering`

**Verdict: LGTM (with caveats)**

### Confidence
Reviewed README.md (+2 lines, -2 lines) as a docs-only re-ordering of two deploy steps. SC scanned for secret/URL leakage — clean. SE confirmed the new ordering is technically correct: `PLATFORM_CONFIG_DIR` must be set before `helm install` reads it. No findings. CI partially pending — Validate Skills jobs green, CodeQL language-analysis jobs still running (irrelevant to a markdown diff). Per the updated matrix, pending CI is noted as a caveat rather than blocking the formal APPROVE; the friendly verdict reflects the caveat as `LGTM (with caveats)`.

### Personas activated

| Persona | Status | Reason |
|---|---|---|
| SE | ✅ pass | ordering correctness verified; docs-only |
| SC | ✅ pass | no leaked secrets / URLs |
| IN | ⏭ skip | docs-only PR |
| DA | ⏭ skip | docs-only PR |
| FE | ⏭ skip | docs-only PR |
| TS | ⏭ skip | docs-only PR |

### Findings

| Severity   | Count |
|---|---|
| Must-fix   | 0 |
| Should-fix | 0 |
| Nits       | 0 |

### Awaiting CI

Recommend awaiting CI completion before merge — 3 check(s) still running: `CodeQL / Analyze (python)`, `CodeQL / Analyze (javascript-typescript)`, `CodeQL / Analyze (java-kotlin)`. APPROVE stands; this is advisory.

### Comment lifecycle

| State | Count |
|---|---|
| Resolved | 0 |
| Won't-fix | 0 |
| Outdated | 0 |
| Possibly addressed | 0 |
| Stale | 0 |
| Open | 0 |

Suppressed 0 findings already discussed in earlier review.

### What's solid

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

1. **Pending CI does not block APPROVE** — the updated matrix surfaces it as an "Awaiting CI" caveat. The formal decision stays `APPROVE`; the friendly verdict label demotes to `LGTM (with caveats)`.
2. **"Awaiting CI" caveat lists pending check names by name** — even checks that are likely irrelevant to the diff (CodeQL on markdown). The skill defers to the human reviewer to decide what to wait for.
3. **No caveat section is emitted when its predicate doesn't hold** — there is no Delegations / Stale / Findings-without-anchor section here because none apply.
4. **APPROVE without inline findings uses the simpler `gh pr review --approve --body` form** (reference.md §6 exception).
5. **`--auto-approve` would NOT have been honored here** because pending CI blocks auto-submit; the local user would have been prompted to confirm submit.
6. **Exit code 0** in CI mode — downstream gating sees a clean pass; pending CI is a body-only signal, not a verdict modifier.
