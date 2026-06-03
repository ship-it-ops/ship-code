# Synthetic PR Input for Fixture 9: DevOps delegation

You are reviewing the following PR. Treat the input below as the result of the `gh` fetch phase.

This PR adds a new microservice (`packing-tracker`) and ships a workflow, Dockerfile, and k8s manifest in one change — a multi-file pipeline review that the IN persona should escalate to `/ship-devops` for depth.

## PR metadata

```json
{
  "owner": "acme",
  "repo": "fulfillment",
  "number": 1842,
  "title": "Ship packing-tracker microservice",
  "body": "New service for tracking packing-room throughput. Deploys via new GitHub Actions workflow; runs as a k8s Deployment in the prod cluster.",
  "headRefName": "feat/packing-tracker",
  "baseRefName": "main",
  "author": "morgan",
  "isDraft": false,
  "labels": [],
  "files": [
    {"path": ".github/workflows/deploy-packing.yml", "additions": 22, "deletions": 0},
    {"path": "services/packing-tracker/Dockerfile", "additions": 8, "deletions": 0},
    {"path": "services/packing-tracker/k8s/deployment.yaml", "additions": 24, "deletions": 0},
    {"path": "services/packing-tracker/src/server.ts", "additions": 35, "deletions": 0}
  ],
  "statusCheckRollup": {"state": "PENDING"},
  "commits": [{"sha": "9f3a21c", "committedDate": "2026-06-02T14:00:00Z"}]
}
```

## Diff (gh pr diff)

```diff
diff --git a/.github/workflows/deploy-packing.yml b/.github/workflows/deploy-packing.yml
new file mode 100644
+name: deploy-packing
+on:
+  push:
+    branches: [main]
+jobs:
+  build-and-deploy:
+    runs-on: ubuntu-latest
+    steps:
+      - uses: actions/checkout@main
+      - uses: actions/setup-node@v4
+      - run: npm ci
+      - run: npm test
+        continue-on-error: true
+      - run: docker build -t myreg.io/packing-tracker:latest .
+      - run: docker push myreg.io/packing-tracker:latest
+      - run: kubectl apply -f services/packing-tracker/k8s/
+        env:
+          KUBECONFIG_DATA: ${{ secrets.KUBECONFIG }}

diff --git a/services/packing-tracker/Dockerfile b/services/packing-tracker/Dockerfile
new file mode 100644
+FROM node:20
+WORKDIR /app
+COPY . /app
+RUN npm install
+CMD ["node", "server.js"]

diff --git a/services/packing-tracker/k8s/deployment.yaml b/services/packing-tracker/k8s/deployment.yaml
new file mode 100644
+apiVersion: apps/v1
+kind: Deployment
+metadata:
+  name: packing-tracker
+  namespace: prod
+spec:
+  replicas: 3
+  strategy:
+    type: Recreate
+  selector:
+    matchLabels:
+      app: packing-tracker
+  template:
+    metadata:
+      labels:
+        app: packing-tracker
+    spec:
+      containers:
+        - name: packing-tracker
+          image: myreg.io/packing-tracker:latest
+          ports:
+            - containerPort: 8080

diff --git a/services/packing-tracker/src/server.ts b/services/packing-tracker/src/server.ts
new file mode 100644
+import express from 'express';
+import fetch from 'node-fetch';
+
+const INVENTORY_URL = process.env.INVENTORY_URL!;
+const app = express();
+
+app.post('/scan', async (req, res) => {
+  const items = await req.body;
+  const stock = await fetch(`${INVENTORY_URL}/lookup?ids=${items.join(',')}`);
+  const data = await stock.json();
+  res.json(data);
+});
+
+app.listen(8080);
```

## Review threads (gh api graphql)

```json
{
  "reviewThreads": []
}
```

## CI checks

Pending — the new deploy-packing workflow is running.

---

Run the multi-persona PR review. The IN persona should activate in deep mode (workflow + Dockerfile + k8s manifest all touched), emit direct-emit IN findings for the high-precision single-line hits, AND emit a `Run /ship-devops` delegation bullet because multiple DEV categories compound across files. Produce the structured output.
