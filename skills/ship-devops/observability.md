# Observability Patterns

Concrete DEV6 / DEV11 patterns for logs, metrics, traces, dashboards, and alerts. Vendor-neutral where possible — patterns translate across Datadog, NewRelic, Grafana stack, Honeycomb, AWS CloudWatch.

---

## DEV6 — OBSERVABILITY

### DEV6.1 — User-facing path with no instrumentation (must-fix)

**Detection:** new code that's a request handler, queue consumer, scheduled job, or external API client, but no log line, metric, or trace span is added/used.

**Antipatterns (TypeScript):**

```ts
export async function POST(req: Request) {
  const body = await req.json();
  const result = await createOrder(body);
  return Response.json(result);
}
```

No log, no metric, no trace. When this fails in prod, the team has nothing to grep.

**Fix:**

```ts
import { logger, metrics } from '@/observability';

export async function POST(req: Request) {
  const correlationId = req.headers.get('x-correlation-id') ?? crypto.randomUUID();
  const start = performance.now();
  logger.info({ event: 'order.create.start', correlationId });

  try {
    const body = await req.json();
    const result = await createOrder(body);
    metrics.histogram('order.create.duration_ms', performance.now() - start, { status: 'ok' });
    logger.info({ event: 'order.create.ok', correlationId, orderId: result.id });
    return Response.json(result);
  } catch (err) {
    metrics.histogram('order.create.duration_ms', performance.now() - start, { status: 'error' });
    metrics.counter('order.create.errors', 1, { errorKind: classify(err) });
    logger.error({ event: 'order.create.error', correlationId, err: serializeError(err) });
    throw err;
  }
}
```

### DEV6.2 — Unstructured logging

**Antipatterns:**
- `console.log("user", userId, "did", action, "in", ms, "ms")`.
- `print(f"order {order_id} ok")`.
- `logger.info("checkout failed: " + err.message)`.

**Fix:** structured logger with a fixed schema. Pino / Winston (Node), `structlog` (Python), SLF4J + logback JSON encoder (Java), `slog` (Go).

```ts
// Pino
logger.info({ event: 'checkout.failed', userId, errorKind: classify(err) });
```

Required fields: `level`, `ts`, `service`, `env`, `correlation_id`, `event`, plus event-specific keys. Forbidden in user-impact logs: PII (see SEC9), full request bodies, raw stack traces (use a serializer).

### DEV6.3 — Missing golden signals

For any user-impacting operation, the skill expects three of four:
- **Latency**: histogram with explicit buckets (don't rely on the default).
- **Traffic**: counter of operations.
- **Errors**: counter labeled by error kind.
- **Saturation**: gauge for the pool/queue/connection-count that throttles this operation.

**Antipatterns:**
- Only `requests_total` (traffic only).
- Latency reported as `mean`/`avg` (loses tail).
- Errors counted but not labeled (`errors_total` without `kind`/`status_code`).

**Fix (Prometheus client):**

```ts
const orderLatency = new Histogram({
  name: 'order_create_duration_seconds',
  help: 'Latency of POST /orders',
  labelNames: ['status'],
  buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
});

const orderErrors = new Counter({
  name: 'order_create_errors_total',
  help: 'POST /orders errors by kind',
  labelNames: ['kind'],
});
```

Histogram buckets matter: defaults rarely match your SLO. Pick buckets around your latency target.

### DEV6.4 — No correlation across services

**Antipatterns:**
- Service A logs `request_id: abc`; service B (called by A) logs its own `request_id: xyz`; no link.
- `X-Request-Id` accepted on ingress but not propagated to downstream HTTP / queue calls.
- Tracer SDK installed but auto-instrumentation off for the http client.

**Fix:** propagate W3C `traceparent` (and `tracestate`) across all boundaries:
- HTTP server reads it; HTTP client writes it.
- Queue publisher attaches as message attribute; consumer extracts.
- Cron / scheduler creates a new root trace context.

OpenTelemetry auto-instrumentation handles most languages.

### DEV6.5 — Dashboard / alert in UI only

**Detection:** PR introduces a new metric / log event, but the Grafana folder / Datadog dashboards-as-code module / Terraform `*_dashboard` resource has no corresponding change.

**Fix:** dashboards in repo:
- Grafana: `dashboards/<service>.json` (or jsonnet / grafonnet); deployed by CI via `grizzly` or the Grafana provider.
- Datadog: `terraform-provider-datadog` `datadog_dashboard_json` resources.
- CloudWatch: `aws_cloudwatch_dashboard` Terraform resources.

The dashboard PR ships in the same change as the metric.

### DEV6.6 — PII in logs

`logger.info({ user })` where `user` includes email, phone, SSN, full request body.

**Fix:** log identifiers, not entities. `logger.info({ userId: user.id })`. SEC9 owns the rubric depth.

---

## DEV11 — INCIDENT-HYGIENE (alert-quality framing)

### DEV11.3 — Alert without runbook link

**Antipatterns (Prometheus alert):**

```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  annotations:
    summary: "High error rate"
```

No `runbook_url`, no `description`, no severity.

**Fix:**

```yaml
- alert: APIHighErrorRate
  expr: |
    sum(rate(http_requests_total{service="api",status=~"5.."}[5m]))
    / sum(rate(http_requests_total{service="api"}[5m])) > 0.05
  for: 5m
  labels:
    severity: page
    team: api
  annotations:
    summary: "API 5xx rate above 5% for 5m"
    description: |
      The api service is returning 5xx on more than 5% of requests
      over the last 5 minutes. Check {{ $labels.instance }}.
    runbook_url: "https://runbooks.internal/api/high-error-rate"
    dashboard_url: "https://grafana.internal/d/api-overview"
```

Every alert that pages a human:
- Has `runbook_url` pointing to a real page.
- Has a `summary` you can read at 3 AM.
- Has a `for:` duration to avoid flapping.
- Is grouped to avoid storm.

### DEV11.4 — Alert thresholds copy-pasted

New alert reuses thresholds from another service that doesn't have the same SLO. Either too sensitive (alert fatigue) or too lax (missed incidents).

**Fix:** thresholds derived from the service's SLO. `for:` duration matches the time-to-burn budget.

---

## Logging schema (canonical)

A consistent log schema across services makes incident response tractable. Suggested minimum:

```json
{
  "ts": "2026-06-02T14:32:18.123Z",
  "level": "info",
  "service": "api",
  "env": "prod",
  "version": "v1.42.0",
  "host": "api-7f9d-xyz",
  "correlation_id": "01HXYZ...",
  "trace_id": "01HXYZ...",
  "span_id": "01HXYZ...",
  "event": "order.create.ok",
  "userId": "u-123",
  "orderId": "o-456",
  "duration_ms": 87
}
```

The reviewer flags new log lines that don't match this schema.

---

## Metric naming (canonical)

Follow Prometheus / OpenMetrics conventions:

- Suffix tells you the type: `_total` (counter), `_seconds` (histogram for time), `_bytes` (histogram for size), `_count` (gauge for current count).
- Lowercase, snake_case.
- Include the unit (`_seconds`, not `_ms` — convert at query time).
- Labels are dimensions, not data: `{service="api", status="500"}` is fine; `{user_id="123"}` is unbounded cardinality and will kill your TSDB.

The reviewer flags:
- High-cardinality labels (`user_id`, `order_id`, `request_id`).
- Naming that doesn't reveal the type.
- Units in the name.

---

## File checklist

| Check | Antipattern | Pattern |
|-------|-------------|---------|
| Logs on user paths | Print/console.log only | Structured logger, correlation id, fixed schema |
| Golden signals | One of four | At least three of four (latency, traffic, errors, saturation) |
| Histograms | Default buckets | Buckets tuned to SLO |
| Correlation | New ID per service | Propagated `traceparent` / `correlation_id` |
| Dashboards | Created in UI | Committed as code (JSON / jsonnet / Terraform) |
| Alerts | No runbook link | `runbook_url` + `summary` + `for` |
| Cardinality | User/order id as label | Identifier in log, not in metric label |
| PII | Full user object in log | Identifier only; serializer strips sensitive fields |
