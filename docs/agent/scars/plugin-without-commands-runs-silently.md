---
type: scar
status: active
created: 2026-05-25
updated: 2026-05-25
author: claude-session-2026-05-25
tags: [plugin, slash-commands, github-action, ship-reviewed-prs]
importance: core
incident-date: 2026-05-25
tripwire: "If a plugin must be invoked via /<name> (especially in a headless GitHub Action), it MUST have plugins/<name>/commands/<command>.md. A skill alone is not reachable as a slash command."
---

# A plugin without a commands/ file silently runs for 5 minutes producing nothing

## What Happened

`ship-reviewed-prs` was wired into the ShipIt-AI repo's CI via `prompt: '/ship-reviewed-prs ${{ pr.number }}'`. The action installed the plugin successfully (logs showed `✔ Successfully installed plugin: ship-reviewed-prs@ship-code`), then Claude ran for 4m56s over 24 turns and posted **no review**. The SDK returned `is_error: false` so the action exited green.

Root cause: the plugin shipped *only* a skill at `plugins/ship-reviewed-prs/skills/ship-reviewed-prs/SKILL.md`. There was no `commands/` directory. Claude Code's `/<name>` syntax resolves only to slash commands, not skills. The skill's frontmatter also had `disable-model-invocation: true`, so it couldn't auto-trigger from a description match either. Claude treated `/ship-reviewed-prs 14` as literal text and wandered for 24 turns.

## Tripwire

If you are wiring a plugin into a non-interactive context that types `/<name>` as the prompt (a GitHub Action, a script, a cron job): **verify `plugins/<name>/commands/<name>.md` exists**. A skill is not enough.

## Why It Hurt

- ~$0.64 burned per silent run.
- The action was "green" so the failure was invisible until someone manually checked the PR for a review and found none.
- This took a full debugging session to localize because the symptom was "nothing happens" rather than an error.

## Don't Do This

- Don't assume `/ship-reviewed-prs` resolves because the plugin is "installed".
- Don't trust `is_error: false` as a success signal — see [bare-slash-command-unknown-in-action](bare-slash-command-unknown-in-action.md) for the related "num_turns: 0" signature.

## Related

- [bare-slash-command-unknown-in-action](bare-slash-command-unknown-in-action.md) — the follow-up failure once a `commands/` file exists but uses the wrong name form.
- [plugin-command-discovery](../patterns/plugin-command-discovery.md) — the positive pattern.
