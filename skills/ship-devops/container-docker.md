# Docker / Container Patterns

Concrete DEV4 / DEV5 / DEV9 patterns specific to Dockerfiles and docker-compose. Most patterns also apply to OCI-equivalent tooling (Podman, Buildah, Kaniko).

---

## DEV4 — CONTAINER-IMAGE

### DEV4.1 — Running as root (must-fix)

**Antipatterns:**

```dockerfile
FROM node:20-alpine
COPY . /app
WORKDIR /app
RUN npm ci
CMD ["node", "server.js"]
# No USER — runs as root.
```

Also:
- `USER root` set explicitly.
- `USER 0`.
- Multi-stage where the final stage doesn't drop privileges.
- `USER` set, but the entrypoint uses `sudo` / `gosu` to escalate.

**Fix:**

```dockerfile
FROM node:20.11.1-alpine@sha256:abc...
WORKDIR /app
RUN addgroup -S app && adduser -S app -G app
COPY --chown=app:app . /app
RUN npm ci --omit=dev
USER app
CMD ["node", "server.js"]
```

Verify: `docker inspect --format='{{.Config.User}}' image:tag` returns `app`.

### DEV4.2 — Floating / unpinned base (must-fix)

**Antipatterns:**
- `FROM node` (no tag — `latest`).
- `FROM node:latest`.
- `FROM node:20` (floats inside the major version).
- `FROM company/private-base:main`.

**Fix:** pin by digest, comment the human-readable tag:

```dockerfile
FROM node:20.11.1-alpine@sha256:6c381d5dc2a11dcdb693f0301e8587e43f440c90cdb8933eaaaabb905d44cdb9
```

Renovate keeps the digest current; the comment in the PR shows the new tag.

### DEV4.3 — Single-stage build leaks toolchain

A Python service that ends up at 1.2 GB because `gcc`, `make`, `python3-dev` are in the final image.

**Fix:** multi-stage:

```dockerfile
FROM python:3.12-slim@sha256:... AS builder
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.12-slim@sha256:... AS runtime
COPY --from=builder /root/.local /home/app/.local
USER app
COPY app /app
CMD ["python", "/app/main.py"]
```

Final image contains the wheels, not the compilers.

### DEV4.4 — `.dockerignore` missing or insufficient

Without `.dockerignore`, `COPY . /app` pulls in `.git/`, `node_modules/`, `.env`, build artifacts, IDE configs, OS junk (`.DS_Store`).

**Minimum `.dockerignore` for a Node service:**

```
.git
.gitignore
node_modules
dist
build
.env
.env.*
!.env.example
*.log
.DS_Store
.vscode
.idea
README.md
docs/
tests/
**/__pycache__
```

Sanity-check by listing the image:

```sh
docker run --rm image:tag find / \( -name '.env' -o -name '.git' \) 2>/dev/null
```

### DEV4.5 — Secret baked into build

**Antipatterns:**

```dockerfile
ARG NPM_TOKEN
RUN echo "//registry.npmjs.org/:_authToken=$NPM_TOKEN" > ~/.npmrc && npm install
```

`docker history image:tag` reveals the ARG value — the token is permanently in the image's layers.

Same for:
- `COPY .env /app/.env` (then editing it out later doesn't erase the layer).
- `RUN curl -H "Authorization: Bearer $TOKEN" ...`.
- `ENV API_KEY=...` (persistent in the image).

**Fix:** BuildKit secrets:

```dockerfile
# syntax=docker/dockerfile:1.6
FROM node:20.11.1-alpine@sha256:...
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci --omit=dev
```

Build with:

```sh
docker build --secret id=npmrc,src=$HOME/.npmrc -t image:tag .
```

The secret is mounted during the layer's execution and is not part of the image.

### DEV4.6 — No HEALTHCHECK

Long-lived service with no `HEALTHCHECK` instruction — Docker can't tell when the container is functional.

**Fix:**

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:8080/healthz || exit 1
```

Keep the check cheap and single-concern. If the service uses k8s probes, the Dockerfile HEALTHCHECK is informational; the manifest probes are authoritative.

### DEV4.7 — Unnecessary capabilities and privilege

In `docker-compose.yml` / k8s manifests, the image is fine but the runtime grants excess privilege:

**Antipatterns:**
- `privileged: true`.
- `cap_add: [ALL]` or unnecessary specific caps.
- `--user 0`.
- Volume mount of `/var/run/docker.sock` without a justification.

**Fix:** drop capabilities (`cap_drop: [ALL]`), add only what's needed; read-only root filesystem; non-root user.

### DEV4.8 — Image without SBOM / provenance

For published images:
- No `cosign sign` step in the publish pipeline.
- No SBOM attached (`syft`/`docker sbom`).
- No provenance attestation.

**Fix:** publish pipeline signs and attaches SBOM:

```sh
syft image:tag -o spdx-json > sbom.spdx.json
cosign sign --key cosign.key image:tag@sha256:...
cosign attest --predicate sbom.spdx.json --type spdx image:tag@sha256:...
```

---

## DEV5 — CONFIG-MGMT (container framing)

### DEV5.4 — Secrets in image or environment

**Antipatterns:**
- `ENV STRIPE_KEY=sk_live_...` (persistent in the image).
- `COPY .env /app/.env`.
- `docker-compose.yml` with `environment:` block containing literal secrets.

**Fix:** secrets injected at runtime via the orchestrator (k8s `Secret`, Docker Compose `secrets:` block, ECS task definition secret reference).

### DEV5.5 — Same image, different env config

The image is built per-environment with bake-time config:

```dockerfile
ARG ENV
COPY config-${ENV}.json /app/config.json
```

Now you have three images for one service.

**Fix:** one image, environment injected at runtime via env var or mounted ConfigMap.

---

## DEV9 — HEALTH-READINESS (container framing)

### DEV9.1 — Container HEALTHCHECK depends on downstream

```dockerfile
HEALTHCHECK CMD wget -qO- http://db:5432/healthz || exit 1
```

When the database hiccups, every container restarts.

**Fix:** liveness checks the process itself ("can I respond?"), not its dependencies.

### DEV9.4 — No graceful shutdown

Container ignores `SIGTERM`. Compose / k8s sends it, waits the grace period, then `SIGKILL`s — in-flight requests are dropped.

**Detection:** look at the entrypoint. `exec` form (`CMD ["node", "server.js"]`) passes signals to PID 1; shell form (`CMD node server.js`) doesn't, unless the entrypoint is a process supervisor like `tini` or `dumb-init`.

**Fix:**

```dockerfile
RUN apk add --no-cache tini
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "server.js"]
```

And the app itself handles `SIGTERM`: stop accepting new connections, drain in-flight, exit cleanly.

---

## Dockerfile checklist

For new or changed Dockerfiles, the skill verifies:

| Check | Antipattern | Pattern |
|-------|-------------|---------|
| `USER` | Missing or `root` | Non-root user added with `addgroup`/`adduser` |
| `FROM` | Floating tag | Pinned by digest with comment |
| Stages | Single stage with toolchain | Multi-stage; final stage minimal |
| `.dockerignore` | Missing | Excludes `.git`, `node_modules`, `.env`, build artifacts |
| Secrets | `ARG SECRET=…` or `COPY .env` | BuildKit `--mount=type=secret` |
| HEALTHCHECK | Missing on long-lived service | Cheap, single-concern probe |
| Signals | Shell-form CMD | Exec-form CMD with `tini` if needed |
| Caps / privilege | `privileged: true`, full caps | Capability-drop + read-only FS at runtime |
| SBOM | No SBOM / signature | `cosign sign` + SPDX attestation in publish |
| Layers | Many `RUN` + many `COPY .` | Grouped, ordered for cache reuse |
