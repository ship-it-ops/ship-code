---
type: decision
status: active
created: 2026-06-02
updated: 2026-06-02
author: claude-session-2026-06-02
tags: [ship-reviewed-prs, ship-devops, persona, delegation, in]
importance: core
---

# IN persona depth target = ship-devops

## Context

After standing up `ship-devops` (DEV1–DEV12 rubric, platform reference files, test fixtures — see [[ship-devops-12-category-catalog]]), the open question was how to plug it into `ship-reviewed-prs`. The orchestrator already had an **IN (Senior Infra / SRE / DevOps)** persona with IN1–IN7 finding IDs and a "deep mode escalates to subagent" note, but no specific depth-target skill named. Two-mode pattern (direct-emit vs delegate) was only documented for SC → `ship-secure-code`.

Choices considered: (1) rename IN → DV everywhere, (2) add a new DV persona alongside IN, (3) keep IN and wire it to `ship-devops` as its depth target. User selected option 3 on 2026-06-02.

## Decision

`ship-reviewed-prs` IN persona's depth target is `ship-devops`. The two-mode rubric from SC → `ship-secure-code` is replicated 1:1:

- **Direct-emit** at the orchestrator level for high-precision single-line patterns: floating action ref, missing `USER` in Dockerfile, missing `resources.limits` in Deployment, secret literal in workflow YAML, `fetch(url)` without timeout, `Recreate` strategy on traffic-serving Deployment.
- **Delegate** via a single `Run /ship-devops on <file>` bullet in the Delegations section when the finding requires deploy-path trace, multi-file pipeline context, platform-specific depth, or two-plus DEV categories compounding.

Finding tags use a compound form: `[INn / DEVm.t-LABEL]` so reviewers see the depth-target's category alongside the orchestrator's priority code.

IN1↔DEV mapping is published in `ship-reviewed-prs/reference-personas.md` § IN → IN ↔ DEV ID mapping. Override knobs `in_delegate_to_ship_devops`, `in_disabled_delegation_categories`, and `in_compound_tag_categories` live in `overrides.example.md`.

Versions bumped: ship-reviewed-prs 1.2.0 → 1.3.0 (feature add, backwards compatible); ship-devops 0.1.0 → 0.2.0 (delegation contract live); root `plugin.json` and `marketplace.json` metadata 1.3.0 → 1.4.0.

New test fixture: `ship-reviewed-prs/tests/fixture-9-devops-delegation/` exercises the direct-emit-plus-delegation case on a PR shipping a workflow + Dockerfile + manifest + service code together.

## Alternatives Considered

- **Rename IN → DV everywhere** — rejected. Touches every fixture, the lang-*.md files, the orchestrator SKILL.md decision matrix references, and the agent-context decision notes. High blast radius for no semantic gain; "IN" already reads as "infra / SRE / DevOps."
- **Add a new DV persona alongside IN** — rejected. Duplicates concerns; risks double-counting findings and rubric drift; introduces a second persona-pass without a clear non-overlapping mandate.
- **Wire delegation but keep finding tags single-form (`[IN1]` only, no DEV tag)** — rejected. The compound tag is the only signal the reviewer gets that depth was consulted. Without it, the delegation looks decorative.

## Consequences

- The IN persona becomes the orchestrator-side "narrow filter"; ship-devops is the canonical authority on DevOps PR concerns. Future DevOps rubric changes happen in ship-devops, not in ship-reviewed-prs.
- Compound `[INn / DEVm.t-LABEL]` tags expand the finding string. Acceptable but worth watching — if a tag becomes too long for readable inline rendering, override `in_compound_tag_categories: []` suppresses the DEV portion per team.
- Anti-overlap between SEC7 (secret leak) and DEV5 (sourcing discipline) now flows through two delegation paths (SC → ship-secure-code AND IN → ship-devops). When both fire on the same line, SC wins for the user-facing finding (per `ship-devops/reference.md` § 5); IN's delegation bullet cross-references. The orchestrator must dedupe these by `(path, line ± 5, root-cause-token)` per the standard merge protocol.
- The DV persona idea is now closed; future "DevOps persona" requests should redirect to this decision.

## Revisit Triggers

- If a real PR review produces `[IN1 / DEV2.1-...]` style tags that read poorly in the GitHub inline-comment UI → tune compound-tag rendering (drop verbose `LABEL`, keep only `DEVm.t`).
- If ship-devops's rubric drifts and IN's direct-emit list becomes inconsistent with the orchestrator's high-precision list → re-sync via the IN ↔ DEV mapping table.
- If false-positive rate on IN5 / DEV1 patterns exceeds 20% → demote via override file rather than changing the rubric inline.

## Related

- [[ship-devops-12-category-catalog]] — the rubric this decision binds the IN persona to.
- [[pr-review-table-driven-summary-format]] — the rendered output shape that compound tags live inside.
- [[relaxed-approve-decision-matrix]] — the parent decision matrix that this delegation respects.
