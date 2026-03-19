# Examples

Usage examples and integration guides showing how to use ship-code skills in real projects.

## Integrations

Guides for using ship-code skills with different AI coding tools:

| Tool | Guide | Description |
|------|-------|-------------|
| [Claude Code](claude-code/) | [README](claude-code/README.md) | Setup, usage examples, team customization, combining with linters |
| [Cursor](cursor/) | [README](cursor/README.md) | Using skills as Cursor Rules, setup, differences from Claude Code |

## Quick Start

### Claude Code

```bash
# One-command install via npx
npx skills add ship-it-ops/ship-code --skill ship-clean-code

# Use it — auto-invokes when writing Python/TS/Java code
claude "write a user service in Python"

# Or invoke explicitly for a review
claude "/ship-clean-code review src/app.py"
```

### Cursor

```bash
# One-command install via npx
npx skills add ship-it-ops/ship-code --skill ship-clean-code -a cursor
```

### Any agent (Claude Code, Cursor, Codex, etc.)

```bash
# Auto-detects all installed agents and installs to each
npx add-skill ship-it-ops/ship-code --skill ship-clean-code
```

See the individual integration guides for manual installation and full details.
