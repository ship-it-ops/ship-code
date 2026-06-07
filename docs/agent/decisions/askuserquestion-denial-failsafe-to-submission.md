---
type: decision
status: active
created: 2026-06-07
updated: 2026-06-07
author: claude-session-2026-06-07
tags: [ship-reviewed-prs, ci-mode, ask-user-question, failsafe, submission-gate]
importance: core
---

# Treat `AskUserQuestion` denial at the submission gate as CI mode (failsafe)

## Context

`ship-reviewed-prs` distinguishes local mode (gate on `AskUserQuestion` for `yes`/`edit`/`no`) from CI mode (submit via `gh api` without prompting). The mode is selected by:

- `CI=true` env var → CI mode
- `--non-interactive` flag → CI mode
- otherwise → local mode

Scar [ci-mode-auto-detect-unreliable](../scars/ci-mode-auto-detect-unreliable.md) established that `CI=true` does not reliably propagate into the model's reasoning context inside `anthropics/claude-code-action@v1`. The mitigation was: always pass `--non-interactive` in the workflow prompt. The shipit-ai PR #48 recurrence on 2026-06-07 proved this mitigation is fragile — a downstream consumer that forgets the flag silently drops complete reviews. The skill computes a clean verdict, calls `AskUserQuestion`, gets denied (no interactive UI in CI), prints a `yes/no` chat fallback, and exits. The job ends cleanly. The review is lost.

The shape of the loss matters: the skill does not crash, the job does not fail, no error is logged anywhere visible, and the PR shows no review. Detection requires pulling `gh run view --log` and noticing `AskUserQuestion` in `permission_denials`. Most consumers never look.

## Decision

When `AskUserQuestion` returns a permission-denied / unavailable error at the **submission gate** (i.e., after the decision is computed and the draft is ready), the skill **switches to CI mode** and submits via `gh api` instead of printing a chat-side `yes/no` fallback.

Specifically:

1. The local-mode gate code path must `AskUserQuestion` first. If that call fails with a permission/tool-unavailable error, do not retry, do not synthesize an in-chat prompt, do not exit. Fall through to the CI-mode submission steps (require `GH_TOKEN`/`GITHUB_TOKEN`, post the pending review, post inline comments, submit with the verdict).
2. Prepend a one-line operator-facing note to the runner log: `(submitted via headless failsafe — calling workflow should add --non-interactive to the prompt)`. This is informational only; it does NOT appear in the PR review body (bot identity stays clean).
3. Exit codes follow the same CI-mode table (0/1/2/3 for APPROVE/REQUEST_CHANGES/COMMENT/ERROR).

## Alternatives Considered

- **Make CI mode the default and require `--interactive` for local mode.** Rejected. Surprising behavior change for local users who already rely on the gate. Breaks the principle that interactive confirmation is the safe default.
- **Detect headless environment proactively (probe for a TTY, sniff env vars, check for SDK markers).** Rejected. The scar established that the model cannot reliably observe these signals from inside `claude-code-action@v1`. Probing is exactly what the existing `CI=true` detection already does and exactly what already fails.
- **Print a stronger chat fallback that includes the full `gh api` command for a human to run.** Rejected. The chat output is invisible — it goes to runner logs that nobody reads unless a problem is already suspected. The work still gets dropped from the PR's point of view.
- **Add a separate `--require-confirmation` opt-in for local mode.** Rejected as scope creep. The current `AskUserQuestion`-based gate is the correct local UX; the failsafe only fires in a state that today produces no review at all.

## Consequences

**Enables:** consumers that misconfigure their workflow (missing `--non-interactive`, missing `CI=true`, headless SDK swallowing env vars) still get the review on the PR. Silent-drop tail case becomes self-healing.

**Commits us to:** the skill must treat `AskUserQuestion` denial as a positive signal of headlessness, not a negative signal of user refusal. Future changes to the gate must preserve this asymmetry — a denial-error means "fall through to submit", a `no` response means "abort".

**Does not regress:** local mode behavior is unchanged because `AskUserQuestion` is available locally. The failsafe only fires in a state where today the skill exits silently.

**Does not replace:** the `--non-interactive` flag is still mandatory in workflow YAML. The new `examples/ci-github-actions-claude-code-action.yml` template bakes it in. The failsafe is a backstop for misconfigured consumers, not a license to omit the flag.

## Revisit Triggers

- If `anthropics/claude-code-action` ships a version that reliably surfaces `CI=true` into the model's reasoning context, the failsafe becomes vestigial and can be downgraded from a behavior rule to a debug warning.
- If a downstream consumer ever reports that the failsafe submitted a review they did not want submitted, we may need to gate the failsafe behind a per-skill override (e.g., a `submission_failsafe: false` knob in `overrides.md`).
- If a different host (Cursor, Continue, custom SDK wrappers) starts denying `AskUserQuestion` for reasons unrelated to headlessness, the trigger condition may need to narrow from "denial of any kind" to "denial that pairs with the absence of a TTY".

## Related

- [ci-mode-auto-detect-unreliable](../scars/ci-mode-auto-detect-unreliable.md) — the parent scar; this decision is its long-term mitigation.
- [bare-slash-command-unknown-in-action](../scars/bare-slash-command-unknown-in-action.md) — the sibling trap that the new template also defends against.
- [relaxed-approve-decision-matrix](relaxed-approve-decision-matrix.md) — the decision-matrix policy that runs before the gate.
