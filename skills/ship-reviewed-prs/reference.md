# PR Review Reference

Detailed rubrics, command reference, and submission protocol. Persona deep-dive lives in `reference-personas.md`; comment-lifecycle algorithm in `reference-lifecycle.md`.

---

## 1. Fetch Phase — `gh` Command Reference

### PR metadata and file list

```bash
gh pr view <n> --json title,body,headRefName,baseRefName,author,labels,files,statusCheckRollup,commits,isDraft,mergeable,reviewDecision
```

Key fields used:
- `title`, `body` — searched for "fixes #N" (bugfix delegation), "WIP"/"DRAFT" markers, "out of scope" declarations
- `headRefName`, `baseRefName` — needed for diff and inline-comment positioning
- `labels` — `wip`, `do-not-merge`, etc.
- `files[].path`, `files[].additions`, `files[].deletions` — triage classification
- `statusCheckRollup` — CI status; required for the APPROVE/CI-green check
- `commits` — for the "addressed in later commit" lifecycle heuristic
- `isDraft` — degrades decision to COMMENT
- `mergeable` — flag if `false`

### Diff

```bash
gh pr diff <n>
```

Plain unified diff. Pipe to a length-cap (e.g., `head -c 200000`) for very large PRs; persona passes only need diff context, not the full patch on monorepo-scale PRs.

### CI status

```bash
gh pr checks <n>
```

Returns each check with status (`pass`, `fail`, `pending`, `skipping`). Decision matrix uses overall pass/fail; details only flagged for IN5 CI-PIPELINE findings on a failing job.

### Review threads (GraphQL — only way to get `isResolved`/`isOutdated`)

```bash
gh api graphql -f query='
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          originalLine
          comments(first: 50) {
            nodes {
              databaseId
              body
              author { login }
              authorAssociation
              createdAt
              reactions(first: 20) {
                nodes { content user { login } }
              }
            }
          }
        }
      }
    }
  }
}' -f owner=<owner> -f repo=<repo> -F number=<n>
```

`authorAssociation` distinguishes OWNER / MEMBER / COLLABORATOR / CONTRIBUTOR / NONE — used to identify maintainers for won't-fix marker detection.

REST `/pulls/{n}/comments` does NOT return resolution state. Use GraphQL.

### Review-level submissions (history)

```bash
gh api repos/<owner>/<repo>/pulls/<n>/reviews --paginate
```

Used to see prior APPROVED / CHANGES_REQUESTED / COMMENTED reviews. A REQUEST_CHANGES that was later dismissed is informational; one still in effect blocks merge regardless of this skill's decision.

---

## 2. Triage Pass — File Bucketing

Classify each changed file into exactly one bucket:

| Bucket | Heuristic |
|--------|-----------|
| `test` | Path matches `test/`, `tests/`, `__tests__/`, `*.test.*`, `*.spec.*`, `*_test.go`, `*Test.java`, `*Spec.*` |
| `infra` | Path matches infra triggers (see SKILL.md DA/IN-deep activation lists) |
| `schema` | Path matches schema triggers (see SKILL.md DA activation list) |
| `docs` | Path matches `*.md`, `*.rst`, `*.txt`, `docs/`, `README*`, `CHANGELOG*` |
| `generated` | Path matches `*.generated.*`, `*.pb.go`, `*.pb.ts`, `*_pb2.py`, files with `@generated` header in first 20 lines |
| `vendor` | Path matches `vendor/`, `node_modules/`, `third_party/`, `external/` |
| `code` | Everything else (default) |

Persona file selectivity:
- SE: `code`, `docs` (for API docs / public signature changes)
- SC: `code`, `schema`, `infra`, `docs` (scans everything for secrets)
- IN-light: `code` (flags missing timeouts/retries)
- IN-deep: `infra`
- DA: `schema`
- TS: `code` (to compute the test-coverage ratio)

`generated` and `vendor` are skipped by all personas. Count them in the output ("12 generated, 3 vendor files skipped").

---

## 3. Persona Passes — Ordering and Bracketing

Always-on personas run sequenced in the orchestrator's context:

```
## SE pass
<orchestrator reads diff with SE rubric only; emits SE1-SE7 findings>

## SC pass
<orchestrator reads diff with SC rubric only; emits SC1-SC7 findings>

## IN-light pass
<orchestrator reads diff with IN rubric (network calls, observability gaps) without going deep on infra files>

## TS pass
<orchestrator computes coverage ratio: prod files modified vs. test files added/modified. Emits TS1 if ratio is bad and the prod file is in the `code` bucket. Emits TS2 if PR body matches "fixes #N" and no test file under `code` bucket was modified.>
```

Bracketing is intentional. It keeps each persona's voice distinct without isolating context. The model reads its rubric, scans the diff, emits, and moves on.

Conditional personas (DA, IN-deep) escalate to Explore subagents because they need to read *adjacent* files (existing schema, downstream consumers, related infra) that the orchestrator hasn't fetched. The subagent receives:
- The activated files (schema files for DA, infra files for IN-deep)
- The persona rubric (just that one section of `reference-personas.md`)
- Repo root path
- Instructions to return a structured findings block, not chatty prose

Subagent timeout: 5 minutes per subagent. On timeout, fall back to a single in-context pass with a confidence flag.

---

## 4. Merge Phase — Deduplication and Priority Ordering

### Deduplication

Every emitted finding gets a fingerprint:

```
fingerprint = (path, floor(line / 5), root_cause_token)
```

Where `root_cause_token` is a normalized form of the finding's category (e.g., `MISSING_AUTH`, `SQL_INJECTION`, `NO_TIMEOUT`, `BACKFILL_MISSING`). The skill's prompt defines the canonical token list; new categories are added explicitly, not invented at runtime.

Conflict resolution:
- Higher-priority persona wins. Within tiers: SC > IN > DA > SE > TS.
- Exception: on schema files (DA-activated), DA wins over IN.
- Lower-priority finding is dropped; not merged. The reviewer sees one finding, with the strongest framing.

### Priority sort

After dedup, sort:
1. By severity tier: Critical (priorities 1-2), Important (3-5), Suggestions (6-7).
2. Within tier, by priority number ascending.
3. Within same number, by persona prefix alphabetical (DA → IN → SC → SE → TS — happens to match severity weight on most schema/infra-heavy PRs).
4. Within same persona, by `path` then `line`.

### 10-finding cap

If after sort there are more than 10 findings:
- Show the top 10 in priority order.
- *1 findings (SC1/IN1/DA1/SE1/TS1) are NEVER suppressed by the cap. If 11 findings exist and one is SC1, drop something else.
- Summarize the rest: `+ 5 more findings (3 P6-readability, 2 P7-style) — see full list with --verbose`.

---

## 5. Decision Matrix — Elaboration

The decision is a function of:
- `critical_count` (unsuppressed findings with priority 1-2)
- `important_count` (priority 3-5)
- `suggestion_count` (priority 6-7)
- `delegation_count`
- `open_thread_count` (lifecycle state OPEN)
- `possibly_addressed_count` (lifecycle state ADDRESSED)
- `ci_state` (`green`, `red`, `pending`)
- `is_draft` (PR is in draft state or WIP-labelled)

| Condition | Decision |
|-----------|----------|
| `is_draft` | `COMMENT` |
| `critical_count > 0` | `REQUEST_CHANGES` |
| `important_count == 0 && suggestion_count == 0 && delegation_count == 0 && open_thread_count == 0 && possibly_addressed_count == 0 && ci_state == green` | `APPROVE` |
| `ci_state == red` | `COMMENT` (with "CI must pass before approval" note) |
| `ci_state == pending` | `COMMENT` (with "Re-run when CI completes" note) |
| `possibly_addressed_count > 0` | `COMMENT` (with "Confirm addressed items to escalate" note) |
| `important_count > 0` | `COMMENT` (advisory) — but never `APPROVE` |
| Otherwise (suggestions or delegations only) | `COMMENT` |

The matrix is intentionally conservative on `APPROVE`. A clean PR with no findings, no open threads, and green CI is the ONLY path to approval. Everything else is at most COMMENT.

---

## 6. Submission Protocol

GitHub's pending-review API ensures atomicity: inline comments + summary are submitted as a single review object. Use this protocol every time, not the simpler `gh pr review --approve` (which has no inline-comment support).

### Step 1: Create pending review

```bash
REVIEW_ID=$(gh api -X POST "repos/<owner>/<repo>/pulls/<n>/reviews" \
  -f body="" \
  --jq '.id')
```

When `event` is omitted, the review is created in PENDING state.

### Step 2: Post each inline comment

```bash
gh api -X POST "repos/<owner>/<repo>/pulls/<n>/reviews/${REVIEW_ID}/comments" \
  -f path="<file>" \
  -F line=<line> \
  -f side="RIGHT" \
  -f body="<finding body>"
```

For multi-line range comments (a finding that spans lines):

```bash
gh api -X POST "repos/<owner>/<repo>/pulls/<n>/reviews/${REVIEW_ID}/comments" \
  -f path="<file>" \
  -F line=<end_line> \
  -F start_line=<start_line> \
  -f start_side="RIGHT" \
  -f side="RIGHT" \
  -f body="<finding body>"
```

### Step 3: Submit the review

```bash
gh api -X POST "repos/<owner>/<repo>/pulls/<n>/reviews/${REVIEW_ID}/events" \
  -f event="APPROVE|REQUEST_CHANGES|COMMENT" \
  -f body="<summary>"
```

### Error handling

- If step 1 fails: exit `3`, no cleanup needed (no resources created).
- If step 2 fails partway: dismiss the pending review with `gh api -X DELETE "repos/.../reviews/${REVIEW_ID}"`. Exit `3`. Never leave a half-formed pending review attached.
- If step 3 fails: same cleanup. Pending reviews are visible to the author and confusing.

### Bot identity prefix (CI mode)

Prepend to the `body` of step 3:

```
Posted by ship-reviewed-prs (bot). Reasoning available in this comment;
ask the author/oncall for human judgment on disputed findings.

---
<actual summary>
```

The prefix line is configurable via `overrides.md` (`ci_bot_identity_prefix`).

---

## 7. Repository Discovery

The skill needs `<owner>` and `<repo>` for GraphQL and REST calls. Derive in order:

1. PR URL provided: parse `https://github.com/<owner>/<repo>/pull/<n>`.
2. PR number only + run from inside a git checkout: `gh repo view --json owner,name`.
3. PR number only + not in a checkout: error, exit `3` with hint to provide a full URL.

For GitHub Enterprise: respect `GH_HOST` env var. `gh` CLI handles routing automatically.

---

## 8. JSON Output Schema (`--json`)

```json
{
  "pr": {
    "owner": "ship-it-ops",
    "repo": "ship-code",
    "number": 47,
    "title": "Add login retry",
    "url": "https://github.com/ship-it-ops/ship-code/pull/47",
    "head_sha": "abc123...",
    "is_draft": false
  },
  "decision": "REQUEST_CHANGES",
  "decision_reason": "1 SC1-AUTH-MISSING, 1 DA1-SCHEMA-BREAK",
  "ci_state": "green",
  "exit_code": 1,
  "findings": [
    {
      "id": "SC1-AUTH-MISSING",
      "persona": "SC",
      "priority": 1,
      "severity": "critical",
      "path": "api/users.ts",
      "line": 42,
      "body": "New POST /admin/users has no auth middleware.",
      "suggestion": "Add requireAdmin middleware; see api/admin/*.ts."
    }
  ],
  "delegations": [
    {
      "skill": "ship-tested-code",
      "path": "services/billing.test.ts",
      "reason": "TS1: production file changed with no corresponding test."
    }
  ],
  "lifecycle": {
    "resolved": 3,
    "outdated": 1,
    "wont_fix": 2,
    "addressed": 1,
    "stale": 0,
    "open": 1,
    "suppressed_findings": 4
  },
  "whats_good": [
    "Migration includes backfill + rollback plan.",
    "BillingClient is constructor-injected."
  ],
  "submission": {
    "submitted": true,
    "submitted_event": "REQUEST_CHANGES",
    "review_url": "https://github.com/ship-it-ops/ship-code/pull/47#pullrequestreview-1234567"
  }
}
```

See `examples/ci-output-json.md` for a fully worked sample with all fields populated.

---

## 9. Pragmatism in Practice

### Generated and vendored code
Skipped by every persona. Reported as a count: "skipped 12 generated, 3 vendor files."

### Docs-only PRs
SC still runs (links to internal infra, leaked URLs, env-var names that reveal architecture). SE/IN/DA/TS skip. Decision: APPROVE or COMMENT only — never REQUEST_CHANGES for docs-only.

### WIP / Draft PRs
- `isDraft: true` → COMMENT only.
- Title contains `WIP`, `DRAFT`, `[WIP]`, `[DRAFT]` → COMMENT only.
- Label `wip`, `do-not-merge`, `draft` → COMMENT only.

### Trivial PRs (≤ 5 changed lines, no new files)
- Skip subagent escalation regardless of triggers.
- If no findings: APPROVE on green CI.

### Long-lived PRs (≥ 50 comments OR ≥ 30 commits)
- Lead the output with the lifecycle summary line (move it above the Confidence section).
- Suppression should match `path` only (drop the line component) for older threads — review threads drift as the diff evolves.

### Repos without `gh` CLI
Exit `3` with a clear message: "gh CLI required. Install: https://cli.github.com/" — no graceful degradation. The skill is fundamentally about GitHub PRs.

### Repos without GraphQL access (rare, mostly self-hosted GHE with strict scopes)
Fall back to REST-only mode. Lose `isResolved`/`isOutdated` signal. Tag the output with `"lifecycle_quality": "degraded"` in JSON. Local prose mode adds a warning.

---

## 10. Failure Modes and Recovery

| Failure | Behavior |
|---------|----------|
| `gh` not installed | Exit `3`, message |
| `gh auth status` fails (local) or `GH_TOKEN` missing (CI) | Exit `3`, message |
| PR not found / no access | Exit `3`, message |
| PR is closed/merged | Exit `2`, COMMENT with "PR is no longer open" |
| GraphQL rate-limited | Wait + retry once with exponential backoff; on second failure fall back to REST and tag `lifecycle_quality: degraded` |
| Diff too large (>500K) | Process in chunks. Personas read 50K-line windows sequentially. Note in Confidence section. |
| Subagent timeout | Fall back to in-context pass for that persona. Note in Confidence section. |
| Pending review cleanup fails | Log to stderr. Do NOT exit `0`. Exit `3` with the orphaned review ID for manual cleanup. |

---

## Quick-Reference Checklist

| Step | Action |
|------|--------|
| 1 | Fetch PR metadata, diff, threads, CI status |
| 2 | Triage files into buckets |
| 3 | Run SE → SC → IN-light → TS passes in-context |
| 4 | If DA/IN-deep activate, spawn subagent(s) |
| 5 | Merge findings (dedup, priority sort, 10-cap) |
| 6 | Classify threads (RESOLVED / OUTDATED / WONT_FIX / ADDRESSED / STALE / OPEN) |
| 7 | Suppress findings matching RESOLVED/OUTDATED/WONT_FIX fingerprints |
| 8 | Compute decision from matrix |
| 9 | Render output (or JSON) |
| 10 | Local: prompt for confirmation. CI: submit immediately. |
| 11 | Exit with appropriate code |

---

## Sources

- **OWASP Top 10** (2021 + ongoing) — Security findings (SC) reference OWASP categories.
- **OWASP API Security Top 10** (2023) — API-specific auth/authz failures.
- **Site Reliability Engineering** — Beyer, Jones, Petoff, Murphy (2016). Source for IN persona principles around observability, error budgets, and graceful degradation.
- **Database Reliability Engineering** — Laine Campbell, Charity Majors (2017). Source for DA persona principles around migration safety, schema evolution, and operational data integrity.
- **Building Secure and Reliable Systems** — Adkins, Beyer, Blankinship, Lewandowski, Oprea, Stubblefield (Google, 2020). Source for the security-and-reliability integration philosophy.
- **GitHub Pull Request Review API documentation** — Submission protocol details, the pending-review state model.
- **The Linux kernel review process / well-run open-source projects** — Comment lifecycle conventions, won't-fix marker culture.
- **Industry consensus on bot-author review etiquette** — Bot disclosure, asymmetric automation rules, decision-matrix-driven verdicts (e.g., Reviewable, Reviewdog, Danger.js conventions).

The skill's specific design choices — five-persona model, two-letter prefix system, fingerprinted suppression algorithm, asymmetric `--auto-approve` semantics — are original to this repo and chosen for review legibility and operational safety.
