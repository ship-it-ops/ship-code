---
type: scar
status: active
created: 2026-05-26
updated: 2026-05-26
author: claude-session-2026-05-26
tags: [pr-review-workflow, github-action, ci-mode, ask-user-question, submission-gate]
importance: core
---

# CI-mode auto-detect via `CI=true` is unreliable inside `anthropics/claude-code-action`

## What happened

On PR #7, the second commit (`3d1e62d` "Fix comment findings") triggered the `PR Review` workflow. The workflow's `Run Claude Code Review` step exited successfully — but **no review was posted on the PR**. The first commit on the same PR (`9913331`) had posted a review fine; the second one silently produced nothing visible.

Pulling the run log (`gh run view 26452416351 --log`) revealed the skill **had** computed a 💬 COMMENT decision with 2 inline findings (SE3 on `ci-output-json.md`, SE3 on `SKILL.md:412`). But the action's `permission_denials` array contained two `AskUserQuestion` calls, and the model's final text was:

> "The interactive question tool appears unavailable. Here's the decision summary — please reply **yes** to submit or **no** to abort"

Translation: the skill fell into **local interactive mode**, tried to gate submission behind `AskUserQuestion` (which the headless action environment denies), produced an ASCII fallback prompt, and the step ended without any `gh api` POST to GitHub.

## Root cause

`skills/ship-reviewed-prs/SKILL.md` Execution-mode detection rule:

> - `CI=true` env var set → CI mode
> - `--non-interactive` flag passed → CI mode
> - Otherwise → local mode

GitHub Actions sets `CI=true` in the runner's outer shell, but the Claude Code SDK that `anthropics/claude-code-action@v1` invokes does not reliably surface that env var into the model's reasoning context. The model's mode decision is non-deterministic — the very same workflow + skill produced CI mode on commit 1 (review posted) and local mode on commit 2 (review silently dropped).

## Fix

Add `--non-interactive` to the workflow's prompt **explicitly**. Do not rely on `CI=true` detection inside this action.

```yaml
prompt: '/ship-reviewed-prs:review-pr ${{ github.event.pull_request.number }} --non-interactive'
```

The SKILL.md spec already documents this: the flag's stated purpose is "Force CI mode behavior locally (skip confirmation gate). Required if CI auto-detection fails." This case is exactly that.

Setting `env.CI: true` in the workflow step alone is **not** sufficient — the env var is already set by the runner, the problem is that the model doesn't observe it. The flag is the only reliable signal because it goes through the slash-command argument parser, which the model always reads.

## Symptoms / how to recognize

A run of `gh run view <id> --log` for the `Run Claude Code Review` step finishes with `terminal_reason: completed` and the result text says "interactive question tool appears unavailable" or "Type yes / no to submit." The `permission_denials` array contains `AskUserQuestion` entries. The PR has no new review or comment from `claude[bot]` after the workflow run.

## Why this matters / how to avoid

- For **any** invocation of a ship-reviewed-prs (or similar interactive-gate) skill inside `anthropics/claude-code-action`, always pass `--non-interactive`. Do not skip it because "GitHub Actions sets CI=true automatically" — that is the trap.
- Pair this scar with [hidden-output-blocks-debugging](hidden-output-blocks-debugging.md): without `show_full_output: true`, the `permission_denials` and "interactive question tool appears unavailable" lines would be invisible and the silent failure would look like the bot simply chose not to review.

## Related

- [pr-review-installs-plugin-from-pr-head](../decisions/pr-review-installs-plugin-from-pr-head.md) — the dogfood-install decision that makes this scar reproducible at all.
- [hidden-output-blocks-debugging](hidden-output-blocks-debugging.md) — the diagnostic toggle that made this debuggable.
- [marketplace-local-path-needs-leading-slash](marketplace-local-path-needs-leading-slash.md) — a separate gotcha in the same workflow file.
- [bare-slash-command-unknown-in-action](bare-slash-command-unknown-in-action.md) — same family of "headless-action behaves subtly differently from local" issues.
