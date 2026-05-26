---
type: status
status: active
created: 2026-05-25
updated: 2026-05-25
author: claude-session-2026-05-25
tags: [ship-reviewed-prs, pr-4, decision-matrix, dogfood]
importance: standard
branch: test-branch
agent: claude-session-2026-05-25
---

# In flight on PR #4: relaxed APPROVE matrix + pr-review workflow tightening

## Scope

Branch `test-branch` → PR #4 on `ship-it-ops/ship-code`. Five commits stacked:

- `5b38d9e` — docs(contributing): point readers at `review-pr.md` as a full command template
- `b12dbce` — docs(contributing): convert `review-pr.md` reference to a markdown link
- `fac022d` — ship-reviewed-prs: relax APPROVE gate for suggestions and pending CI (matrix change + fixtures 7–8)
- `6fc00bb` — ship-reviewed-prs: revert version bump (held at 1.1.0 per user; NOT releasing v2)
- (uncommitted, local) — `.github/workflows/pr-review.yml`: flip `plugin_marketplaces` from URL to `.` so PRs self-review against their own plugin changes

Touches: `CONTRIBUTING.md`, `skills/ship-reviewed-prs/SKILL.md`, `skills/ship-reviewed-prs/reference.md`, `skills/ship-reviewed-prs/tests/{README.md,fixture-7-suggestions-only-approve/*,fixture-8-pending-ci-approve/*}`, `.github/workflows/pr-review.yml`.

## Why

- Two real reviews on PR #4 demonstrated the "always-one-nitpick" trap in the conservative matrix.
- The user explicitly asked: *"Important stuff can warrant a comment, critical can warrant a deny."*

See [relaxed-approve-decision-matrix](../decisions/relaxed-approve-decision-matrix.md) and [pr-review-installs-plugin-from-pr-head](../decisions/pr-review-installs-plugin-from-pr-head.md).

## Verification status

- Local validators all pass (`validate-skills.py`, `check-skill-links.py`, `markdownlint-cli2`).
- The dogfood self-review on PR #4 does **not** yet exercise these changes, because the workflow file from main is still the URL-based install. The first PR to self-review with the new matrix + local install will be the one *after* PR #4 merges.

## Blocked on

User decision on:
- Whether to commit the local `pr-review.yml` change onto `test-branch` (and let it ride into main with PR #4) — staged but not committed per the "ask before committing" memory rule.

## Related

- [relaxed-approve-decision-matrix](../decisions/relaxed-approve-decision-matrix.md)
- [pr-review-installs-plugin-from-pr-head](../decisions/pr-review-installs-plugin-from-pr-head.md)
- [hidden-output-blocks-debugging](../scars/hidden-output-blocks-debugging.md) — `show_full_output: true` is currently on; reminder to revisit removing once stable.
