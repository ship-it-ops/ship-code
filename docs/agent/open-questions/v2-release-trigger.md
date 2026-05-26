---
type: open-question
status: active
created: 2026-05-25
updated: 2026-05-25
author: claude-session-2026-05-25
tags: [ship-reviewed-prs, versioning, semver]
importance: standard
opened: 2026-05-25
answer-source: maintainer
---

# When do we release ship-reviewed-prs v2.0.0?

## Context

PR #4 (test-branch) lands a decision-matrix change that per `CONTRIBUTING.md:139` ("decision-matrix changes are MAJOR") should bump `ship-reviewed-prs` from 1.1.0 → 2.0.0. The user explicitly held the version at 1.1.0 — *"I do not want to release a v2 yet."*

This means downstream consumers (e.g. ShipIt-AI's CI pinning `ship-reviewed-prs@ship-code`) will get the new behavior silently when ship-code's main is updated, without a version signal that anything has changed.

## Tried

Captured the relaxed-matrix change as a decision with explicit `Revisit Triggers` ([relaxed-approve-decision-matrix](../decisions/relaxed-approve-decision-matrix.md)), and recorded the held-back version bump under "Consequences" of that note so it does not get forgotten.

## Who Can Answer

The repo maintainer (user). They will signal when downstream dogfooding has confirmed the new matrix is stable enough to attach the v2.0.0 label.

When the answer is "ship it": bump *both* `plugins/ship-reviewed-prs/.claude-plugin/plugin.json:version` and the `ship-reviewed-prs` entry in `.claude-plugin/marketplace.json:version` from `1.1.0` to `2.0.0` in the same commit. CI's marketplace-consistency check requires they match.
