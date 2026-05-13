# Synthetic PR Input for Fixture 4: Clean Approve

You are reviewing a small, clean PR. Treat the input below as the result of the `gh` fetch phase.

## PR metadata

```json
{
  "owner": "acme",
  "repo": "docs",
  "number": 1234,
  "title": "Fix typo in onboarding doc",
  "body": "Fixes a typo: 'recieve' -> 'receive' in docs/onboarding.md.",
  "headRefName": "fix/onboarding-typo",
  "baseRefName": "main",
  "author": "henry",
  "isDraft": false,
  "labels": [],
  "files": [
    {"path": "docs/onboarding.md", "additions": 1, "deletions": 1}
  ],
  "statusCheckRollup": {"state": "SUCCESS"},
  "commits": [{"sha": "fff999", "committedDate": "2026-05-12T08:00:00Z"}]
}
```

## Diff (gh pr diff)

```diff
diff --git a/docs/onboarding.md b/docs/onboarding.md
@@ -42,7 +42,7 @@ Once your environment is set up:
 1. Clone the repo
 2. Install dependencies
-3. You will recieve a welcome email
+3. You will receive a welcome email
 4. Verify the email link
```

## Review threads (gh api graphql)

```json
{
  "reviewThreads": []
}
```

## CI checks

All green.

## Invocation flags

The user invoked the skill with `--auto-approve`.

---

Run the multi-persona PR review. This is a clean, docs-only, single-typo change. The skill should produce APPROVE and (because `--auto-approve` is set on a green-path APPROVE) submit without prompting.
