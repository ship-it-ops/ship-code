---
name: ship-reviewed-prs
description: >
  Perform a thorough, multi-persona pull-request review (senior engineer, senior
  security engineer, senior infra/SRE, conditional senior data engineer, plus
  test-coverage signal). Reads existing PR comment threads and suppresses
  findings that are already resolved, marked won't-fix, or addressed in a later
  commit. Computes a deterministic APPROVE / REQUEST_CHANGES / COMMENT decision
  and can submit the review via gh CLI (with confirmation gating in local mode
  and full automation in CI). Manual invocation only.
disable-model-invocation: true
allowed-tools: Bash(gh *), Bash(git *), Read, Grep, Glob
argument-hint: "[pr-number-or-url] [--auto-approve] [--non-interactive] [--json] [--strict]"
---

# Multi-Persona PR Review Skill

## Purpose

This skill performs a structured, multi-persona pull-request review that catches concerns a single rubric misses, respects the comment history of long-lived PRs, and produces a decisive APPROVE / REQUEST_CHANGES / COMMENT recommendation. It runs locally with an interactive confirmation gate or in CI with full automation. It composes with the sibling skills (`ship-clean-code`, `ship-tested-code`, `ship-debugged-code`) by delegating concerns those skills own rather than duplicating them.

## Quickstart (New to This Skill?)

Start with these 3 rules and internalize them before learning the rest:
1. **Read the PR description and the existing review threads BEFORE forming new findings** — the most expensive review is one that re-raises a concern already discussed.
2. **Personas have distinct rubrics, but findings deduplicate** — one finding per `(file, line, root cause)`, owned by the highest-priority persona.
3. **The decision is mechanical** — APPROVE / REQUEST_CHANGES / COMMENT follows from the merged finding list and CI status. The skill writes prose; the verdict is computed.

The detailed reference files (`reference.md`, `reference-personas.md`, `reference-lifecycle.md`) assume familiarity with `gh` CLI, GitHub's review-thread model, and the sibling skills.

## Invocation

```
/ship-reviewed-prs <pr-number-or-url> [flags]
```

**Flags:**

| Flag | Effect |
|------|--------|
| `--auto-approve` | Local only: auto-submit on clean APPROVE (green CI, zero open threads, no findings). Never honored for REQUEST_CHANGES or COMMENT. Ignored in CI. |
| `--non-interactive` | Force CI mode behavior locally (skip confirmation gate). Required if CI auto-detection fails. |
| `--json` | Change the local terminal output format to machine-readable JSON instead of formatted prose. Does NOT bypass the local confirmation gate — submission still requires `yes`/`--auto-approve` per the rules below. In CI mode it changes the stdout format only (submission happens regardless). |
| `--strict` | CI only: exit code `1` for COMMENT decisions as well as REQUEST_CHANGES. Default is `1` only for REQUEST_CHANGES. |

**Execution mode detection:**
- `CI=true` env var set → CI mode (used by GitHub Actions, GitLab CI, CircleCI, Jenkins, Buildkite, etc.).
- `--non-interactive` flag passed → CI mode.
- Otherwise → local mode.

## Mode Detection

This skill operates in **review mode only**. There is no writing mode — the skill never generates production code. It produces:
- A structured review draft (the report you see).
- A submission plan (`gh` commands that would post the review).
- A decision (APPROVE / REQUEST_CHANGES / COMMENT).
- In CI: actual submission. In local: submission only after confirmation (or `--auto-approve` on green-path).

## Core Principles - Always Apply

These 12 rules apply to every PR review:

### 1. Read before reviewing.
Read the PR title, description, linked issue, and existing review threads before generating findings. A skill that re-raises resolved concerns wastes reviewer time and loses trust.

### 2. Personas have distinct rubrics; output has one priority order.
Each persona (SE/SC/IN/DA/TS) reads the diff through its own concerns lens and emits findings with its own prefix. The merge step deduplicates and produces one priority-ordered list. Reviewers see "[SC1-AUTH-MISSING]" not "Five separate reviews."

### 3. Delegate, don't duplicate.
If a finding is fundamentally about naming, function size, magic numbers, dead code, error swallowing, or readability, emit a single bullet: "Run `/ship-clean-code` on `<file>`." Same pattern for `ship-tested-code` (test design/flakiness/AAA) and `ship-debugged-code` (root-cause for bugfix PRs).

### 4. Suppress, don't re-raise.
Before emitting any finding, fingerprint it `(file, line ± 5, root-cause-token)` and compare against the existing thread state (RESOLVED, OUTDATED, WONT_FIX). On match, drop the finding and increment a "Suppressed N findings already discussed" counter shown in the output. This is the single most important behavior for keeping reviews tolerable on long-lived PRs.

### 5. The decision is deterministic.
APPROVE / REQUEST_CHANGES / COMMENT is computed by table lookup on the merged finding list + CI status + open-thread count. The skill explains the decision in prose but does not negotiate it.

### 6. CI failing blocks APPROVE.
Never approve over red CI. The decision degrades to COMMENT with a "CI must pass before approval" note.

### 7. "Possibly addressed" needs human confirmation.
A later commit touching the same file:line as an open comment is a heuristic, not a fact. Surface the signal, do not assume resolution. APPROVE is degraded to COMMENT until a human confirms.

### 8. Surface confidence, not opinion.
The output includes a Confidence section that names what was reviewed, what was *not* reviewed (out of scope, large generated files, unreviewable binaries), and what's residual risk. A confident "REQUEST_CHANGES" is paired with the specific finding that drove the decision.

### 9. Always include "What's Good".
Reviews are not just findings. Naming substantive positive observations — sound architectural decisions, good test coverage, clean migration plans — keeps the review collaborative and helps the author trust the critical findings.

### 10. Submission is a separate step from analysis.
Analysis produces a draft. Submission requires either interactive confirmation (local) or a green-path `--auto-approve` (local) or `CI=true` (CI mode). The skill never submits silently in local mode.

### 11. Bot identity is honest.
When submitted from CI, the review body includes a prefix line `Posted by ship-reviewed-prs (bot). Reasoning available in this comment; ask the author/oncall for human judgment on disputed findings.` Removes any ambiguity about reviewer identity.

### 12. Exit codes carry the verdict.
In CI, exit codes (0 APPROVE, 1 REQUEST_CHANGES, 2 COMMENT, 3 ERROR) let downstream CI steps gate on severity without parsing output. Pipelines that need stricter gating use `--strict` to fail on COMMENT too.

## Personas

The skill runs five personas against every PR. The first three (SE, SC, IN-light) plus TS gap-check are always on; DA and IN-deep escalate to Explore subagents only when the diff actually touches relevant files.

| Code | Persona | Trigger | Owns |
|------|---------|---------|------|
| SE | Senior Engineer | Always | API contracts, backward compatibility, rollout safety, module-level SRP. Defers naming/length/readability to `ship-clean-code`. |
| SC | Senior Security Engineer | Always | AuthN/Z, injection, secrets, crypto, supply-chain, PII, log leakage. Overrides `ship-clean-code` P2-SEC on overlap. |
| IN | Senior Infra / SRE / DevOps | Always (light); deep when infra files touched | Timeouts, retries, idempotency, observability, resource limits, CI/CD, IaC, migration safety (ops dimension). |
| DA | Senior Data Engineer | Conditional on schema/event/migration files | Schema break risk, data loss, backfill, indexes, type precision, event-contract evolution, retention/PII. |
| TS | Test Reviewer | Always (delegation-only) | Surfaces test-coverage gap signals. All test-quality depth defers to `ship-tested-code`. |

Full persona rubrics — concerns, triggers, anti-overlap rules, finding examples — live in `reference-personas.md`.

### Conditional persona triggers

**DA activates** when the diff touches any of:
- `migrations/`, `*.sql`, `alembic/`, `flyway/`, `prisma/migrations/`, `db/migrate/`
- ORM model files (Django models, SQLAlchemy declarative, Prisma `schema.prisma`, TypeORM entities, JPA entities)
- Event-schema files: `*.avsc`, `*.proto`, `events/*.json`, `schemas/*.yaml`
- Warehouse models: `dbt/`, `models/*.sql`

**IN deep mode activates** when the diff touches any of:
- `*.tf`, `*.tfvars` (Terraform), `pulumi/`, `cdk/` (Pulumi/CDK)
- `Dockerfile*`, `*.containerfile`, `docker-compose.y*ml`
- `k8s/`, `kubernetes/`, `helm/`, `*.yaml` under any of those
- `.github/workflows/`, `.gitlab-ci.yml`, `circle.yml`, `.circleci/`, `Jenkinsfile`
- `infra/`, `deploy/`, `ops/` (project convention)

Triggers are tunable via `overrides.md` — see Team Overrides below.

## Delegation Table

Personas defer to sibling skills rather than duplicating their rubrics. The decision is made BEFORE emitting a finding:

| If the finding is fundamentally about... | Replace with |
|---|---|
| Naming, function size, magic numbers, dead code, error swallowing, readability | `Run /ship-clean-code on <file>` |
| Test design, test coverage depth, flakiness, AAA structure, mocking strategy | `Run /ship-tested-code on <file>` |
| Root cause of a bug the PR claims to fix (PR description contains "fixes #N") | `Run /ship-debugged-code on PR #N` |

A "Delegations" section in the output lists these. They do NOT count toward the decision matrix — they are advisory pointers.

## Priority Hierarchy

Findings are tagged with a two-letter persona prefix + priority number. Severity tier follows the number (1-2 Critical, 3-5 Important, 6-7 Suggestion):

- **SE**: SE1 BREAKING-CHANGE → SE7 DOCSTRING-MISMATCH
- **SC**: SC1 AUTH-MISSING → SC7 LOG-LEAKAGE
- **IN**: IN1 PROD-OUTAGE-RISK → IN7 PERF-HOTPATH
- **DA**: DA1 SCHEMA-BREAK → DA7 RETENTION-PII
- **TS**: TS1 NO-TEST-FOR-NEW-CODE, TS2 NO-REGRESSION-FOR-BUGFIX

Full finding-ID definitions and examples in `reference-personas.md`.

## Decision Matrix

Computed deterministically from the merged finding list. No LLM judgment.

| State | Decision |
|-------|----------|
| Any unsuppressed *1 finding (SC1/IN1/DA1/SE1/TS1) | `REQUEST_CHANGES` |
| Any unsuppressed *2 finding | `REQUEST_CHANGES` |
| Only *3-*5 findings | `COMMENT` |
| Only *6-*7 findings or only Delegations | `COMMENT` |
| Zero new findings AND zero OPEN threads AND CI green | `APPROVE` |
| CI failing | `COMMENT` (never APPROVE over red CI) |
| Any "Possibly addressed" items | `COMMENT` (manual confirmation required to escalate) |

## Comment Lifecycle

Before emitting findings, classify every existing review thread into one of six states:

| State | Definition | Behavior |
|-------|------------|----------|
| RESOLVED | `isResolved: true` on the thread | Suppress; count only |
| OUTDATED | `isOutdated: true` AND line no longer exists in current diff | Suppress; count only |
| WONT_FIX | Last author/maintainer comment matches won't-fix marker OR reaction-marker | Suppress; count only |
| ADDRESSED | Open thread, later commit touched `path` near `original_line ± 5` after the comment | Surface as "Possibly addressed — needs reviewer confirmation"; do not re-derive |
| STALE | Open, last activity > 14 days, no author response | Surface under "Stale comments needing reply" |
| OPEN | Open, recent activity | Blocking until addressed |

Default won't-fix markers (case-insensitive substring match on the last comment from the PR author or a maintainer):
- `won't fix`, `wontfix`, `out of scope`, `out-of-scope`, `not in this pr`, `tracked in #<n>`, `see #<n>`, `agreed to skip`, `discussed offline`
- `:white_check_mark:` or `:thumbsup:` reaction from the original commenter

Full classification logic, fingerprinting algorithm, and override knobs in `reference-lifecycle.md`.

## Orchestration

The skill runs as a hybrid: always-on personas in-context, conditional personas as Explore subagents.

1. **Fetch phase** (orchestrator, in-context):
   ```bash
   gh pr view <n> --json title,body,headRefName,baseRefName,author,labels,files,statusCheckRollup,commits
   gh pr diff <n>
   gh pr checks <n>
   gh api graphql -f query='query { repository(owner:"...", name:"...") { pullRequest(number:<n>) { reviewThreads(first:100) { nodes { id isResolved isOutdated path line comments(first:50) { nodes { databaseId body author { login } createdAt } } } } } } }'
   ```

2. **Triage pass** (orchestrator, in-context): classify each changed file into `code | test | infra | schema | docs | generated | vendor`. Determine which conditional personas activate.

3. **Always-on personas** run bracketed in-context, sequenced SE → SC → IN(light) → TS(gap-check). Each pass reads only its relevant file buckets.

4. **Conditional escalation** (Explore subagents, up to 2 in parallel):
   - If DA activates: spawn one subagent with the DA rubric and the schema/migration/event files. The subagent reads adjacent context (existing schema, downstream consumers) the orchestrator hasn't fetched.
   - If IN deep mode activates: spawn one subagent with the IN deep rubric and the infra files.

5. **Merge phase** (orchestrator):
   - Deduplicate by fingerprint `(path, line ± 5, root-cause-token)`. Higher-priority persona wins (SC > SE; DA > IN on schema files).
   - Apply suppression against RESOLVED/OUTDATED/WONT_FIX threads.
   - Compute decision via the matrix above.
   - Render output. In CI, emit `--json` if requested; in local, prompt for confirmation.

## Submission Protocol

Use the GitHub pending-review protocol so inline comments and the summary post atomically:

```bash
# 1. Create a pending review
REVIEW_ID=$(gh api -X POST repos/{owner}/{repo}/pulls/<n>/reviews \
  -f event=PENDING -f body="(pending — comments will follow)" --jq .id)

# 2. Post each inline finding as a review comment
for finding in $findings; do
  gh api -X POST repos/{owner}/{repo}/pulls/<n>/reviews/$REVIEW_ID/comments \
    -f path=<file> -F line=<line> -f body=<body>
done

# 3. Submit the pending review with the verdict
gh api -X POST repos/{owner}/{repo}/pulls/<n>/reviews/$REVIEW_ID/events \
  -f event=APPROVE|REQUEST_CHANGES|COMMENT -f body=<summary>
```

For APPROVE with no inline findings, the simpler `gh pr review <n> --approve --body <summary>` is acceptable.

Full `gh` command reference in `reference.md`.

## Local Submission Gate

In local mode, after computing the decision and rendering the draft:

```
Decision: REQUEST_CHANGES
3 inline comments will be posted on: api/users.ts:42, services/billing.ts:118, migrations/0042.sql:5

Submission preview:
  gh api -X POST .../reviews -f event=PENDING ...
  gh api -X POST .../comments ... (3×)
  gh api -X POST .../events -f event=REQUEST_CHANGES ...

Proceed? Type "yes" to submit, "edit" to revise the body, "no" to abort.
```

`--auto-approve` skips the gate **only** when:
- Decision is APPROVE, AND
- CI is green, AND
- Zero OPEN threads, AND
- No "Possibly addressed" items.

For all other states the gate fires regardless of `--auto-approve`.

## CI Mode

When `CI=true` is set (or `--non-interactive` flag passed):

1. Require `GH_TOKEN` or `GITHUB_TOKEN` env var. Exit `3` with a clear message if missing.
2. No interactive prompts. Decision matrix runs to completion and submits.
3. Apply `ci_max_decision` override if set (downgrades a stronger decision to the configured ceiling — see Team Overrides).
4. Exit code reflects the *original* (uncapped) decision:
   - `0` — APPROVE (or no findings)
   - `1` — REQUEST_CHANGES
   - `2` — COMMENT
   - `3` — Error
5. With `--strict`, exit `1` for COMMENT decisions too.
6. With `--json`, emit a structured result to stdout (schema in `examples/ci-output-json.md`). Logs go to stderr.

Bot identity prefix is prepended to the review body in CI:

```
Posted by ship-reviewed-prs (bot). Reasoning available in this comment; ask
the author/oncall for human judgment on disputed findings.

---
<the actual review>
```

A drop-in GitHub Actions workflow and GitLab CI snippet ship in `examples/ci-github-actions.yml` and `examples/ci-gitlab.yml`.

## Review Output Format

```
## PR Review: #<n> — <title>

### Decision: APPROVE | REQUEST_CHANGES | COMMENT

### Confidence
<2-4 sentences: what was reviewed, what was not (out of scope, large generated
files), what's the residual risk, why this decision is the right one.>

### Critical (must fix before merge)
- **[SC1-AUTH-MISSING] api/users.ts:42**: <problem>. → <fix>.
- **[DA1-SCHEMA-BREAK] migrations/0042.sql:5**: <problem>. → <fix>.

### Important (should fix)
- **[IN2-OBSERVABILITY-GAP] services/billing.ts:118**: <problem>. → <fix>.
- **[SE2-CONTRACT-DRIFT] sdk/index.ts:7**: <problem>. → <fix>.

### Suggestions (improve when convenient)
- **[IN7-PERF-HOTPATH] services/search.ts:88**: <problem>. → <fix>.

### Delegations
- Run `/ship-tested-code` on `services/billing.test.ts` (TS1: PR adds production code with no test).
- Run `/ship-clean-code` on `services/billing.ts` (naming/readability concerns deferred).

### Comment lifecycle
- 3 resolved | 2 won't-fix | 1 outdated | 1 possibly addressed in commit <sha> — please confirm | 1 open
- Suppressed: 4 findings already discussed in earlier review.

### Stale comments needing reply
- `services/auth.ts:30` — opened 23 days ago, no author response.

### What's Good
- Migration includes backfill + rollback plan in PR body.
- BillingClient is constructor-injected, replacing a static singleton.
- New tests use the standard factory pattern.

### Submission preview (local mode only)
  gh api ... (create pending review)
  gh api ... (post 2 inline comments)
  gh api ... -f event=REQUEST_CHANGES -f body=<summary>
Proceed? yes / edit / no
```

Rules for the output:
- **Decision is always present.** No "I'm not sure" — the matrix decides.
- **Confidence section is always present** and substantive (not "looks fine").
- **What's Good is always present** with concrete observations.
- **Delegations are separate** from findings and do not affect the decision.
- **Comment lifecycle line is always present**, even if everything is empty (show zeros).
- Tag every finding with its priority code (SE1, SC2, etc.).
- Include specific file:line.
- Every finding has a concrete fix suggestion.
- More than 10 findings: show top 10 strictly ordered by priority. Never suppress *1 findings due to the cap.

## Pragmatism Guidelines

- **Trust signals from the PR description.** If the author wrote "Known issue: X is out of scope, tracked in #4711," do not re-flag X. Match the issue reference in won't-fix detection.
- **Vendored and generated code gets a pass.** Files under `vendor/`, `node_modules/`, `*.generated.*`, `*.pb.go`, `dist/`, `build/` are not reviewed. Note as a count.
- **Docs-only PRs**: SC still runs (links to secrets, leaked URLs). SE/IN/DA/TS skip.
- **WIP PRs** (label or `[WIP]` / `[DRAFT]` in title): emit COMMENT only, never REQUEST_CHANGES. The author will iterate.
- **Trivial PRs**: 1-5 line changes get a lightweight pass. Skip subagent escalation; if no findings, APPROVE on green CI.
- **Match team conventions over ideals.** If the team's `overrides.md` disables a rule or persona, respect it without lecturing.
- **Never block on a P6/P7 finding.** Those are suggestions. Decision matrix only escalates *1 and *2.

## Working with Long-Lived PRs

PRs over 100 comments deserve special handling:
- **Lead with the lifecycle line.** The reviewer needs to see "12 resolved | 5 won't-fix" before the new findings.
- **Aggressive suppression.** Be willing to suppress 80%+ of findings if they match prior threads. The cost of re-raising is worse than the cost of missing.
- **Old findings get archived.** Findings older than the head SHA's parent-of-parent commit are by definition outdated. Confirm via `gh api` before suppressing.

## Related Skills

- **`/ship-clean-code`** — File-level code-quality review (naming, SRP, error handling, 66 smells). The SE persona delegates here.
- **`/ship-tested-code`** — Test-quality review (T1-T7 hierarchy, mocking strategy, flakiness). The TS persona always delegates here for depth.
- **`/ship-debugged-code`** — Bug investigation and root-cause analysis. Useful on bugfix PRs ("fixes #N") to verify the fix is at the right layer.

This skill is the **orchestrator** that brings PR context (diff, threads, CI status) to the others. The others provide the file-level rubrics.

## Team Overrides

Before applying review rules, check for override files in this order (later files win on conflicts):

1. `overrides.md` next to this `SKILL.md` (team-wide overrides bundled with the skill)
2. `.claude/ship-reviewed-prs-overrides.md` in the user's project root (project-specific overrides)

Read whichever exist and apply their rules on top of the defaults. Use overrides for:

- **Won't-fix marker set** — additional phrases your team uses (e.g., "punt", "next sprint")
- **Stale threshold** — days before an open thread is considered stale (default 14)
- **Conditional persona triggers** — additional file patterns that activate DA or IN-deep
- **Disabled personas** — `disable: [DA]` to skip data review on a repo with no DB
- **`ci_max_decision`** — cap CI submissions to `COMMENT`, `REQUEST_CHANGES`, or `APPROVE` (default: full matrix)
- **Bot identity prefix** — custom bot-disclosure text for CI submissions
- **Decision matrix adjustments** — escalate or demote specific finding IDs for your context

A template is available at `overrides.example.md` — copy and edit. Do not modify `overrides.example.md` directly; it is reference material.

## Team Adoption

Phased rollout recommended:
- **Weeks 1-4**: Local-only, `--auto-approve` disabled. Build trust by reviewing alongside the team's human reviewers.
- **Month 2**: Enable `--auto-approve` for local users on green-path APPROVE. CI integration in comment-only mode (`ci_max_decision: COMMENT`).
- **Month 3+**: Full CI integration with REQUEST_CHANGES gating. Track: false-positive rate (findings reverted by maintainer), suppression accuracy (findings re-raised that were already discussed), time-to-first-review.

Track: false-positive rate per PR (target trending toward zero), reviewer-feedback signal in `overrides.md` (which marker phrases the team adds), CI gating effectiveness (PRs that needed `--strict` vs. didn't).

## Reference Loading

For deeper analysis, load supporting reference files alongside this `SKILL.md`:

- `reference.md` — Persona rubrics in full, gh command reference, submission protocol, decision matrix elaboration, sources
- `reference-personas.md` — Per-persona deep dive: concerns, triggers, anti-overlap rules, finding examples, common false-positive patterns
- `reference-lifecycle.md` — Six-state classification details, won't-fix markers, fingerprinting algorithm, stale threshold logic
- `lang-python.md`, `lang-typescript.md`, `lang-java.md` — Language-specific PR-review patterns (auth middlewares, migration tooling, dependency files)
- `examples/review-output-example.md` — End-to-end PR review output sample with mixed personas and lifecycle visible
- `examples/persona-delegation-example.md` — Worked example of SE deferring to `ship-clean-code`
- `examples/lifecycle-classification-example.md` — All six lifecycle states demonstrated on one PR
- `examples/ci-github-actions.yml`, `examples/ci-gitlab.yml` — CI integration snippets
- `examples/ci-output-json.md` — `--json` output schema for downstream CI tooling
- `tests/` — Self-test fixtures (sample PR + thread state, expected output)

Paths are relative to this `SKILL.md`. Load on-demand when doing thorough reviews or when the user asks for detailed guidance on a specific topic.
