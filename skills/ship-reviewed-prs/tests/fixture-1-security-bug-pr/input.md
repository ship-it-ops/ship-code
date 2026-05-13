# Synthetic PR Input for Fixture 1: Security Bug

You are reviewing the following PR. Treat the input below as the result of the `gh` fetch phase. Do not actually run `gh` commands.

## PR metadata

```json
{
  "owner": "acme",
  "repo": "billing",
  "number": 5012,
  "title": "Add tier-upgrade endpoint",
  "body": "Adds a new endpoint POST /api/users/:id/upgrade-tier so admins can change user tiers.",
  "headRefName": "feat/tier-upgrade",
  "baseRefName": "main",
  "author": "carol",
  "isDraft": false,
  "labels": [],
  "files": [
    {"path": "api/users.ts", "additions": 18, "deletions": 0}
  ],
  "statusCheckRollup": {"state": "SUCCESS"},
  "commits": [{"sha": "abc123", "committedDate": "2026-05-12T10:00:00Z"}]
}
```

## Diff (gh pr diff)

```diff
diff --git a/api/users.ts b/api/users.ts
@@ -10,3 +10,21 @@
 router.get("/api/users/:id", requireAuth, async (req, res) => {
   const user = await db.users.findById(req.params.id);
   res.json(user);
 });
+
+router.post("/api/users/:id/upgrade-tier", async (req, res) => {
+  const { tier } = req.body;
+  const updated = await db.users.update(req.params.id, { tier });
+  res.json(updated);
+});
```

## Review threads (gh api graphql)

```json
{
  "reviewThreads": []
}
```

## CI checks (gh pr checks)

All green.

---

Run the multi-persona PR review and produce the structured output.
