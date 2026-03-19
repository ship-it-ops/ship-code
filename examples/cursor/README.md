# Using ship-code Skills with Cursor

## Setup

Cursor supports custom instructions through its Rules system. You can use ship-code skills as Cursor Rules.

### 1. Install the skill

```bash
# Quickest — npx with Cursor target
npx skills add ship-it-ops/ship-code --skill ship-clean-code -a cursor

# Or npx add-skill (auto-detects Cursor)
npx add-skill ship-it-ops/ship-code --skill ship-clean-code

# Or manually copy into Cursor Rules
mkdir -p your-project/.cursor/rules
cp skills/ship-clean-code/SKILL.md your-project/.cursor/rules/ship-clean-code.md
```

### 2. Add supporting files

For the full experience, copy the reference files too:

```bash
# Copy all supporting files
cp skills/ship-clean-code/reference.md your-project/.cursor/rules/ship-clean-code-reference.md
cp skills/ship-clean-code/reference-smells.md your-project/.cursor/rules/ship-clean-code-smells.md

# Copy the language-specific file for your project
cp skills/ship-clean-code/lang-python.md your-project/.cursor/rules/ship-clean-code-python.md
# or
cp skills/ship-clean-code/lang-typescript.md your-project/.cursor/rules/ship-clean-code-typescript.md
# or
cp skills/ship-clean-code/lang-java.md your-project/.cursor/rules/ship-clean-code-java.md
```

### 3. Alternative: Use .cursorrules file

You can also paste the core principles from `SKILL.md` into your project's `.cursorrules` file:

```bash
# Append the skill to your existing .cursorrules
cat skills/ship-clean-code/SKILL.md >> your-project/.cursorrules
```

## Usage in Cursor

Once installed as a Rule, Cursor will automatically apply the clean code principles when:

- **Composing code** in the editor (Cmd+K / Ctrl+K)
- **Chatting** about code in the sidebar
- **Generating** new files or functions

### Asking for a review

In Cursor Chat, you can ask:

```
Review this file for code quality issues, using the priority hierarchy:
bugs > security > error handling > testability > maintainability > readability
```

### Refactoring

Select code and use Cmd+K:

```
Refactor this to follow clean code principles — small functions,
clear names, proper error handling
```

## Differences from Claude Code

| Feature | Claude Code | Cursor |
|---------|-------------|--------|
| Auto-invocation | Skill triggers automatically | Rule always loaded |
| Slash commands | `/ship-clean-code` | Not available |
| Reference loading | Loads files on demand | All rules loaded at once |
| Team overrides | Separate overrides file | Edit the rule directly |

## Tips

- Only copy the language file relevant to your project — loading all three adds unnecessary context
- Keep the core `SKILL.md` content in your rules; add reference files only if you want deeper reviews
- Cursor's context window is smaller than Claude Code's, so prefer the compact `SKILL.md` over the full `reference.md` when possible
