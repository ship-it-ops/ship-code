# DevOps Categories — Deep Rubric

For each of DEV1-DEV12: antipatterns, canonical fixes, common false-positives, cross-references to related categories.

---

## DEV1 — CI-PIPELINE

The merge-gate: what runs between `git push` and `merge`, how fast it gives feedback, and whether it actually blocks bad code.

### DEV1.1 — Floating action/image reference (must-fix in shared workflows)

**Antipatterns:**
- `uses: actions/checkout@main` / `@master` / `@v3` — floats to whatever tag points there today. A typosquat or compromised maintainer ships into your build.
- `uses: org/private-action@latest`.
- GitLab CI: `image: node:latest` / `image: node` (no tag).
- CircleCI: `docker: - image: cimg/node:current`.
- Jenkins: `agent { docker 'node' }` (no tag).
- `FROM node` in a Dockerfile used inside CI.

**Fix:** pin to a commit SHA (actions) or digest (images). `uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1`. `image: node:20.11.1-alpine@sha256:...`. Renovatebot / Dependabot keeps the pins fresh.

### DEV1.2 — Merge gate runs no real tests (must-fix)

**Antipatterns:**
- Workflow has `lint` and `format` jobs but no `test` job; merge protection requires only `lint`.
- `pytest tests/` runs but is `continue-on-error: true`, so a failure does not block the merge.
- Test job is in a separate workflow with no required-check rule.
- "All checks passed" on a PR with 0 checks (no workflow ran because the path filter excluded everything that changed).

**Fix:** every PR runs the test suite, and the test job is a required check in branch protection. `continue-on-error` reserved for *informational* matrix legs, not the canonical run.

### DEV1.3 — Slow feedback loop

**Antipatterns:**
- CI takes >15 min for the typical PR. Reviewers context-switch; defects compound.
- No caching: `actions/setup-node` without `cache: 'npm'`; `pip install -r requirements.txt` with no `pip` cache; Docker layer cache missing.
- No parallelism: all tests in one job; matrix of N items run sequentially with `max-parallel: 1`.
- Heavyweight tests (integration, e2e) run on every push without selection.

**Fix:** profile slowest jobs first; cache dependencies; split tests; run heavyweight stages only on `main` or via label.

### DEV1.4 — Skipped or disabled tests

**Antipatterns:**
- `@pytest.mark.skip` / `@unittest.skip` / `it.skip` / `xit` / `describe.skip` introduced in this PR with no linked issue.
- `pytest --ignore=tests/integration` baked into the CI command.
- `jest --testPathIgnorePatterns=...` newly added.
- Disabled GitHub Actions matrix legs: `if: false` / `if: ${{ false }}`.

**Fix:** delete the test or fix it. If neither is possible right now, mark with `@pytest.mark.xfail(reason=..., strict=True)` (or framework equivalent) and open an issue.

### DEV1.5 — Privileged CI tokens

**Antipatterns:**
- `permissions:` block missing or set to `write-all` at the workflow level (GitHub Actions defaults to `contents: read` only when `permissions:` is omitted on newer setups; older workflows inherit broad scopes).
- `GITHUB_TOKEN` exposed to PR-triggered workflows from forks (`pull_request_target` running untrusted code).
- Long-lived PATs (`secrets.PAT_TOKEN`) instead of GitHub App tokens or OIDC.
- AWS / GCP credentials in CI as static keys instead of OIDC federation.

### False positives

- Vendored action mirrors in a private org are sometimes referenced by branch name when the team has its own pinning policy (Renovate watches the mirror) — verify the override file.
- Dev-only workflows (`*-experimental.yml`, `*-staging.yml`) may legitimately float versions for fast iteration.

### Cross-refs

- SEC7 (secrets) — CI YAML with literal secret = SEC7.4.
- SEC8 (supply chain) — floating action ref = supply-chain risk.

---

## DEV2 — DEPLOYMENT-SAFETY

Whether the deploy can be undone, gradually rolled out, and validated before it owns the user.

### DEV2.1 — No rollback path (must-fix)

**Antipatterns:**
- Deploy script is `kubectl apply -f manifest.yaml` with no previous-revision tracking.
- `docker push prod:latest && docker pull prod:latest && restart` — the previous image is gone.
- Migration is irreversible (`DROP TABLE` / `DROP COLUMN`) committed in the same deploy as application code that depends on the drop.
- Helm release uses `--force` without `--atomic`.
- Lambda deploy overwrites `$LATEST` with no alias/version.

**Fix:** all deploys produce a previous-revision pointer. `kubectl rollout undo` works. `helm rollback` works. Lambda versions are pinned and aliases promoted. For migrations, see DEV8 — two-phase.

### DEV2.2 — Big-bang rollout (must-fix on user-facing services)

**Antipatterns:**
- `Deployment.strategy.type: Recreate` on a service that serves traffic.
- `maxSurge: 0, maxUnavailable: 100%` on RollingUpdate.
- ECS service deploy with `minimumHealthyPercent: 0`.
- No canary, no feature flag, no progressive rollout for a user-facing change with non-trivial blast radius.

**Fix:** RollingUpdate with surge / canary (`Argo Rollouts`, `Flagger`, weighted target groups) / feature flag wrapping the new code path. Document the cohort schedule.

### DEV2.3 — Deploy not idempotent

**Antipatterns:**
- Shell script that `mkdir`s without `-p`, `cp`s without overwriting, or appends to a config file with `>>` instead of templating it.
- Ansible playbook that runs `command: ...` (always changed) instead of `state: present`.
- `kubectl create` instead of `kubectl apply`.
- Terraform `null_resource` with a `local-exec` that mutates remote state.

**Fix:** desired-state tooling (Helm/Kustomize/Terraform). For shell, use `set -euo pipefail` and idempotent primitives (`mkdir -p`, `install -m`, declarative file generators).

### DEV2.4 — Missing pre-deploy validation

**Antipatterns:**
- Deploy job runs `apply` immediately on merge with no `plan`/`diff`/`dry-run`/`kubectl apply --dry-run=server`.
- No staging environment between PR and prod.
- No smoke test between deploy completion and "deploy succeeded" marker.

**Fix:** plan-or-diff stage as a separate, gating job; staging deploy precedes prod; post-deploy smoke runs against the prod target and gates promotion.

### DEV2.5 — Manual deploy steps

**Antipatterns:**
- README says "after CI passes, SSH into prod and run `deploy.sh` manually."
- Slack message describes the human handoff: "@oncall please cut the release."
- "Click Deploy in Vercel/Netlify/Heroku" listed as a release step.

**Fix:** automated deploy on tag/merge with explicit approval gates (environment-protected jobs), not human-executed steps.

### Cross-refs

- DEV8 — schema migrations are the most common source of "we can't roll back."
- DEV9 — rollback is only safe if you can observe the rollout.

---

## DEV3 — IAC-IMMUTABILITY

Whether infrastructure is in code, version-controlled, planned before changed, and reproducible.

### DEV3.1 — Hand-edited resource (must-fix when prod)

**Antipatterns:**
- Console clickops creating an S3 bucket, RDS instance, IAM role used by the new code, with no corresponding Terraform/Pulumi/CloudFormation change.
- `aws cli` commands in a runbook to "configure" the new resource.
- Drift between the deployed state and the repo (`terraform plan` shows pending destroys for things that should exist).
- Secret created via console and referenced by the new code (also DEV5 / SEC7).

**Fix:** import the resource into state, or recreate it from code. `terraform import`, `pulumi import`, `cfn-flip`. Plan-clean is part of definition-of-done.

### DEV3.2 — No remote state / no locking

**Antipatterns:**
- Terraform `terraform.tfstate` checked into git (also SEC7 — state can contain secrets in plain text).
- No backend block; local state only.
- S3 backend without DynamoDB lock table; concurrent applies race.

**Fix:** remote state with locking. S3 + DynamoDB, Terraform Cloud, GCS with object versioning + locking, or HashiCorp Consul.

### DEV3.3 — Provisioner with mutating shell

**Antipatterns:**
- `provisioner "local-exec"` running `aws cli` / `gcloud` / `kubectl` to mutate state that should be a resource.
- `null_resource` + `triggers: { always = timestamp() }` — runs on every apply.
- Inline curl/bash to install software on instances (use AMI/golden image or config-management tool).

**Fix:** model the side effect as a resource (Helm provider, k8s provider, AWS provider). For instance bootstrap, build a golden image (Packer) or use a config-management tool.

### DEV3.4 — Renamed resource without `moved {}` block

**Antipatterns:**
- Renaming a Terraform resource (`aws_s3_bucket.old` → `aws_s3_bucket.new`) without a `moved {}` block plans a destroy + recreate. For stateful resources, this is data loss.
- Module reorganization that changes addresses without `moved {}`.

**Fix:** every rename gets a `moved {}` block. Verify the plan is no-op.

### DEV3.5 — Environment drift

**Antipatterns:**
- `dev.tfvars`, `staging.tfvars`, `prod.tfvars` with diverged structure (prod has fields dev lacks; dev has fields prod lacks).
- Different module versions per environment.
- One-off resources in prod with no `dev` analog.

**Fix:** environments differ in *values*, not *structure*. Same module set, same variable set, different `.tfvars`.

### Cross-refs

- DEV5 — IaC that hardcodes secrets cross-refs SEC7.
- SEC1.4 — IaC that grants `*` IAM permissions.

---

## DEV4 — CONTAINER-IMAGE

Image hygiene: what's in it, who runs it, how it's built, and how it's pulled.

### DEV4.1 — Running as root (must-fix)

**Antipatterns:**
- Dockerfile with no `USER` directive (defaults to root).
- `USER root` set explicitly.
- `USER 0`.
- Multi-stage build where the final stage drops back to root.

**Fix:** `RUN addgroup -S app && adduser -S app -G app` then `USER app`. Verify with `docker inspect --format='{{.Config.User}}'`.

### DEV4.2 — Floating / unpinned base (must-fix)

**Antipatterns:**
- `FROM ubuntu:latest`, `FROM node`, `FROM python:3` (no minor pin).
- `FROM company/private-base:main`.
- Different tag in dev (`node:20`) vs CI (`node:20.11.1`) vs prod.

**Fix:** `FROM node:20.11.1-alpine@sha256:abc...`. The digest pins the exact image; the tag is for human reading.

### DEV4.3 — Single-stage build that includes build toolchain

**Antipatterns:**
- Final image includes `gcc`, `make`, `npm`, `pip`, source repositories, dev dependencies.
- Image size unexplained (e.g., 1.5 GB for a Node service that should be 200 MB).

**Fix:** multi-stage build. Final stage contains only the runtime and the built artifact.

### DEV4.4 — `.dockerignore` missing or insufficient

**Antipatterns:**
- No `.dockerignore` — `COPY . /app` pulls in `.git/`, `node_modules/`, `.env`, build artifacts, IDE configs.
- `.dockerignore` doesn't list `.env`, `.git`, `*.pem`, `.aws/`.

**Fix:** explicit `.dockerignore` allowlist or denylist matching the project. Verify image content with `docker run --rm -it image find / -name '.env'`.

### DEV4.5 — Secret in build

**Antipatterns:**
- `ARG NPM_TOKEN` followed by `RUN npm install` — the ARG value is in the image's build history.
- `RUN curl -H "Authorization: Bearer $TOKEN" ...` with the token in an env var that persists in a layer.
- `COPY .env /app/.env` (also SEC7).

**Fix:** BuildKit secrets (`RUN --mount=type=secret`), build-arg only for non-sensitive metadata.

### DEV4.6 — No HEALTHCHECK

**Antipatterns:**
- Dockerfile defines an HTTP service with no `HEALTHCHECK` instruction.
- HEALTHCHECK runs a heavyweight command (full smoke test) on every probe.

**Fix:** `HEALTHCHECK --interval=30s --timeout=3s --start-period=5s CMD curl -fsS http://localhost:8080/healthz || exit 1`. Cheap, fast, single concern.

### Cross-refs

- DEV9 — HEALTHCHECK pairs with k8s liveness/readiness.
- SEC1.4 — `USER root` is also a SEC tier-1 if framed as least-privilege.

---

## DEV5 — CONFIG-MGMT

How the application gets its config and secrets at runtime — sourcing discipline, not the literal leak surface.

### DEV5.1 — Config hardcoded in source (must-fix for prod values)

**Antipatterns:**
- `const DB_HOST = "db.prod.internal"` in code.
- Production URLs / connection strings / region codes in a checked-in `config.json` with no env-specific variant.
- Feature flag defaults baked in: `if (FEATURE_X_ENABLED)` where `FEATURE_X_ENABLED = true` is hardcoded.

**Fix:** read from env: `os.environ['DB_HOST']` / `process.env.DB_HOST` / `System.getenv("DB_HOST")`. For complex config, use a typed schema (Pydantic Settings, `zod` env validator, Spring `@ConfigurationProperties`).

### DEV5.2 — Silent fallback default for required value

**Antipatterns:**
- `const SECRET = process.env.SECRET ?? 'dev-secret'` — boots in prod with the dev secret if env is missing.
- `os.environ.get('DATABASE_URL', 'sqlite:///./dev.db')`.
- `redisHost := getenv("REDIS_HOST", "localhost")` — silently connects to nothing in prod.

**Fix:** fail loudly if required: `const SECRET = required('SECRET')` where `required` throws on missing. Validate config at boot before serving traffic.

### DEV5.3 — Same config artifact across environments

**Antipatterns:**
- `config.yaml` with no env distinction; deploy script reaches into it to "patch" values for prod.
- `application.properties` in the jar with prod values baked in.
- Same Helm `values.yaml` deployed to all envs with no per-env override.

**Fix:** per-env overrides (`values-prod.yaml`, profile-based Spring config, Kustomize overlays). The base file holds the structure; overrides hold the values.

### DEV5.4 — `.env` committed (cross-ref SEC7.2)

- `.env`, `.env.local`, `.env.production`, `.env.development` tracked by git.

**Fix:** `.gitignore` them; commit `.env.example` with placeholder values only. See SEC7.2 for the security framing — DEV5 owns the *config-source* framing (`.env` should never be the prod source even if it weren't leaked).

### DEV5.5 — Runtime-mutable config without versioning

**Antipatterns:**
- Feature flag service with no version pinning ("whatever Optimizely says right now").
- Live-reload of `config.yaml` from a shared volume; no audit trail of what was loaded when.

**Fix:** snapshot the config used at boot into logs/metrics; pin flag versions to a release for the SLO-critical paths.

### DEV5.6 — Per-env structure drift

- Prod config has fields dev lacks (silent prod-only code paths) or vice versa.

**Fix:** schema enforces presence in all envs; missing prod-only values fail validation at PR time.

### Cross-refs

- SEC7.1 — DEV5.1 with a recognized secret prefix is SEC7.1 (tier 1 security).
- DEV3 — IaC that supplies the config has its own rubric.

---

## DEV6 — OBSERVABILITY

Whether changes are visible in production: logs, metrics, traces, dashboards, alerts.

### DEV6.1 — User path with no instrumentation (must-fix)

**Antipatterns:**
- New HTTP endpoint logs nothing on success or failure.
- New background job has no "started/completed/failed" log or metric.
- New external API client wraps `fetch` with no latency/error metric.
- New cache code has no hit/miss metric.

**Fix:** structured log on entry/exit with correlation id; counter+histogram for the operation; for distributed flows, propagate trace context.

### DEV6.2 — Unstructured logging

**Antipatterns:**
- `console.log("user", user, "did", action)` — string concatenation, not queryable.
- `logger.info(f"checkout for user {user.id} succeeded in {ms}ms")`.
- Logs in mixed formats across services.

**Fix:** structured logger (Pino/Winston/Python `structlog`/Java SLF4J with logback JSON encoder). Fixed schema: `level`, `ts`, `service`, `correlation_id`, `event`, payload keys.

### DEV6.3 — Missing golden signals

Latency / Traffic / Errors / Saturation — at least three of the four for any user-impacting path.

**Antipatterns:**
- Metric reports `requests_total` (traffic only) — no latency, no error rate.
- Latency reported as average only (no histogram, no percentiles).
- No saturation metric for the queue/pool that throttles this code.

**Fix:** histogram for latency (p50/p90/p99/p999), counter for errors broken down by code, gauge for saturation. Use the framework's standard middleware where possible.

### DEV6.4 — No correlation across services

**Antipatterns:**
- Each service logs with its own request id; no trace id propagated.
- `X-Request-Id` accepted but not forwarded.
- Trace context dropped at the queue boundary (publishers don't attach, consumers don't read).

**Fix:** propagate the W3C `traceparent` header / equivalent across HTTP, gRPC, and queue boundaries. OpenTelemetry SDK handles most of this with auto-instrumentation.

### DEV6.5 — Dashboard or alert created in UI only

**Antipatterns:**
- Grafana / Datadog / NewRelic dashboard added by clicking around; no JSON / Terraform / dashboards-as-code commit.
- Alert thresholds defined in the UI; nobody knows what they are without logging in.

**Fix:** dashboard-as-code (Grafana JSON in repo, Datadog `dashboards` Terraform provider, jsonnet for Grafonnet). Alerts as code with the threshold rationale in commit message.

### DEV6.6 — PII in logs (cross-ref SEC9)

- `logger.info("user", user)` where `user` contains email/phone.

**Fix:** log identifiers, not contents. SEC9 owns the deep rubric.

### Cross-refs

- DEV11 — alerts feed on-call; alert quality is DEV11.
- SEC9 — PII leakage through logs.

---

## DEV7 — RELEASE-MGMT

Versioning, changelog, tags, breaking-change signaling, lockfile discipline.

### DEV7.1 — Breaking change shipped as patch/minor (must-fix on public APIs)

**Antipatterns:**
- `1.2.3 → 1.2.4` with a removed function in a published library.
- `fix:` commit in Conventional Commits that introduces a breaking change.
- Public API endpoint changes response shape without a versioned path.

**Fix:** bump major; add `BREAKING CHANGE:` footer; for HTTP APIs, version the route or use content negotiation.

### DEV7.2 — Missing or stale CHANGELOG

**Antipatterns:**
- Release tag created with no CHANGELOG entry.
- CHANGELOG entries written days after the release.
- `Unreleased` section grows but is never cut.

**Fix:** CHANGELOG entry is required for any user-visible change; release tooling cuts `Unreleased` into the new version automatically.

### DEV7.3 — Tag drift

**Antipatterns:**
- Tag `v1.2.3` points to a commit that doesn't match the npm/PyPI/Maven release.
- Tag created but not pushed.
- Re-tag without `-f` discipline (rewrites without history).

**Fix:** release pipeline creates and pushes the tag atomically with the artifact publish.

### DEV7.4 — Lockfile drift

**Antipatterns:**
- `package.json` changes a dep range; `package-lock.json` not regenerated.
- `pyproject.toml` updated; `poetry.lock` not committed.
- Lockfile resolved against a different registry mirror in CI vs. local.

**Fix:** CI step verifies lockfile is up to date (`npm ci`, `pnpm install --frozen-lockfile`, `poetry install --no-update` with a check). Block merge if drifted.

### DEV7.5 — Release artifacts unsigned

**Antipatterns:**
- Published package has no provenance / `.intoto.jsonl` / SBOM.
- Container image not signed (cosign).
- Released binary has no checksum file.

**Fix:** sign during publish; verify on install where possible.

### Cross-refs

- SEC8 — lockfile from non-registry source = SEC8.2.

---

## DEV8 — SCHEMA-MIGRATION

Database schema changes are the highest-blast-radius part of any deploy. Treat accordingly.

### DEV8.1 — Non-reversible migration in same deploy as dependent code (must-fix)

**Antipatterns:**
- Application code drops a field reference *and* migration drops the column in the same release. Rollback brings back code that reads the missing column.
- `DROP TABLE` paired with the feature that removes its last reader.
- Migration changes a column type non-reversibly (e.g., `varchar(255)` → `enum`).

**Fix:** two-phase migration. Release N stops writing; release N+1 stops reading; release N+2 drops the column. Each step is reversible alone.

### DEV8.2 — `ALTER TABLE` adds NOT NULL with no default

**Antipatterns:**
- `ALTER TABLE orders ADD COLUMN region VARCHAR(2) NOT NULL` on a table with rows. Fails immediately.
- Same with a default that requires a full table rewrite (Postgres < 11 for non-constant defaults).

**Fix:** add nullable column, backfill in batches, then add the NOT NULL constraint as a separate migration.

### DEV8.3 — Long-running lock on a hot table

**Antipatterns:**
- `ALTER TABLE users ADD INDEX ...` on a 100M-row table without `CONCURRENTLY` (Postgres) / `ALGORITHM=INPLACE, LOCK=NONE` (MySQL/InnoDB).
- Foreign key add without `NOT VALID` then `VALIDATE CONSTRAINT` (Postgres).
- `pg_repack` / `gh-ost` skipped on tables that need it.

**Fix:** use the online-DDL variant for your engine. Cap migration time; bail and retry if the lock isn't acquired within a budget.

### DEV8.4 — Forward-only migration tooling

**Antipatterns:**
- Tool used (Flyway/Alembic/Goose/Sequel) does not generate or accept a `down` script.
- `down` script is `raise NotImplementedError`.
- Down-migrations not tested.

**Fix:** every migration has a tested down. CI runs `up → down → up` on a representative dataset.

### DEV8.5 — Migration ordering not canary-safe

**Antipatterns:**
- Canary cohort runs new code against the *old* schema; the migration runs only after all instances are upgraded.
- Migration depends on data written by the new code that the old code hasn't yet produced.

**Fix:** migrations land *before* the code that depends on them; new code must work on both N and N+1 schemas for one release.

### Cross-refs

- DEV2 — DEV8 violations are the most common reason DEV2.1 (no rollback) fires.

---

## DEV9 — HEALTH-READINESS

Whether the platform can tell the difference between "starting", "alive", "ready", and "draining".

### DEV9.1 — No health endpoint (must-fix for k8s/ECS/Cloud Run workloads)

**Antipatterns:**
- New service ships with no `/healthz`, `/ready`, `/live`, or framework-equivalent.
- Health endpoint returns 200 unconditionally (`return Response("OK")`) — no actual check.
- Health endpoint requires auth (probes get 401).

**Fix:** dedicated unauthenticated endpoint that returns a structured payload. For k8s, separate liveness and readiness.

### DEV9.2 — Liveness depends on downstream

**Antipatterns:**
- `/healthz` checks DB connection; when DB hiccups, k8s restarts every pod simultaneously (cascading failure).
- Health probe runs full smoke test.

**Fix:** liveness checks *the process* (it can respond). Readiness checks *traffic-serving capability* (the DB is reachable). Different endpoints, different semantics.

### DEV9.3 — Missing startup probe on slow boot

**Antipatterns:**
- k8s `Deployment` with no `startupProbe` on a service that takes >10s to load models / warm caches / replay journal.
- Liveness fires during boot; pod gets killed before it ever serves traffic.

**Fix:** `startupProbe.failureThreshold` covers worst-case boot; liveness/readiness only fire after startup passes.

### DEV9.4 — No graceful shutdown / drain

**Antipatterns:**
- Deploy strategy interrupts in-flight requests because the service doesn't catch `SIGTERM`.
- `terminationGracePeriodSeconds: 0` or unset (defaults to 30s but service ignores SIGTERM).
- No pre-stop hook on services with non-trivial cleanup.

**Fix:** trap SIGTERM, stop accepting new work, drain in-flight, exit. Match k8s/ECS `terminationGracePeriod` to worst-case drain time.

### DEV9.5 — No post-deploy smoke

**Antipatterns:**
- Deploy job's success criterion is "kubectl rollout status returned 0."
- No external probe against the prod URL after rollout.

**Fix:** smoke step hits real endpoints (login, key API, the changed feature) against the deployed target and gates promotion.

### Cross-refs

- DEV4.6 — Docker `HEALTHCHECK` is the container-level analog.
- DEV2.4 — pre-deploy validation; DEV9.5 is the post-deploy analog.

---

## DEV10 — SLO-PERFORMANCE

SLOs, resource limits, timeouts, perf regression detection.

### DEV10.1 — k8s workload without resource limits/requests (must-fix in shared clusters)

**Antipatterns:**
- `Deployment.spec.template.spec.containers[].resources` empty or `requests` without `limits` (or vice versa).
- HPA configured but target workload has no `requests` (HPA has nothing to scale on).
- `limits.memory` < typical RSS — OOMKills.

**Fix:** set both `requests` and `limits`; derive from observed usage; alert on `limits` reached.

### DEV10.2 — No HTTP timeout / circuit breaker

**Antipatterns:**
- `fetch(url)` / `requests.get(url)` / `RestTemplate.exchange(...)` with no timeout argument — defaults are often "infinite" or absurdly long.
- HTTP client to a flaky downstream with no retry budget or circuit breaker.
- Database client without statement timeout.

**Fix:** explicit timeout on every external call (connect + read). Retries bounded by budget. Circuit breaker for downstream you don't control (Resilience4j, Polly, `tenacity`, manual).

### DEV10.3 — Perf regression undetected

**Antipatterns:**
- No perf test in CI; new endpoint quietly 5× slower than the old one.
- Load test exists but is never run as a gate.
- Benchmark numbers logged but not tracked over time.

**Fix:** perf test as part of pipeline (k6, Locust, autocannon, JMH for Java); baseline tracked; regression fails the build.

### DEV10.4 — Unbounded concurrency / queue (cross-ref SEC10)

**Antipatterns:**
- `Promise.all` over an untrusted-size list.
- Goroutine spawned per request with no limit.
- Queue consumer pulls without backpressure.

**Fix:** bounded concurrency; consumer respects queue depth; producer respects backpressure signals.

### DEV10.5 — SLO not stated

**Antipatterns:**
- New user-facing service ships with no SLO (availability, latency target).
- SLO defined but no error budget tracking.

**Fix:** SLO documented in the service README; SLI implementation in observability stack; error budget burn rate alerts.

### Cross-refs

- SEC10 — same antipattern family; DEV10 is the operability framing, SEC10 is the DoS framing.
- DEV6 — SLO requires SLIs, which are observability primitives.

---

## DEV11 — INCIDENT-HYGIENE

Whether the team can find out what changed, how to fix it, and who to wake up.

### DEV11.1 — No runbook for new prod service (must-fix on critical-path services)

**Antipatterns:**
- New service deployed to prod with no runbook in `docs/runbooks/<service>.md` (or wherever the team keeps them).
- Runbook is a single line ("page the owner").
- Runbook references tools that no longer exist.

**Fix:** runbook covers: ownership, dependencies, common alerts (link to dashboard, diagnosis steps, mitigation), escalation path. Tested in a game day.

### DEV11.2 — On-call doc stale

**Antipatterns:**
- `oncall.md` lists people who left the team.
- Escalation chain references a Slack channel that's been archived.
- "Last updated: 2 years ago."

**Fix:** ownership rotation captured in code (CODEOWNERS + on-call config); doc auto-references current state.

### DEV11.3 — Alert without runbook link

**Antipatterns:**
- New alert created with no `runbook_url`/`docs` field.
- Alert message is "Error rate high" with no link to investigation steps.
- Alert defined but no on-call test triggered it.

**Fix:** every alert has a `runbook_url` annotation; the linked page exists.

### DEV11.4 — Production-touching path missing from CODEOWNERS

**Antipatterns:**
- `services/checkout/` has no `CODEOWNERS` entry; PRs auto-merge with no owner review.
- CODEOWNERS uses a person who left the team.
- Wildcard `*` owner; nobody is actually accountable.

**Fix:** every production path mapped to a team in CODEOWNERS; CODEOWNERS-required-review enforced in branch protection.

### DEV11.5 — Fix PR with no post-mortem link

When a PR fixes a real prod incident (the diff contains an "incident: …" / "outage: …" reference, or the branch name encodes one):
- Missing link to the post-mortem doc → tier-2.
- Missing tests for the failure mode → cross-ref to ship-tested-code.
- Missing tripwire (alert that would catch the recurrence) → tier-2.

**Fix:** PR description links to the postmortem; tests added for the failure mode; alert added or existing alert tuned.

### Cross-refs

- DEV6.5 — alerts come from observability primitives.

---

## DEV12 — FLOW-BATCH

Size, age, and shape signals visible in the PR itself. Flag without moralizing.

### DEV12.1 — Oversized PR

**Antipatterns:**
- > 500 changed lines in a single PR with no clear surface boundary.
- > 30 files changed.
- Touches > 3 services.
- Mixes refactor + feature + dependency bump.

**Fix:** split. Land the refactor first, then the feature. Use feature flags to ship in pieces.

This category is **signal-based, not gating** — large PRs sometimes are correct (initial scaffolding, codemod). Tier-3 advisory unless the size correlates with rule violations elsewhere.

### DEV12.2 — Long-lived branch

**Antipatterns:**
- Branch `feature/x` open for > 14 days.
- Branch > 50 commits behind main.
- Repeated merges from main into the branch ("kept it up to date") instead of rebase or trunk-based.

**Fix:** trunk-based development; feature flags wrap unfinished work; branches live for hours/days, not weeks/months.

### DEV12.3 — WIP signals in commit history

**Antipatterns:**
- Commit messages "wip", "fixup", "tmp", "asdf", "save", "checkpoint" landed unsquashed.
- 50 commits with no semantic grouping.
- "Final final final.docx"-style noise.

**Fix:** rebase/squash before merge; commit messages explain the why.

### DEV12.4 — Partial work shipped without a flag

**Antipatterns:**
- New endpoint added that isn't called yet; no flag, no docs.
- New module exported but never imported.
- "Plumbing for X" commits with no flag and no PR linking the consumer.

**Fix:** wrap in a feature flag; or land plumbing + consumer together; or hold the PR until the consumer is ready.

### DEV12.5 — Atomic-commit violations

**Antipatterns:**
- One commit mixes the test, the implementation, the unrelated refactor, and the dependency bump.
- Commit message says "various improvements".
- A revert would necessarily revert unrelated work.

**Fix:** one logical change per commit; the message captures the why; reverts are surgical.

### False positives

- Initial scaffolding PRs and codemods are legitimately large.
- Some teams squash everything and lose the per-commit granularity intentionally — respect the override.
- Generated-file diffs (lockfiles, schema dumps) inflate line counts without semantic weight; subtract them from the size signal.

### Cross-refs

- DEV2.2 — big PRs increase the blast radius if rollout isn't progressive.

---

## Quick-Reference Severity Mapping

| Finding ID | Tier 1 (must-fix) trigger | Tier 2 trigger |
|------------|----------------------------|----------------|
| DEV1 | Merge gate runs no tests; floating action in shared workflow; CI tokens with broad scope | Slow feedback; skipped tests; missing cache |
| DEV2 | No rollback path; big-bang Recreate strategy on user traffic; non-idempotent prod deploy script | Manual deploy step; staging gap; missing post-deploy smoke |
| DEV3 | Hand-edited prod resource w/ no IaC backing; provisioner mutating prod state | Local state; renamed resource w/o `moved {}`; env drift |
| DEV4 | Running as root; floating base image; secret baked into image | Missing HEALTHCHECK; single-stage with toolchain; missing `.dockerignore` |
| DEV5 | Prod secret hardcoded; silent fallback default for required value; same config across envs | `.env` committed; runtime mutable w/o version; per-env structure drift |
| DEV6 | User path with no logs/metrics; PII in INFO logs | Unstructured logs; missing golden signals; dashboard in UI only |
| DEV7 | Breaking change shipped as patch/minor; lockfile drift on security-sensitive dep | Stale CHANGELOG; tag drift; unsigned artifact |
| DEV8 | Non-reversible migration with same-deploy code dep; NOT NULL w/o default on hot table | Long-running lock; forward-only tooling; non-canary-safe ordering |
| DEV9 | No health endpoint on k8s/ECS service; auth required on probe | Liveness depends on downstream; no startup probe; no graceful shutdown |
| DEV10 | Shared-cluster workload without resource limits; HTTP call without timeout | No perf test; no circuit breaker; SLO not stated |
| DEV11 | New critical-path service with no runbook; CODEOWNERS missing on prod path | Alert without runbook link; on-call doc stale; fix PR no post-mortem link |
| DEV12 | (advisory only) | Oversized PR + correlated rule violation; long-lived branch; partial work unflagged |
