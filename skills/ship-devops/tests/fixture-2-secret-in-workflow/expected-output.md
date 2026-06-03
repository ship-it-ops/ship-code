# Expected Review Output — fixture-2-secret-in-workflow

The skill should produce a report substantially matching the structure below. The **DEV5.1 tier-1 finding (cross-ref SEC7.4) is non-negotiable**; wording can vary.

---

```
## DevOps Review: .github/workflows/publish.yml

### Confidence
Reviewed 1 file (~25 lines). Pipeline: `tag:v*.*.* → npm ci → build → test → npm publish` to the public npm registry. Skipped 0 generated files. CI hygiene is good (pinned actions, cached deps) but two literal secrets land in the workflow YAML — committed to git history and visible to anyone with repo read access. Two tier-1 findings drive the REQUEST_CHANGES decision.

### Critical (must fix before merge)

- **[DEV5.1-SECRET-LITERAL-IN-WORKFLOW] .github/workflows/publish.yml:21**: `NODE_AUTH_TOKEN: npm_...` is a literal npm publish token in the workflow YAML — already in git history, already leaked. Cross-ref SEC7.4 (ship-secure-code owns the leak rubric — rotate immediately). DEV5 owns the source-discipline: `NODE_AUTH_TOKEN` must come from `${{ secrets.NPM_TOKEN }}`. Deploy path: `tag → publish job → npm publish (leaked token authenticates)`. → Replace with `NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}`; rotate the leaked token in npm; audit git history for prior exposure (likely commits, definitely PR descriptions).

- **[DEV5.1-SECRET-LITERAL-IN-WORKFLOW] .github/workflows/publish.yml:22**: `STRIPE_KEY: sk_live_...` is a literal Stripe live key. Same failure mode, higher blast radius — Stripe key allows charges against your account. Cross-ref SEC7.1. → Rotate immediately via Stripe dashboard; replace with `${{ secrets.STRIPE_KEY }}`; audit Stripe API logs for any unauthorized use during the leak window.

### Important (should fix)

- **[DEV1.5-CI-PERMISSIONS] .github/workflows/publish.yml**: no top-level `permissions:` block. A publish job needs `id-token: write` (for npm provenance) and `contents: read` only. Without an explicit block, the job inherits broad scope on older repos. → Add at the workflow level: `permissions: { contents: read, id-token: write }`.

- **[DEV7.5-RELEASE-UNSIGNED] .github/workflows/publish.yml:18**: `npm publish` without `--provenance` flag — the published package has no SLSA provenance attestation. Consumers can't verify the artifact came from this CI run. → `run: npm publish --provenance` (requires `id-token: write` permission, see above).

### Advisory (hygiene)

- **[DEV2.4-NO-POST-PUBLISH-SMOKE] .github/workflows/publish.yml** (advisory): no smoke step after `npm publish`. A successful publish doesn't mean the package installs in a fresh project. → Add a final job (or step) that `npm install`s the just-published version into a temp dir and runs a trivial smoke import.

### What's Good

- **Tag-triggered, not push-triggered** — `on: push: tags: ['v*.*.*']` couples the publish to a release tag, not every commit. The team is thinking about release discipline.
- **Pinned actions by SHA** — both `actions/checkout` and `actions/setup-node` reference commits with comments. Renovate-friendly.
- **Tests gate the publish** — `npm test` runs before `npm publish`; a regression doesn't ship.
- **Registry URL explicit** — `registry-url` set on `setup-node` rather than relying on the global default. The token scope and registry pair correctly.
```
