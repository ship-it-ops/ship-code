---
type: decision
status: active
created: 2026-05-25
updated: 2026-05-25
author: claude-session-2026-05-25
tags: [ship-reviewed-prs, decision-matrix, approve, ci]
importance: core
---

# ship-reviewed-prs APPROVE no longer blocked by suggestions or pending CI

## Context

The original `ship-reviewed-prs` decision matrix (v1.1.0 prose) required *zero* findings of any tier *and* green CI to APPROVE. Anything else degraded to COMMENT. Two real cases on this repo's PR #4 demonstrated the trap:

1. A docs-only PR with one P6 cosmetic finding (`[SE6-DOC-EXAMPLE-GAP]`) degraded APPROVE → COMMENT. The next pass surfaced a fresh P6 and degraded again. Any sufficiently thorough reviewer always finds one suggestion, so APPROVE was asymptotically unreachable.
2. Pending CI (unrelated CodeQL language-analysis jobs on a markdown-only PR) forced COMMENT even when nothing else was wrong.

The user's intent: *"Important stuff can warrant a comment, critical can warrant a deny. Suggestions and pending CI shouldn't block APPROVE."*

## Decision

Rewrite the decision matrix as a top-down priority cascade. First matching condition wins:

| Condition | Verdict |
|---|---|
| `is_draft` / WIP-labelled | COMMENT |
| Any unsuppressed *1-*2 finding (Critical) | REQUEST_CHANGES |
| Any unsuppressed *3-*5 finding (Important) | COMMENT |
| `ci_state == red` | COMMENT — "CI must pass before approval" |
| `lifecycle_quality == degraded` | COMMENT |
| `possibly_addressed_count > 0` | COMMENT |
| **Otherwise (incl. only suggestions, delegations, and/or pending CI)** | **APPROVE — caveats noted inline** |

APPROVE may carry optional "Suggestions", "Delegations", or "Awaiting CI" caveat sections in the body. These are advisory and do not change the verdict.

`--auto-approve` stays **strict** — only a *clean* APPROVE (zero findings + green CI) auto-submits without confirmation. APPROVE-with-caveats requires interactive confirm.

## Alternatives Considered

- **Keep the conservative matrix**: rejected — the "always-one-nitpick" trap made APPROVE unreachable.
- **Relax `--auto-approve` to match**: rejected — auto-submitting an APPROVE that has caveats is risky; the human should glance first.
- **Bump the plugin to v2.0.0 immediately** (per `CONTRIBUTING.md:139`, decision-matrix changes are MAJOR): held back per user request — *"I do not want to release a v2 yet."* Version stays at 1.1.0; behavior changes ship without a version signal.

## Consequences

- PRs with only cosmetic findings now reach APPROVE. ShipIt-AI and other downstream consumers will see the new behavior the moment ship-code's marketplace updates.
- The MAJOR version bump is deferred. Downstream pinning to `ship-reviewed-prs@1.1.0` will get the new behavior silently. **This is an intentional behavior-change-without-version-signal — track it as a future v2.0.0 commitment, not as a forgotten version bump.**
- Two new self-test fixtures lock in the new behavior:
  - `tests/fixture-7-suggestions-only-approve/` — one P6 + green CI → APPROVE with Suggestions caveat
  - `tests/fixture-8-pending-ci-approve/` — zero findings + pending CodeQL → APPROVE with Awaiting CI caveat

## Revisit Triggers

- User decides to actually release v2.0.0 — bump `plugins/ship-reviewed-prs/.claude-plugin/plugin.json` and the ship-reviewed-prs entry in `.claude-plugin/marketplace.json` together.
- Downstream consumers report that "always one nitpick" returns in a new form (e.g. delegations becoming the new always-on caveat).
- Real APPROVE rate stays low — investigate whether Important findings (P3-P5) are being misclassified.

## Related

- [pr-review-installs-plugin-from-pr-head](pr-review-installs-plugin-from-pr-head.md) — the workflow change that makes this matrix self-review on the PR introducing it.
- `SKILL.md` Decision Matrix section — the canonical spec.
- `reference.md` §5 Decision Matrix — Elaboration — the count-predicate version.
