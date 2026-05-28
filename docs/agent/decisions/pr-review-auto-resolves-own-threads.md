---
name: pr-review-auto-resolves-own-threads
description: ship-reviewed-prs auto-resolves bot-authored review threads when the same finding no longer fires on the next run
metadata:
  type: decision
type: decision
status: active
created: 2026-05-28
updated: 2026-05-28
author: claude-session-2026-05-28
tags: [ship-reviewed-prs, comment-lifecycle, auto-resolve, github-graphql]
importance: core
---

# pr-review auto-resolves bot-authored threads on re-runs

## Context

PR #8 demonstrated the failure mode. The bot left two inline findings on a prior run (`SE3-SKILL-TOO-LONG` and `SE5-EXAMPLE-INCONSISTENCY`). The maintainer pushed a fix commit that addressed both. On the next run, the bot's lifecycle classifier saw a post-comment commit had touched both `file:line ± 5` anchors and marked them `ADDRESSED` — then degraded the verdict to `COMMENT` per the spec rule "any 'Possibly addressed' items → COMMENT, needs human confirmation."

This is the spec working as designed, but it produces a bad pattern: the only thing keeping the verdict from being `LGTM` is two threads the bot *itself* opened, that *the bot itself* can now see no longer fire. The clutter compounds on long PRs — every fix-commit cycle re-surfaces every prior bot finding under "Possibly addressed" until a human goes through the GitHub UI and clicks "Resolve thread" on each one.

The conservative reason ADDRESSED was COMMENT-degrading in the original design is sound: the "commit touched file:line ± 5" heuristic is just a heuristic. A commit reformatting nearby code looks identical to a fix. For threads where the bot can't know whether the concern was actually addressed, surfacing for human confirmation is correct.

But the bot CAN know for its own threads: the original finding has a deterministic fingerprint (`path, line ± 5, finding-id`), and on the next run the skill re-derives findings from the current diff. If the same fingerprint no longer fires, the bot is the one source of truth on whether its own concern was addressed. The new diff demonstrates the absence of the violation.

## Decision

Add a Step 4 to the submission protocol that auto-resolves bot-authored review threads when the same fingerprint no longer fires on the current run. Scope strictly limited to threads the bot itself authored — never touches human-authored threads.

**Detection.** A thread is "bot-authored" if its first comment's `author.login` matches the configured `bot_identity_login` (default `claude[bot]`), OR its first comment's body starts with the `**[<persona-id>-<finding-id>]**` content marker (fallback for setups where login varies across auth modes).

**Action.** For each bot-authored, unresolved thread whose fingerprint does NOT match any finding emitted this run:

1. Post a reply comment beginning with the literal token `✅ Resolved by ship-reviewed-prs` plus a short reason (`finding no longer fires at this anchor (run <sha>)`). This gives humans an audit trail and a target for re-opening if they disagree.
2. Call the GraphQL `resolveReviewThread(threadId)` mutation.

**Step ordering.** Step 4 runs strictly after Step 3 succeeds. If Step 3 errors, Step 4 is skipped entirely — a half-resolved thread set without a corresponding new review is confusing.

**Re-opened bot threads (BOT_RESOLVED_REOPENED).** If a thread is bot-authored AND `isResolved: false` AND its comment timeline contains a prior `✅ Resolved by ship-reviewed-prs` reply, the bot DOES NOT re-resolve. Treat as OPEN; if the same finding still fires, emit it normally. The un-resolve is the human's deliberate signal that the concern is not actually addressed.

**Observability.** Summary body gets a `Resolved N stale bot-authored threads this run.` trailing line (only when N > 0). JSON output gets `submission.threads_resolved` and `submission.threads_resolved_reopened`.

**Override control.** `auto_resolve_own_threads: true|false` in `overrides.md` (default `true`). Disable to skip Step 4 entirely.

## Alternatives Considered

- **Auto-resolve human-authored ADDRESSED threads too.** Rejected — the heuristic is too unreliable. A formatting commit looks identical to a fix. Silently dismissing human review concerns is worse than the clutter we're solving.
- **Auto-resolve human-authored WONT_FIX threads (where the human said "tracked in #N" but never clicked Resolve).** Considered, deferred. The human explicitly signaled "done"; this is safer than ADDRESSED. But it conflates two intents: the human chose to leave the thread visible. Better to add a separate behavior with a separate flag later if needed. Not in scope for this decision.
- **Resolve immediately on emit (atomic with the first review).** Rejected — the bot can't resolve a finding it just emitted. Resolution is by construction a cross-run operation: emit on run N, resolve on run N+1 when the fingerprint stops firing.
- **Require the human to push the resolving commit (not just any commit).** Considered — would prevent the bot from resolving threads addressed by another bot or by force-push. Deferred: the fingerprint check already gates on "finding no longer fires," which subsumes "the change actually fixed it" regardless of who pushed.

## Consequences

- PR #8 (and structurally similar future PRs) will see `LGTM` / `LGTM (with caveats)` verdicts on the run after a maintainer fix, instead of `Comment` with two "Possibly addressed" items. Solves the reported clutter without weakening conservatism.
- The bot's reviews now consume `resolveReviewThread` GraphQL mutations. No new permission scope needed — `pull-requests: write` (already required for posting reviews) covers it.
- A new lifecycle classification — `BOT_RESOLVED_REOPENED` — exists to detect human disagreement with prior bot resolutions and prevent resolution loops.
- The bot's resolution reply body MUST start with the token `✅ Resolved by ship-reviewed-prs` for the BOT_RESOLVED_REOPENED detection on later runs. Changing that token is a breaking change for self-thread reconciliation.

## Revisit Triggers

- A human reports the bot resolved a thread they considered unresolved (i.e. the "finding no longer fires" heuristic produced a false positive). Counter-measure: tighten the fingerprint match (e.g., require an exact `path:line` match, not `line ± 5`).
- Resolution rate stays at 0 across many runs — suggests `bot_identity_login` defaulting isn't matching the actual posting account (some auth modes post as the human, not `claude[bot]`). Counter-measure: lean harder on the content-marker fallback.
- A human reports they un-resolved a bot-resolved thread and the bot still re-resolved it — BOT_RESOLVED_REOPENED detection failed. Counter-measure: audit the comment-timeline fetch and the token-match logic.

## Related

- [[pr-review-table-driven-summary-format]] — the layout the auto-resolve count is rendered into
- [[relaxed-approve-decision-matrix]] — the matrix Step 4 short-circuits before the "Possibly addressed" → COMMENT row fires
- [[pr-review-installs-plugin-from-pr-head]] — the dogfood workflow that will exercise this end-to-end on the next PR
