---
description: Multi-persona pull-request review with lifecycle-aware suppression. Submits via gh CLI (CI auto-submits; local prompts to confirm).
argument-hint: "<pr-number-or-url> [--auto-approve] [--non-interactive] [--json] [--strict]"
allowed-tools: Skill, Task, TodoWrite, Bash, Read, Grep, Glob
---

Run the `ship-reviewed-prs` skill against the pull request identified by the arguments below.

Arguments: $ARGUMENTS

Instructions:
1. Invoke the `ship-reviewed-prs` skill via the Skill tool — the skill owns the full review workflow (persona rubrics, comment-lifecycle suppression, decision matrix, gh submission).
2. Pass the arguments through verbatim; the first positional argument is the PR number or URL, the rest are flags documented in the skill's frontmatter.
3. Do not perform the review yourself before loading the skill — its `reference-*.md` files contain the rubrics and lifecycle rules you need.
4. Honor the skill's mode detection: if `CI=true` is set in the environment, the skill submits automatically; otherwise it prints a draft and waits for confirmation (unless `--non-interactive` is passed).
