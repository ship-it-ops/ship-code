# ship-code

[![Validate Skills](https://github.com/ship-it-ops/ship-code/actions/workflows/validate-skills.yml/badge.svg)](https://github.com/ship-it-ops/ship-code/actions/workflows/validate-skills.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Ship better code with AI. An open-source collection of skills, agents, and workflows for AI-assisted software development.

Built on the [Agent Skills open standard](https://agentskills.io) and the Claude Code Skills 2.0 format. Every skill ships through six CI validation jobs (structure, frontmatter, plugin layout, marketplace consistency, links, markdown style) — see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Featured Skills

Four skills covering the lifecycle of production code — write it clean, prove it works, fix it when it breaks, and review the pull request before it merges. The first three follow the same architecture (writing/review modes with language-specific idioms for Python, TypeScript/JavaScript, and Java). The fourth orchestrates a multi-persona PR review and composes with the others via delegation.

### ship-clean-code

Write cleaner, more maintainable code across Python, TypeScript/JavaScript, and Java. Combines established clean code principles with modern best practices.

**What it covers:**
- 12 core principles (naming, functions, classes, SRP, error handling, DRY, and more)
- 66 cataloged code smells with detection and fix guidance
- Logging & observability, quality gates, language-specific idioms
- Priority-ranked review findings (P1-Bugs through P7-Style)
- Pragmatism guidelines (won't rewrite code you didn't ask it to touch)

### ship-tested-code

Write effective, maintainable tests and review existing ones for design, coverage, and flakiness.

**What it covers:**
- 12 core principles (test behavior not implementation, AAA, deterministic tests, mock at boundaries, etc.)
- 49 cataloged test smells across design, data, assertions, mocking, flakiness, naming, structure, coverage
- Test strategy by architecture (monolith, microservices, frontend), property-based and mutation testing
- Priority-ranked review findings (T1-Missing Coverage through T7-Assertions)
- Language-specific patterns (pytest fixtures, MSW, TestContainers, Pact, jqwik)

### ship-debugged-code

Investigate and resolve bugs systematically — hypothesis-driven, with regression tests as the deliverable.

**What it covers:**
- 12 core principles (reproduce first, bisect, change one thing at a time, never trust intermittents, etc.)
- Cataloged debugging anti-patterns (shotgun debugging, premature fixes, log spamming)
- Tools and techniques per language (pdb/breakpoint, Chrome DevTools, jdb/IntelliJ, profilers)
- Priority-ranked findings (D1-Cannot Reproduce through D7-Documentation)
- Regression-test-driven fixes — every confirmed bug ships with a test that fails before the fix

### ship-reviewed-prs

A senior-team review of every pull request — security, infra, data, and engineering perspectives in one pass, with comment-lifecycle awareness and a decisive verdict.

**What it covers:**
- Five personas (SE Senior Engineer, SC Senior Security Engineer, IN Senior Infra/SRE, DA Senior Data Engineer conditional, TS Test Reviewer delegation-only) with distinct rubrics that compose into a single priority-ordered review
- Six-state comment lifecycle (RESOLVED, OUTDATED, WONT_FIX, ADDRESSED, STALE, OPEN) — re-raised findings get suppressed silently, won't-fix markers are honored, "possibly addressed" is surfaced for human confirmation
- Deterministic decision matrix: APPROVE / REQUEST_CHANGES / COMMENT with no LLM negotiation
- Local mode with interactive confirmation gate; CI mode with full automation, exit codes for pipeline gating, `--json` output, and `ci_max_decision` override for teams whose policy forbids bot approvals
- Composes with the other three skills via a delegation table — naming/readability goes to `ship-clean-code`, test depth to `ship-tested-code`, root-cause to `ship-debugged-code`

## Installation

### Option 1: Add as a marketplace (recommended — get all current and future skills)

This repo is a Claude Code plugin marketplace. Add it once and get access to all skills — including new ones as they're released:

```bash
# In Claude Code, run:
/plugin marketplace add ship-it-ops/ship-code

# Then install any skill from the marketplace:
/plugin install ship-clean-code@ship-code
/plugin install ship-tested-code@ship-code
/plugin install ship-debugged-code@ship-code
/plugin install ship-reviewed-prs@ship-code

# To see all available skills:
/plugin marketplace list ship-code
```

To auto-update when we release new skills or improvements:
```bash
/plugin marketplace update ship-code
```

You can also configure your project to recommend this marketplace to your team. Add to `.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "ship-code": {
      "source": {
        "source": "github",
        "repo": "ship-it-ops/ship-code"
      }
    }
  }
}
```

### Option 2: npx (one command, single skill)

Using Vercel's [skills CLI](https://github.com/vercel-labs/skills):

```bash
# Install a single skill to your current project
npx skills add ship-it-ops/ship-code --skill ship-clean-code
npx skills add ship-it-ops/ship-code --skill ship-tested-code
npx skills add ship-it-ops/ship-code --skill ship-debugged-code
npx skills add ship-it-ops/ship-code --skill ship-reviewed-prs

# Install globally (available in all projects)
npx skills add ship-it-ops/ship-code --skill ship-clean-code -g

# Install to a specific agent (Claude Code, Cursor, Codex, etc.)
npx skills add ship-it-ops/ship-code --skill ship-clean-code -a claude-code
```

### Option 3: npx add-skill (multi-agent)

Using [add-skill](https://add-skill.org/) to install across multiple agents at once:

```bash
# Auto-detects your installed agents and installs to all of them
npx add-skill ship-it-ops/ship-code --skill ship-clean-code

# Install to specific agents
npx add-skill ship-it-ops/ship-code --skill ship-clean-code -a claude-code -a cursor

# Non-interactive (great for dotfiles / CI)
npx add-skill ship-it-ops/ship-code --skill ship-clean-code -g -y
```

### Option 4: Copy into your project

```bash
# Clone and copy
git clone https://github.com/ship-it-ops/ship-code.git
cp -r ship-code/skills/ship-clean-code/ your-project/.claude/skills/ship-clean-code/
```

### Option 5: Install globally (all projects)

```bash
git clone https://github.com/ship-it-ops/ship-code.git
mkdir -p ~/.claude/skills
cp -r ship-code/skills/ship-clean-code/ ~/.claude/skills/ship-clean-code/
```

### Option 6: Symlink for automatic updates

```bash
# Clone somewhere permanent
git clone https://github.com/ship-it-ops/ship-code.git ~/ship-code

# Symlink into your project (stays in sync with git pull)
ln -s ~/ship-code/skills/ship-clean-code/ your-project/.claude/skills/ship-clean-code

# Or symlink globally
mkdir -p ~/.claude/skills
ln -s ~/ship-code/skills/ship-clean-code/ ~/.claude/skills/ship-clean-code
```

### Option 7: Direct download (no clone, no npm)

```bash
# Download just the ship-clean-code skill using curl + tar
mkdir -p your-project/.claude/skills/ship-clean-code
curl -sL https://github.com/ship-it-ops/ship-code/archive/refs/heads/main.tar.gz \
  | tar xz --strip-components=3 -C your-project/.claude/skills/ship-clean-code \
  "ship-code-main/skills/ship-clean-code"
```

### Verify installation

```bash
# In Claude Code, type / and look for ship-clean-code
# Or run:
ls ~/.claude/skills/ship-clean-code/SKILL.md 2>/dev/null \
  || ls .claude/skills/ship-clean-code/SKILL.md 2>/dev/null \
  && echo "Installed!" || echo "Not found"
```

## Usage

Once installed, the skill works automatically in Claude Code:

```bash
# The skill auto-invokes when you write or review Python/TS/Java code
claude "write a user authentication service in Python"

# Explicitly invoke for a code review
claude "/ship-clean-code review src/services/payment.ts"

# Ask for clean code guidance
claude "review this file for code quality"
```

### Writing Mode (automatic)

When you ask Claude to write or modify Python, TypeScript, or Java code, the skill silently applies clean code principles — good naming, small functions, proper error handling, no magic numbers — without explaining itself unless you ask.

### Review Mode (explicit)

When you invoke `/ship-clean-code` or ask for a review, you get a structured report:

```
## Code Review: payment_service.py

### Critical (must fix before merge)
- [P1-BUG] Line 42: Off-by-one in pagination...
- [P2-SEC] Line 15: SQL injection via f-string...

### Important (should fix)
- [P3-ERR] Line 67: Bare except swallows all errors...
- [P4-TEST] Line 12: PaymentGateway hardcoded in constructor...

### Suggestions (improve when convenient)
- [P6-READ] Line 33: Variable `d` should be `discount_rate`...

### What's Good
- Clean separation between validation and processing logic...
```

### Team Customization

Create an overrides file to adapt rules to your team's conventions:

```bash
# Project-level overrides
cat > your-project/.claude/ship-clean-code-overrides.md << 'EOF'
# Clean Code Overrides

- We use Hungarian notation for COM interop classes (skip rule N6 in those files)
- Line length limit is 100, not 120
- We allow 4 function arguments for API handlers
EOF
```

## What's Inside

```text
.claude-plugin/                      — Plugin marketplace manifest
  ├── marketplace.json               — Marketplace catalog (add via /plugin marketplace add)
  └── plugin.json                    — Root plugin descriptor for the skills CLI
plugins/                             — Plugin-packaged skills (for marketplace distribution)
  ├── ship-clean-code/               — Plugin wrapper (symlinks to skills/ship-clean-code)
  ├── ship-tested-code/              — Plugin wrapper (symlinks to skills/ship-tested-code)
  ├── ship-debugged-code/            — Plugin wrapper (symlinks to skills/ship-debugged-code)
  └── ship-reviewed-prs/             — Plugin wrapper (symlinks to skills/ship-reviewed-prs)
skills/                              — Standalone SKILL.md directories (for manual / npx install)
  ├── ship-clean-code/               — Clean code skill (12 principles, 66 smells, P1-P7 review)
  │   ├── SKILL.md                   — Core skill (mode detection, review format, pragmatism)
  │   ├── reference.md               — Detailed rules by concern (10 sections)
  │   ├── reference-smells.md        — 66 code smells with detection & fixes
  │   ├── lang-{python,typescript,java}.md — Language idioms
  │   ├── overrides.example.md       — Team override template
  │   ├── examples/                  — Before/after code transformations
  │   └── tests/                     — Self-test fixtures (sample input + expected review)
  ├── ship-tested-code/              — Testing skill (12 principles, 49 smells, T1-T7 review)
  │   └── ... (same structure)
  ├── ship-debugged-code/            — Debugging skill (12 principles, D1-D7 review)
  │   └── ... (same structure)
  └── ship-reviewed-prs/             — PR review workflow (5 personas, lifecycle suppression, decision matrix)
      ├── SKILL.md                   — Workflow skill (disable-model-invocation, gh CLI integration)
      ├── reference.md               — Fetch protocol, merge logic, decision matrix, submission protocol
      ├── reference-personas.md      — Per-persona rubrics (SE, SC, IN, DA, TS)
      ├── reference-lifecycle.md     — Six-state classification, won't-fix markers, fingerprinting
      ├── lang-{python,typescript,java}.md — Per-language PR-review patterns
      ├── overrides.example.md       — Team override template (ci_max_decision, won't-fix markers, etc.)
      ├── examples/                  — Review-output samples, persona-delegation walkthrough, CI snippets
      └── tests/                     — Four self-test fixtures (security, migration, lifecycle, clean-approve)
templates/                           — Starter templates for creating new skills
docs/                                — Guides on writing, testing, and sharing skills
examples/                            — Integration examples for Claude Code, Cursor, etc.
```

## Skill Format (Skills 2.0)

Every skill is a directory with a `SKILL.md` entry point:

```text
skill-name/
├── SKILL.md              # Required — frontmatter + instructions (max 500 lines)
├── reference.md          # Optional — detailed docs Claude loads on demand
├── examples.md           # Optional — example inputs/outputs
└── scripts/              # Optional — helper scripts the skill can execute
```

`SKILL.md` uses YAML frontmatter to control behavior:

```yaml
---
name: skill-name
description: What this skill does. Claude uses this to decide when to auto-invoke.
allowed-tools: Read, Grep, Glob
---

Your skill instructions in markdown...
```

See [docs/writing-skills.md](docs/writing-skills.md) for the full guide.

## Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) before submitting a pull request.

### Adding a new skill

1. Create a new directory under `skills/` with your skill name
2. Copy a template from [templates/](templates/)
3. Customize the `SKILL.md` frontmatter and instructions
4. Add supporting reference files as needed
5. Test it in Claude Code with `/skill-name`
6. Submit a PR

## License

[MIT](LICENSE) -- Copyright (c) 2026 ship-it-ops
