# Synthetic Input for Fixture 7: Clean PR — expected to APPROVE

You are reviewing the following three files. Apply the `ship-devops` rubric. This is the "no critical findings" case used as a regression check.

The change adds a new endpoint to an existing service. Pipeline, IaC, and ops affordances are already in place from earlier work.

## File: `services/billing/src/routes/refund.ts`

```ts
import { Router } from 'express';
import { z } from 'zod';
import { logger, metrics } from '../observability';
import { requireAuth } from '../middleware/auth';
import { issueRefund } from '../service';

const RefundSchema = z.object({
  orderId: z.string().uuid(),
  amount: z.number().int().positive(),
  reason: z.string().min(1).max(280),
}).strict();

export const refundRoute = Router();

refundRoute.post('/refund', requireAuth, async (req, res, next) => {
  const correlationId = req.headers['x-correlation-id'] as string ?? crypto.randomUUID();
  const start = performance.now();
  logger.info({ event: 'refund.start', correlationId, userId: req.user.id });

  try {
    const body = RefundSchema.parse(req.body);
    const result = await issueRefund({ ...body, userId: req.user.id, correlationId });
    metrics.histogram('refund_duration_seconds', (performance.now() - start) / 1000, { status: 'ok' });
    logger.info({ event: 'refund.ok', correlationId, refundId: result.id });
    res.status(200).json(result);
  } catch (err) {
    metrics.histogram('refund_duration_seconds', (performance.now() - start) / 1000, { status: 'error' });
    metrics.counter('refund_errors_total', 1, { kind: err instanceof z.ZodError ? 'validation' : 'service' });
    logger.warn({ event: 'refund.error', correlationId, errKind: classify(err) });
    next(err);
  }
});

function classify(err: unknown): string {
  if (err instanceof z.ZodError) return 'validation';
  if (err instanceof Error && err.name === 'StripeError') return 'stripe';
  return 'unknown';
}
```

## File: `services/billing/k8s/deployment.yaml` (unchanged portion of an existing manifest, included for context)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: billing
  namespace: prod
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }
  template:
    spec:
      automountServiceAccountToken: false
      securityContext: { runAsNonRoot: true, runAsUser: 10001, fsGroup: 10001 }
      terminationGracePeriodSeconds: 30
      containers:
        - name: billing
          image: myreg.io/billing@sha256:bf8a3c... # v3.4.7
          securityContext: { allowPrivilegeEscalation: false, readOnlyRootFilesystem: true, capabilities: { drop: ["ALL"] } }
          ports: [{ name: http, containerPort: 8080 }]
          resources:
            requests: { cpu: 250m, memory: 512Mi }
            limits:   { cpu: 1,    memory: 1Gi  }
          livenessProbe:  { httpGet: { path: /healthz, port: http }, periodSeconds: 10 }
          readinessProbe: { httpGet: { path: /readyz,  port: http }, periodSeconds: 5 }
          startupProbe:   { httpGet: { path: /healthz, port: http }, periodSeconds: 10, failureThreshold: 30 }
          lifecycle:
            preStop:
              exec: { command: ["/bin/sh", "-c", "kill -USR1 1 && sleep 20"] }
```

## File: `services/billing/ops/dashboards/billing-refund.json` (new dashboard, abbreviated)

```json
{
  "title": "Billing — Refund",
  "panels": [
    { "title": "Refund p99 latency", "expr": "histogram_quantile(0.99, sum(rate(refund_duration_seconds_bucket[5m])) by (le))" },
    { "title": "Refund error rate",  "expr": "sum(rate(refund_errors_total[5m])) by (kind)" },
    { "title": "Refund traffic",     "expr": "sum(rate(refund_duration_seconds_count[5m]))" }
  ]
}
```

---

Apply the ship-devops rubric and produce a structured review.
