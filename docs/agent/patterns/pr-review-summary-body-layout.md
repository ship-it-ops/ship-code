---
name: pr-review-summary-body-layout
description: Canonical markdown layout the ship-reviewed-prs skill emits as the review body — verdict label, three tables, conditional sections
metadata:
  type: pattern
type: pattern
status: active
created: 2026-05-26
updated: 2026-05-26
author: claude-session-2026-05-26
tags: [ship-reviewed-prs, output-format, summary-body]
importance: core
---

# `ship-reviewed-prs` summary-body layout

## When to Use

Any time you emit, parse, or modify the markdown body of a `ship-reviewed-prs` review. The shape is fixed; deviating from it counts as a regression and will be flagged by the verification greps below.

## Implementation

The canonical template lives in `skills/ship-reviewed-prs/SKILL.md` under `## Review Output Format` → `### Summary body (posted as review body)`. Worked examples in `skills/ship-reviewed-prs/examples/review-output-example.md` and every `tests/fixture-*/expected-output.md`.

Shape, in order:

1. Optional bot-identity prefix (only when CI override is set).
2. `## PR Review — #<n> \`<title>\`` header (em dash, backticks around title).
3. `**Verdict: <label>**` bold paragraph (not a heading). Label ∈ {`LGTM`, `LGTM (with caveats)`, `Changes requested`, `Comment`}.
4. `### Confidence` — prose, 2-4 sentences.
5. `### Personas activated` — six-row table SE / SC / IN / DA / FE / TS, status ∈ {`✅ active`, `✅ pass`, `⏭ skip`}.
6. `### Findings` — three-row table Must-fix (P1-2) / Should-fix (P3-5) / Nits (P6-7), `Count` + `Inline anchors`.
7. `### Findings without inline anchor` (conditional — only when ≥1 anchorless finding exists).
8. `### Delegations` (conditional — omitted when empty).
9. `### Comment lifecycle` — six-row table Resolved / Won't-fix / Outdated / Possibly addressed / Stale / Open + trailing `Suppressed N findings...` line. ALWAYS rendered.
10. `### Stale comments needing reply` (conditional — omitted when empty).
11. `### What's solid` — substantive bullets, always present.

Always-rendered sections: Verdict line, Confidence, Personas activated, Findings, Comment lifecycle, What's solid. Everything else is conditional on having content.

## Examples

- Clean LGTM: `skills/ship-reviewed-prs/tests/fixture-4-clean-approve-pr/expected-output.md` and `fixture-6-frontend-clean/expected-output.md`.
- LGTM (with caveats): `fixture-7-suggestions-only-approve/expected-output.md` (Nit-tier finding) and `fixture-8-pending-ci-approve/expected-output.md` (pending CI caveat).
- Changes requested: `fixture-1-security-bug-pr`, `fixture-2-migration-pr`, `fixture-5-frontend-pr`.
- Comment: `fixture-3-stale-resolved-pr/expected-output.md` (open thread blocks LGTM).

## Gotchas

- **"Lifecycle counts" is not a valid heading.** The severity-count surface is `### Findings`; the thread-state surface is `### Comment lifecycle`. Conflating them under a single "lifecycle" heading is the original freelance shape this layout explicitly rejected — see [[pr-review-table-driven-summary-format]].
- **Verdict is a bold paragraph, not a heading.** `### Decision:` heading is gone from the spec; any reviewer model that re-emits it has regressed.
- **Always six rows in Personas activated**, even when a persona is skipped. Consistent shape across PRs lets reviewers scan multiple reviews comparably.
- **`✅ pass` ≠ `⏭ skip`.** `pass` means the persona ran and produced zero findings; `skip` means it didn't run at all (conditional trigger missed, or disabled by override). Mixing these loses the "we looked" signal.
- **Friendly label in markdown, formal keyword in JSON.** The JSON `decision` field is still `APPROVE` / `REQUEST_CHANGES` / `COMMENT`. The new `verdict_label` field carries the friendly enum (`LGTM` / `LGTM_WITH_CAVEATS` / `CHANGES_REQUESTED` / `COMMENT`). Exit codes follow `decision`, not `verdict_label`.
- **Inline anchors use `<persona-id> path:line` form**, separated by ` · ` (middle dot, spaces). If a cell exceeds ~5 anchors, switch to `<br>` line breaks; if it would exceed ~250 chars, truncate and append ` · +N more`. Full list always available in `--json`.
- **No `A11y` persona.** A11y concerns belong to `FE`. Watch for reviewer models freelancing an `A11y` row in the Personas table.

## Verification

Inside `skills/ship-reviewed-prs/`:

```bash
grep -rn "What's Good"        --include="*.md" .  # expect 0
grep -rn "^### Decision:"     --include="*.md" .  # expect 0
grep -rn "Lifecycle counts"   --include="*.md" .  # expect 0 (allowed: a single "watch for this misuse" line in tests/README.md)
grep -rn "Personas activated" --include="*.md" .  # expect ≥9 (SKILL.md spec + 8 fixtures + every example)
```
