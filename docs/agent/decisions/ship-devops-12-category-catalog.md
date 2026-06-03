---
type: decision
status: active
created: 2026-06-02
updated: 2026-06-02
author: claude-session-2026-06-02
tags: [ship-devops, rubric, category-catalog, devops, ci-cd]
importance: core
---

# ship-devops DEV1–DEV12 category catalog

## Context

The ship-* family already covers clean code (style), secure code (appsec), tested code (test design), debugged code (root cause), and reviewed PRs (orchestration). Pull-request review on DevOps / CI-CD concerns — deploy pipelines, IaC, containers, observability, release management — was left to the senior-infra/SRE persona inside ship-reviewed-prs with no depth target. This decision establishes ship-devops as that depth target, mirroring the ship-secure-code shape exactly so the existing patterns (12-category catalog, tier sub-tags, decision matrix, override file, platform reference splits, test fixture layout) carry over without re-invention.

The rubric was derived from three canonical DevOps texts (The DevOps Handbook, The Phoenix Project, Effective DevOps) plus OWASP CI/CD Top 10 and SRE-book conventions. Sources are cited per category in `skills/ship-devops/reference.md` § 9.

## Decision

The ship-devops skill ships with a fixed 12-category catalog. Each category owns a slice of DevOps PR-review concern, with tier-1 / tier-2 / tier-3-5 severity sub-tags computed mechanically from finding ID + context:

| ID | Label | Owns |
|----|-------|------|
| DEV1 | CI-PIPELINE | Workflow YAML quality, pinned actions, fast feedback, real test gate, privileged tokens |
| DEV2 | DEPLOYMENT-SAFETY | Rollback path, progressive rollout, idempotency, pre/post-deploy validation |
| DEV3 | IAC-IMMUTABILITY | IaC drift, state management, plan-gate, rename safety, environment parity |
| DEV4 | CONTAINER-IMAGE | Dockerfile hygiene: non-root, pinned base, multi-stage, build secrets, HEALTHCHECK |
| DEV5 | CONFIG-MGMT | Runtime sourcing discipline (env/vault), 12-factor, per-env overrides, default-on-missing |
| DEV6 | OBSERVABILITY | Structured logs, golden signals, correlation IDs, dashboard-as-code |
| DEV7 | RELEASE-MGMT | Semver, CHANGELOG, tag policy, lockfile drift, artifact signing |
| DEV8 | SCHEMA-MIGRATION | Two-phase migrations, online DDL, reversibility, canary-safe ordering |
| DEV9 | HEALTH-READINESS | Probes, graceful shutdown, smoke tests, dependency-health propagation |
| DEV10 | SLO-PERFORMANCE | Resource limits, timeouts, perf-test gate, SLO documentation |
| DEV11 | INCIDENT-HYGIENE | Runbooks, alert quality, CODEOWNERS, post-mortem links |
| DEV12 | FLOW-BATCH | PR size, branch age, partial-work flag wrapping (signal-based, not gating) |

Anti-overlap with ship-secure-code is explicit:
- SEC7 owns "hardcoded secret literal in code" (data leak). DEV5 owns "how does this code source config/secrets at runtime" (sourcing discipline). Cross-references only; no double-counting.
- SEC1.4 (over-privileged service account) cross-cuts DEV4.1 (Dockerfile `USER root`) and DEV3 (IaC IAM); same tier-1 fires once via the delegation parent.
- SEC8 (supply chain) cross-cuts DEV1.1 (floating action references); SEC framing wins for the leak surface.

## Alternatives Considered

- **Language-based reference split** (`lang-python.md`, `lang-typescript.md`, `lang-java.md`) — rejected because DevOps signal is not language-tied. Pipelines, Dockerfiles, manifests, IaC are platform-bound, not language-bound. Adopted platform-based splits: `ci-github-actions.md`, `iac-terraform.md`, `container-docker.md`, `k8s.md`, `observability.md`.
- **Full Three Ways + CAMS cultural categories** (psychological safety, knowledge sharing, hero culture) — rejected as too subjective to flag in a diff. Kept only the flow signals that *are* visible (PR size, branch age, WIP-commit messages, runbook presence) under DEV11 and DEV12.
- **Bundle the ship-reviewed-prs DV persona into this release** — rejected. The rubric needs to prove itself in standalone use first; the persona is a separate concern with its own design decisions (detection patterns, delegation contract, decision-matrix mapping). Tracked as Phase 2.

## Consequences

- Future agents reviewing DevOps concerns now have a fixed rubric to anchor against; no more ad-hoc "looks like a deploy issue" framing.
- ship-clean-code, ship-secure-code, and ship-devops will increasingly need explicit anti-overlap policies as the rubric overlaps grow. The boundary docs in each `reference.md` § Anti-overlap section are the single source of truth.
- The Phase 2 DV persona in ship-reviewed-prs has a stable delegation target to point at. The persona itself will need: DV1-DVn detection patterns (high-precision regex hits on diff content), delegation contract (when to call ship-devops vs. flag inline), decision-matrix mapping (DEV*.1 → DV*.1), and parallel test fixtures.
- 0.1.0 release reflects deliberate uncertainty; the rubric is expected to iterate against real PRs before 1.0.

## Revisit Triggers

- More than ~20% false-positive rate on any single DEV category in real-world use → demote that category via the override file mechanism, or split it.
- A new platform stack becomes a primary review surface (e.g., Pulumi, Bun, Knative) → add a platform reference file.
- A category is consistently flagged but never acted on → either escalate severity, demote the category, or refine its rubric.
- DV persona work begins → update the anti-overlap and delegation contract sections of `reference.md`.

## Related

- [pr-review-table-driven-summary-format](pr-review-table-driven-summary-format.md) — output shape that the future DV persona will need to produce inside ship-reviewed-prs.
- [pr-review-installs-plugin-from-pr-head](pr-review-installs-plugin-from-pr-head.md) — the dogfood workflow that will exercise ship-devops once the DV persona ships.
- [relaxed-approve-decision-matrix](relaxed-approve-decision-matrix.md) — the parent decision-matrix shape that ship-devops's tier mapping needs to match.
