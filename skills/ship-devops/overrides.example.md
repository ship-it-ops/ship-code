# DevOps Overrides — Example

Copy this file to `overrides.md` (next to `SKILL.md`) or to `.claude/ship-devops-overrides.md` in your project root, then edit. Anything documented here supersedes the defaults in `SKILL.md`, `reference.md`, `reference-categories.md`, and the platform reference files.

> The skill loader reads override files in this order, with later files winning:
> 1. `SKILL.md` defaults
> 2. `overrides.md` (next to `SKILL.md`, team-wide)
> 3. `.claude/ship-devops-overrides.md` in the project root (project-specific)

Format is loose `key: value` or `key: [list]`. The skill reads override files as plain text and pattern-matches keys.

---

## Disabled categories

For repos that genuinely don't have a category's surface (e.g., a static-site project has no DEV8 schema-migration surface):

```
dev_disabled_categories: [DEV8]    # no databases in this repo
```

For finer control, disable specific sub-rules:

```
dev_disabled_rules:
  - DEV1.6     # not using pull_request_target anywhere
  - DEV4.6     # HEALTHCHECK enforced at the k8s manifest layer, not Dockerfile
```

The skill still scans these but never emits findings.

---

## Severity overrides

Escalate categories for codebases with strict SLOs / on-call expectations:

```
dev_escalate: [DEV11]    # incident hygiene is tier 1 for us (24/7 service)
dev_escalate: [DEV10]    # SLO/perf is tier 1 (latency-critical)
```

Demote categories for low-risk codebases:

```
dev_demote: [DEV12]      # internal tool, batch size doesn't matter
```

---

## Platform exclusions

If the repo uses a non-default platform stack, suppress patterns specific to others:

```
dev_disabled_platforms:
  - github-actions      # we use GitLab CI
  - terraform           # we use Pulumi
  - k8s                 # we use ECS only
```

The corresponding reference file's patterns are not applied.

---

## Path overrides

Extend the default dev/scripts exemption list:

```
dev_dev_only_paths:
  - "scripts/local/"
  - "tools/dev-shell/"
  - "**/*.local.yml"
```

Findings in these paths are demoted to advisory (max tier 3).

Ignore paths entirely:

```
dev_ignored_paths:
  - "vendor/"
  - "third_party/"
  - "deprecated/legacy-deploy/"
```

---

## Runbook and dashboard locations

If your org keeps runbooks somewhere non-standard, tell the skill so DEV11.1 doesn't false-fire:

```
dev_runbook_paths:
  - "docs/runbooks/"
  - "internal-docs/runbooks/"
  - "https://confluence.internal/runbooks/"
```

For dashboards-as-code:

```
dev_dashboard_paths:
  - "ops/dashboards/"
  - "modules/observability/dashboards.tf"
```

The skill verifies the linked dashboard files / directories exist; it does not fetch external URLs.

---

## Test fixture allowances

By default, files under `tests/fixtures/` and `examples/` are exempt from DEV findings (they often contain intentional smells for testing). Configure additional patterns:

```
dev_test_fixture_paths:
  - "tests/fixtures/"
  - "examples/"
  - "**/*.example.yml"
  - "spec/fixtures/"
```

---

## CI / IaC environment hints

If the skill can't auto-detect your stack, tell it:

```
dev_ci_platform: github-actions          # github-actions | gitlab-ci | circleci | jenkins | azure-pipelines
dev_iac_tool: terraform                  # terraform | pulumi | cloudformation | ansible | crossplane
dev_orchestrator: kubernetes             # kubernetes | ecs | nomad | cloud-run | lambda
dev_observability_stack: prometheus      # prometheus | datadog | newrelic | cloudwatch | honeycomb
```

The skill tunes its patterns to match.

For monorepos with multiple stacks, list them:

```
dev_orchestrator: [kubernetes, lambda]
```

---

## Reporting tuning

```
dev_findings_cap: 15                # default: 10 — show more findings before summarizing
dev_include_what_good: true         # default: true — set false for terse output
dev_pr_size_threshold_lines: 800    # default: 500 — bump if your team ships larger atomic changes
dev_pr_size_threshold_files: 50     # default: 30
```

---

## Custom rules

Team-specific concerns appended to the rubric. Each rule maps to an existing DEV category and severity tier.

```
dev_custom_rules:
  - id: DEV1.X-CUSTOM
    description: "Any new workflow must call the org's required-checks composite action. Tier 1."
    fire_on: "new file under .github/workflows/ that does not call uses: org/required-checks@*"
  - id: DEV4.X-CUSTOM
    description: "All Dockerfiles must FROM our hardened base. Tier 1."
    fire_on: "FROM line not matching ^FROM company/hardened-(node|python|go|java):"
  - id: DEV11.X-CUSTOM
    description: "Every production-deployed service has an entry in services-catalog.yml. Tier 2."
    fire_on: "new file under services/ without matching entry in ops/services-catalog.yml"
```

---

## CI-mode tuning

When invoked from `ship-reviewed-prs` IN delegation:

```
dev_max_delegation_decision: REQUEST_CHANGES         # default: full matrix
dev_inline_comment_categories: [DEV1, DEV2, DEV4, DEV8]   # which findings post as inline GitHub comments
```
