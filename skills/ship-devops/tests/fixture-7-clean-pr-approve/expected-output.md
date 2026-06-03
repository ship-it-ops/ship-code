# Expected Review Output — fixture-7-clean-pr-approve

The skill should produce a report substantially matching the structure below. **Zero tier-1 findings**; the decision is `APPROVE` (or `NO_FINDINGS` when run standalone). This fixture is the regression check that the skill doesn't over-fire on clean changes.

---

```
## DevOps Review: services/billing/src/routes/refund.ts, services/billing/k8s/deployment.yaml, services/billing/ops/dashboards/billing-refund.json

### Confidence
Reviewed 3 files (~80 lines). Change adds a `/refund` endpoint to the existing `billing` service. The k8s manifest (unchanged in this PR) already encodes most DEV4/DEV9/DEV10 disciplines; the new endpoint adds instrumentation and a dashboard alongside the code. No tier-1 findings; one advisory.

### Critical (must fix before merge)

None.

### Important (should fix)

None.

### Advisory (hygiene)

- **[DEV11.3-RUNBOOK-LINK] services/billing/ops/dashboards/billing-refund.json** (advisory): dashboard committed but no alert rules visible alongside. When refund p99 breaches SLO, the on-call should be paged with a link to this dashboard and a runbook entry. → Add `alerts/billing-refund.yml` with `RefundHighLatency` and `RefundHighErrorRate` rules, each carrying `runbook_url` and `dashboard_url` annotations.

### What's Good

- **Structured logging with correlation id** — every log line carries `correlationId`; downstream traces and metrics carry the same. DEV6.2 and DEV6.4 both satisfied.
- **Three of four golden signals** on the new endpoint — latency histogram, traffic (via histogram count), errors labeled by kind. DEV6.3 satisfied; saturation gauge optional but nice-to-have for a future PR.
- **Dashboard as code** — `billing-refund.json` in the repo, not a click-around dashboard. DEV6.5 satisfied.
- **Schema validation with `.strict()`** — Zod schema rejects extra fields; downstream code receives a narrow type. Prevents the partial-validation class of bug.
- **Image pinned by digest** — `myreg.io/billing@sha256:bf8a3c...` plus a comment for the human-readable tag. DEV4.2 satisfied with full immutability.
- **k8s securityContext properly configured** — non-root, no privilege escalation, read-only root FS, all capabilities dropped, SA token not mounted. DEV4.1 / SEC1.4 satisfied.
- **Probes properly separated** — liveness checks the process, readiness checks traffic-serving capability, startup probe covers slow boot. DEV9.1, DEV9.2, DEV9.3 all satisfied.
- **Graceful shutdown wired up** — `preStop` hook signals drain, `terminationGracePeriodSeconds` sized to drain time. DEV9.4 satisfied.
- **Resource requests and limits** — both set, balanced. Pod gets Guaranteed QoS. DEV10.1 satisfied.

### Decision

`APPROVE` (or `NO_FINDINGS` when run standalone).
```
