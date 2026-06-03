# Expected Review Output — fixture-5-missing-health-check

The skill should produce a report substantially matching the structure below. The **DEV9.1 tier-1 finding (prod namespace) is non-negotiable**; wording can vary.

---

````
## DevOps Review: services/notifications/k8s/deployment.yaml

### Confidence
Reviewed 1 manifest (~35 lines). New production Deployment for `notifications` service (label `team: messaging`, namespace `prod`). RollingUpdate, resource limits set, secret-sourced redis URL. The single critical gap is health: no liveness, readiness, or startup probes. One tier-1 finding drives the REQUEST_CHANGES decision.

### Critical (must fix before merge)

- **[DEV9.1-NO-HEALTH-PROBES] services/notifications/k8s/deployment.yaml**: Production Deployment has no `livenessProbe` and no `readinessProbe`. k8s sends traffic to the pod the moment the container starts (not when it's actually ready), and never restarts a hung process. Deploy path: `kubectl apply → pod starts → service endpoints include the new pod immediately → traffic served against a not-yet-warmed-up app → first-N requests fail`. → Add probes:
  ```yaml
  livenessProbe:
    httpGet: { path: /healthz, port: http }
    initialDelaySeconds: 30
    periodSeconds: 10
    failureThreshold: 3
  readinessProbe:
    httpGet: { path: /readyz, port: http }
    initialDelaySeconds: 5
    periodSeconds: 5
    failureThreshold: 3
  ```
  Liveness checks the process can respond (no downstream dependencies). Readiness checks the service is ready to serve traffic (Redis reachable, queues drained, etc.). The app must implement these endpoints — a flag on the application code review.

### Important (should fix)

- **[DEV2.3-NO-PDB] services/notifications/k8s/deployment.yaml**: 3 replicas in prod with no PodDisruptionBudget. A simultaneous node drain (cluster upgrade, autoscaler scale-down) can take all 3 down. → Add `policy/v1 PodDisruptionBudget` with `minAvailable: 2` selecting `app: notifications`.

- **[DEV9.4-NO-GRACEFUL-SHUTDOWN] services/notifications/k8s/deployment.yaml**: no `terminationGracePeriodSeconds` set (defaults to 30s) and no `preStop` hook. For a message-processing service, in-flight work may be dropped on rollout. → Set `terminationGracePeriodSeconds: 60` and add `lifecycle.preStop` to ask the app to start draining: `exec: { command: ["/bin/sh", "-c", "kill -USR1 1 && sleep 20"] }` (assuming the app handles USR1 as drain signal).

### Advisory (hygiene)

- **[DEV4.X-AUTOMOUNT-SA-TOKEN] services/notifications/k8s/deployment.yaml** (advisory): `automountServiceAccountToken` not set. If the service doesn't call the k8s API, mounting the SA token is unnecessary surface. → `spec.template.spec.automountServiceAccountToken: false`.

- **[DEV6.1-OBSERVABILITY] services/notifications/k8s/deployment.yaml** (advisory, application-side): no annotation enabling Prometheus scraping (`prometheus.io/scrape: "true"`, `prometheus.io/port: "8080"`), no sidecar for log forwarding visible. Verify telemetry is enabled cluster-wide or annotate the pod.

- **[DEV11.1-NO-RUNBOOK] services/notifications/** (advisory): new prod service — verify `docs/runbooks/notifications.md` exists in the same PR or in a near-term follow-up.

### What's Good

- **RollingUpdate with maxUnavailable: 0** — no capacity dip during rollouts. The team understands availability.
- **Resource requests + limits set** — pod gets Guaranteed QoS; no surprise OOM-kills, no first-to-be-evicted under pressure.
- **Secret-sourced env vars** — `REDIS_URL` from `secretKeyRef`, not a literal. DEV5.1 doesn't fire.
- **Named port** — `name: http` on the containerPort, then probes can reference it by name (more refactor-safe than a number).
- **Team label** — `team: messaging` enables ownership-aware routing of alerts and dashboards.
````
