# Synthetic Input for Fixture 5: New k8s Deployment without health probes

You are reviewing the following file. Apply the `ship-devops` rubric.

The change adds a new production service `notifications` to the cluster.

## File: `services/notifications/k8s/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notifications
  namespace: prod
  labels:
    app: notifications
    team: messaging
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: notifications
  template:
    metadata:
      labels:
        app: notifications
    spec:
      containers:
        - name: notifications
          image: myreg.io/notifications:${IMAGE_TAG}
          ports:
            - name: http
              containerPort: 8080
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
          env:
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: notifications-secrets
                  key: redis-url
```

---

Apply the ship-devops rubric and produce a structured review.
