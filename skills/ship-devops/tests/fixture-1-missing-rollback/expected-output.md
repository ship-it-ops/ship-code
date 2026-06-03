# Expected Review Output — fixture-1-missing-rollback

The skill should produce a report substantially matching the structure below. The **DEV2.1 tier-1 finding is non-negotiable**; wording can vary.

---

```
## DevOps Review: .github/workflows/deploy.yml, services/api/k8s/deployment.yaml

### Confidence
Reviewed 2 files (~45 lines). Pipeline: `push:main → npm test → docker push :latest → kubectl apply` against the prod namespace. Skipped 0 generated files. CI hygiene is good (pinned actions, cached deps, real test gate). The deploy path is the failure — image overwrites :latest with no SHA-pinned trail, and `strategy: Recreate` makes every rollout (forward or back) a downtime event. One tier-1 finding drives the REQUEST_CHANGES decision.

### Critical (must fix before merge)

- **[DEV2.1-NO-ROLLBACK] services/api/k8s/deployment.yaml:9-10 + .github/workflows/deploy.yml:14-15**: Image tagged `:latest` and pushed on every merge; previous image is overwritten in the registry. Manifest pins to `:latest`, so even `kubectl rollout undo` would re-pull the broken image. Combined with `strategy.type: Recreate`, every rollout terminates all pods before starting the new ones — downtime in both directions. Deploy path: `push:main → docker push :latest (overwrites previous) → kubectl apply (Recreate kills, then starts)`. → Tag images by commit SHA: `myreg.io/api:${{ github.sha }}`; patch the manifest in CI to that SHA; switch strategy to `RollingUpdate` with `maxSurge: 25%, maxUnavailable: 0`; verify `kubectl rollout undo deployment/api -n prod` works in staging.

### Important (should fix)

- **[DEV2.3-NO-PDB] services/api/k8s/deployment.yaml**: 4 replicas in prod with no `PodDisruptionBudget`. Node drains during cluster maintenance can take all 4 pods down. → Add `policy/v1 PodDisruptionBudget` with `minAvailable: 3` selecting `app: api`.

### Advisory (hygiene)

- **[DEV1.5-CI-PERMISSIONS] .github/workflows/deploy.yml** (advisory): no top-level `permissions:` block. → `permissions: { contents: read, id-token: write }` and use OIDC for the kubectl auth.

### What's Good

- **Pinned actions by SHA** — `actions/checkout` and `actions/setup-node` reference full commit hashes with version comments. Renovate-friendly.
- **Real test gate** — `npm test` runs without `continue-on-error`; a failure blocks the deploy job.
- **Cache configured** — `cache: 'npm'` on setup-node keeps CI fast on subsequent runs.
- **Resource limits set** — `requests` and `limits` defined for both CPU and memory; pod gets Guaranteed QoS.
- **Health probes present** — separate `livenessProbe` and `readinessProbe`. The team understands the distinction.
```
