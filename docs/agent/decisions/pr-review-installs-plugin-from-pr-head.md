---
type: decision
status: active
created: 2026-05-25
updated: 2026-05-25
author: claude-session-2026-05-25
tags: [pr-review-workflow, github-action, security, dogfooding]
importance: core
---

# pr-review.yml installs the plugin from the local PR checkout, not main

## Context

`.github/workflows/pr-review.yml` is the dogfood loop that runs `ship-reviewed-prs` against PRs to this repo. The `anthropics/claude-code-action@v1` action accepts both URLs and local filesystem paths for `plugin_marketplaces` (confirmed by reading `base-action/src/install-plugins.ts`, function `isLocalPath`).

Two viable configurations:

- **URL** (`https://github.com/ship-it-ops/ship-code.git`): reviews use whatever is on the marketplace's default branch (main). Safe — a PR cannot rewrite its own reviewer. But PR-side plugin changes do not self-review; they only take effect on subsequent PRs after merge.
- **Local path** (`.`): reviews use the PR merge ref's checkout. PR-side plugin changes self-review immediately. Trust-model risk: a PR could rewrite `SKILL.md` to exfiltrate the workflow's `GITHUB_TOKEN` or post fake APPROVE comments.

## Decision

Use the local path: `plugin_marketplaces: '.'`.

## Alternatives Considered

- **URL → main**: rejected because the dogfood loop's whole point is to catch plugin regressions on the PR introducing them. Reviewing with main's plugin means a bug merged today is only caught by the *next* PR — too slow.
- **Conditional via label (e.g. `dogfood-plugin-head`)**: considered, would give the best-of-both default. Rejected as unnecessary complexity for this repo's trust model — see Consequences.

## Consequences

- PRs that change `plugins/ship-reviewed-prs/**` or `skills/ship-reviewed-prs/**` will be reviewed by their *own* version of the plugin. Faster signal on regressions.
- The trust-model risk is mitigated by GitHub's "Require approval for all outside collaborators" repo setting — PRs from non-members must be manually approved before the workflow runs.
- If that GitHub setting is ever relaxed, the workflow comment header documents the revert: flip `plugin_marketplaces` back to `'https://github.com/ship-it-ops/ship-code.git'`.

## Revisit Triggers

- The repo's branch protection / fork-PR approval settings change such that arbitrary outside contributors can run the workflow without review.
- An incident where a PR's plugin modification damages the review-bot's identity or leaks secrets.
- This repo gains many external contributors (e.g. transitions from internal-team to OSS-style governance).

## Related

- [plugin-without-commands-runs-silently](../scars/plugin-without-commands-runs-silently.md) — one of the regressions a local-checkout install would have caught on the *introducing* PR.
- [plugin-command-discovery](../patterns/plugin-command-discovery.md) — the layout the action expects when installing from a path.
