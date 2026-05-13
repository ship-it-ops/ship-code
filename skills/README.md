# Skills

Ready-to-use AI skills for software development. Each skill follows the [Skills 2.0 format](../docs/writing-skills.md) with a `SKILL.md` entry point.

Skills live at `skills/<skill-name>/` — one flat directory per skill, no nested subfolders.

## Available Skills

| Skill | Description |
|-------|-------------|
| [ship-clean-code](ship-clean-code/) | Apply clean code principles when writing, reviewing, or refactoring code. Covers naming, functions, classes, error handling, and formatting for Python, TypeScript/JavaScript, and Java. |
| [ship-tested-code](ship-tested-code/) | Apply testing best practices when writing or reviewing tests. Covers test design, TDD, test strategy, mocking, integration testing, and flaky-test management for Python, TypeScript/JavaScript, and Java. |
| [ship-debugged-code](ship-debugged-code/) | Apply systematic debugging practices when investigating, isolating, and fixing bugs. Covers root-cause analysis, hypothesis-driven debugging, logging, observability, and regression prevention for Python, TypeScript/JavaScript, and Java. |
| [ship-reviewed-prs](ship-reviewed-prs/) | Perform a thorough, multi-persona pull-request review (senior engineer, senior security, senior infra/SRE, conditional senior data engineer, plus test-coverage signal). Reads existing PR comment threads and suppresses already-resolved or won't-fix findings. Computes a deterministic APPROVE / REQUEST_CHANGES / COMMENT decision and submits via `gh` CLI — interactive in local mode, fully automated in CI. |

## Installation

See [Installing Skills](../docs/installing-skills.md) for setup instructions.

## Creating a New Skill

1. Create a new directory under `skills/` with your skill name
2. Copy a template from [templates/](../templates/)
3. Customize the `SKILL.md` frontmatter and instructions
4. Test it in Claude Code with `/skill-name`
5. Submit a PR
