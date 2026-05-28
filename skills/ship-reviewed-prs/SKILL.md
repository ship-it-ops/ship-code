---
name: ship-reviewed-prs
description: >
  Perform a thorough, multi-persona pull-request review (senior engineer, senior
  security engineer, senior infra/SRE, conditional senior data engineer, plus
  test-coverage signal). Reads existing PR comment threads and suppresses
  findings that are already resolved, marked won't-fix, or addressed in a later
  commit. Computes a deterministic APPROVE / REQUEST_CHANGES / COMMENT decision
  and can submit the review via gh CLI (with confirmation gating in local mode
  and full automation in CI).
allowed-tools: Task, TodoWrite, Bash, Read, Grep, Glob
argument-hint: "[pr-number-or-url] [--auto-approve] [--non-interactive] [--json] [--strict]"
---

# Multi-Persona PR Review Skill

## Purpose

This skill performs a structured, multi-persona pull-request review that catches concerns a single rubric misses, respects the comment history of long-lived PRs, and produces a decisive APPROVE / REQUEST_CHANGES / COMMENT recommendation. It runs locally with an interactive confirmation gate or in CI with full automation. It composes with the sibling skills (`ship-clean-code`, `ship-tested-code`, `ship-debugged-code`) by delegating concerns those skills own rather than duplicating them.

## Quickstart (New to This Skill?)

Start with these 3 rules and internalize them before learning the rest:
1. **Read the PR description and the existing review threads BEFORE forming new findings** — the most expensive review is one that re-raises a concern already discussed.
2. **Personas have distinct rubrics, but findings deduplicate** — one finding per `(file, line, root cause)`, owned by the highest-priority persona.
3. **The decision is mechanical** — APPROVE / REQUEST_CHANGES / COMMENT follows from the merged finding list and CI status. The skill writes prose; the verdict is computed. Suggestions (P6/P7) and pending CI become advisory notes inside the APPROVE body rather than verdict downgrades.

The detailed reference files (`reference.md`, `reference-personas.md`, `reference-lifecycle.md`) assume familiarity with `gh` CLI, GitHub's review-thread model, and the sibling skills.

## Invocation

```
/ship-reviewed-prs <pr-number-or-url> [flags]
```

**Flags:**

| Flag | Effect |
|------|--------|
| `--auto-approve` | Local only: auto-submit on **clean** APPROVE (green CI, zero open threads, zero findings of any tier — including suggestions). Suggestion findings, delegations, or pending CI block auto-submit and require interactive confirm; APPROVE-with-caveats is still APPROVE but the human should glance at the caveats before submitting. Never honored for REQUEST_CHANGES or COMMENT. Ignored in CI. |
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

### 6. CI failing blocks APPROVE; pending CI is noted, not blocking.
Never approve over red CI — the decision degrades to COMMENT with a "CI must pass before approval" note. Pending CI (checks still running) does NOT block APPROVE; instead the review body adds a "Recommend awaiting CI completion before merge" caveat so the human reviewer has the signal without losing the verdict.

### 7. "Possibly addressed" needs human confirmation — except for bot-own threads.
A later commit touching the same file:line as an open comment is a heuristic, not a fact. **Human-authored threads**: surface the signal, do not assume resolution; APPROVE is degraded to COMMENT until a human confirms. **Bot-authored threads** (the skill posted the original inline comment on a prior run): on the next run, if the same fingerprint no longer fires, the bot posts a one-line `✅ Resolved by ship-reviewed-prs` reply and calls `resolveReviewThread`. Full protocol in `reference.md` §6 Step 4. Override knob `auto_resolve_own_threads` (default `true`).

### 8. Surface confidence, not opinion.
The output includes a Confidence section that names what was reviewed, what was *not* reviewed (out of scope, large generated files, unreviewable binaries), and what's residual risk. A confident "REQUEST_CHANGES" is paired with the specific finding that drove the decision.

### 9. Always include "What's solid".
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
| FE | Senior Frontend Engineer | Conditional on tsx/jsx/component files | A11Y contract correctness, controlled-component state desync, command/history completeness, no-op prop values, SSR/global-CSS constraints, range clamping, changeset accuracy. |
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

**FE activates** when the diff touches any of:
- `*.tsx`, `*.jsx`
- `*.ts` / `*.js` that declare `useState`, `useEffect`, or return JSX
- `next.config.*`, `vite.config.*`, `webpack.config.*`
- A new `import './*.css'` line inside a non-entry module
- A new `aria-*`, `role=`, or `tabIndex` attribute on any element
- `packages/*/src/` in a React/UI library workspace
- `.changeset/*.md` accompanying any of the above (FE7 cross-checks changeset vs. diff)

Triggers are tunable via `overrides.md` — see Team Overrides below.

## Delegation Table

Personas defer to sibling skills rather than duplicating their rubrics. The decision is made BEFORE emitting a finding:

| If the finding is fundamentally about... | Replace with |
|---|---|
| Naming, function size, magic numbers, dead code, error swallowing, readability | `Run /ship-clean-code on <file>` |
| Test design, test coverage depth, flakiness, AAA structure, mocking strategy | `Run /ship-tested-code on <file>` |
| Root cause of a bug the PR claims to fix (PR description contains "fixes #N") | `Run /ship-debugged-code on PR #N` |
| Security depth (data-flow trace, framework-specific injection / XSS / SSRF / deserialization / supply chain / crypto / IDOR) beyond a one-line SC pattern match | `Run /ship-secure-code on <file>` |

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

Computed deterministically from the merged finding list. No LLM judgment. Evaluated top-down — the first matching row wins:

| State | Decision |
|-------|----------|
| `is_draft` or WIP-labelled | `COMMENT` |
| Any unsuppressed *1-*2 finding (Critical) | `REQUEST_CHANGES` |
| Any unsuppressed *3-*5 finding (Important) | `COMMENT` |
| CI failing (`ci_state == red`) | `COMMENT` — "CI must pass before approval" |
| `lifecycle_quality == degraded` (pagination incomplete) | `COMMENT` — suppression unreliable |
| Any "Possibly addressed" items | `COMMENT` — needs human confirmation |
| Otherwise (incl. only suggestions, delegations, and/or pending CI) | `APPROVE` — caveats noted inline |

APPROVE may carry optional "Suggestions", "Delegations", or "Awaiting CI" caveats in the review body; these are advisory and do not change the verdict. APPROVE never accompanies an Important or Critical finding.

## Comment Lifecycle

Before emitting findings, classify every existing review thread into one of six states:

| State | Definition | Behavior |
|-------|------------|----------|
| RESOLVED | `isResolved: true` on the thread | Suppress; count only |
| OUTDATED | `isOutdated: true` AND line no longer exists in current diff | Suppress; count only |
| WONT_FIX | Last author/maintainer comment matches won't-fix marker OR reaction-marker | Suppress; count only |
| ADDRESSED (bot-own) | Bot authored the thread on a prior run AND the fingerprint no longer fires | Auto-resolve (reply + `resolveReviewThread`); count only |
| ADDRESSED (human) | Human-authored open thread, later commit touched `path` near `original_line ± 5` | Surface as "Possibly addressed — needs reviewer confirmation"; do not re-derive |
| BOT_RESOLVED_REOPENED | Bot resolved on a prior run; human unresolved it since | Treat as OPEN; do NOT re-resolve. Surface "maintainer disagrees with prior bot resolution" |
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

4. **Conditional escalation** (Explore subagents, up to 3 in parallel):
   - If DA activates: spawn one subagent with the DA rubric and the schema/migration/event files. The subagent reads adjacent context (existing schema, downstream consumers) the orchestrator hasn't fetched.
   - If IN deep mode activates: spawn one subagent with the IN deep rubric and the infra files.
   - If FE activates: spawn one subagent with the FE rubric and the component/tsx files. The subagent reads adjacent test files alongside each component (to detect missing axe-state coverage), the package's `index.ts` for exported types, and any sibling `*.css.ts` token files. It also reads `.changeset/*.md` bodies to cross-check FE7-CHANGESET-DRIFT.

5. **Merge phase** (orchestrator):
   - Deduplicate by fingerprint `(path, line ± 5, root-cause-token)`. Higher-priority persona wins (SC > SE; DA > IN on schema files).
   - Apply suppression against RESOLVED/OUTDATED/WONT_FIX threads.
   - Compute decision via the matrix above.
   - Render output. In CI, emit `--json` if requested; in local, prompt for confirmation.

## Submission Protocol

Every Critical and Important finding that has a concrete `file:line` target **MUST** be posted as an inline review comment via the pending-review protocol below. Posting all findings as a single summary blob is a regression — the developer cannot see feedback in the diff and cannot accept fixes with one click. A finding without a precise line (architectural concern, cross-file pattern) lives in the summary body only. Suggestion-tier (P6/P7) findings post inline **when** they include a mechanical fix; otherwise they appear in the summary body.

The summary body is an **index, not a duplicate**. It carries Verdict, Confidence, Personas activated, Findings (a two-column severity-count table followed by per-tier anchor sub-lists), Delegations, Comment lifecycle, and What's solid. It does NOT repeat the full inline body — each Critical/Important finding lives in its inline comment, and the per-tier anchor sub-lists point readers there.

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

The simpler `gh pr review <n> --approve --body <summary>` form is allowed **only** when the decision is APPROVE AND the inline-comment count is exactly zero (clean APPROVE with nothing to anchor). REQUEST_CHANGES, COMMENT, and any APPROVE with at least one inline finding must use the three-step pending-review protocol above.

Full `gh` command reference in `reference.md`.

## Suggested-change Blocks

When an inline finding carries a small, self-contained, mechanical fix, embed it in a GitHub `suggestion` fence so the author can hit "Commit suggestion" instead of editing by hand. Qualify/disqualify rules, the alignment requirement, and a worked `gh` example live in `reference.md` §6.2a.

## Local Submission Gate

In local mode, after computing the decision and rendering the draft:

```
Verdict: Changes requested
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

The output is split into two surfaces: a list of **inline comments** (anchored at `file:line`, posted via the pending-review protocol) and a single **summary body** (a scannable index, posted as the review body). The two are submitted as one atomic review.

### Inline comments to post

Render one block per inline comment, in priority order. Each block names the persona/finding ID, the file and line range, whether a `suggestion` fence is included, and the body that gets posted.

```
--- inline comment 1 ---
[IN1-PROD-OUTAGE-RISK]  services/billing.ts:5
suggestion: yes

**[IN1-PROD-OUTAGE-RISK]** `fetch("https://billing.internal/users/...")` has
no timeout. A slow billing-internal will hang this function indefinitely,
blocking the calling request and exhausting connection-pool capacity.

```suggestion
  const user = await fetch(`https://billing.internal/users/${userId}`, { signal: AbortSignal.timeout(5000) }).then(r => r.json());
```

--- inline comment 2 ---
[IN2-OBSERVABILITY-GAP]  api/admin.ts:42
suggestion: no  (needs new import + new metric — keep as prose)

**[IN2-OBSERVABILITY-GAP]** New admin endpoint has no audit log and no metric.
Admin actions that change user state always warrant audit logging. Add
`logger.info("admin.tier_changed", { actor_id, target_user_id, new_tier })`
and increment a counter `admin.actions.tier_change`. The logger and counter
both need imports from `lib/observability.ts`, so this isn't a one-line
suggestion.
```

### Summary body (posted as review body)

```
## PR Review — #<n> `<title>`

**Verdict: LGTM | LGTM (with caveats) | Changes requested | Comment**

### Confidence
<2-4 sentences: what was reviewed, what was not (out of scope, large generated
files), what's the residual risk, why this verdict is the right one.>

### Personas activated

| Persona | Status | Reason |
|---|---|---|
| SE | ✅ active / ✅ pass / ⏭ skip | <one-line reason, lowercase noun phrase> |
| SC | ✅ active / ✅ pass / ⏭ skip | <one-line reason> |
| IN | ✅ active / ✅ pass / ⏭ skip | <light or deep, plus the trigger> |
| DA | ✅ active / ✅ pass / ⏭ skip | <one-line reason> |
| FE | ✅ active / ✅ pass / ⏭ skip | <one-line reason> |
| TS | ✅ active / ✅ pass / ⏭ skip | <one-line reason> |

### Findings

| Severity   | Count |
|---|---|
| Must-fix   | <n> |
| Should-fix | <n> |
| Nits       | <n> |

**Must-fix anchors:** (rendered only when Count > 0)
- `SC1` api/users.ts:42 — see inline comment
- `DA1` migrations/0042.sql:5 — see inline comment

**Should-fix anchors:**
- `IN2` services/billing.ts:118 — see inline comment
- `SE4-MODULE-SHAPE` services/billing — three responsibilities should split. (no inline anchor)

**Nit anchors:** `IN7` services/search.ts:88 — see inline comment

### Delegations
- Run `/ship-tested-code` on `services/billing.test.ts` (TS1: PR adds production code with no test).
- Run `/ship-clean-code` on `services/billing.ts` (naming/readability concerns deferred).

### Comment lifecycle

| State | Count |
|---|---|
| Resolved | 3 |
| Won't-fix | 2 |
| Outdated | 1 |
| Possibly addressed | 1 |
| Stale | 0 |
| Open | 1 |

Suppressed 4 findings already discussed in earlier review.

### Stale comments needing reply
- `services/auth.ts:30` — opened 23 days ago, no author response.

### What's solid
- Migration includes backfill + rollback plan in PR body.
- BillingClient is constructor-injected, replacing a static singleton.
- New tests use the standard factory pattern.
```

### Submission preview (local mode only)

Posts 4 inline comments (2 with `suggestion` fences) + 1 anchorless finding (SE4) bodied in the Should-fix sub-list; verdict `Changes requested` (decision REQUEST_CHANGES). Three `gh api` steps — create PENDING review → post inline comments × 4 → submit `event=REQUEST_CHANGES` with body. Local prompt: `yes` / `edit` / `no`.

Rules for the output (full rendering detail in `reference.md` §6a):

- **Inline comments are mandatory** for every Critical and Important finding with a `file:line` target. The summary body is a pointer index, not a duplicate of the inline bodies.
- **Verdict is a bold paragraph, not a heading.** Friendly labels (`LGTM` / `LGTM (with caveats)` / `Changes requested` / `Comment`) map to the formal `APPROVE` / `REQUEST_CHANGES` / `COMMENT` keywords used in JSON output, exit codes, and `gh` API calls. Mapping in `reference.md` §6a.
- **Confidence is always present** and substantive (not "looks fine").
- **Personas activated table is always rendered with all six rows** (SE / SC / IN / DA / FE / TS). Status semantics and reason-text rubric in `reference.md` §6a.
- **Findings table is always rendered** with three rows Must-fix (priority 1-2) / Should-fix (3-5) / Nits (6-7) and exactly two columns: Severity, Count. Per-tier `**<Tier> anchors:**` bullet sub-lists render below the table only for tiers with `Count > 0`. Anchor format and anchorless-finding handling in `reference.md` §6a.
- **Comment lifecycle table is always present.** Distinct surface from the Findings table — thread states, not severity counts.
- **What's solid is always present** with concrete observations.
- **Conditional sections** (per-tier anchor sub-lists, `Delegations`, `Stale comments needing reply`) are omitted when empty rather than rendered with `(none)` placeholders.
- Tag every finding with its priority code (SE1, SC2, etc.) in both the anchor sub-list and the inline comment.
- Every inline finding includes a concrete fix — either a `suggestion` fence (when it qualifies) or prose.
- More than 10 inline findings: post the top 10 strictly ordered by priority. Never suppress *1 findings due to the cap. The Findings-table `Count` is always true; only the anchor sub-list truncates. Full list always available in `--json`.

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
- **`/ship-secure-code`** — Application-security depth (SEC1-SEC12: auth, input validation, injection, XSS, CSRF/origin, crypto, secrets, supply chain, PII/logging, resource exhaustion, path traversal, deserialization/SSRF). The SC persona scans the diff with high-precision single-line patterns and delegates anything requiring data-flow trace or framework-specific depth here.

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

Phased rollout: local-only with `--auto-approve` disabled (weeks 1-4) → green-path `--auto-approve` + CI in `ci_max_decision: COMMENT` (month 2) → full CI gating with REQUEST_CHANGES (month 3+).

Track: false-positive rate (findings reverted by maintainers), suppression accuracy (re-raised concerns already discussed), CI gating effectiveness (`--strict` usage). Monthly eval cadence and recommended CSV format in `reference.md` §Monthly Eval.

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
