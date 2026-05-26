# Synthetic PR Input for Fixture 8: Pending-CI APPROVE

You are reviewing a clean docs PR with no findings, but CI is still in progress — some checks have passed, others are pending (e.g. language-analysis jobs that don't apply to a markdown-only diff). Under the relaxed decision matrix (v2.0.0+), pending CI is noted as an advisory "Awaiting CI" caveat inside the APPROVE body rather than downgrading the verdict to COMMENT.

## PR metadata

```json
{
  "owner": "acme",
  "repo": "platform",
  "number": 2201,
  "title": "docs(readme): clarify deploy step ordering",
  "body": "Swaps the order of two steps in the README deploy section so the env-var-export step comes before the first `helm install`. Caught while onboarding a new engineer.",
  "headRefName": "docs/readme-deploy-order",
  "baseRefName": "main",
  "author": "sasha",
  "isDraft": false,
  "labels": ["docs"],
  "files": [
    {"path": "README.md", "additions": 2, "deletions": 2}
  ],
  "statusCheckRollup": {"state": "PENDING"},
  "commits": [
    {"sha": "bbb222", "committedDate": "2026-05-25T22:40:00Z"}
  ]
}
```

## Diff (gh pr diff)

```diff
diff --git a/README.md b/README.md
@@ -88,8 +88,8 @@ Deploy:

-1. Run `helm install platform charts/platform`.
-2. Export `PLATFORM_CONFIG_DIR=/etc/platform`.
+1. Export `PLATFORM_CONFIG_DIR=/etc/platform`.
+2. Run `helm install platform charts/platform`.
 3. Verify `kubectl get pods -n platform` shows all containers Ready.
```

## CI checks (gh pr checks)

| Check | Status |
|---|---|
| `Validate Skills / structure` | pass |
| `Validate Skills / links` | pass |
| `Validate Skills / markdown` | pass |
| `Validate Skills / json` | pass |
| `Validate Skills / yaml` | pass |
| `Validate Skills / plugin-symlinks` | pass |
| `CodeQL / Analyze (python)` | pending |
| `CodeQL / Analyze (javascript-typescript)` | pending |
| `CodeQL / Analyze (java-kotlin)` | pending |

No failing checks. Three CodeQL language-analysis jobs are still running; they don't analyze markdown so are irrelevant to this diff, but the skill should still surface them by name and let the human reviewer judge whether to wait.

## Review threads (gh api graphql)

```json
{
  "reviewThreads": []
}
```

## Invocation flags

The user invoked the skill in CI mode (`CI=true`). No flags.

---

Run the multi-persona PR review. Expected outcome:

- Zero findings of any tier. CI not failing; some checks pending. No "Possibly addressed" items. No draft state.
- Per the v2.0.0 decision matrix, the verdict is **APPROVE** with an "Awaiting CI" caveat listing the three pending CodeQL checks.
- The "Suggestions" caveat is **absent** (no P6/P7 findings).
- In CI mode, the bot disclosure prefix appears before the body. Submission uses the simpler `gh pr review --approve --body` form because the finding list has zero inline comments.
