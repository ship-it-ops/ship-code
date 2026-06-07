---
type: scar
status: active
created: 2026-05-26
updated: 2026-06-07
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

## Recurrence — 2026-06-07, PR #48 on ship-it-ops/shipit-ai

Same failure mode in a downstream consumer ([run 27085369112](https://github.com/ship-it-ops/shipit-ai/actions/runs/27085369112/job/79938821159?pr=48)). The shipit-ai `ci.yml` workflow invoked the skill with `prompt: '/ship-reviewed-prs ${{ github.event.pull_request.number }}'` — bare slash command, no `--non-interactive` flag. The skill ran 33 turns, computed a clean REQUEST_CHANGES verdict with two inline comments (SC2 session fixation, IN2 missing timeout), called `AskUserQuestion` twice (both denied), and exited with `Should I submit this to GitHub now? (yes to submit, no to abort)` — submitting nothing. Same scar, different repo.

This recurrence is what motivated two follow-up changes in the ship-code repo (see [askuserquestion-denial-failsafe-to-submission](../decisions/askuserquestion-denial-failsafe-to-submission.md)):

1. **Skill failsafe**: `SKILL.md` now treats `AskUserQuestion` denial at the submission gate as a switch to CI mode and submits via `gh api`. Prevents the silent-drop tail case even when the workflow forgets the flag.
2. **Authoritative template**: `skills/ship-reviewed-prs/examples/ci-github-actions-claude-code-action.yml` ships the canonical `anthropics/claude-code-action@v1` workflow shape with the namespaced slash command and `--non-interactive` baked in. Future consumers copy from this template.

The flag is still mandatory in workflow YAML — the failsafe is a backstop, not a replacement.

## Related

- [askuserquestion-denial-failsafe-to-submission](../decisions/askuserquestion-denial-failsafe-to-submission.md) — the skill-level failsafe added in response to this recurrence.
- [pr-review-installs-plugin-from-pr-head](../decisions/pr-review-installs-plugin-from-pr-head.md) — the dogfood-install decision that makes this scar reproducible at all.
- [hidden-output-blocks-debugging](hidden-output-blocks-debugging.md) — the diagnostic toggle that made this debuggable.
- [marketplace-local-path-needs-leading-slash](marketplace-local-path-needs-leading-slash.md) — a separate gotcha in the same workflow file.
- [bare-slash-command-unknown-in-action](bare-slash-command-unknown-in-action.md) — same family of "headless-action behaves subtly differently from local" issues.
