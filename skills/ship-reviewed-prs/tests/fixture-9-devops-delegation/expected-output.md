# Expected Review Output — fixture-9-devops-delegation

> **Format note:** Under the inline-first protocol the four Critical and two Important findings below should be posted as **six inline review comments** at their respective `file:line` anchors. The summary body that ships in the review-body step reduces each Critical/Important bullet to `[ID] path:line — see inline comment`. The full finding text below is what should appear in the inline-comment bodies.
>
> **Delegation note:** This fixture is the canonical regression check that the IN persona's depth target is `ship-devops`. The orchestrator emits direct IN findings for the high-precision single-line hits (floating action, missing test gate, `:latest` tag, `Recreate` strategy, missing `USER`, missing timeout) and a single `Run /ship-devops on services/packing-tracker/` delegation bullet for the compound multi-file pipeline review the depth target owns. The compound tags `[IN1 / DEV2.1-NO-ROLLBACK]` etc. are mandatory — the DEV ID surfaces alongside the IN priority code so reviewers see which `ship-devops` category drove the finding.

````
## PR Review — #1842 `Ship packing-tracker microservice`

**Verdict: Changes requested**

### Confidence
Reviewed 4 files (~89 lines). New microservice ships with a new GitHub Actions deploy workflow, a Dockerfile, a k8s Deployment manifest, and the service code itself — a textbook multi-file pipeline review. IN persona escalated to deep mode (workflow + Dockerfile + manifest all touched) and delegated depth to `/ship-devops`. CI is pending; per matrix that does not block APPROVE, but four tier-1 IN findings drive REQUEST_CHANGES regardless. No existing review threads.

### Personas activated

| Persona | Status | Reason |
|---|---|---|
| SE | ✅ pass | new endpoint is internally consistent; no PR-shaped contract concerns |
| SC | ✅ active | secret-source check on the workflow `env:` block |
| IN | ✅ active | deep mode — workflow + Dockerfile + manifest all touched; delegated depth to `ship-devops` |
| DA | ⏭ skip | no schema files |
| FE | ⏭ skip | no TSX/JSX |
| TS | ✅ active | new production code with no tests added — delegation-only |

### Findings

| Severity   | Count |
|---|---|
| Must-fix   | 4 |
| Should-fix | 2 |
| Nits       | 0 |

**Must-fix anchors:**
- `[IN5 / DEV1.1-FLOATING-ACTION]` .github/workflows/deploy-packing.yml:9 — see inline comment
- `[IN5 / DEV1.2-MERGE-GATE-NO-TESTS]` .github/workflows/deploy-packing.yml:13 — see inline comment
- `[IN1 / DEV2.1-NO-ROLLBACK]` services/packing-tracker/k8s/deployment.yaml:8 — see inline comment (`:latest` tag + `Recreate` strategy = manual+downtime rollback)
- `[IN1 / DEV4.1-IMAGE-ROOT-USER]` services/packing-tracker/Dockerfile:1 — see inline comment

**Should-fix anchors:**
- `[IN1 / DEV10.2-NO-HTTP-TIMEOUT]` services/packing-tracker/src/server.ts:9 — see inline comment (`fetch(...)` to inventory service has no timeout)
- `[IN3 / DEV10.1-NO-RESOURCE-LIMITS]` services/packing-tracker/k8s/deployment.yaml:14 — see inline comment

### Delegations
- Run `/ship-devops on services/packing-tracker/` — multi-file pipeline review across workflow + Dockerfile + manifest + service code; depth target owns the compound DEV1/DEV2/DEV4/DEV9/DEV10 rubric, post-deploy smoke checks, runbook/CODEOWNERS verification, and the per-category fix suggestions.
- Run `/ship-tested-code on services/packing-tracker/` — TS1: 35 lines of new production code with no test files added.
- Run `/ship-secure-code on .github/workflows/deploy-packing.yml` — verify the `KUBECONFIG_DATA` env-var sourcing is via OIDC federation rather than a long-lived static secret (DEV5 / SEC7 cross-cut).

### Comment lifecycle

| State | Count |
|---|---|
| Resolved | 0 |
| Won't-fix | 0 |
| Outdated | 0 |
| Possibly addressed | 0 |
| Stale | 0 |
| Open | 0 |

Suppressed 0 findings.

### What's solid

- **3 replicas declared** — the team is thinking about availability from day one; the missing pieces are rollback strategy and probes, not the basic shape.
- **Secrets reference uses `${{ secrets.KUBECONFIG }}`** — no literal secret in the YAML. DEV5.1 doesn't fire on that line.
- **Service code uses `process.env.INVENTORY_URL!`** — non-null assertion fails loudly at boot if the env var is missing; the `!` is the right call for a required config (DEV5.2 doesn't fire).
- **k8s namespace explicit (`prod`)** — the manifest doesn't default to `default`; deploys land where intended.

### Submission preview (local mode)
  gh api -X POST repos/acme/fulfillment/pulls/1842/reviews (create pending review)
  gh api -X POST .../reviews/{id}/comments × 6 (six inline findings)
  gh api -X POST .../reviews/{id}/events -f event=REQUEST_CHANGES -f body=<summary>

Proceed? Type "yes" to submit, "edit" to revise, or "no" to abort.
````

## What this fixture demonstrates

1. **IN deep mode triggers correctly** on workflow + Dockerfile + manifest in one PR.
2. **Compound finding tags** (`[IN1 / DEV2.1-NO-ROLLBACK]`) surface the depth-target's category alongside the orchestrator's priority code — readers see which `ship-devops` rubric drove the finding without losing the orchestrator's decision-matrix mapping.
3. **Direct-emit vs delegation split** matches the rubric in `reference-personas.md` § IN → Delegation to `ship-devops`. High-precision single-line hits fire directly; multi-file pipeline review goes to `/ship-devops`.
4. **CI pending does not block REQUEST_CHANGES** — per the decision matrix, tier-1 findings drive the verdict regardless of CI status.
5. **Multiple delegations co-exist** — `/ship-devops`, `/ship-tested-code`, and `/ship-secure-code` are all listed under Delegations and none count toward the decision matrix.
6. **What's solid is substantive** — names specific disciplines that exist (replicas, secret sourcing, env var assertion, explicit namespace) rather than boilerplate.
