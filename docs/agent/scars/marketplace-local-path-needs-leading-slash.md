---
type: scar
status: active
created: 2026-05-26
updated: 2026-05-26
author: claude-session-2026-05-26
tags: [pr-review-workflow, github-action, plugin_marketplaces, dogfood]
importance: core
---

# `plugin_marketplaces: '.'` is rejected — the action requires `./`

## What happened

PR #6 (the "snazzy seahorse" emoji PR) ran the `PR Review` workflow on its first push and the `anthropics/claude-code-action@v1` step failed immediately with:

```
##[error]Action failed with error: Invalid marketplace URL format: .
```

The workflow file had been switched from the marketplace URL to `plugin_marketplaces: '.'` in PR #4 (the dogfood-loop change) — see [pr-review-installs-plugin-from-pr-head](../decisions/pr-review-installs-plugin-from-pr-head.md). Locally `.` *looks* like a path, but the action's validator disagrees.

## Root cause

`claude-code-base-action/src/install-plugins.ts` has two functions that gate the input:

```ts
function isLocalPath(input: string): boolean {
  return (
    input.startsWith("./") ||
    input.startsWith("../") ||
    input.startsWith("/") ||
    /^[a-zA-Z]:[\\\/]/.test(input)
  );
}
```

Bare `.` matches **none** of those four conditions, so it falls through to `MARKETPLACE_URL_REGEX` (which requires `https://...\.git`) and is rejected as an invalid URL.

The error message is misleading — it says "Invalid marketplace URL format" when the user clearly intended a local path. The path check is silently checking only for specific prefixes.

## Fix

Change the value to `'./'` (or any other accepted local-path form):

```yaml
plugin_marketplaces: './'
```

That's it. The dogfood-loop semantics from the original decision are preserved; only the surface form had to change.

## Why this matters / how to avoid

- When configuring `plugin_marketplaces` for a local path, **always** use one of the four accepted forms: `./<path>`, `../<path>`, `/<absolute>`, or `<DriveLetter>:\` on Windows.
- The action's error message points at "URL format" because `.` failed the URL regex *after* failing the path check. Don't be misled — if you intended a path, the path-check rule is what to debug.
- Pair this scar with [hidden-output-blocks-debugging](hidden-output-blocks-debugging.md): had `show_full_output: false` been on, the actual error line would have been hidden and we'd have spent much longer locating it.

## Related

- [pr-review-installs-plugin-from-pr-head](../decisions/pr-review-installs-plugin-from-pr-head.md) — the design decision the value implements.
- [hidden-output-blocks-debugging](hidden-output-blocks-debugging.md) — why the full-output toggle still earns its keep on the dogfood loop.
