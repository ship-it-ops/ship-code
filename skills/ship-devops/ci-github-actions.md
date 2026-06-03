# GitHub Actions Patterns

Concrete DEV1 / DEV2 / DEV5 / DEV7 patterns specific to GitHub Actions workflows. For per-category rubric depth (anti-overlap, false positive notes), see `reference-categories.md`. For non-GitHub CI (GitLab, Jenkins, CircleCI), the same DEV categories apply but the syntax differs — translate.

---

## DEV1 — CI-PIPELINE

### DEV1.1 — Floating action reference (must-fix in shared workflows)

**Antipatterns:**
- `uses: actions/checkout@main` — floats to whatever `main` points to. Compromised maintainer or typosquat ships into your build.
- `uses: actions/checkout@v4` — floats inside the major version. Safer than `main` but still moves; vulnerable when a malicious commit reaches the major tag (has happened).
- `uses: org/private-action@latest`.
- `uses: ./` (local action) with no commit pin on a submodule it depends on.

**Fix:** pin to a full commit SHA, with a trailing comment for human readability:

```yaml
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
```

Renovate or Dependabot updates the pin; the bot's PR shows the new commit and gets reviewed before it merges.

### DEV1.2 — Merge gate runs no real tests

**Antipatterns:**
- Workflow has `lint` and `format` jobs but no `test` job; branch protection requires only `lint`.
- `pytest tests/` runs but the job is `continue-on-error: true`.
- `if: github.event_name == 'push'` on the test job — skips on PR, runs on push to a feature branch (no protection benefit).
- Path filter excludes test directories: `paths-ignore: ['tests/**']`.

**Fix:** every PR runs the test suite; the test job is a required check in branch protection; `continue-on-error` only on informational matrix legs.

Verify branch protection in the repo settings includes the test job name.

### DEV1.3 — Slow feedback / missing cache

**Antipatterns:**
- `actions/setup-node@v4` without `cache: 'npm'`.
- `actions/setup-python@v5` without `cache: 'pip'`.
- Docker layer cache missing: no `cache-from: type=gha` / `cache-to: type=gha,mode=max` in `docker/build-push-action`.
- Test job runs serially with no `strategy.matrix` parallelism even though tests are partitionable.

**Fix:**

```yaml
- uses: actions/setup-node@b39b52d1213e96004bfcb1c61a8a6fa8ab84f3e8 # v4.0.1
  with:
    node-version-file: .nvmrc
    cache: 'npm'
```

### DEV1.4 — Skipped tests added without a linked issue

Look at the diff for new occurrences of `@pytest.mark.skip`, `it.skip`, `xit`, `describe.skip`, `@Disabled`, `@Ignore`, `t.Skip`. Each needs a linked issue.

### DEV1.5 — Privileged CI tokens

**Antipatterns:**
- Workflow without a top-level `permissions:` block running on a repo where default workflow permissions are `read and write` (older repos / older orgs).
- `pull_request_target` running checkout of the PR branch — gives the PR's code access to repo secrets.
- Long-lived PATs (`secrets.PAT_TOKEN`) instead of GitHub App tokens or OIDC federation.
- Cloud credentials as static secrets instead of OIDC: `aws-actions/configure-aws-credentials` called with `aws-access-key-id` instead of `role-to-assume`.

**Fix:** restrict at the top of every workflow:

```yaml
permissions:
  contents: read
  pull-requests: write   # only if needed
```

For cloud auth, OIDC federation:

```yaml
permissions:
  id-token: write
  contents: read
jobs:
  deploy:
    steps:
      - uses: aws-actions/configure-aws-credentials@<SHA> # vX.Y.Z
        with:
          role-to-assume: arn:aws:iam::123:role/deploy
          aws-region: us-east-1
```

### DEV1.6 — `pull_request_target` misuse

`pull_request_target` runs in the base-branch context with secrets. Combined with `actions/checkout@v4` of `${{ github.event.pull_request.head.sha }}`, a PR's code can exfiltrate any secret in scope.

**Fix:** if you must use `pull_request_target`, never check out the PR's code in the same job. Split into two workflows.

---

## DEV2 — DEPLOYMENT-SAFETY (GitHub Actions framing)

### DEV2.1 — Deploy with no rollback

**Antipatterns:**
- `deploy.yml` runs `kubectl apply` / `aws cli` / `vercel --prod` on every push to main with no version tracking.
- Deploy job overwrites `latest` tag and discards the previous image.
- No `environment:` declaration; no audit trail.

**Fix:**

```yaml
jobs:
  deploy:
    environment:
      name: production
      url: https://app.example.com
    steps:
      # ... pinned actions, OIDC auth, deploy
```

Environment protection rules add manual approval and required reviewers for prod.

### DEV2.2 — Big-bang deploy on merge

Deploy job triggers on `push` to `main` with no canary, no flag check, no staging gate.

**Fix:** chain workflows — `staging-deploy.yml` runs first, smoke tests gate the `production-deploy.yml`.

### DEV2.4 — Missing post-deploy smoke

Deploy job's last step is `kubectl apply` / `vercel deploy --prod`; success is "kubectl rollout status returned 0."

**Fix:** smoke step probes real endpoints after deploy completes:

```yaml
- name: Smoke
  run: |
    curl -fsS --retry 5 --retry-delay 5 https://api.example.com/healthz
    curl -fsS --retry 5 --retry-delay 5 https://api.example.com/api/v1/ping
```

---

## DEV5 — CONFIG-MGMT (GitHub Actions framing)

### DEV5.1 — Secret literal in workflow YAML (cross-ref SEC7.4)

**Antipatterns:**
- `env: STRIPE_KEY: sk_live_...`.
- `with: api-token: ghp_...`.
- Cloud credentials hardcoded as `aws-access-key-id: AKIA...`.

**Fix:** `env: STRIPE_KEY: ${{ secrets.STRIPE_KEY }}`. Always.

### DEV5.2 — Env var referenced but not set

Workflow `run:` step references `$DEPLOY_ENV` with no `env:` declaration. Step silently runs against the default (often empty string, often interpreted as "dev" or "current").

**Fix:** explicit `env:` block on the step or job; missing env values fail at `actions/setup` time, not at the `run:` step.

---

## DEV7 — RELEASE-MGMT (GitHub Actions framing)

### DEV7.5 — Release without signing

**Antipatterns:**
- `gh release create` with no asset signing.
- Container push without `cosign sign`.
- Publishing to npm / PyPI without provenance (`npm publish --provenance`, `gh attestation`).

**Fix:**

```yaml
permissions:
  id-token: write
  attestations: write
jobs:
  publish:
    steps:
      - run: npm publish --provenance
```

---

## Workflow file checklist

For a new workflow file, the skill verifies all of these:

| Check | Antipattern | Pattern |
|-------|-------------|---------|
| Top-level `permissions:` | Block missing | Explicit minimum scopes |
| Action refs | Floating (`@main`, `@v4`) | SHA-pinned with version comment |
| Tests gate | `lint` only | `test` required by branch protection |
| Cache | Setup actions without `cache:` | `cache:` matched to package manager |
| Concurrency | No `concurrency:` block | `concurrency: { group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true }` for PR workflows |
| Secrets | Literal token in YAML | `${{ secrets.NAME }}` |
| Cloud auth | Static keys | OIDC `role-to-assume` |
| Deploy gate | `push: main` direct to prod | `environment:` with approval rules |
| Post-deploy | Rollout-status only | Explicit smoke step |
| Triggers | `pull_request_target` checking out PR code | Either `pull_request` or split workflows |
