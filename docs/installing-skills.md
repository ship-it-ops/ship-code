# Installing Skills

How to use ship-code skills in your projects.

## Marketplace (recommended — get all skills + auto-updates)

This repo is a Claude Code plugin marketplace. Add it once and get access to all current and future skills:

```bash
# In Claude Code:
/plugin marketplace add ship-it-ops/ship-code

# Install a skill:
/plugin install ship-clean-code@ship-code

# Update when new skills or improvements are released:
/plugin marketplace update ship-code
```

### Team setup

Add to your project's `.claude/settings.json` so teammates get prompted to install automatically:

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

## Quick Install (npx)

The fastest way to install a skill — no cloning required:

```bash
# Using Vercel's skills CLI (recommended)
npx skills add ship-it-ops/ship-code --skill ship-clean-code

# Or using add-skill (auto-detects all your agents)
npx add-skill ship-it-ops/ship-code --skill ship-clean-code
```

### Install globally (all projects)

```bash
npx skills add ship-it-ops/ship-code --skill ship-clean-code -g
```

### Install to specific agents

```bash
# Claude Code only
npx skills add ship-it-ops/ship-code --skill ship-clean-code -a claude-code

# Multiple agents at once
npx add-skill ship-it-ops/ship-code --skill ship-clean-code -a claude-code -a cursor

# Non-interactive (dotfiles / CI)
npx add-skill ship-it-ops/ship-code --skill ship-clean-code -g -y
```

## Manual Installation

### Per-Project

Copy a skill directory into your project's `.claude/skills/` folder:

```bash
# From the ship-code repo
cp -r skills/ship-clean-code/ /path/to/your-project/.claude/skills/ship-clean-code/
```

The skill is now available only in that project.

### Global

Copy a skill to your personal skills directory to make it available across all projects:

```bash
mkdir -p ~/.claude/skills
cp -r skills/ship-clean-code/ ~/.claude/skills/ship-clean-code/
```

### Symlink (auto-update with git pull)

```bash
# Clone the repo somewhere permanent
git clone https://github.com/ship-it-ops/ship-code.git ~/ship-code

# Symlink globally
mkdir -p ~/.claude/skills
ln -s ~/ship-code/skills/ship-clean-code/ ~/.claude/skills/ship-clean-code
```

### Direct download (no clone, no npm)

```bash
mkdir -p your-project/.claude/skills/ship-clean-code
curl -sL https://github.com/ship-it-ops/ship-code/archive/refs/heads/main.tar.gz \
  | tar xz --strip-components=3 -C your-project/.claude/skills/ship-clean-code \
  "ship-code-main/skills/ship-clean-code"
```

## Verifying Installation

1. Open Claude Code in your project
2. Type `/` to see available skills — your installed skill should appear
3. Invoke it: `/ship-clean-code`

Or verify from the command line:

```bash
ls ~/.claude/skills/ship-clean-code/SKILL.md 2>/dev/null \
  || ls .claude/skills/ship-clean-code/SKILL.md 2>/dev/null \
  && echo "Installed!" || echo "Not found"
```

## Updating Skills

```bash
# If installed via npx — just re-run the install command
npx skills add ship-it-ops/ship-code --skill ship-clean-code -g -y

# If installed via symlink — just pull
cd ~/ship-code && git pull

# If installed via copy — re-copy
cp -r skills/ship-clean-code/ ~/.claude/skills/ship-clean-code/
```

## Uninstalling

```bash
# Remove from project
rm -rf /path/to/your-project/.claude/skills/ship-clean-code/

# Remove globally
rm -rf ~/.claude/skills/ship-clean-code/
```
