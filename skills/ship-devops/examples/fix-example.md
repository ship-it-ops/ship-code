# Fix Example: DEV2.1 No Rollback Path

Walkthrough of a single finding from identification through fix and post-deploy verification. Uses the no-rollback failure from `examples/review-example.md` as the worked example. The skill produces this kind of trace when asked "how do I fix [finding]?" interactively, but never auto-applies the patch.

---

## The finding

```
[DEV2.1-NO-ROLLBACK] .github/workflows/deploy.yml:12-13 + services/packing-tracker/k8s/deployment.yaml:8:

Image tagged :latest and pushed on every merge; previous image is
overwritten. Combined with strategy.type: Recreate in the Deployment,
rollback requires manually pushing the previous image and downtime.

Deploy path: push:main → docker push :latest (overwrites) →
              kubectl apply (Recreate kills then starts)

→ Tag images by commit SHA; pin the manifest to the same SHA;
  replace Recreate with RollingUpdate; verify kubectl rollout undo works.
```

## 1. Identify

Two co-located antipatterns combine to make the deploy irreversible:

**`.github/workflows/deploy.yml`:**

```yaml
- run: docker build -t packing-tracker:latest .
- run: docker push myregistry.io/packing-tracker:latest
```

The image at `myregistry.io/packing-tracker:latest` is overwritten on every merge. The previous image's digest still exists in the registry, but nothing points to it — the team would need to dig through registry history to find which digest was running ten minutes ago.

**`services/packing-tracker/k8s/deployment.yaml`:**

```yaml
spec:
  strategy:
    type: Recreate
  template:
    spec:
      containers:
        - name: packing-tracker
          image: myregistry.io/packing-tracker:latest
```

The manifest also pins to `:latest`. So even if `kubectl rollout undo` worked, the new ReplicaSet would pull the *current* `:latest`, which is the broken one. And `Recreate` strategy means the rollback (whichever direction) involves downtime: all pods die, then start.

## 2. Confirm the failure path

The deploy path the skill traced was:

```
push:main → npm build → docker build :latest → docker push :latest (overwrites previous)
         → kubectl apply (Recreate: terminate all, then start all)
         → ReplicaSet pulls latest (now the broken image)
```

Three steps; no rollback affordance at any of them. To roll back the team must:

1. Find the previous good image digest in the registry (no record of which one).
2. Re-push it as `:latest` (overwriting again — destroys the audit trail).
3. `kubectl apply` again — incurring another `Recreate` downtime.

This is roughly the worst possible deploy structure.

## 3. The Fix

Two changes that compose:

**Tag images by commit SHA. Pin the manifest to that SHA.**

`.github/workflows/deploy.yml`:

```yaml
env:
  IMAGE: myregistry.io/packing-tracker:${{ github.sha }}

steps:
  # ... build steps
  - run: docker build -t $IMAGE .
  - run: docker push $IMAGE
  - name: Patch image
    run: |
      yq -i '.spec.template.spec.containers[0].image = strenv(IMAGE)' \
        services/packing-tracker/k8s/deployment.yaml
  - run: kubectl apply -f services/packing-tracker/k8s/
```

Now every deploy has a unique image tag, the registry retains both versions, and the manifest history (in git) shows exactly which SHA was deployed when.

**Switch to RollingUpdate so deploys don't bottleneck on downtime.**

`services/packing-tracker/k8s/deployment.yaml`:

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 0
  template:
    spec:
      containers:
        - name: packing-tracker
          image: PLACEHOLDER   # patched by CI
```

`maxUnavailable: 0` means the rollout never reduces healthy capacity. `maxSurge: 25%` controls how fast new pods spin up.

**(Optional, recommended)** Add a `PodDisruptionBudget`:

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: packing-tracker
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: packing-tracker
```

This protects against node-drain-induced disruption — independent of deploys.

## 4. Verify

Rollback now works without manual archaeology:

```sh
# in staging
kubectl rollout undo deployment/packing-tracker
# k8s pulls the previous ReplicaSet's image — pinned to a real SHA, still in registry
kubectl rollout status deployment/packing-tracker --timeout=60s
# verify the rolled-back service is serving traffic
curl -fsS https://packing-tracker.staging.internal/healthz
```

Add this as a smoke test that runs in CI on every merge to staging:

```yaml
- name: Verify rollback works
  run: |
    PREV_RS=$(kubectl rollout history deployment/packing-tracker | tail -3 | head -1 | awk '{print $1}')
    kubectl rollout undo deployment/packing-tracker --to-revision=$PREV_RS
    kubectl rollout status deployment/packing-tracker --timeout=60s
    curl -fsS https://packing-tracker.staging.internal/healthz
    # restore current
    kubectl rollout undo deployment/packing-tracker
    kubectl rollout status deployment/packing-tracker --timeout=60s
```

## 5. Define the rollback runbook

Even with `kubectl rollout undo`, the human running it at 3 AM needs a one-page script. Add `docs/runbooks/packing-tracker.md`:

```markdown
# Packing Tracker — Runbook

## Rollback

1. `kubectl rollout undo deployment/packing-tracker -n prod`
2. Watch: `kubectl rollout status deployment/packing-tracker -n prod`
3. Verify: `curl -fsS https://api.example.com/packing/healthz`
4. Confirm metrics recovered:
   - `packing_request_duration_seconds` p99 < 500ms
   - `packing_errors_total` rate < 1%
5. Post in #incident-fulfillment with the commit SHA you rolled back from and to.

## Common alerts

- `PackingTrackerHighErrorRate` — > 5% 5xx for 5m → rollback usually right.
- `PackingTrackerHighLatency` — p99 > 2s for 5m → check downstream `inventory-svc` first; if healthy, rollback.
- `PackingTrackerPodCrashLoop` — likely a misconfigured env var; check ConfigMap diff.

## Dependencies

- `inventory-svc` — read RPC, timeout 200ms
- `orders-db` — read+write, connection pool 20

## Ownership

- Code: `@your-org/team-fulfillment` (CODEOWNERS)
- On-call: PagerDuty schedule `fulfillment-primary`
```

The runbook closes the loop on DEV11.1 (now satisfied) and DEV11.3 (alerts reference real diagnostic steps).

## 6. The combined diff

A single PR lands:

1. `deploy.yml` — SHA tagging + manifest patch step.
2. `deployment.yaml` — RollingUpdate strategy + placeholder image.
3. `pdb.yaml` — PodDisruptionBudget (new file).
4. `docs/runbooks/packing-tracker.md` — runbook (new file).
5. `CODEOWNERS` — add `services/packing-tracker/`.

After this PR, re-running `ship-devops` on the same diff produces no DEV2 / DEV11 findings. The DEV4 and DEV9 findings from the original review are still open and would land in follow-up PRs — incremental progress is the right shape; bundling everything into one giant fix would itself fire DEV12.1.
