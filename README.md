# ship-code

> Ship better code with AI. An open-source collection of skills, agents, and workflows for AI-assisted software development.

Built on the [Agent Skills open standard](https://agentskills.io) and the Claude Code Skills 2.0 format.

## Featured Skill: ship-clean-code

Write cleaner, more maintainable code across Python, TypeScript/JavaScript, and Java. Combines established clean code principles with modern best practices.

**What it does:**
- **Writing mode** — Silently applies clean code principles when generating code
- **Review mode** — Produces structured code reviews with priority-ranked findings (P1-Bugs through P7-Style)
- **Language-aware** — Auto-detects Python, TypeScript, or Java and loads language-specific idioms

**What it covers:**
- 12 core principles (naming, functions, classes, SRP, error handling, DRY, and more)
- 66 cataloged code smells with detection and fix guidance
- Logging & observability, testing best practices, quality gates
- Before/after examples for each language
- Pragmatism guidelines (won't rewrite code you didn't ask it to touch)

## Installation

### Option 1: Add as a marketplace (recommended — get all current and future skills)

This repo is a Claude Code plugin marketplace. Add it once and get access to all skills — including new ones as they're released:

```bash
# In Claude Code, run:
/plugin marketplace add ship-it-ops/ship-code

# Then install any skill from the marketplace:
/plugin install ship-clean-code@ship-code

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
# Install to your current project
npx skills add ship-it-ops/ship-code --skill ship-clean-code

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
  └── marketplace.json               — Marketplace catalog (add via /plugin marketplace add)
plugins/                             — Plugin-packaged skills (for marketplace distribution)
  └── ship-clean-code/               — Plugin wrapper (symlinks to skills/)
skills/                              — Standalone SKILL.md files (for manual / npx install)
  └── ship-clean-code/               — Clean code skill
      ├── SKILL.md                   — Core skill (12 principles, review format, pragmatism rules)
      ├── reference.md               — Detailed rules (naming, functions, classes, errors, testing, logging)
      ├── reference-smells.md        — 66 code smells checklist with detection & fixes
      ├── lang-python.md             — Python idioms (type hints, async, pytest, common traps)
      ├── lang-typescript.md         — TypeScript/JS idioms (type safety, React, Jest/Vitest)
      ├── lang-java.md               — Java idioms (records, virtual threads, JUnit 5, Spring)
      └── examples/                  — Before/after code transformations
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
