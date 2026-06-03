# DevOps Reference

Methodology, sources, cross-cutting principles, and anti-overlap with sibling skills. The per-category rubric (antipatterns, fixes, false-positives) lives in `reference-categories.md`. Platform-specific patterns live in `ci-github-actions.md`, `iac-terraform.md`, `container-docker.md`, `k8s.md`, and `observability.md`.

---

## 1. Methodology

### Pipeline modeling at review time

Every DevOps review begins with an implicit pipeline-model question: **what changes does this PR push toward production, and through what path?** The reviewer maps:

1. **Triggers** — `git push`, tag creation, manual workflow_dispatch, scheduled job, external webhook.
2. **Stages** — lint, unit, integration, build, sign, publish, plan, apply, smoke, promote.
3. **Targets** — local, ephemeral PR env, staging, canary cohort, prod.
4. **Gates** — required checks, manual approvals, environment protection rules, branch protection.
5. **Artifacts** — built images, signed packages, infrastructure plans, deploy manifests.

A finding fires when a trigger → stage → target path lacks an appropriate gate, artifact lineage, or rollback. The output format requires the path to be explicit ("deploy path: trigger → action → blast radius").

### Severity is a function of two things

- **Reachability**: does the change reach prod automatically, on merge, on tag, or only via manual approval? Reachability scales severity up; non-prod paths scale it down.
- **Blast radius**: what does the failure mode affect? A failed migration on the primary database is high blast radius. A broken dev-only Makefile target is low. Severity scales with blast radius.

The skill's tier-1 / tier-2 / tier-3-5 split codifies these two axes. Tier-1 = reaches prod + high blast radius; tier-2 = secondary defense missing OR low-blast-radius path; tier-3-5 = hygiene and depth.

### What gets reviewed, what doesn't

| Reviewed | Skipped |
|----------|---------|
| CI workflows (`.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/config.yml`, `azure-pipelines.yml`) | Generated manifests (`*.generated.yaml`, files with `# DO NOT EDIT` header) |
| IaC (`*.tf`, `*.tf.json`, Pulumi `index.*`, CloudFormation `*.yaml`, Ansible `*.yml`, Chef `recipes/*.rb`, Puppet `*.pp`) | Vendored modules (`.terraform/`, `vendor/`, `node_modules/`) |
| Container files (`Dockerfile*`, `docker-compose.yml`, `*.dockerfile`, `.dockerignore`) | Binary blobs |
| k8s manifests (`*.yaml` containing `apiVersion`, Helm charts, Kustomize overlays) | Build outputs (`dist/`, `build/`, `.next/`) |
| Application code that touches deploy concerns (config loaders, health-check handlers, telemetry instrumentation, migration tooling) | Pure styling, formatting, lint config |
| Schema migrations (`migrations/*.sql`, Alembic/Flyway/Goose files) | Lockfiles (read for drift signal only, not full-text review) |
| Deploy scripts (`deploy/*.sh`, `scripts/release.*`, `Makefile` targets that mutate state) | Documentation that doesn't include runnable pipeline / IaC samples |
| Observability config (Prometheus alert rules, Grafana dashboards as JSON, OpenTelemetry collector configs) | Tests for non-deploy code (defer to ship-tested-code) |
| Process / ownership files (`CODEOWNERS`, `RUNBOOK.md`, `oncall.md`, on-call configs, runbook indexes) | |

Skipped categories are noted in the Confidence section with counts.

---

## 2. The 12 categories — high-level boundaries

### DEV1 — CI-PIPELINE

Owns: the merge gate. What runs, what passes, what blocks, how fast. Floating action references, missing test gates, slow feedback, skipped tests, privileged tokens.

- **Tier 1**: New workflow uses a floating action / image; merge gate has no real test; `continue-on-error: true` on the canonical test job; CI uses long-lived PAT with broad scope where OIDC is available.
- **Tier 2**: CI feedback >15 min; cache misconfigured; skipped tests added without a linked issue; matrix legs disabled silently.
- **Tier 3-5**: workflow-level `permissions:` block missing on a new workflow even though job-level ones exist; cache key not pinned to a lockfile hash.

### DEV2 — DEPLOYMENT-SAFETY

Owns: how the change reaches prod and how it gets undone. Rollback path, progressive rollout, idempotency, pre-deploy validation, post-deploy smoke.

- **Tier 1**: No rollback path on a user-facing deploy; `Recreate` strategy on a service that serves traffic; non-idempotent prod deploy script; deploy with no canary/flag for non-trivial blast radius.
- **Tier 2**: Manual deploy step; missing staging environment; missing post-deploy smoke; rollback path exists but is untested.
- **Tier 3-5**: Documentation of the rollback flow missing; rollout pauses not configured for canary.

### DEV3 — IAC-IMMUTABILITY

Owns: infrastructure as code. Drift, state, modules, provisioners, rename safety.

- **Tier 1**: Hand-edited prod resource with no IaC backing; provisioner mutating prod state; `terraform.tfstate` committed.
- **Tier 2**: Local state only; renamed Terraform resource without `moved {}`; environment files have diverged structure.
- **Tier 3-5**: Modules versioned by branch instead of tag; missing `required_providers` constraints.

### DEV4 — CONTAINER-IMAGE

Owns: image hygiene. `USER`, base, multi-stage, build secrets, HEALTHCHECK.

- **Tier 1**: Container runs as root in prod; base image floats / unpinned; secret baked into image build.
- **Tier 2**: Single-stage build pulls toolchain into runtime; missing `.dockerignore`; HEALTHCHECK absent on long-lived service.
- **Tier 3-5**: Image size unexplained; no SBOM.

### DEV5 — CONFIG-MGMT

Owns: how the application sources config and secrets at runtime. Env vs. vault, fallback discipline, per-env overrides, structure parity.

- **Tier 1**: Prod-required secret hardcoded; silent fallback default for required env value; same config artifact across envs with prod values baked in.
- **Tier 2**: `.env` committed (also SEC7.2); runtime-mutable config without version pinning; per-env structure drift.
- **Tier 3-5**: Boot-time config not snapshotted in logs; missing schema validation on config.

Anti-overlap with SEC7: ship-secure-code owns "this literal is a leaked credential" (data leak). ship-devops owns "this code reaches its secret via a fragile mechanism" (sourcing discipline). On the same line both can apply; SEC7 wins for the user-facing finding, DEV5 cross-references.

### DEV6 — OBSERVABILITY

Owns: how production changes become visible. Logs, metrics, traces, dashboards, alerts.

- **Tier 1**: New user-facing endpoint logs nothing on entry/exit; PII landing in INFO logs (cross-ref SEC9).
- **Tier 2**: Unstructured logging; missing golden signals; correlation IDs absent across the call chain; dashboard added only in the UI.
- **Tier 3-5**: Log levels inconsistent across services; metric naming inconsistent.

### DEV7 — RELEASE-MGMT

Owns: how artifacts go from commit to consumable. Versioning, CHANGELOG, tag policy, lockfile, signing.

- **Tier 1**: Breaking change shipped under a non-major version on a public library or API; lockfile drift on a security-sensitive dep.
- **Tier 2**: Missing or stale CHANGELOG; tag points at the wrong commit; published artifact unsigned.
- **Tier 3-5**: Conventional-commit footer missing; release notes lack migration guidance.

### DEV8 — SCHEMA-MIGRATION

Owns: schema changes and the deploy choreography around them. Two-phase, online DDL, reversibility, canary safety.

- **Tier 1**: Non-reversible migration shipped with code that depends on the new schema (rollback breaks); `ALTER TABLE` adds NOT NULL with no default on a populated hot table.
- **Tier 2**: Long-running lock on a hot table without online-DDL variant; forward-only tooling; ordering not canary-safe.
- **Tier 3-5**: Down-migration not exercised; migration not timed on staging.

### DEV9 — HEALTH-READINESS

Owns: liveness/readiness/startup probes, graceful shutdown, smoke tests.

- **Tier 1**: No health endpoint on a k8s/ECS/Cloud-Run service; health endpoint requires auth.
- **Tier 2**: Liveness depends on downstream (cascading failures); missing startup probe on slow boot; no graceful shutdown.
- **Tier 3-5**: Health response not structured; probe timeouts default; smoke test only on staging.

### DEV10 — SLO-PERFORMANCE

Owns: resource limits, timeouts, perf regression detection, SLOs.

- **Tier 1**: k8s workload missing `requests` and `limits` in a shared cluster; HTTP client to a third-party service with no timeout.
- **Tier 2**: No perf test in pipeline; no circuit breaker on flaky downstream; SLO not documented.
- **Tier 3-5**: HPA not configured on autoscale-eligible workload; alerting on average latency only.

### DEV11 — INCIDENT-HYGIENE

Owns: runbooks, on-call docs, alert quality, ownership, post-mortem traces.

- **Tier 1**: New critical-path service with no runbook; CODEOWNERS missing on a production path.
- **Tier 2**: Alert created without `runbook_url`; on-call doc references departed people; fix PR has no postmortem link when one exists.
- **Tier 3-5**: Runbook last-updated > 1 year; CODEOWNERS uses individuals instead of teams.

### DEV12 — FLOW-BATCH

Owns: PR shape signals visible in the diff. Size, age, partial-work, atomicity.

- **Tier 1**: (none — DEV12 is signal-based; tier-1 escalations come from correlation with rule violations in other categories).
- **Tier 2**: Oversized PR + correlated DEV2.1 / DEV8.1 violation (large + irreversible = high blast radius); long-lived branch (> 30 days behind main); partial work shipped without a flag.
- **Tier 3-5**: WIP commit messages unsquashed; atomic-commit violations.

---

## 3. Decision matrix (full)

Compute from the merged finding list:

| Condition | Decision (standalone run) | When invoked via ship-reviewed-prs IN delegation |
|-----------|---------------------------|--------------------------------------------------|
| Any tier-1 finding | `REQUEST_CHANGES` | Maps to IN1 / IN3 / IN5 / IN6 priority-1 at the parent level (per the IN↔DEV mapping in `ship-reviewed-prs/reference-personas.md`) |
| Only tier-2 findings | `COMMENT` | Maps to IN*.3 (priority-3) at parent |
| Only tier-3-5 findings | `COMMENT` | Maps to IN*.5+ (priority-5+) at parent |
| Zero findings | `APPROVE` (or `NO_FINDINGS`) | IN persona reports clean |

The skill never APPROVEs on a tier-1 finding regardless of overrides. `ci_max_decision: COMMENT` is honored for parent-skill submission but the skill's own report still names the finding as Critical.

---

## 4. Cross-cutting principles (expanded)

### 4.1 Automation: where to automate

Automate the **handoff**, not the artisanal skill. Deploys, IaC applies, image builds, migrations, smoke tests, rollbacks — all handoffs.

Things that should *not* be automated: the decision to deploy a risky change (gate it on human approval), the decision to bypass a failed check (don't bypass — fix the check or the code), incident response runbooks (have humans run them with tooling support, not vice versa).

Common mistakes:
- Auto-merge on green CI without a human review — the test suite isn't the only filter.
- Skipping `terraform plan` on the assumption that "it's just a small change."
- One-button rollback that doesn't restore data state alongside code.

Rule: every state change between commit and prod is either code-defined or human-approved. The skill flags state changes that are neither.

### 4.2 Reversibility: how to make a change undoable

Three mechanisms, used in combination:

1. **Two-phase migrations** for schema and contract changes. Release N stops writing the old shape; release N+1 stops reading it; release N+2 deletes it.
2. **Feature flags** for code paths. The new behavior ships disabled; ops flip it on after smoke; flip it off if something burns.
3. **Progressive rollout** (canary, blue/green, cohort) for everything else. The new version takes a slice of traffic; observability tells you whether to promote or roll back.

A change that uses none of these is a tier-1 DEV2.1 finding.

### 4.3 Observability is a feature, not a follow-up

Telemetry lands with the code that produces it. Logs / metrics / traces / dashboard updates appear in the same PR as the new endpoint, the new job, the new client.

Findings:
- **Telemetry deferred to "later"** → tier 2. There is no "later."
- **Telemetry present but in unstructured form** → tier 2; the data is unqueryable in an incident.
- **Telemetry missing on the user-facing path** → tier 1.

### 4.4 Fail closed in prod, fail loud in CI

Prod failure denies access / refuses requests / returns 500 with a clear correlation id. CI failure is loud, fast, and blocks merge.

The catch-and-continue antipattern is the most common operability bug in code that *looks* defended:
- Migration runner that catches the SQL error and continues.
- Deploy script that catches the kubectl error and reports "deploy succeeded."
- CI step with `|| true` appended to silence a flaky test.

### 4.5 Least-privilege at every layer

- CI tokens scoped to repo and minimum permission.
- Container `USER` non-root; capabilities dropped.
- IAM roles per-service, per-stage; OIDC federation over static keys.
- k8s service accounts mount only what they need; `automountServiceAccountToken: false` by default.
- Database users per-service with table-level grants.

DEV4, DEV5, DEV3 all carry sub-rules for their layer; cross-refs SEC1.4.

---

## 5. Anti-overlap with sibling skills

### vs. `ship-secure-code`

| Concern | Owned by | Boundary |
|---------|----------|----------|
| Hardcoded secret literal in code | SEC7.1 | The data-leak framing. SEC wins the user-facing finding. |
| Same hardcoded literal but framed as "wrong sourcing mechanism" | DEV5.1 | Cross-reference only; don't double-report. |
| `.env` committed | SEC7.2 + DEV5.4 | Both fire — SEC for the leak, DEV for the config-source. Parent skill merges. |
| Container running as root | SEC1.4 + DEV4.1 | SEC for least-privilege framing; DEV for image-hygiene framing. Same tier-1 fires once via parent. |
| Floating action reference / typosquat | SEC8.1 + DEV1.1 | SEC for supply-chain framing; DEV for pipeline-pinning framing. |
| PII in logs | SEC9 | SEC owns the deep rubric; DEV6 cross-refs. |
| Privileged CI token reaching forks | SEC1 + DEV1.5 | SEC for the auth/escalation surface; DEV for the workflow design. |

On overlap, the skill that owns the "user-impact" framing wins; the other cross-references.

### vs. `ship-clean-code`

`ship-clean-code` covers naming, structure, error handling, formatting — at the file level. `ship-devops` covers operability. A poorly named Terraform variable is ship-clean-code; a Terraform module that mutates state outside `terraform plan` review is DEV3.

### vs. `ship-tested-code`

`ship-tested-code` reviews test design. DEV1 reviews whether tests *run in CI*, *fail fast*, and *gate merge*. Non-overlapping by intent: the same test can be well-designed (clean-tested approves) and run in a workflow that doesn't gate merge (DEV1 flags). Both findings stand.

### vs. `ship-debugged-code`

After an incident, `ship-debugged-code` designs the regression test; `ship-devops` reviews the pipeline change that lands the fix and ensures the post-mortem link and alert tuning are present (DEV11.5).

### vs. `ship-reviewed-prs`

`ship-reviewed-prs` IN persona (Senior Infra / SRE / DevOps) is the **detection** orchestrator: it scans the diff with high-precision patterns for IN1-IN7 hits, then delegates depth to this skill. Specifically:

- Hits the IN orchestrator emits directly (high-confidence single-line patterns): floating action ref, missing `USER` in Dockerfile, missing `resources.limits` in Deployment, secret literal in workflow YAML, `fetch(url)` without timeout, `Recreate` strategy on traffic-serving Deployment.
- Hits the IN orchestrator turns into a delegation bullet: anything requiring multi-file pipeline trace (workflow + Dockerfile + manifest + migration in one PR), environment-context awareness (which env does this deploy reach?), migration-choreography reasoning (DEV8 depth), or compound DEV category overlap (e.g., DEV2 + DEV4 + DEV9 all firing across a single new-service PR).

The delegation is one-way: `ship-reviewed-prs` IN → `ship-devops`. Running `ship-devops` does not back-invoke `ship-reviewed-prs`.

Compound tagging: when invoked from delegation, this skill's findings appear in the orchestrator's output as `[INn / DEVm.t-LABEL]` so the parent's priority code and this skill's category are both visible. See `ship-reviewed-prs/reference-personas.md` § IN → IN ↔ DEV ID mapping for the full table.

---

## 6. Triage: file-bucketing for the skill

When invoked on a directory or PR diff, classify files first:

| Bucket | Heuristic | Action |
|--------|-----------|--------|
| `ci-pipeline` | `.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/config.yml` | Full review (DEV1, DEV2, DEV7) |
| `iac` | `*.tf`, `*.tf.json`, `Pulumi.yaml`, CloudFormation templates, Ansible playbooks | Full review (DEV3, DEV5) |
| `container` | `Dockerfile*`, `docker-compose.yml`, `*.dockerfile`, `.dockerignore` | Full review (DEV4) |
| `k8s-manifest` | YAML containing `apiVersion`/`kind` for k8s, Helm charts, Kustomize | Full review (DEV2, DEV9, DEV10) |
| `migration` | `migrations/*.sql`, Alembic versions, Flyway `V*__*.sql`, Goose | Full review (DEV8) |
| `deploy-script` | `deploy/*.sh`, `scripts/release.*`, `Makefile` targets that mutate state | Full review (DEV2) |
| `observability-config` | Prometheus rules, Grafana dashboards as JSON, OpenTelemetry collector config, alert YAML | Full review (DEV6, DEV11) |
| `code-deploy-touching` | App code that loads config, exposes health endpoints, emits metrics, runs migrations | Targeted review (DEV5, DEV6, DEV9, DEV10) |
| `process` | `CODEOWNERS`, `RUNBOOK.md`, `oncall.md`, runbook indexes | Targeted review (DEV11) |
| `generated`, `vendor` | Generated manifests, vendored modules | Skip; count in Confidence |
| `lockfile` | `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `Pipfile.lock`, `poetry.lock`, `Cargo.lock`, `terraform.lock.hcl` | Read for DEV7.4 drift; full-text not reviewed |

---

## 7. Output schema (machine-readable, for delegation)

When invoked from `ship-reviewed-prs` IN persona, the skill returns a structured object:

```json
{
  "scope": "services/api/Dockerfile, .github/workflows/deploy.yml",
  "summary": {
    "tier_1": 2,
    "tier_2": 1,
    "tier_3_5": 0
  },
  "findings": [
    {
      "id": "DEV4.1-IMAGE-ROOT-USER",
      "tier": 1,
      "path": "services/api/Dockerfile",
      "line": 8,
      "trigger": "git push to main",
      "action": "image built and pushed to prod registry",
      "blast_radius": "container compromise gives attacker root in pod",
      "fix": "RUN addgroup -S app && adduser -S app -G app\\nUSER app"
    }
  ],
  "what_good": [
    "Multi-stage build keeps toolchain out of final image",
    "Base image pinned by digest"
  ],
  "confidence": "Reviewed 1 Dockerfile + 1 workflow. Skipped helm-charts/generated/. Pipeline identified as Build → Push → Promote."
}
```

The parent skill maps this into its own decision matrix.

---

## 8. Quick-Reference Checklist

| Area | Key Question |
|------|--------------|
| Pipeline | Does the merge gate run real tests, on every PR, with pinned actions and minimum permissions? |
| Rollback | Can this change be undone within minutes, without manual intervention? |
| IaC | Is every prod resource defined in code, with a `plan`/`diff` gate before apply? |
| Image | Non-root `USER`, pinned base, multi-stage, no build-time secrets, HEALTHCHECK? |
| Config | Required values fail loudly on missing; per-env overrides; secrets sourced at runtime? |
| Observability | Logs + metrics + (where applicable) trace for the changed path; dashboard-as-code? |
| Release | Semver respected; CHANGELOG updated; tags signed and lockfile consistent? |
| Migration | Two-phase; reversible; online-DDL on hot tables; canary-safe ordering? |
| Health | `/healthz` + `/readyz` distinct; graceful shutdown; post-deploy smoke? |
| SLO/Perf | `requests`+`limits` set; timeouts on external calls; perf test as gate? |
| Incident | Runbook present; CODEOWNERS covers prod; alerts have `runbook_url`? |
| Flow | PR size appropriate to risk; partial work flagged; branch fresh? |

---

## 9. Sources

The rubric is grounded in three canonical DevOps texts and a working knowledge of the platforms it reviews:

- **The DevOps Handbook** (Kim, Humble, Debois, Willis, 2nd ed.). Primary source for DEV1, DEV2, DEV6, DEV11. The Three Ways framing maps to DEV1+DEV2 (Flow), DEV6+DEV11 (Feedback), and to the "small batches" emphasis in DEV12 (Continual Learning).
- **The Phoenix Project** (Kim, Behr, Spafford, 2013). Primary source for DEV12 (Four Types of Work — business projects, internal projects, changes, unplanned work — and the Theory-of-Constraints lens on the pipeline) and DEV11 (unplanned-work / firefighting tells).
- **Effective DevOps** (Davis, Daniels, O'Reilly 2016). Primary source for DEV5 (CAMS automation pillar applied to config), DEV11 (sharing pillar — runbooks, CODEOWNERS, on-call docs), and the PR-visible cultural signals in DEV12.
- **Accelerate** (Forsgren, Humble, Kim, 2018) — implicit source for the DEV10.5 / DEV11 metrics framing (deploy frequency, lead time, MTTR, change failure rate).
- **Site Reliability Engineering** (Beyer, Jones, Petoff, Murphy, eds., Google 2016) — implicit source for DEV9 (probes), DEV10 (SLO/error budget, golden signals), DEV11 (post-mortems).
- **OWASP CI/CD Top 10** (2022) — overlapping reference for DEV1.5 / DEV1.1 (privileged CI tokens, supply chain in pipeline).
- **CNCF / Kubernetes documentation**, **Terraform documentation**, **Docker best-practices** — platform-specific authoritative sources, captured in each platform reference file.

The skill's specific organization (12-category catalog, tier sub-tags, deploy-path output requirement, anti-overlap with ship-secure-code/ship-tested-code/ship-clean-code) is original to this repo and chosen for review legibility.
