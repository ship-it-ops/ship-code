# Writing Skills

A complete guide to creating skills using the Skills 2.0 format.

## Anatomy of a Skill

A skill is a directory containing a `SKILL.md` file and optional supporting files:

```text
my-skill/
├── SKILL.md              # Entry point — frontmatter + instructions
├── reference.md          # Detailed docs (loaded on demand)
├── examples.md           # Example inputs/outputs
└── scripts/
    └── helper.sh         # Executable scripts
```

## SKILL.md Format

Every `SKILL.md` starts with YAML frontmatter between `---` markers, followed by markdown instructions:

```yaml
---
name: my-skill
description: What this skill does and when to use it
---

Your instructions here...
```

## Frontmatter Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | directory name | Slash command name (lowercase, hyphens, max 64 chars) |
| `description` | string | — | When to use this skill. Claude uses this for auto-invocation |
| `disable-model-invocation` | bool | `false` | Set `true` to prevent Claude from auto-invoking |
| `user-invocable` | bool | `true` | Set `false` to hide from the `/` menu |
| `allowed-tools` | string | — | Comma-separated tools granted without permission prompts |
| `model` | string | — | Pin to a specific model (e.g., `claude-sonnet-4-6`) |
| `context` | string | — | Set to `fork` to run in an isolated subagent |
| `agent` | string | — | Subagent type when using `context: fork` (e.g., `Explore`, `Plan`) |
| `argument-hint` | string | — | Autocomplete hint shown to users (e.g., `[filename]`) |

## Writing Good Descriptions

The `description` field is critical — Claude uses it to decide when to auto-invoke your skill.

**Good:**
```yaml
description: Review code for bugs, security vulnerabilities, and quality issues. Use when reviewing PRs, changed files, or before merging.
```

**Bad:**
```yaml
description: Code review skill
```

Include keywords users would naturally say and explain both what the skill does AND when to use it.

## Dynamic Content

### Arguments

Access user-provided arguments with `$ARGUMENTS`:

```yaml
---
name: fix-issue
description: Fix a GitHub issue by number
argument-hint: "[issue-number]"
---

Fix GitHub issue $ARGUMENTS following our coding standards.
```

Positional arguments: `$0` or `$ARGUMENTS[0]`, `$1` or `$ARGUMENTS[1]`, etc.

### Shell Commands

Inject live data with `` !`command` `` — executes before Claude sees the content:

```yaml
---
name: review-pr
description: Review the current pull request
context: fork
allowed-tools: Bash(gh *)
---

## PR Context
- Diff: !`gh pr diff`
- Comments: !`gh pr view --comments`

Review this PR for issues...
```

### Built-in Variables

- `${CLAUDE_SESSION_ID}` — Current session ID
- `${CLAUDE_SKILL_DIR}` — Path to the skill's directory

## Skill Types

### Reference Skills (Background Knowledge)

Provide conventions, patterns, or domain knowledge that Claude applies automatically:

```yaml
---
name: api-conventions
description: API design patterns and conventions for this codebase
---

When writing API endpoints:
- Use RESTful naming
- Return consistent error formats
- Include request validation
```

### Task Skills (Explicit Actions)

Step-by-step instructions invoked manually with `/skill-name`:

```yaml
---
name: deploy
description: Deploy the application to production
disable-model-invocation: true
argument-hint: "[environment]"
---

Deploy to $ARGUMENTS:
1. Run the test suite
2. Build the application
3. Push to the deployment target
```

### Agent Skills (Isolated Execution)

Run in a forked subagent for complex, multi-step tasks:

```yaml
---
name: deep-review
description: Thorough code review with architecture analysis
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
---

Perform a deep review of the codebase:
1. Identify architectural patterns
2. Find potential issues
3. Suggest improvements
```

## Where Skills Load From

Priority order (highest first):

| Level | Path | Scope |
|-------|------|-------|
| Enterprise | Managed settings | Organization-wide |
| Personal | `~/.claude/skills/<name>/SKILL.md` | All your projects |
| Project | `.claude/skills/<name>/SKILL.md` | This project only |

## Tips

- Keep `SKILL.md` under 500 lines — move details to supporting files
- Use `allowed-tools` to grant just the permissions needed
- Set `disable-model-invocation: true` for anything with side effects
- Use `context: fork` for skills that do heavy exploration or research
- Test with both manual invocation (`/skill-name`) and auto-invocation
