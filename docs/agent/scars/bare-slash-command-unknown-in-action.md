---
type: scar
status: active
created: 2026-05-25
updated: 2026-05-25
author: claude-session-2026-05-25
tags: [plugin, slash-commands, github-action, claude-code-sdk]
importance: core
incident-date: 2026-05-25
tripwire: "In the anthropics/claude-code-action@v1 headless SDK context, slash commands resolve only as /<plugin>:<command>. The bare /<command> form returns 'Unknown command' and exits in milliseconds."
---

# Bare /command form fails in the action; must use /<plugin>:<command>

## What Happened

After adding a slash command at `plugins/ship-reviewed-prs/commands/ship-reviewed-prs.md` to fix [plugin-without-commands-runs-silently](plugin-without-commands-runs-silently.md), the workflow still produced no review. The action's full-output log showed:

```json
{
  "type": "text",
  "text": "Unknown command: /ship-reviewed-prs"
}
```

Followed by `duration_ms: 22, num_turns: 0, total_cost_usd: 0, is_error: false`.

Root cause: in interactive Claude Code, `/foo` may resolve through a shortcut when unambiguous. In the headless SDK invocation the action uses, it does not — commands must be invoked as `/<plugin>:<command>`. Compare to working examples in the user's installed plugins: `commit-commands:commit`, `commit-commands:clean_gone`, `ralph-loop:cancel-ralph` — every plugin command is exposed in the namespaced form.

## Tripwire

If you see `"text": "Unknown command: /<name>"` in the action's full output, **the issue is namespace, not whether the command exists**. Switch the prompt to `/<plugin-name>:<command-name>`. Rename the command file if the doubled-name form (e.g. `/ship-reviewed-prs:ship-reviewed-prs`) reads badly.

## Why It Hurt

- The previous tripwire (no commands/ file at all) was fixed, then this one bit immediately. The two failures look identical from outside (action runs, posts nothing) but have different SDK signatures.
- Without `show_full_output: true` enabled, the "Unknown command" text is hidden — you only see `num_turns: 0` and have to guess. See [hidden-output-blocks-debugging](hidden-output-blocks-debugging.md).

## Don't Do This

- Don't write workflow prompts as `/<command>`; always use `/<plugin>:<command>`.
- Don't name a single command the same as its plugin — `/foo:foo` is ugly. Pick a verb (e.g. `review-pr`) instead.

## Related

- [plugin-without-commands-runs-silently](plugin-without-commands-runs-silently.md) — the earlier scar.
- [hidden-output-blocks-debugging](hidden-output-blocks-debugging.md) — why this took so long to diagnose.
- [plugin-command-discovery](../patterns/plugin-command-discovery.md) — naming and namespacing pattern.
