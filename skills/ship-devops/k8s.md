# Kubernetes Patterns

Concrete DEV2 / DEV4 / DEV9 / DEV10 patterns specific to Kubernetes manifests, Helm charts, and Kustomize overlays.

---

## DEV2 — DEPLOYMENT-SAFETY (k8s framing)

### DEV2.1 — Recreate strategy on traffic-serving workload

```yaml
spec:
  strategy:
    type: Recreate     # kills all pods before starting new ones
```

For a Deployment that serves traffic, this is a downtime window. Tier-1.

**Fix:**

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 0    # or 1, never 100%
```

### DEV2.2 — Big-bang `maxUnavailable`

```yaml
rollingUpdate:
  maxSurge: 0
  maxUnavailable: 100%
```

Equivalent to Recreate.

**Fix:** `maxUnavailable: 0` or `1` depending on replica count; `maxSurge` controls how fast the new version comes up.

### DEV2.3 — No PodDisruptionBudget

A workload that must remain available during node drains has no PDB.

**Fix:**

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api
spec:
  minAvailable: 1     # or maxUnavailable: 1
  selector:
    matchLabels:
      app: api
```

### DEV2.4 — Argo Rollouts / Flagger not used for sensitive services

For a service that should canary-rollout but uses a plain Deployment, the rollout is all-or-nothing once the new ReplicaSet exists.

**Fix:** use Argo Rollouts (`Rollout` CRD with `canary` or `blueGreen` strategy) or Flagger for traffic-weighted rollout.

---

## DEV4 — CONTAINER-IMAGE (k8s framing)

### DEV4.1 / SEC1.4 — securityContext gaps

**Antipatterns:**
- `securityContext` block absent.
- `runAsUser: 0` or `runAsNonRoot: false`.
- `allowPrivilegeEscalation: true` (default).
- `readOnlyRootFilesystem: false` for an app that doesn't write to disk.
- `capabilities: { add: [...] }` without justification.
- `automountServiceAccountToken: true` on a workload that doesn't call the k8s API.

**Fix:**

```yaml
spec:
  template:
    spec:
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        fsGroup: 10001
      containers:
        - name: api
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
```

For paths that need write access, use `emptyDir` volumes at the specific mount points.

---

## DEV9 — HEALTH-READINESS

### DEV9.1 — No probes

`Deployment.spec.template.spec.containers[].livenessProbe` and `readinessProbe` absent. k8s sends traffic immediately and never restarts a hung pod.

**Fix:**

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /readyz
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 3
```

### DEV9.2 — Liveness depends on downstream

```yaml
livenessProbe:
  httpGet:
    path: /healthz       # internally checks DB connection
```

When the DB hiccups, every pod restarts simultaneously → cascading failure.

**Fix:** liveness checks process health only; readiness checks dependency health. Separate endpoints, separate semantics.

### DEV9.3 — Slow boot without startup probe

Service takes 40s to warm caches; liveness fires at 30s and kills the pod before it ever serves traffic.

**Fix:**

```yaml
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  periodSeconds: 10
  failureThreshold: 30    # covers up to ~5 min boot
```

Liveness/readiness only start after `startupProbe` passes.

### DEV9.4 — No graceful shutdown / terminationGracePeriodSeconds

```yaml
spec:
  terminationGracePeriodSeconds: 5     # too short for an HTTP service draining
```

Or absent — defaults to 30, often fine, but verify against your service's drain time.

**Fix:** sized to the service's drain. Pre-stop hook to ask the app to start draining before SIGTERM:

```yaml
lifecycle:
  preStop:
    exec:
      command: ["/bin/sh", "-c", "kill -USR1 1 && sleep 15"]
terminationGracePeriodSeconds: 30
```

---

## DEV10 — SLO-PERFORMANCE

### DEV10.1 — Missing requests / limits (must-fix in shared clusters)

```yaml
containers:
  - name: api
    image: ...
    # resources block absent
```

Pod gets default QoS (BestEffort) — first to be evicted under pressure. No scheduling guarantees.

**Fix:**

```yaml
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

Set both. Derive numbers from observed usage (look at the metric over the last 30 days, take p95).

### DEV10.2 — HPA without resource requests

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

If the target Deployment has no `requests.cpu`, the HPA has nothing to measure against and won't scale.

**Fix:** HPA requires `requests` to be set on the workload.

### DEV10.3 — No timeout / circuit breaker for service-to-service

App code (cross-ref DEV10.2 in code) calls `http.get("http://other-svc")` with no timeout. k8s networking + flaky downstream = thread-pool exhaustion.

**Fix:** explicit timeouts in code; consider service mesh (Istio, Linkerd) for cluster-level timeout + retry policies.

---

## Helm chart checklist

Per template:

| Check | Antipattern | Pattern |
|-------|-------------|---------|
| Resource requests | Missing | `requests` + `limits` set, parameterized in `values.yaml` |
| Probes | Missing or liveness=readiness | Separate liveness/readiness; startup if slow boot |
| Security context | Missing or root | `runAsNonRoot`, `readOnlyRootFilesystem`, `capabilities: { drop: [ALL] }` |
| Image | Tag-only or floating | Pinned to digest via values |
| Strategy | `Recreate` on traffic-serving | `RollingUpdate` with `maxUnavailable: 0` |
| PDB | Missing | `minAvailable` set for production workloads |
| ConfigMap rollout | Manually triggered | `checksum/config` annotation triggers rollout on change |
| ServiceAccount | Uses default | Dedicated SA with minimum RBAC |
| Network policy | None | `NetworkPolicy` restricting ingress/egress |
| HPA | Absent on autoscale candidate | HPA with `behavior` block tuned |

---

## kubectl-apply gate

Before any `kubectl apply` against prod, the pipeline should run:

```sh
kubectl diff -f manifests/                       # shows what will change
kubectl apply --dry-run=server -f manifests/     # server-side validation
kubeconform manifests/                            # schema validation
kube-linter lint manifests/                       # policy checks
```

`kubectl diff` results posted as a PR comment make change review tractable. Failing `kubeconform` or `kube-linter` blocks the merge.
