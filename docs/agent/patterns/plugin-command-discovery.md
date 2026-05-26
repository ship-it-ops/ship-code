---
type: pattern
status: active
created: 2026-05-25
updated: 2026-05-25
author: claude-session-2026-05-25
tags: [plugin, slash-commands, layout, claude-code]
importance: core
---

# Plugin command discovery: layout, naming, and namespacing

## When to Use

When authoring a plugin in this marketplace that should be invokable via `/<name>` — especially from a non-interactive context (a GitHub Action, a script, anything that types the literal slash command as its prompt).

## Implementation

A plugin command lives at:

```
plugins/<plugin-name>/commands/<command-name>.md
```

Three rules govern how Claude Code resolves the command:

1. **Filename = command name.** `plugins/ship-reviewed-prs/commands/review-pr.md` exposes a command named `review-pr`. Drop the `.md`. Use kebab-case.
2. **Plugin name = namespace.** The plugin name comes from `plugins/<plugin-name>/.claude-plugin/plugin.json:name`. It does *not* come from the directory name (though by convention they match).
3. **Slash form is always namespaced as `/<plugin>:<command>`.** In the headless SDK context (the `anthropics/claude-code-action@v1` action), the bare `/<command>` form does **not** resolve — even when unambiguous. Always type `/ship-reviewed-prs:review-pr` not `/review-pr`. See [bare-slash-command-unknown-in-action](../scars/bare-slash-command-unknown-in-action.md).

## Examples

Working pattern from this repo's `ship-reviewed-prs` plugin (commit `b35954b` adds the file, `fac022d`+ rename to `review-pr`):

```
plugins/ship-reviewed-prs/
├── .claude-plugin/
│   └── plugin.json           # {"name": "ship-reviewed-prs", ...}
├── commands/
│   └── review-pr.md          # exposes /ship-reviewed-prs:review-pr
└── skills/
    └── ship-reviewed-prs/    # per-file symlinks back to skills/<name>/
        ├── SKILL.md          # symlink
        ├── reference.md      # symlink
        ├── examples          # directory symlink
        └── tests             # directory symlink
```

Command body template (the file's content, with frontmatter):

```markdown
---
description: One-line summary shown in the picker.
argument-hint: "<arg-1> [flags]"
allowed-tools: Skill, Task, TodoWrite, Bash, Read, Grep, Glob
---

Run the `<skill-name>` skill with arguments: $ARGUMENTS

[concrete instructions for delegation]
```

## Gotchas

- **`allowed-tools` on the *command* is the binding constraint at runtime.** The skill's own `allowed-tools` does not expand it. If the skill spawns subagents (Task) or runs compound shell, the command must declare them.
- **Skills marked `disable-model-invocation: true` are reachable *only* via a slash command.** They don't auto-trigger from description matching. If you mark a skill that way, the `commands/` file is mandatory.
- **Don't name the command the same as the plugin.** `/ship-reviewed-prs:ship-reviewed-prs` reads badly. Pick a verb (e.g. `review-pr`).
- **Plugin symlinks**: `plugins/<name>/skills/<name>/` uses *per-file* symlinks for files inside (SKILL.md, reference.md, etc.). The `tests/` and `examples/` *subdirectories* are directory symlinks. CI's `plugin-symlinks` job catches violations of the per-file rule (see `.github/workflows/validate-skills.yml`).

## Related

- [plugin-without-commands-runs-silently](../scars/plugin-without-commands-runs-silently.md) — what happens with no `commands/` file.
- [bare-slash-command-unknown-in-action](../scars/bare-slash-command-unknown-in-action.md) — what happens with the wrong slash form.
- `CONTRIBUTING.md` "Slash Commands (optional)" section — the canonical authoring docs.
