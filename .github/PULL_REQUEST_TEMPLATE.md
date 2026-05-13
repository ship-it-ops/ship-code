<!--
Thanks for contributing to ship-code!

CI runs five validation jobs on every PR (see .github/workflows/validate-skills.yml).
You can run them locally before pushing:

  python3 scripts/validate-skills.py    # structure & frontmatter
  python3 scripts/check-skill-links.py  # relative-link integrity
  npx --yes markdownlint-cli2           # markdown style
-->

## Summary

<!-- 1-3 sentences describing what this PR changes and why. -->

## Type of change

- [ ] New skill
- [ ] Modification to an existing skill
- [ ] Documentation / examples
- [ ] CI / tooling
- [ ] Other (describe):

## If adding a new skill

- [ ] `skills/<name>/SKILL.md` has YAML frontmatter with `name` and `description`
- [ ] `name` in frontmatter matches the directory name (skill discovery requires this)
- [ ] `SKILL.md` is under 500 lines (detail belongs in `reference.md`)
- [ ] Per-file symlinks created under `plugins/<name>/skills/<name>/` (not a single directory symlink — that layout is broken for discovery)
- [ ] `plugins/<name>/.claude-plugin/plugin.json` created with matching `name` and `version`
- [ ] Entry added to `.claude-plugin/marketplace.json` with description, keywords, category
- [ ] Skill added to `.claude-plugin/plugin.json` `skills` array
- [ ] `skills/README.md` and root `README.md` updated to list the new skill
- [ ] Sibling SKILL.md files' "Related Skills" sections cross-link the new skill (when applicable)

## If modifying an existing skill

- [ ] Bumped `version` in `plugins/<name>/.claude-plugin/plugin.json` AND `.claude-plugin/marketplace.json` (they must match)
- [ ] Any new files under `skills/<name>/` also added as symlinks under `plugins/<name>/skills/<name>/`
- [ ] `SKILL.md` still under 500 lines

## Validation

CI will run automatically. To run locally:

```bash
python3 scripts/validate-skills.py --verbose
python3 scripts/check-skill-links.py
npx --yes markdownlint-cli2
```

- [ ] CI passes on this PR

## Test plan

<!-- How did you verify this works? At minimum, invoke the affected skill in Claude Code and confirm output. -->

- [ ] Invoked the affected skill(s) and verified the output matches expectations
- [ ] Verified the change doesn't break sibling skills' "Related Skills" cross-links
