# Contributing to ship-code

Thanks for your interest in contributing! This guide covers how to add or modify skills and what CI will enforce on your PR.

## How to Contribute

1. **Fork** the repository
2. **Create a branch** for your contribution (`git checkout -b add-my-skill`)
3. **Make your changes** following the guidelines below
4. **Run validation locally** (see below) before pushing
5. **Submit a pull request** — the PR template will walk you through the checklist

## What to Contribute

- **New skills** — full `SKILL.md`-based skills (place in `skills/<name>/`)
- **Improvements** — enhancements to existing skills (bump the version)
- **Examples** — integration guides and usage examples (place in `examples/`)
- **Docs** — guides, tutorials, and reference material (place in `docs/`)
- **CI / tooling** — improvements to the validation scripts under `scripts/` or workflows under `.github/workflows/`

## Skill Structure

Skills live at `skills/<skill-name>/` — one flat directory per skill, no nested category subfolders.

```text
skills/<skill-name>/
├── SKILL.md                # Required — frontmatter + instructions (max 500 lines)
├── reference.md            # Recommended — detailed rules and rubrics
├── reference-*.md          # Optional — additional reference files (per-persona, per-topic)
├── lang-python.md          # Optional — Python-specific idioms
├── lang-typescript.md      # Optional — TypeScript/JavaScript-specific idioms
├── lang-java.md            # Optional — Java-specific idioms
├── overrides.example.md    # Recommended — template for team overrides
├── examples/               # Recommended — worked examples, review output samples
└── tests/                  # Recommended — self-test fixtures (input + expected-output)
```

### Naming

- Use `kebab-case` for directory names: `ship-clean-code`, not `ShipCleanCode` or `ship_clean_code`
- The directory name MUST match the `name` field in `SKILL.md` frontmatter (skill discovery breaks otherwise)
- Be descriptive: prefer `ship-reviewed-prs` over `pr-reviewer`

### SKILL.md Frontmatter

Required:

```yaml
---
name: my-skill              # Must match directory name
description: >              # 50-2000 chars, used for auto-invocation matching
  What this skill does and when to use it. Be specific — Claude uses this
  to decide when to auto-invoke. Include keywords users would naturally say.
---
```

Optional:

```yaml
allowed-tools: Read, Grep, Glob, Bash(gh *)  # comma-separated, supports tool patterns
disable-model-invocation: true               # for skills with side effects (gh, deploys, commits)
user-invocable: false                        # background-only knowledge skills
context: fork                                # run in isolated subagent
agent: Explore                               # subagent type (requires context: fork)
model: claude-sonnet-4-6                     # pin to a specific model
argument-hint: "[pr-number-or-url]"          # autocomplete hint for users
```

CI rejects unknown frontmatter keys; see `scripts/validate-skills.py` for the allowed set.

### SKILL.md Body

- Keep under 500 lines (CI fails over this). Move detail into `reference.md` and other supporting files.
- Document a Mode Detection section if the skill has multiple modes (writing/review/investigation).
- Structure follows the established sibling pattern: Purpose → Quickstart → Mode Detection → Core Principles (12) → Priority Hierarchy → Pragmatism → Language Routing → Review Output Format → Related Skills → Team Overrides → Reference Loading.
- Use relative paths to reference supporting files (`reference.md`, not `${SKILL_DIR}/reference.md`).

## Plugin Wiring (required for marketplace distribution)

Every skill must have a matching plugin under `plugins/<name>/`. The layout uses per-file symlinks pointing back to `skills/<name>/`:

```text
plugins/<skill-name>/
├── .claude-plugin/
│   └── plugin.json                 # {name, description, version}
└── skills/<skill-name>/             # NOTE the doubled <skill-name> — required
    ├── SKILL.md       -> ../../../../skills/<skill-name>/SKILL.md
    ├── reference.md   -> ../../../../skills/<skill-name>/reference.md
    ├── ... (one per-file symlink for every source file)
    ├── examples       -> ../../../../skills/<skill-name>/examples
    └── tests          -> ../../../../skills/<skill-name>/tests
```

> **CRITICAL:** Use per-file symlinks. Do NOT replace `plugins/<name>/skills/<name>/` with a single directory symlink at `plugins/<name>/skills/` — that collapses the path level and breaks skill discovery. CI catches this regression in the `plugin-symlinks` job.

After creating the plugin, add an entry to:

1. **`.claude-plugin/marketplace.json`** — the marketplace catalog with description, version, keywords, category. Bump the top-level `version` if this is a notable release.
2. **`.claude-plugin/plugin.json`** — the root skill list (`skills` array). Append `./skills/<name>`.

Plugin version MUST match between `plugins/<name>/.claude-plugin/plugin.json` and the corresponding `marketplace.json` entry. CI verifies this.

### Slash Commands (optional)

A skill is only auto-invocable if its `SKILL.md` description matches what the user is asking. If you want users to be able to invoke the skill explicitly with `/<name>` (or run it from a non-interactive CI job that types the literal `/<name>` as its prompt), you also need a slash command file:

```text
plugins/<skill-name>/
├── .claude-plugin/plugin.json
├── commands/
│   └── <skill-name>.md         # The slash command — body is the prompt
└── skills/<skill-name>/...     # The skill (as documented above)
```

The command body should delegate to the skill rather than reimplement it:

```markdown
---
description: One-line summary shown in the slash-command picker.
argument-hint: "<arg-1> [flags]"
allowed-tools: Skill, Bash, Read, Grep, Glob
---

Run the `<skill-name>` skill with arguments: $ARGUMENTS
```

Important: `allowed-tools` on the *command* is the binding constraint at runtime — the skill's own `allowed-tools` does not expand it. If the skill needs `Task` (subagents) or shell beyond `gh`/`git`, the command must declare them too. Skills marked `disable-model-invocation: true` are reachable *only* via a slash command, so the `commands/` file is mandatory for those.

For skills that require mode detection, subagent orchestration, or any non-trivial delegation logic, the minimal one-line body above is not enough — an LLM handed only that sparse body may attempt to inline-implement the skill instead of loading it. See [`review-pr.md`](plugins/ship-reviewed-prs/commands/review-pr.md) for a complete template that passes arguments through verbatim, instructs Claude to invoke the skill via the `Skill` tool, and honors the skill's CI-vs-local mode detection.

## Validation

CI runs six jobs on every PR (`.github/workflows/validate-skills.yml`):

| Job | What it checks |
|---|---|
| `structure` | Frontmatter parses, `name` matches directory, SKILL.md under 500 lines, plugin layout intact, marketplace consistency, no `${SKILL_DIR}` leakage, fixture parity |
| `links` | Every relative markdown link in `skills/**/*.md` resolves on disk |
| `markdown` | `markdownlint-cli2` against `.markdownlint-cli2.yaml` (real correctness issues, not stylistic ones) |
| `json` | Every `.json` file in the repo is valid JSON |
| `yaml` | Every `.yml`/`.yaml` file is valid YAML |
| `plugin-symlinks` | `plugins/<name>/skills/<name>/SKILL.md` resolves for every plugin |

Run locally before pushing:

```bash
# Structure + frontmatter + marketplace
python3 scripts/validate-skills.py --verbose

# Internal link integrity
python3 scripts/check-skill-links.py

# Markdown style
npx --yes markdownlint-cli2
```

If you're using a Python without PyYAML available (some clean envs), install it: `pip install pyyaml`.

The validator is intentionally strict on layout (CI is the easiest place to catch a broken plugin symlink before it ships to users) and lenient on prose style (skills are dense and tight spacing is intentional).

## Versioning

Skills follow semver (MAJOR.MINOR.PATCH):

- **PATCH** — typo fixes, prose clarifications, formatting
- **MINOR** — new examples, new override knobs, additional finding IDs that don't change existing behavior
- **MAJOR** — finding-ID renumbering, decision-matrix changes, breaking changes to output format

When you bump the skill's version, bump it in BOTH `plugins/<name>/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`. CI verifies they match.

## Quality

- Test your skill before submitting — invoke it with `/<skill-name>` in Claude Code against a representative input.
- Include before/after examples and at least one self-test fixture under `tests/`.
- Document any prerequisites or dependencies in `SKILL.md`.

## Commits

- Write clear, concise commit messages
- One logical change per commit
- For skill changes, prefix the commit subject with the skill name: `ship-clean-code: tighten N3 rule for ML notebooks`

## Code of Conduct

Be respectful, constructive, and inclusive. We're all here to build better tools together.

## Questions?

Open an issue if you have questions or need help getting started.
