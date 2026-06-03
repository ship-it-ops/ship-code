# Synthetic Input for Fixture 6: Missing perf budget — no resource limits + no HTTP timeout

You are reviewing the following two files. Apply the `ship-devops` rubric.

## File: `services/recommender/k8s/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recommender
  namespace: prod
spec:
  replicas: 2
  selector:
    matchLabels:
      app: recommender
  template:
    metadata:
      labels:
        app: recommender
    spec:
      containers:
        - name: recommender
          image: myreg.io/recommender:abc123
          ports:
            - containerPort: 8080
          livenessProbe:
            httpGet: { path: /healthz, port: 8080 }
            initialDelaySeconds: 30
          readinessProbe:
            httpGet: { path: /readyz, port: 8080 }
            initialDelaySeconds: 5
```

## File: `services/recommender/src/client.ts`

```ts
import fetch from 'node-fetch';

const INVENTORY_URL = process.env.INVENTORY_URL!;

export async function getInventoryFor(productIds: string[]): Promise<Map<string, number>> {
  const res = await fetch(`${INVENTORY_URL}/batch?ids=${productIds.join(',')}`);
  if (!res.ok) throw new Error(`inventory: ${res.status}`);
  const body = await res.json();
  return new Map(Object.entries(body.stock));
}
```

---

Apply the ship-devops rubric and produce a structured review.
