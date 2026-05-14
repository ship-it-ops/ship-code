# Synthetic PR Input for Fixture 2: Schema Migration

You are reviewing the following PR. Treat the input below as the result of the `gh` fetch phase.

## PR metadata

```json
{
  "owner": "acme",
  "repo": "billing",
  "number": 5013,
  "title": "Drop legacy_external_id from users table",
  "body": "Removing the legacy_external_id column. We haven't used it for new signups since 2023.",
  "headRefName": "chore/drop-legacy-id",
  "baseRefName": "main",
  "author": "dan",
  "isDraft": false,
  "labels": [],
  "files": [
    {"path": "migrations/0042_drop_legacy_id.sql", "additions": 1, "deletions": 0},
    {"path": "models/user.py", "additions": 0, "deletions": 1}
  ],
  "statusCheckRollup": {"state": "SUCCESS"},
  "commits": [{"sha": "def456", "committedDate": "2026-05-12T11:00:00Z"}]
}
```

## Diff (gh pr diff)

```diff
diff --git a/migrations/0042_drop_legacy_id.sql b/migrations/0042_drop_legacy_id.sql
new file mode 100644
+ALTER TABLE users DROP COLUMN legacy_external_id;

diff --git a/models/user.py b/models/user.py
@@ -8,5 +8,4 @@ class User(Base):
     __tablename__ = "users"
     id = Column(Integer, primary_key=True)
     email = Column(String(255), nullable=False)
-    legacy_external_id = Column(String(64), nullable=True)
     tier = Column(String(32), nullable=False, default="free")
```

## Adjacent context (the DA subagent would discover this)

A search across the codebase reveals:

```
analytics-etl/dbt/models/users_dim.sql:14:  legacy_external_id AS source_system_id,
exports/customer_export_lambda/handler.py:42:  "legacy_id": user.legacy_external_id,
```

Two downstream consumers reference the column being dropped.

## Review threads (gh api graphql)

```json
{
  "reviewThreads": []
}
```

## CI checks

All green.

---

Run the multi-persona PR review. The DA persona should activate (schema file detected). The orchestrator should escalate to an Explore subagent for DA. Produce the structured output.
