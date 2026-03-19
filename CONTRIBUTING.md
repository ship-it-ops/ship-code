# Contributing to ship-code

Thanks for your interest in contributing! Here's how to get started.

## How to Contribute

1. **Fork** the repository
2. **Create a branch** for your contribution (`git checkout -b add-my-skill`)
3. **Make your changes** following the guidelines below
4. **Submit a pull request**

## What to Contribute

- **Skills** — New `SKILL.md`-based skills (place in `skills/<category>/`)
- **Improvements** — Enhancements to existing skills
- **Examples** — Integration guides and usage examples (place in `examples/`)
- **Docs** — Guides, tutorials, and reference material (place in `docs/`)

## Skill Guidelines

### Structure

Every skill must follow the Skills 2.0 format:

```text
skills/<category>/skill-name/
├── SKILL.md              # Required — frontmatter + instructions
├── reference.md          # Optional — detailed reference material
├── examples.md           # Optional — example inputs/outputs
└── scripts/              # Optional — helper scripts
```

### Naming

- Use `kebab-case` for directory names
- Be descriptive: `code-review/` not `review1/`
- Place skills in the appropriate category (`coding/`, `testing/`, `debugging/`, `devops/`, `docs/`)

### SKILL.md Requirements

- Must include YAML frontmatter with at least `name` and `description`
- `description` should clearly state what the skill does AND when to use it
- Keep `SKILL.md` under 500 lines — use supporting files for detailed content
- Specify `allowed-tools` to limit tool access appropriately
- Set `disable-model-invocation: true` for skills with side effects (deploys, commits, etc.)

### Quality

- Test your skill before submitting (invoke it with `/skill-name` in Claude Code)
- Include examples of expected behavior
- Document any prerequisites or dependencies

### Commits

- Write clear, concise commit messages
- One logical change per commit

## Code of Conduct

Be respectful, constructive, and inclusive. We're all here to build better tools together.

## Questions?

Open an issue if you have questions or need help getting started.
