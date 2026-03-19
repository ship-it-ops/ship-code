# Using ship-code Skills with Claude Code

## Setup

### 1. Install a skill

```bash
# Quickest — one command via npx
npx skills add ship-it-ops/ship-code --skill ship-clean-code

# Or install globally (all projects)
npx skills add ship-it-ops/ship-code --skill ship-clean-code -g

# Or manually copy into your project
cp -r skills/ship-clean-code/ your-project/.claude/skills/ship-clean-code/
```

See the full [installation guide](../../docs/installing-skills.md) for all options (symlink, curl, multi-agent).

### 2. Verify installation

Open Claude Code in your project and type `/` — you should see `ship-clean-code` in the skill list.

## Usage Examples

### Writing code (automatic)

The skill auto-invokes when you write production Python, TypeScript, or Java code:

```
> write a user registration service in Python with email validation

Claude will produce clean code with:
- Descriptive names (no single-letter variables)
- Small, focused functions
- Proper error handling (no bare except, no None returns)
- Type hints
- Named constants instead of magic values
```

### Code review (explicit)

```
> /ship-clean-code review src/services/payment.py

Claude produces a structured report:
- Critical (P1-BUG, P2-SEC) — must fix before merge
- Important (P3-ERR, P4-TEST, P5-MAINT) — should fix
- Suggestions (P6-READ, P7-STYLE) — improve when convenient
- What's Good — positive observations
```

### Refactoring

```
> refactor this function to follow clean code principles

Claude will:
- Extract long functions into smaller ones
- Rename unclear variables
- Remove dead code and unnecessary comments
- Apply language-specific idioms
```

### Reviewing a PR diff

```
> review the changes in this PR for code quality

Claude reads the diff and applies the priority hierarchy:
bugs > security > error handling > testability > maintainability > readability > style
```

## Team Customization

Create an overrides file to adapt the skill to your team's conventions:

```bash
cat > your-project/.claude/ship-clean-code-overrides.md << 'EOF'
# Ship Clean Code Overrides

## Naming
- We use `I` prefix for interfaces in TypeScript (e.g., `IUserService`)
- Database models use `snake_case` even in TypeScript

## Functions
- API route handlers may exceed 30 lines when they contain validation logic
- We allow 4 arguments for constructor injection

## Testing
- We use `jest` not `vitest`
- Minimum branch coverage is 70%, not 80%

## Disabled Rules
- Skip magic number check for HTTP status codes (200, 404, 500)
- Allow `any` type in test files only
EOF
```

## Combining with Other Tools

### With ESLint/Prettier

The skill focuses on design-level quality (P1-P5) that linters can't catch. Let your linter handle formatting (P7) and basic style — the skill won't duplicate that work.

### With pre-commit hooks

```bash
# .pre-commit-config.yaml
# Use linters for syntax, use /ship-clean-code for design reviews
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff        # catches syntax issues
      - id: ruff-format # handles formatting
# Then use /ship-clean-code in your PR review process for deeper analysis
```

## Tips

- The skill is most valuable during PR reviews — it catches design issues linters miss
- Use `/ship-clean-code` explicitly for thorough reviews; let it auto-invoke for writing
- Start with P1-P3 findings only (first month), then expand to full P1-P7
- Create an overrides file early — it prevents friction when the skill conflicts with your conventions
