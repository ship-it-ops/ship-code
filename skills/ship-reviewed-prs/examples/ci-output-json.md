# `--json` Output Schema and Sample

When invoked with `--json`, the skill emits a structured result to stdout. This is the schema and a fully-populated sample for downstream CI tooling.

---

## Schema

```typescript
interface ReviewResult {
  // Identification
  pr: {
    owner: string;
    repo: string;
    number: number;
    title: string;
    url: string;
    head_sha: string;
    is_draft: boolean;
  };

  // The verdict
  decision: "APPROVE" | "REQUEST_CHANGES" | "COMMENT";
  decision_reason: string;  // Short human-readable summary of why
  ci_state: "green" | "red" | "pending" | "unknown";
  exit_code: 0 | 1 | 2 | 3;

  // Findings, in priority order
  findings: Finding[];

  // Delegations to sibling skills
  delegations: Delegation[];

  // Lifecycle summary
  lifecycle: {
    resolved: number;
    outdated: number;
    wont_fix: number;
    addressed: number;
    stale: number;
    open: number;
    suppressed_findings: number;
  };

  // Substantive positive observations
  whats_good: string[];

  // Submission result (only present if submission actually happened)
  submission?: {
    submitted: boolean;
    submitted_event: "APPROVE" | "REQUEST_CHANGES" | "COMMENT";
    review_url: string;
    capped: boolean;        // true if ci_max_decision downgraded the action
    capped_from?: string;   // original decision if capped
  };

  // Confidence metadata
  confidence: {
    files_reviewed: number;
    files_skipped_generated: number;
    files_skipped_vendor: number;
    files_skipped_docs: number;
    personas_run: string[];        // ["SE", "SC", "IN-light", "TS", "DA"]
    personas_escalated: string[];  // subset that escalated to subagents
    degraded_signals: string[];    // e.g., ["lifecycle_quality:degraded"] if GraphQL unavailable
  };
}

interface Finding {
  id: string;                  // e.g., "SC1-AUTH-MISSING"
  persona: "SE" | "SC" | "IN" | "DA" | "TS";
  priority: 1 | 2 | 3 | 4 | 5 | 6 | 7;
  severity: "critical" | "important" | "suggestion";
  path: string;
  line: number;
  line_end?: number;           // for range findings
  body: string;                // Problem description
  suggestion: string;          // Fix suggestion
  fingerprint: string;         // Internal dedup key — useful for CI tooling that merges runs
}

interface Delegation {
  skill: "ship-clean-code" | "ship-tested-code" | "ship-debugged-code";
  path?: string;               // file or null for PR-level delegations
  reason: string;              // Short justification
  finding_id?: string;         // e.g., "TS1-NO-TEST-FOR-NEW-CODE" if it originated as a finding
}
```

---

## Sample

```json
{
  "pr": {
    "owner": "ship-it-ops",
    "repo": "billing-service",
    "number": 4811,
    "title": "Add billing-tier feature flag and migration",
    "url": "https://github.com/ship-it-ops/billing-service/pull/4811",
    "head_sha": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
    "is_draft": false
  },
  "decision": "REQUEST_CHANGES",
  "decision_reason": "1 SC1-AUTH-MISSING (api/admin.ts), 1 DA3-BACKFILL-MISSING (migrations/0042)",
  "ci_state": "green",
  "exit_code": 1,
  "findings": [
    {
      "id": "SC1-AUTH-MISSING",
      "persona": "SC",
      "priority": 1,
      "severity": "critical",
      "path": "api/admin.ts",
      "line": 42,
      "body": "New POST /admin/users/:id/tier route has no auth middleware. Any unauthenticated request can change any user's tier.",
      "suggestion": "Add requireAdmin middleware (see api/admin/users.ts:8 for the existing pattern). Verify with: curl -X POST localhost:3000/admin/users/123/tier -d '{\"tier\":\"premium\"}' returns 401.",
      "fingerprint": "api/admin.ts:8:MISSING_AUTH"
    },
    {
      "id": "DA3-BACKFILL-MISSING",
      "persona": "DA",
      "priority": 3,
      "severity": "important",
      "path": "migrations/0042_add_user_tier.sql",
      "line": 1,
      "body": "Adding NOT NULL `tier` to an existing populated users table will fail when run against production data.",
      "suggestion": "Three-step migration: (1) add column nullable with default, (2) backfill in a separate deploy, (3) add NOT NULL constraint in a follow-up migration after backfill completes.",
      "fingerprint": "migrations/0042_add_user_tier.sql:0:BACKFILL_MISSING"
    },
    {
      "id": "IN1-PROD-OUTAGE-RISK",
      "persona": "IN",
      "priority": 1,
      "severity": "critical",
      "path": "services/billing.ts",
      "line": 5,
      "body": "fetch to billing-internal has no timeout; slow upstream will exhaust connection pool.",
      "suggestion": "Add signal: AbortSignal.timeout(5000) and use the team's httpWithRetry helper from lib/http.ts.",
      "fingerprint": "services/billing.ts:1:NO_TIMEOUT"
    },
    {
      "id": "SC7-LOG-LEAKAGE",
      "persona": "SC",
      "priority": 7,
      "severity": "suggestion",
      "path": "services/billing.ts",
      "line": 6,
      "body": "console.log writes the full user object to logs, including email.",
      "suggestion": "Use logger.info(\"billing.premium_check\", { user_id: userId }) — structured, redacted, and uses the project logger.",
      "fingerprint": "services/billing.ts:1:LOG_LEAK"
    },
    {
      "id": "SE2-CONTRACT-DRIFT",
      "persona": "SE",
      "priority": 2,
      "severity": "critical",
      "path": "sdk/index.ts",
      "line": 7,
      "body": "User.tier is added as Optional to the public SDK type. SDK consumers that destructure { tier } will receive undefined where the field didn't exist before.",
      "suggestion": "If the migration backfills tier for all users, mark required. If optional during rollout, document in the SDK changelog and set a removal-of-optionality target release.",
      "fingerprint": "sdk/index.ts:1:CONTRACT_DRIFT"
    }
  ],
  "delegations": [
    {
      "skill": "ship-tested-code",
      "path": null,
      "reason": "52 net added lines in services/billing.ts and api/admin.ts with no test files modified. TS1 triggered.",
      "finding_id": "TS1-NO-TEST-FOR-NEW-CODE"
    },
    {
      "skill": "ship-debugged-code",
      "path": null,
      "reason": "PR description references 'fixes #4801' but no regression test was added.",
      "finding_id": "TS2-NO-REGRESSION-FOR-BUGFIX"
    }
  ],
  "lifecycle": {
    "resolved": 1,
    "outdated": 1,
    "wont_fix": 1,
    "addressed": 0,
    "stale": 0,
    "open": 1,
    "suppressed_findings": 1
  },
  "whats_good": [
    "PR description is clear: explicit scope, out-of-scope items with ticket references, and links the bug being fixed.",
    "Feature gated by a column-as-flag (tier), making the rollout reversible by leaving the column nullable until backfill completes.",
    "SDK type updated in the same PR as the underlying schema change, avoiding a temporary inconsistency window."
  ],
  "submission": {
    "submitted": true,
    "submitted_event": "REQUEST_CHANGES",
    "review_url": "https://github.com/ship-it-ops/billing-service/pull/4811#pullrequestreview-1234567",
    "capped": false
  },
  "confidence": {
    "files_reviewed": 4,
    "files_skipped_generated": 0,
    "files_skipped_vendor": 0,
    "files_skipped_docs": 0,
    "personas_run": ["SE", "SC", "IN-light", "DA", "TS"],
    "personas_escalated": ["DA"],
    "degraded_signals": []
  }
}
```

---

## Sample: `ci_max_decision` cap in effect

When the team's `overrides.md` has `ci_max_decision: COMMENT` set and the skill computed REQUEST_CHANGES, the submission is downgraded but the exit code reflects the *original* severity:

```json
{
  "decision": "REQUEST_CHANGES",
  "exit_code": 1,
  "submission": {
    "submitted": true,
    "submitted_event": "COMMENT",
    "capped": true,
    "capped_from": "REQUEST_CHANGES",
    "review_url": "..."
  }
}
```

CI pipelines that read the exit code will still gate on severity 1; downstream tooling that reads the JSON sees both the cap and the original decision.

---

## Sample: degraded mode (GraphQL unavailable)

```json
{
  "decision": "COMMENT",
  "exit_code": 2,
  "confidence": {
    "files_reviewed": 4,
    "personas_run": ["SE", "SC", "IN-light", "TS"],
    "degraded_signals": [
      "lifecycle_quality:degraded",
      "reason:graphql_unavailable",
      "fallback:rest_threads_only_no_isResolved"
    ]
  },
  "lifecycle": {
    "resolved": 0,
    "outdated": 0,
    "wont_fix": 0,
    "addressed": 0,
    "stale": 0,
    "open": null,
    "suppressed_findings": null
  }
}
```

When `lifecycle_quality` is degraded, the skill cannot reliably suppress duplicate findings. It will not APPROVE in this mode regardless of finding count, and will surface a warning in the human-readable output.

---

## Consuming the JSON

A common pattern: post the result as a status check, or aggregate across multiple PRs in a dashboard.

```bash
# Example: post a GitHub commit status from the JSON
DECISION=$(jq -r .decision review-result.json)
COMMIT_SHA=$(jq -r .pr.head_sha review-result.json)
case "$DECISION" in
  APPROVE) STATE=success ;;
  REQUEST_CHANGES) STATE=failure ;;
  COMMENT) STATE=success ;;  # advisory only
esac
gh api -X POST repos/$OWNER/$REPO/statuses/$COMMIT_SHA \
  -f state=$STATE \
  -f context="ship-reviewed-prs" \
  -f description="$(jq -r .decision_reason review-result.json)"
```
