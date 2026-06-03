# Expected Review Output — fixture-6-no-perf-budget

The skill should produce a report substantially matching the structure below. The **DEV10.1 + DEV10.2 tier-1 findings are non-negotiable**; wording can vary.

---

````
## DevOps Review: services/recommender/k8s/deployment.yaml, services/recommender/src/client.ts

### Confidence
Reviewed 2 files (~30 lines). Production Deployment for `recommender` calling `inventory` service over HTTP. The k8s workload has probes and a pinned image but no resource requests/limits. The client has no HTTP timeout. Two tier-1 findings drive the REQUEST_CHANGES decision.

### Critical (must fix before merge)

- **[DEV10.1-NO-RESOURCE-LIMITS] services/recommender/k8s/deployment.yaml**: Container has no `resources.requests` and no `resources.limits`. Pod gets BestEffort QoS — first evicted under cluster memory pressure, no scheduling guarantees. A noisy neighbor can starve `recommender` of CPU; a memory leak in `recommender` can crowd out other workloads. Deploy path: `apply → unconstrained pod scheduled anywhere → resource contention surprises in prod`. → Add:
  ```yaml
  resources:
    requests: { cpu: 250m, memory: 512Mi }
    limits:   { cpu: 1,    memory: 1Gi  }
  ```
  Derive numbers from a 30-day p95 of observed CPU/RSS on staging.

- **[DEV10.2-NO-HTTP-TIMEOUT] services/recommender/src/client.ts:7**: `fetch(...)` to the inventory service has no timeout. Node-fetch default is "wait forever." A slow or hung downstream blocks the calling request indefinitely, exhausts the connection pool, and cascades upstream. Deploy path: `inventory hiccup → recommender threads block on the fetch → recommender pool exhausted → upstream traffic stalls → outage spans services`. → Add an explicit timeout via `AbortController`:
  ```ts
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), 500); // ms; size to your SLO
  try {
    const res = await fetch(url, { signal: ctl.signal });
    // ...
  } finally {
    clearTimeout(t);
  }
  ```
  Consider also: retry with exponential backoff (bounded budget), circuit breaker (opossum, cockatiel), bulkhead on the connection pool.

### Important (should fix)

- **[DEV6.1-NO-OBSERVABILITY] services/recommender/src/client.ts:7**: the inventory call has no log line, no latency metric, no error counter. When the timeout fires (it will), the team has no signal beyond "recommender errors went up." → Wrap the call: log entry/exit with correlation id; histogram `inventory_client_duration_seconds`; counter `inventory_client_errors_total{kind=timeout|http_5xx|http_4xx}`.

- **[DEV10.X-NO-CIRCUIT-BREAKER] services/recommender/src/client.ts** (advisory): no circuit breaker. With a timeout in place the failure is bounded, but repeated failures still consume threads. → For a third-party-like dependency, wrap in `opossum` / `cockatiel`. For internal services, evaluate vs. service-mesh-level policies.

- **[DEV10.5-NO-SLO] services/recommender/** (advisory): no documented SLO. Without one, "is this latency OK?" is unanswerable. → Add `docs/services/recommender/slo.md` with availability target, latency target (p95, p99), and error-budget burn-rate alert rules.

### Advisory (hygiene)

- **[DEV3.X-IMAGE-SHA-NOT-DIGEST] services/recommender/k8s/deployment.yaml:11** (advisory): `image: myreg.io/recommender:abc123` — `abc123` is presumably a short SHA, but the manifest doesn't pin a digest. If the registry tag is moved (manually or by a misconfigured retag), the manifest would silently pull a different image. → `image: myreg.io/recommender:abc123@sha256:<full-digest>`.

### What's Good

- **Image pinned by SHA tag** — `abc123` (vs. `:latest`) gives an audit trail. Pair with a digest for full immutability (advisory above).
- **Both liveness and readiness probes** — separate paths (`/healthz`, `/readyz`); the team understands the distinction.
- **Required env via non-null assertion** — `process.env.INVENTORY_URL!` — fails loudly at boot if missing (DEV5.2 doesn't fire). For depth, replace with a validated config object that catches missing values *before* the first request.
- **Single concern per HTTP call** — the function fetches batch inventory and returns a typed `Map`. The bug is operability (no timeout), not structure.
````
