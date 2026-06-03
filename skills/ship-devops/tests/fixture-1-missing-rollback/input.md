# Synthetic Input for Fixture 1: Missing rollback path

You are reviewing the following two files. Apply the `ship-devops` rubric.

## File: `.github/workflows/deploy.yml`

```yaml
name: deploy
on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
      - uses: actions/setup-node@b39b52d1213e96004bfcb1c61a8a6fa8ab84f3e8 # v4.0.1
        with:
          node-version-file: .nvmrc
          cache: 'npm'
      - run: npm ci
      - run: npm test
      - run: docker build -t myreg.io/api:latest .
      - run: docker push myreg.io/api:latest
      - run: kubectl apply -f k8s/
```

## File: `services/api/k8s/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: prod
spec:
  replicas: 4
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
        - name: api
          image: myreg.io/api:latest
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: 200m
              memory: 256Mi
            limits:
              cpu: 1
              memory: 512Mi
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
          readinessProbe:
            httpGet:
              path: /readyz
              port: 8080
```

---

Apply the ship-devops rubric and produce a structured review.
