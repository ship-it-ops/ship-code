# Expected Review Output — fixture-4-clean-approve-pr

```
## PR Review — #1234 `Fix typo in onboarding doc`

**Verdict: LGTM**

### Confidence
Reviewed 1 docs file (docs/onboarding.md, 1 line changed). Docs-only PR — SE, IN, DA, FE, TS skip per Pragmatism guidelines. SC scanned for secrets/leaked URLs/sensitive references; clean. No existing review threads. CI green. This is the cleanest possible approval path: docs typo fix, no operational dimension, no surface for new findings.

### Personas activated

| Persona | Status | Reason |
|---|---|---|
| SE | ⏭ skip | docs-only PR |
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

- Single-character correction; small, reviewable, low-risk.

### Submission preview (would have submitted automatically)
  Auto-approve honored: green-path LGTM on a clean, docs-only PR with no findings, no open threads, and green CI.
  gh pr review 1234 --approve --body <summary>

  ✓ Review submitted: https://github.com/acme/docs/pull/1234#pullrequestreview-<id>
```

## CI mode variant

If invoked with `CI=true GH_TOKEN=...`, the same LGTM is produced and submitted (formal `APPROVE` in the GitHub API call). Bot-disclosure prefix is added to the body:

```
Posted by ship-reviewed-prs (bot). Reasoning available in this comment;
ask the author/oncall for human judgment on disputed findings.

---
<summary>
```

Exit code: `0` (APPROVE).

If `ci_max_decision: COMMENT` is set in `overrides.md`, the submission downgrades to COMMENT with the disclosure prefix and `[advisory — bot policy: COMMENT-only]` note. Exit code stays at `0` (the original decision was APPROVE; the friendly verdict label remains `LGTM`).

## What this fixture demonstrates

1. **Auto-approve honored on green-path**: the only condition where `--auto-approve` is allowed to bypass the confirmation gate. The verdict shows as `LGTM` (clean), distinguishing it from `LGTM (with caveats)`.
2. **Docs-only PR skips most personas** per Pragmatism guidelines; SC still runs (scans for leaked secrets, internal URLs). The Personas-activated table makes this visible at a glance.
3. **APPROVE submission uses the simpler `gh pr review --approve --body` form** — no inline comments needed, no pending-review protocol needed.
4. **"What's solid" is short but real** — doesn't pad with boilerplate. A one-line correction gets a one-line acknowledgment.
5. **Exit code 0** in CI mode — downstream CI gating sees a clean pass.
