# Expected Review Output — fixture-3-dockerfile-root-user

The skill should produce a report substantially matching the structure below. The **DEV4.1 + DEV4.2 tier-1 findings are non-negotiable**; wording can vary.

---

```
## DevOps Review: services/api/Dockerfile

### Confidence
Reviewed 1 Dockerfile (~15 lines). Image is single-stage Python with build toolchain in the runtime. No `USER` directive, no pinned base, no `.dockerignore` visible alongside the diff, no HEALTHCHECK, no multi-stage split. Three tier-1 findings drive the REQUEST_CHANGES decision.

### Critical (must fix before merge)

- **[DEV4.1-IMAGE-ROOT-USER] services/api/Dockerfile**: No `USER` directive — container runs as root. If the API is exploited (RCE, deserialization), the attacker has root inside the container, can install tools, and depending on cluster setup may escape. Cross-ref SEC1.4 (least privilege). → Add: `RUN groupadd -r app && useradd -r -g app app` then `USER app` before `CMD`. Verify with `docker inspect --format='{{.Config.User}}' image:tag`.

- **[DEV4.2-FLOATING-BASE] services/api/Dockerfile:1**: `FROM python:3.12` floats to whatever 3.12.x is current; a base-image regression (or a CVE not yet patched in your image's snapshot) ships into your build silently. → `FROM python:3.12.2-slim-bookworm@sha256:<digest> # python:3.12.2-slim-bookworm`. Use Renovate to keep the digest current.

- **[DEV4.3-SINGLE-STAGE-WITH-TOOLCHAIN] services/api/Dockerfile**: `build-essential` and `libpq-dev` are needed to compile psycopg2 (and similar) but persist into the runtime image — extra surface area and ~200MB of size that the running container doesn't need. → Multi-stage build:
  ```
  FROM python:3.12.2-slim-bookworm@sha256:... AS builder
  RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
  COPY requirements.txt .
  RUN pip install --user --no-cache-dir -r requirements.txt

  FROM python:3.12.2-slim-bookworm@sha256:... AS runtime
  RUN groupadd -r app && useradd -r -g app app
  COPY --from=builder --chown=app:app /root/.local /home/app/.local
  ENV PATH=/home/app/.local/bin:$PATH
  USER app
  WORKDIR /app
  COPY --chown=app:app . /app
  EXPOSE 8080
  CMD ["python", "main.py"]
  ```

### Important (should fix)

- **[DEV4.4-NO-DOCKERIGNORE] services/api/**: no `.dockerignore` visible. `COPY . /app` pulls in `.git/`, `__pycache__/`, possibly `.env`, IDE configs. → Add `.dockerignore` covering `.git`, `__pycache__`, `*.pyc`, `.env*` (but not `.env.example`), `.venv`, `tests/`, `docs/`.

- **[DEV4.6-NO-HEALTHCHECK] services/api/Dockerfile**: no `HEALTHCHECK`. k8s probes will substitute in cluster, but local + CI debugging loses the signal. → `HEALTHCHECK --interval=30s --timeout=3s --start-period=10s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz')" || exit 1`.

### Advisory (hygiene)

- **[DEV4.X-PIP-VERSION-PINNING] services/api/Dockerfile** (advisory): `pip install -r requirements.txt` doesn't pin pip itself. → `RUN pip install --no-cache-dir --upgrade pip==24.0` before installing requirements; ensures consistent resolver behavior.

### What's Good

- **APT cache cleanup** — `rm -rf /var/lib/apt/lists/*` after apt-get install. Image stays slim on that axis.
- **Single-purpose CMD** — exec-form `CMD ["python", "main.py"]` (not shell-form), so PID 1 is the actual python process. Signals propagate correctly.
- **EXPOSE documented** — `EXPOSE 8080` is metadata; doesn't open ports but documents intent for downstream consumers.
```
