---
name: ship-devops
description: >
  Apply DevOps and CI/CD review principles (CI pipelines, infrastructure-as-code,
  container images, secrets/config sourcing, observability, release management,
  schema migrations, health/readiness, SLO/performance, incident hygiene, and
  flow/batch signals) when writing or reviewing pipeline YAML, IaC, Dockerfiles,
  k8s manifests, deploy scripts, and the application code that integrates with
  them. Invoke explicitly for DevOps/CI/CD reviews, or as the delegation target
  from the ship-reviewed-prs IN (Senior Infra / SRE / DevOps) persona. Do not invoke for pure styling,
  application-only logic, one-off prototypes, or test-design depth (use
  ship-clean-code, ship-secure-code, or ship-tested-code respectively).
allowed-tools: Read, Grep, Glob
---

# DevOps Skill

## Purpose

This skill applies DevOps and CI/CD principles to help you write and review the pipeline, infrastructure, container, and deploy-adjacent code that turns a working commit into a safe production change. It operates in **review mode** only — it does not auto-remediate. Sibling skills handle non-DevOps concerns: `ship-clean-code` (file quality), `ship-secure-code` (appsec), `ship-tested-code` (test design), `ship-debugged-code` (root cause), `ship-reviewed-prs` (PR-level orchestration).

The rubric draws on three canonical DevOps texts: *The DevOps Handbook* (Kim/Humble/Debois/Willis), *The Phoenix Project* (Kim/Behr/Spafford), and *Effective DevOps* (Davis/Daniels). Every finding ID traces to one of: the Three Ways (Flow, Feedback, Continual Learning), the Four Types of Work, or the CAMS pillars (Culture, Automation, Measurement, Sharing). Sources are cited per category in `reference.md`.

## Quickstart (New to DevOps Review?)

Start with these 3 rules and internalize them before learning the rest:

1. **Automate the deploy.** A change that requires a human to follow a checklist or SSH into a box is not deployable; it is a future incident. The skill flags every manual step that should be code.
2. **Make every deploy reversible.** Blue-green, canary, feature flags, reversible migrations — at least one mechanism must let the next deploy go back. "Fix forward" is not a rollback strategy.
3. **Make every prod change observable.** Logs, metrics, traces, and dashboards land with the feature, not after the first incident. If the PR cannot answer "how will we know if this broke?", it isn't ready.

The detailed reference files (`reference.md`, `reference-categories.md`, the platform files) assume familiarity with these three and with the OWASP-of-ops surface: pipeline YAML, IaC, containers, k8s, observability stacks.

## Mode Detection

- **Review mode** (default and currently only mode): Read the target files, analyze against the 12-category rubric below, produce a structured report. Never edit code, never produce patches except as advisory snippets in the report.
- **Triggered explicitly** by: `/ship-devops <path|file>`, "devops review", "ci review", "deploy review", "infra review", "pipeline review", or invocation from `ship-reviewed-prs` IN-persona delegation.

If asked to *write* deploy-adjacent code (e.g., a new GitHub Actions workflow, a Terraform module, a Dockerfile), the skill does not apply directly — write the code with `ship-clean-code`, then run this skill to review it. The write/review split is intentional; a single mode that does both tends to produce pipelines that look defended (lots of steps, lots of `if` guards) without actually being safe.

## Core Principles - Always Apply

These 12 rules apply to ALL DevOps review:

### 1. Deploy pipeline first.
Identify the pipeline before reading the changed file. What gates run? What artifacts are produced? Where does this PR's change land in the pipeline graph? Findings hang off this map. If the repo doesn't have a pipeline at all, that's the first finding.

### 2. Idempotent infrastructure.
Running the deploy/IaC twice must produce the same result. Hand-edited resources, non-idempotent shell scripts, and `if [ -f x ]; then mv` patterns all fail this rule. DEV3 owns the deeper rubric.

### 3. Immutable images and artifacts.
Container images, lambda zips, and AMIs are built once and promoted across environments. Editing the running container, hot-patching prod, or rebuilding per-environment all fail this rule.

### 4. Reversible by default.
Every change ships with a rollback. Two-phase migrations, feature flags, blue-green slots, or canary cohorts — the skill flags changes that cannot be undone within minutes.

### 5. Fail fast in CI, fail closed in prod.
CI signals failure as early as possible (cheap stages before expensive ones, fail-fast matrix). Prod failure denies access / refuses traffic / falls back to safe-mode rather than serving partial state.

### 6. Observability is a feature.
If the change touches a user-impacting path, the PR must add or reuse a log line, a metric, and (where the stack supports it) a trace span. Dashboards live in code. DEV6 owns the deeper rubric.

### 7. Pin versions everywhere.
Action references, base images, package versions, Terraform providers — everything that changes silently can break silently. Pin to a digest (containers, actions) or a lockfile (npm/pip/cargo). Float only in dev.

### 8. Secrets sourced, never literal.
Production secrets enter the process at runtime via env var, vault client, or platform-managed identity. SEC7 owns the leak surface (hardcoded literal in code/CI); DEV5 owns the *sourcing discipline*. See "Related Skills" for the boundary.

### 9. Least-privilege everywhere.
CI tokens scoped to the minimum repo/permission set, container `USER` is non-root, IAM roles are per-service, k8s service accounts mount only what they need. Cross-cuts with SEC1.4.

### 10. Small batches, fast feedback.
Big PRs and long-lived branches turn deploys into events. DEV12 flags batch-size signals: file count, line count, branch age, "WIP" commit messages. The goal is not to gate large PRs, but to surface the risk.

### 11. Severity is mechanical from finding ID.
DEVn.1 findings (must-fix) block merge. DEVn.2 findings (should-fix) ship with mitigation plans. DEVn.3-5 are advisory. The skill computes tier from the finding ID and the surrounding context (touches prod path vs. dev-only); no LLM negotiation.

### 12. Surface confidence, not opinion.
Include a Confidence section naming what was reviewed, what was not (binaries, generated manifests, vendored modules), and what's the residual risk. A confident "must fix" pairs with the specific pipeline/infra path that drove the finding.

## The 12-Category Catalog

| ID | Label | Covers | Tier-1 examples (must-fix) |
|----|-------|--------|----------------------------|
| DEV1 | CI-PIPELINE | Workflow YAML quality, build/test parallelism, caching, fast feedback (<10 min), pinned action versions, fail-fast vs. continue-on-error, matrix coverage | New workflow uses `actions/checkout@main` (floating tag); merge gate runs no tests; `continue-on-error: true` on the test step |
| DEV2 | DEPLOYMENT-SAFETY | Rollback path, blue-green/canary/feature-flag presence, big-bang detection, deploy idempotency, missing pre-deploy validation | New deploy script overwrites prod with no rollback; rollout strategy is `Recreate` on a stateful service; deploy job has no health-gate |
| DEV3 | IAC-IMMUTABILITY | Terraform/Pulumi/CloudFormation/Ansible hygiene, drift signals, environment parity, missing `terraform plan` gate, hand-edited resources | `local-exec` provisioner running `aws cli` with mutating verbs; no remote state; resources renamed in `.tf` without `moved {}` block |
| DEV4 | CONTAINER-IMAGE | Dockerfile hygiene: non-root `USER`, multi-stage build, pinned base, `.dockerignore` present, no secrets in layers, healthcheck, minimal surface | `FROM ubuntu:latest`; no `USER`; `ARG SECRET=...` in build; `COPY . /app` with no `.dockerignore` |
| DEV5 | CONFIG-MGMT | Env-var/vault sourcing, 12-factor compliance, per-env overrides, default-value handling, runtime mutability, no committed `.env` | New service reads secrets from a checked-in `config.json`; required env var has a silent fallback default; same config used for dev and prod |
| DEV6 | OBSERVABILITY | Structured logging, golden signals (latency/traffic/errors/saturation), correlation IDs, distributed tracing, dashboard-as-code, metrics on user paths | New endpoint logs nothing; metric only reports success counter, no error/latency; dashboard added in the UI, not the repo |
| DEV7 | RELEASE-MGMT | Versioning (semver), CHANGELOG, release-tag policy, conventional commits where adopted, breaking-change signaling, lockfile drift | Major-version bump with no CHANGELOG entry; breaking API change in a `fix:` commit; lockfile diff conflicts with `package.json` |
| DEV8 | SCHEMA-MIGRATION | Backward-compatible migrations (N and N-1 readers), reversible default, no `DROP COLUMN` without two-phase, online-DDL when needed, canary-safe ordering | `ALTER TABLE` adds `NOT NULL` with no default to a hot table; migration removes column still read by previous version; long-running lock |
| DEV9 | HEALTH-READINESS | `/healthz`/`/readyz` endpoints, liveness vs. readiness distinction, smoke test post-deploy, k8s startup-probe correctness, dependency-health propagation | New service ships with no health endpoint; liveness probe also checks dependencies (cascading failure); deploy job has no smoke step |
| DEV10 | SLO-PERFORMANCE | Perf test in pipeline, latency budget acknowledged, regression detection, resource limits/requests on workloads, timeouts/circuit breakers, DORA signals | k8s `Deployment` has no `resources.limits`; HTTP client has no timeout; new perf-sensitive endpoint has no load test |
| DEV11 | INCIDENT-HYGIENE | Runbook in repo, on-call doc freshness, post-mortem link on fix PRs, alert quality (actionable, non-noisy), `CODEOWNERS` coverage for prod paths | New prod service has no runbook; alert thresholds copy/pasted from an unrelated service; production-touching path missing from `CODEOWNERS` |
| DEV12 | FLOW-BATCH | PR size (lines/files/surface), trunk-based vs. long-lived branch, WIP signals (commits-in-flight), feature-flag wrapping for partial work, atomic-commit hygiene | PR touches 80 files across 5 services with no flag; branch age > 30 days behind main; "WIP" / "tmp" commit messages without squash |

Full per-category rubric — antipatterns, canonical fixes, false-positive notes, cross-references — lives in `reference-categories.md`.

## Severity Tiers

Each finding ID has a tier sub-tag computed from the deployment context:

- **Tier 1 (must-fix, REQUEST_CHANGES)** — the change touches a prod path and breaks rule 1, 2, 3, 4, 6, or 8 above (automated/reversible/observable/secrets). The textbook DevOps failure mode. Blocks merge.
- **Tier 2 (should-fix, COMMENT)** — secondary defense missing where a primary defense exists, OR the antipattern lands in a non-prod path (dev, staging, internal-only). Ship with mitigation plan.
- **Tier 3-5 (advisory, COMMENT)** — flow/hygiene improvements, depth fixes, docs gaps that won't bite this PR but will the next one.

The full tier definitions per finding ID are in `reference-categories.md`.

## Decision Matrix

| State | Decision |
|-------|----------|
| Any unsuppressed *.1 (must-fix) finding | `REQUEST_CHANGES` |
| Only *.2 findings | `COMMENT` |
| Only *.3-*.5 findings | `COMMENT` |
| Zero findings | `APPROVE` (or `NO_FINDINGS` when run standalone) |

`ship-devops` does not have its own submission semantics — when run standalone, it produces a structured report. When run as the delegation target from `ship-reviewed-prs` IN persona, the parent skill maps the report to its own decision matrix (DEVn.1 → IN priority-1, DEVn.2 → IN priority-3, DEVn.3-5 → IN priority-5+) and renders findings with compound tags `[INn / DEVm.t-LABEL]` so the depth-target's category surfaces alongside the orchestrator's priority code.

## Review Output Format

```
## DevOps Review: [scope]

### Confidence
<2-4 sentences: pipeline identified, what was reviewed, what was not
reviewed (binaries, generated manifests, vendored modules, autogenerated
lockfiles), residual risk.>

### Critical (must fix before merge)
- **[DEV2.1-NO-ROLLBACK] deploy/release.sh:14**: <deploy path: trigger → action → blast radius>. → <fix>.
- **[DEV4.1-IMAGE-ROOT-USER] services/api/Dockerfile:8**: <description>. → <fix>.

### Important (should fix)
- **[DEV1.2-FLOATING-ACTION] .github/workflows/ci.yml:22**: <action ref>. → <fix>.

### Advisory (hygiene)
- **[DEV11.4-MISSING-RUNBOOK] services/api/**: <description>. → <fix>.

### What's Good
- <substantive observation about a discipline done well — not boilerplate>
```

Rules for the output:
- Include the **deploy path** for every Critical finding: identify the trigger (where the change reaches prod), the action (what it does there), and the blast radius (what it affects on failure). A finding without that trace is not actionable.
- Tag every finding with its full ID (`DEVn.t-LABEL`) — tier is part of the ID, not a separate field.
- Specific file:line every time.
- "What's Good" is mandatory. Name disciplines that exist (pinned digests, dashboard-as-code, idempotent migration) so the author trusts the negative findings.
- More than 10 findings: top 10 strictly ordered by severity. Never suppress a tier-1 finding due to the cap.

## Pragmatism Guidelines

- **Dev-only code is held to a lower bar.** Files under `scripts/`, `tools/`, `dev/`, `local/`, or marked "dev only" in the file header get advisory-tier findings only — no blocking findings on convenience scripts that never touch prod.
- **Test fixtures and example IaC are OK.** A Dockerfile under `tests/fixtures/` or an example Terraform module under `examples/` with intentional smells is not flagged.
- **Match team conventions.** If the override file disables a category (e.g., a static-site repo has no DEV8 schema-migration surface), respect it. If the repo uses GitLab CI instead of GitHub Actions, the GitHub-specific rules in `ci-github-actions.md` don't fire.
- **Trust signals from the PR description.** If the author wrote "Known issue: X is out of scope, tracked in #N," do not re-flag X.
- **Monorepo per-package overrides** are honored — a service marked `internal-only: true` in its package metadata does not fire DEV11 runbook/CODEOWNERS findings.
- **Pre-existing infra debt is advisory.** If the code under review *already* contains an old pipeline antipattern not introduced by this PR/diff, note it in Advisory tier with a `(pre-existing)` marker; do not block.

## Working with Existing Antipatterns

If the code under review *already* contains an old DevOps antipattern not introduced by this PR/diff:
- Note it in Advisory tier with a `(pre-existing)` marker.
- Do not block the current PR on it.
- Recommend opening a separate issue.

Newly-introduced antipatterns (this PR adds them) are full-tier per the matrix.

## Team Overrides

Before applying DevOps rules, check for override files in this order:

1. `overrides.md` next to this `SKILL.md` (team-wide overrides bundled with the skill)
2. `.claude/ship-devops-overrides.md` in the user's project root (project-specific overrides)

Use overrides for:
- Disabled categories (e.g., a static-site repo with no DEV8 schema-migration surface).
- Severity overrides (e.g., escalate DEV11 to tier 1 for codebases with strict on-call SLOs).
- Platform exclusions (e.g., the repo uses GitLab CI, so suppress GitHub-Actions-specific patterns).
- Extra runbook/dashboard path patterns (e.g., your org keeps runbooks in a sibling `docs/runbooks/` directory).
- Ignored paths.

A template is at `overrides.example.md`.

## Team Adoption

Phased rollout recommended:
- **Weeks 1-4**: Enable DEV1, DEV4, DEV5, DEV9 only — the "OWASP-of-ops" core (pipeline, container, config, health). Build the review habit. Most teams ship at least one of these per quarter.
- **Month 2**: Add DEV2, DEV3, DEV6, DEV8 — the broader deploy-safety / IaC / observability / schema surface.
- **Month 3+**: Full DEV1-DEV12. Add DEV7 (release), DEV10 (SLO/perf), DEV11 (incident hygiene), DEV12 (flow/batch).

Track: tier-1 findings per PR (should trend toward zero); false-positive rate per category (if any category fires noisily, demote it via overrides).

## Related Skills

- **`ship-reviewed-prs`** — PR-level orchestrator. Its IN persona (Senior Infra / SRE / DevOps) delegates depth here, exactly as SC delegates to `ship-secure-code`. The orchestrator emits direct IN1–IN7 findings for high-precision single-line hits and `Run /ship-devops on <file>` delegation bullets for multi-file pipeline review. Compound finding tags `[IN1 / DEV2.1-NO-ROLLBACK]` surface this skill's category alongside the orchestrator's priority code. See `ship-reviewed-prs/reference-personas.md` § IN → Delegation to `ship-devops` for the full direct-emit-vs-delegate rubric.
- **`ship-secure-code`** — SEC7 owns hardcoded-secret-literal-in-code (the data leak). DEV5 owns sourcing-discipline (vault client, 12-factor, default-on-missing). On the same line both could fire; ship-secure-code wins for the user-facing finding, ship-devops adds a cross-reference. SEC1.4 (over-privileged service account) cross-cuts DEV4 (container `USER`) and DEV3 (IaC IAM); same tier-1 fires only once via the delegation parent. See `reference.md` § Anti-overlap for the full boundary.
- **`ship-clean-code`** — File-level code quality. DEV reviews operability, not style. A poorly-named Terraform variable is `ship-clean-code`; a Terraform module that mutates state without `terraform plan` is DEV3.
- **`ship-tested-code`** — Test design. DEV1 reviews whether tests *run in CI*, gate merge, and fail fast — not whether they're well-designed. The two are non-overlapping by intent.
- **`ship-debugged-code`** — Use after an incident to design the regression test, then run this skill to review the pipeline change that lands the fix.

## Reference Loading

For deeper analysis, load supporting reference files alongside this `SKILL.md`:

- `reference.md` — Methodology, sources (Three Ways, Four Types, CAMS), cross-cutting principles, anti-overlap with sibling skills, output schema for delegation.
- `reference-categories.md` — DEV1-DEV12 deep rubric: antipatterns, canonical fixes, false-positive notes, cross-references.
- `ci-github-actions.md` — GitHub Actions specific patterns (workflow YAML, action pinning, secret usage, gating).
- `iac-terraform.md` — Terraform-specific patterns (state, plan-gate, modules, drift, `moved {}`).
- `container-docker.md` — Dockerfile + compose patterns (`USER`, multi-stage, digest pinning, healthcheck, `.dockerignore`).
- `k8s.md` — Kubernetes manifest patterns (probes, resources, securityContext, PDB, rollout strategy, HPA).
- `observability.md` — Logging/metrics/tracing patterns (structured logs, golden signals, correlation, dashboards as code).
- `overrides.example.md` — Template for team overrides.
- `examples/review-example.md` — End-to-end review on a sample diff.
- `examples/fix-example.md` — One finding walked from identification through fix and verification.
- `tests/` — Self-test fixtures (sample input + expected report).

Paths are relative to this `SKILL.md`. Load on-demand when doing thorough reviews or when the user asks for detailed guidance on a specific topic.
