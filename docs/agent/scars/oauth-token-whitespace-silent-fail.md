---
type: scar
status: active
created: 2026-05-25
updated: 2026-05-25
author: claude-session-2026-05-25
tags: [secrets, github-actions, oauth, anthropic-sdk, debugging]
importance: standard
incident-date: 2026-05-25
tripwire: "If the action's SDK exits with duration_ms < 100, num_turns: 0, total_cost_usd: 0, AND is_error: false — suspect the CLAUDE_CODE_OAUTH_TOKEN. Leading/trailing whitespace from paste is a silent killer."
---

# OAuth token with leading whitespace silently kills the run

## What Happened

The `pr-review.yml` workflow's first run after the secret was set produced `duration_ms: 45, num_turns: 0, total_cost_usd: 0, is_error: false`. The action installed Claude Code, initialized the SDK ("Claude Code initialized"), and exited cleanly without making any model call.

Inspecting the action's input dump revealed a leading space inside the redacted value:

```
"claude_code_oauth_token": " ***",   ← note the leading space
  claude_code_oauth_token:  ***       ← two spaces between : and ***
```

Compare to a working run:

```
"claude_code_oauth_token": "***",    ← no leading space
  claude_code_oauth_token: ***        ← one space
```

The token had been pasted with a leading whitespace character. The SDK rejected it but did so silently (no error event), returning `is_error: false` to keep the action green.

## Tripwire

Diagnostic signature in the log:
- `duration_ms` under ~100ms
- `num_turns: 0`
- `total_cost_usd: 0`
- `is_error: false`
- Quoted token value in the inputs dump starts with a leading space

If you see this pattern, **don't chase plugin or workflow logic** — re-set the secret first.

## Why It Hurt

- The action reports success, so the symptom is "no review posted" — same as the slash-command scars. Hard to distinguish without log access.
- Fixing it requires re-setting the secret cleanly, which the user has to do (Claude can't read secret values).

## Don't Do This

- Don't paste OAuth tokens into the GitHub web UI without trimming.
- For programmatic secret-setting, pipe to stdin to avoid shell-quoting surprises:
  ```bash
  claude setup-token | tr -d '[:space:]' | gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo <org>/<repo>
  ```
- Verify the token starts with `sk-ant-oat01-` (OAuth) and not `sk-ant-api03-` (API key); the wrong type would also produce the silent exit, by a different mechanism.

## Related

- [hidden-output-blocks-debugging](hidden-output-blocks-debugging.md) — without `show_full_output: true`, the only diagnostic is the result-JSON's shape.
