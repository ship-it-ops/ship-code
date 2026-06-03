# DevOps Review Example

End-to-end demonstration of `ship-devops` running on a small change that ships a new HTTP service to k8s. The codebase is synthetic but representative — each finding maps to a real-world failure mode. The review output shows the structure the skill produces when invoked standalone.

---

## The PR under review

Three files. The diff: a new microservice ("packing-tracker") ships to prod via a new workflow and a Helm chart.

### `.github/workflows/deploy.yml`

```yaml
name: deploy
on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@main
      - uses: actions/setup-node@v4
      - run: npm install
      - run: npm test
        continue-on-error: true
      - run: docker build -t packing-tracker:latest .
      - run: docker push myregistry.io/packing-tracker:latest
      - run: kubectl apply -f k8s/
        env:
          KUBECONFIG_DATA: ${{ secrets.KUBECONFIG }}
          DEPLOY_KEY: sk_live_dEpL0Y_FakeBuTReal-ish
```

### `services/packing-tracker/Dockerfile`

```dockerfile
FROM node:20
WORKDIR /app
COPY . /app
RUN npm install
CMD ["node", "server.js"]
```

### `services/packing-tracker/k8s/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: packing-tracker
spec:
  replicas: 3
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: packing-tracker
  template:
    metadata:
      labels:
        app: packing-tracker
    spec:
      containers:
        - name: packing-tracker
          image: myregistry.io/packing-tracker:latest
          ports:
            - containerPort: 8080
```

---

## Review Output (what the skill produces)

```
## DevOps Review: .github/workflows/deploy.yml, services/packing-tracker/Dockerfile, services/packing-tracker/k8s/deployment.yaml

### Confidence
Reviewed 3 files (~55 lines). Pipeline identified as `push:main` → `npm build` → `docker push :latest` → `kubectl apply`. Skipped 0 generated files. The change adds a new microservice deploy path with no rollback signal, no observability, no health probes, root-running container, floating images and actions, and a hardcoded secret literal in the workflow. Seven tier-1 findings drive the REQUEST_CHANGES decision.

### Critical (must fix before merge)

- **[DEV1.2-MERGE-GATE-NO-TESTS] .github/workflows/deploy.yml:11**: `npm test` runs with `continue-on-error: true` — a failing test does not block the deploy. Deploy path: `push:main → npm test (informational) → docker push → kubectl apply`, so a regression ships unnoticed. → Remove `continue-on-error: true`; make the test step a required check on `main` via branch protection. Move the deploy job behind a separate workflow whose first step depends on the test workflow succeeding.

- **[DEV1.1-FLOATING-ACTION] .github/workflows/deploy.yml:8**: `uses: actions/checkout@main` floats to whatever `main` points to in the actions/checkout repo. A compromised maintainer or malicious commit ships into your build. Same risk with `actions/setup-node@v4` (line 9) — pinned to the major, still moves. → `uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1` and `uses: actions/setup-node@b39b52d1213e96004bfcb1c61a8a6fa8ab84f3e8 # v4.0.1`. Enable Renovate for automated digest bumps.

- **[DEV1.5-CI-PRIVILEGED] .github/workflows/deploy.yml:1-15**: Workflow has no `permissions:` block; on older repos it inherits broad scope, and a compromised step can push to other repos / branches. → Add top-level `permissions: { contents: read }` and grant per-job what's needed (e.g., `id-token: write` for OIDC cloud auth — replace `KUBECONFIG_DATA` secret with OIDC federation to the cluster).

- **[DEV5.1-SECRET-LITERAL-IN-WORKFLOW] .github/workflows/deploy.yml:15**: `DEPLOY_KEY: sk_live_...` is a literal secret in the workflow YAML, committed to git history forever. Cross-ref SEC7.4 (ship-secure-code owns the leak rubric — rotate immediately). DEV5 owns the source-discipline: secrets must come from `${{ secrets.NAME }}`. → `DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}` AND rotate the leaked key in the upstream provider AND audit git history.

- **[DEV4.1-IMAGE-ROOT-USER] services/packing-tracker/Dockerfile:1-5**: No `USER` directive; container runs as root. Cross-ref SEC1.4. → Add a non-root user: `RUN addgroup -S app && adduser -S app -G app` then `USER app` before `CMD`.

- **[DEV4.2-FLOATING-BASE] services/packing-tracker/Dockerfile:1**: `FROM node:20` floats inside the major. Today's `node:20` is `node:20.11.1`; tomorrow's may include a regression or a CVE. → `FROM node:20.11.1-alpine@sha256:6c381d5dc2a11dcdb693f0301e8587e43f440c90cdb8933eaaaabb905d44cdb9 # node:20.11.1-alpine`.

- **[DEV2.1-NO-ROLLBACK] .github/workflows/deploy.yml:12-13 + services/packing-tracker/k8s/deployment.yaml:8**: Image tagged `:latest` and pushed on every merge; previous image is overwritten. Combined with `strategy.type: Recreate` in the Deployment, a rollback requires manually pushing the previous image *and* downtime. Deploy path: `push:main → docker push :latest (overwrites) → kubectl apply (Recreate kills then starts)`. → Tag images by commit SHA (`packing-tracker:${{ github.sha }}`); pin the manifest to the same SHA; replace `Recreate` with `RollingUpdate` with `maxSurge: 25%, maxUnavailable: 0`; verify `kubectl rollout undo deployment/packing-tracker` works in staging.

### Important (should fix)

- **[DEV9.1-NO-HEALTH-PROBES] services/packing-tracker/k8s/deployment.yaml:14-18**: Container has no `livenessProbe` or `readinessProbe`. k8s sends traffic immediately on Pod start and never restarts a hung process. → Add probes against `/healthz` (liveness, process-only) and `/readyz` (readiness, dependency-aware). If boot is slow, also add `startupProbe`. The service must implement these endpoints; flag the missing application-side handlers as DEV9.1 too.

- **[DEV10.1-NO-RESOURCE-LIMITS] services/packing-tracker/k8s/deployment.yaml:14-18**: Container has no `resources.requests` or `resources.limits`. In a shared cluster, this pod gets BestEffort QoS — first evicted under pressure, no scheduling guarantees. → `resources: { requests: { cpu: 100m, memory: 256Mi }, limits: { cpu: 500m, memory: 512Mi } }`. Derive numbers from a load-test on staging.

- **[DEV6.1-NO-OBSERVABILITY] services/packing-tracker/k8s/deployment.yaml + Dockerfile**: New service with no log driver configured, no metrics endpoint, no dashboard committed alongside. → Application emits structured logs (Pino/Winston) with correlation IDs; exposes `/metrics` (Prometheus) with at least latency/traffic/errors; PR includes a Grafana dashboard JSON in `ops/dashboards/packing-tracker.json`.

### Advisory (hygiene)

- **[DEV4.4-NO-DOCKERIGNORE] services/packing-tracker/Dockerfile** (advisory): no `.dockerignore` visible; `COPY . /app` pulls in `.git/`, `node_modules/`, possibly `.env`. → Add a minimum `.dockerignore` covering `.git`, `node_modules`, `.env*`, `dist/`, `*.log`.

- **[DEV4.3-SINGLE-STAGE] services/packing-tracker/Dockerfile** (advisory): single-stage build leaves dev dependencies in the runtime image. → Multi-stage build: install in `builder`, copy `node_modules` into `runtime`. Image shrinks; surface area shrinks.

- **[DEV4.6-NO-HEALTHCHECK] services/packing-tracker/Dockerfile** (advisory): no `HEALTHCHECK` directive. k8s probes will do the job in cluster, but `docker run` (local + CI debugging) loses the signal. → `HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:8080/healthz || exit 1`.

- **[DEV11.1-NO-RUNBOOK] services/packing-tracker/** (advisory): new prod service without a runbook in `docs/runbooks/`. → Stub `docs/runbooks/packing-tracker.md` with ownership, dependencies, common alerts, and escalation; even a stub beats nothing.

- **[DEV11.4-CODEOWNERS] services/packing-tracker/** (advisory): no entry in `CODEOWNERS` covering the new service. → `services/packing-tracker/ @your-org/team-fulfillment`.

### What's Good

- **`replicas: 3`** is the right floor for a service that will sit behind a PDB. The team is thinking about availability.
- **`matchLabels` consistent** between Deployment selector and Pod template — selector failures are a common first-deploy bug, and this PR doesn't make it.
- **No secrets in the Dockerfile** — the `DEPLOY_KEY` leak is in the workflow only (still tier-1, still rotate, but the build pipeline didn't bake it into image layers).
```

---

## What this example demonstrates

1. **Deploy path is explicit in every Critical finding** — each lists trigger (where the change reaches prod), action (what happens there), and blast radius (what fails on failure). A reviewer can verify without reading the full file.
2. **Tier-1 is reserved for change-shipping-without-safety** — seven tier-1 findings: floating action, broken test gate, leaked secret, root container, floating base, no rollback. Each maps to "this change will cause an incident."
3. **Tier-2 covers operability gaps that won't blow up immediately** but will the next time the service is touched: no probes, no resource limits, no observability.
4. **Advisory tier is hygiene** — `.dockerignore`, multi-stage, runbook stub, CODEOWNERS. Improvements to land in the same PR or the next one.
5. **"What's Good" names specific disciplines that exist** — replicas floor, selector consistency, secrets-not-in-image. Evidence the reviewer engaged with the change, not just ran a checklist.
6. **Fix suggestions are platform-specific** — exact `RUN`/`USER`/digest/`resources` snippets. A reader can copy-paste.
