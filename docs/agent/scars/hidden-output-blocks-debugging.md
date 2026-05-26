---
type: scar
status: active
created: 2026-05-25
updated: 2026-05-25
author: claude-session-2026-05-25
tags: [github-action, debugging, claude-code-sdk, show-full-output]
importance: core
incident-date: 2026-05-25
tripwire: "When the pr-review action returns num_turns: 0 with is_error: false and you can't tell why, flip `show_full_output: true` on the action's `with:` block. The default hides Claude's actual response, including 'Unknown command' diagnostics."
---

# show_full_output: false hides the actual failure mode

## What Happened

Three separate failures all produced the same external symptom — action job ✓ green, no review posted — but had three different root causes (missing commands file, wrong slash-command namespace, whitespace-contaminated OAuth token). The only externally visible diagnostic was the result-JSON shape (`num_turns`, `duration_ms`, `total_cost_usd`, `is_error`), which is the same when Claude says "Unknown command" as when it never authenticates.

The action says so explicitly:

```
Running Claude Code via SDK (full output hidden for security)...
Rerun in debug mode or enable `show_full_output: true` in your workflow file for full output.
```

But the user had to discover this only after multiple failed iterations. Each iteration cost real wall-clock time (~5 minutes per run plus debug overhead).

## Tripwire

If the pr-review action job is green but no review appears on the PR, **add `show_full_output: true` to the action's `with:` block** before running anything else. Without it you cannot tell whether the failure is auth, command resolution, or skill execution.

The flag is on as of commit `e34352e` (PR-review workflow update on main). It is kept on while the dogfood loop stabilizes; revisit removing only once reviews land reliably.

## Why It Hurt

- Hours of guessing at root cause when the action was literally telling Claude things visible in the hidden output.
- The "security" framing of the default is over-protective for an internal dogfood loop where the prompt body and tool calls are owned by the repo itself.

## Don't Do This

- Don't debug "num_turns: 0" or "Unknown command" symptoms without enabling `show_full_output: true` first.
- Don't turn the flag off until the dogfood pipeline has been stable for several PRs and you can articulate a privacy reason to flip it back.

## Related

- [oauth-token-whitespace-silent-fail](oauth-token-whitespace-silent-fail.md)
- [bare-slash-command-unknown-in-action](bare-slash-command-unknown-in-action.md)
- [plugin-without-commands-runs-silently](plugin-without-commands-runs-silently.md)
