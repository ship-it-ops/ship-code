# Agent Context
Last updated: 2026-05-26 | Total notes: 9

<!--
  This file is the index for `docs/agent/`. Agents read it at session start.
  Format: - [slug] | type | status | importance | YYYY-MM-DD | 8-word summary
-->

## Status (in-flight)
<!-- always-read at session start -->
- [pr-4-relax-approve-and-dogfood-workflow](status/pr-4-relax-approve-and-dogfood-workflow.md) | status | active | standard | 2026-05-25 | PR #4 stacks matrix + workflow + docs changes

## Decisions
- [pr-review-installs-plugin-from-pr-head](decisions/pr-review-installs-plugin-from-pr-head.md) | decision | active | core | 2026-05-25 | Dogfood workflow uses local checkout, not main URL
- [relaxed-approve-decision-matrix](decisions/relaxed-approve-decision-matrix.md) | decision | active | core | 2026-05-25 | APPROVE allowed with suggestions and pending CI caveats

## Patterns
- [plugin-command-discovery](patterns/plugin-command-discovery.md) | pattern | active | core | 2026-05-25 | Plugin slash commands live at commands/<name>.md namespaced

## Scars
- [plugin-without-commands-runs-silently](scars/plugin-without-commands-runs-silently.md) | scar | active | core | 2026-05-25 | Skill-only plugin runs 5 min posting nothing
- [bare-slash-command-unknown-in-action](scars/bare-slash-command-unknown-in-action.md) | scar | active | core | 2026-05-25 | Headless SDK needs /plugin:command form not bare
- [oauth-token-whitespace-silent-fail](scars/oauth-token-whitespace-silent-fail.md) | scar | active | standard | 2026-05-25 | Whitespace in OAuth secret kills run silently
- [hidden-output-blocks-debugging](scars/hidden-output-blocks-debugging.md) | scar | active | core | 2026-05-25 | show_full_output false hides Unknown-command and auth diagnostics
- [marketplace-local-path-needs-leading-slash](scars/marketplace-local-path-needs-leading-slash.md) | scar | active | core | 2026-05-26 | `plugin_marketplaces: '.'` rejected; needs `./` prefix

## Open Questions
- [v2-release-trigger](open-questions/v2-release-trigger.md) | open-question | active | standard | 2026-05-25 | When do we cut ship-reviewed-prs v2.0.0 release
