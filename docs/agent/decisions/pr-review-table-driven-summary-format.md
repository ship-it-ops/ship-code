---
name: pr-review-table-driven-summary-format
description: Canonical PR-review summary body uses table-driven layout (Personas activated, Findings, Comment lifecycle) with LGTM-style friendly verdict labels
metadata:
  type: decision
type: decision
status: active
created: 2026-05-26
updated: 2026-05-26
author: claude-session-2026-05-26
tags: [ship-reviewed-prs, output-format, summary-body, verdict-labels]
importance: core
---

# PR-review summary body uses a table-driven layout

## Context

The `ship-reviewed-prs` skill posted reviews using a heading-driven summary body — `### Decision: ✅ APPROVE`, `### Critical`, `### Important`, `### Suggestions`, `### Comment lifecycle` (bullet line), `### What's Good`. On a clean APPROVE this rendered 7+ headings of `(none)` placeholders. A real review on `ship-it-design#57` was rendered by the model in a different table-driven shape (Personas activated table, Lifecycle counts table, "What's solid", `**Verdict: LGTM**`) which the user found materially better at a glance. That format was **not** in the spec at the time — it was model freelance.

## Decision

Adopt the table-driven layout as the canonical summary body. The new layout is:

- `## PR Review — #<n> \`<title>\`` (header)
- `**Verdict: <label>**` as a bold paragraph (not a heading), where `<label>` is one of `LGTM`, `LGTM (with caveats)`, `Changes requested`, `Comment`
- `### Confidence` (prose, unchanged)
- `### Personas activated` — six-row table SE / SC / IN / DA / FE / TS with `Status` ∈ {`✅ active`, `✅ pass`, `⏭ skip`} and a short `Reason` noun phrase
- `### Findings` — two-column table Severity | Count, three rows Must-fix (priority 1-2) / Should-fix (3-5) / Nits (6-7). For each tier with `Count > 0`, render a `**<Tier> anchors:**` bullet sub-list below the table — one bullet per finding (`` - `<persona-id>` <path>:<line> — see inline comment ``). Anchorless findings appear as one-line bullets in the same sub-list with a `(no inline anchor)` marker; there is no separate `### Findings without inline anchor` section. Initial draft used a third `Inline anchors` column inside the table; reversed on 2026-05-26 because GitHub's renderer squeezed the narrow Severity/Count columns into ugly header wraps — see Revisit Triggers below.
- `### Delegations` (unchanged; omitted when empty)
- `### Comment lifecycle` — six-row table for thread states Resolved / Won't-fix / Outdated / Possibly addressed / Stale / Open, plus a trailing `Suppressed N findings...` line
- `### Stale comments needing reply` (unchanged; omitted when empty)
- `### What's solid` (renamed from `What's Good`)

The JSON output and exit codes keep the formal `APPROVE` / `REQUEST_CHANGES` / `COMMENT` keywords for back-compat. A new additive `verdict_label` field (`LGTM` / `LGTM_WITH_CAVEATS` / `CHANGES_REQUESTED` / `COMMENT`) reflects the friendly markdown label so downstream tooling can render either surface without re-deriving. A new `confidence.personas` map provides the per-persona status + reason for table rendering.

## Alternatives Considered

- **Keep heading-driven format.** Rejected — the `(none)` placeholder repetition on clean PRs is genuinely noisy, and "which personas ran" is a useful surface that didn't exist before. The user explicitly preferred the freelance table format after seeing it on PR #57.
- **Use the freelance format verbatim including `### Lifecycle counts` for severity counts.** Rejected — collides semantically with `### Comment lifecycle` (thread-state counts). Renamed the severity table to `### Findings`.
- **Use `LGTM` only for clean APPROVE; keep `APPROVE (with caveats)` / `REQUEST_CHANGES` / `COMMENT` for everything else.** Rejected after a direct user choice — the user picked friendly labels for all four states (`LGTM` / `LGTM (with caveats)` / `Changes requested` / `Comment`).
- **Keep separate `### Critical` / `### Important` / `### Suggestions` sections for the inline-pointer index.** Rejected after a direct user choice — the user picked folding the inline anchors INTO the Findings table as a third column.

## Consequences

- Every fixture-expected-output, every example, and the SKILL.md template was rewritten to the new layout (16 files touched in `skills/ship-reviewed-prs/`).
- JSON consumers that read `decision` / `exit_code` continue to work unchanged; `personas_run` is preserved as a back-compat array alongside the new richer `personas` map.
- A new style invariant is enforceable via `grep`: `What's Good`, `### Decision:`, and `### Lifecycle counts` should all return zero hits in the skill directory (except the `tests/README.md` "watch for this misuse" line that intentionally names the rejected `Lifecycle counts` label).
- Reviewers can scan a PR review and tell at a glance which lenses (personas) were applied — previously this was buried in the Confidence prose.

## Revisit Triggers

- **Already triggered and resolved 2026-05-26:** the original three-column Findings table (Severity | Count | Inline anchors) rendered poorly on GitHub. GitHub's renderer squeezed the Severity/Count columns to fit the wide third column, wrapping the headers ("Severit-y", "Cou-nt"). Resolution: dropped the third column; anchors now live in per-tier `**<Tier> anchors:**` bullet sub-lists below the table. The separate `### Findings without inline anchor` section is also gone — anchorless findings appear inline in their tier's sub-list with a `(no inline anchor)` marker.
- The `LGTM_WITH_CAVEATS` enum value proves too coarse (e.g. users want to distinguish "suggestion only" from "pending CI only" in the label itself).
- The fixed six-row Personas table feels redundant for repos that disable specific personas via override; if so, render only enabled personas.

## Related

- [[pr-review-summary-body-layout]] — pattern note capturing the canonical layout for quick reference during a review
- [[pr-review-installs-plugin-from-pr-head]] — the dogfood workflow that will exercise this format change on the next PR
- [[relaxed-approve-decision-matrix]] — the matrix that now maps to `LGTM` vs `LGTM (with caveats)` in the friendly verdict
