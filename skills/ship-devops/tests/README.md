# Self-Test Fixtures — ship-devops

These fixtures are regression checks for the skill. Each fixture provides a synthetic input (a workflow YAML, a Dockerfile, a manifest, a migration, an application snippet) and the expected DevOps review.

## How to use

1. Open Claude Code with the skill installed.
2. Paste the fixture's `input.md` content as the user message.
3. The skill should produce output substantially matching `expected-output.md`.

Minor wording differences are fine. Watch for: missing tier-1 findings, wrong DEV category attribution, wrong tier, missing deploy-path trace, missing "What's Good" section.

## Fixtures

| Fixture | What it tests |
|---|---|
| `fixture-1-missing-rollback` | DEV2.1 — image tagged `:latest` + `Recreate` strategy combine to make rollback manual + downtime-laden. |
| `fixture-2-secret-in-workflow` | DEV5.1 (cross-ref SEC7.4) — secret literal in `.github/workflows/*.yml`; tier-1; expected fix uses `${{ secrets.NAME }}`. |
| `fixture-3-dockerfile-root-user` | DEV4.1 — Dockerfile with no `USER`; tier-1; expected fix adds non-root user. |
| `fixture-4-non-reversible-migration` | DEV8.1 — `DROP COLUMN` in same release as the app code that stops reading it; rollback breaks. |
| `fixture-5-missing-health-check` | DEV9.1 — new k8s Deployment with no liveness/readiness probes; tier-2 in standalone, tier-1 if labeled production. |
| `fixture-6-no-perf-budget` | DEV10.1 + DEV10.2 — k8s Deployment with no `resources.limits` and HTTP client with no timeout. |
| `fixture-7-clean-pr-approve` | The clean case — well-structured deploy change should produce no tier-1 findings and an APPROVE/NO_FINDINGS report. |
