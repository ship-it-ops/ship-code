# Expected Review Output — fixture-2-migration-pr

> **Format note (v1.2+):** Under the inline-first protocol the three Critical findings below should be posted as **three inline review comments** on `migrations/0042_drop_legacy_id.sql:1` (the migration script is one logical anchor; co-locating all three findings keeps the diff context coherent). None qualifies for a `suggestion` fence — each fix requires coordination with downstream consumers or a multi-step deploy sequence. The summary body that ships in the review-body step should reduce each Critical bullet to `[DA1-SCHEMA-BREAK] migrations/0042_drop_legacy_id.sql:1 — see inline comment` and so on. The full finding text below is what should appear in the inline-comment bodies.

```
## PR Review: #5013 — Drop legacy_external_id from users table

### Decision: 🛑 REQUEST_CHANGES

### Confidence
Reviewed 2 files (1 schema migration, 1 ORM model). DA persona activated (schema migration detected) and escalated to subagent for adjacent-context discovery. The subagent found 2 downstream consumers of the dropped column. CI green. No existing review threads. The DA1 finding is the blocker — this is a one-way schema change with active downstream readers.

### 🛑 Critical (must fix before merge)

- **[DA1-SCHEMA-BREAK] migrations/0042_drop_legacy_id.sql:1**: Dropping `users.legacy_external_id` will break two downstream consumers:
  - `analytics-etl/dbt/models/users_dim.sql:14` (references the column as `source_system_id`)
  - `exports/customer_export_lambda/handler.py:42` (uses `user.legacy_external_id`)
  Both will fail silently or with a hard error depending on how they fetch. → Coordinate with the data team and the export Lambda owner. Recommended sequence: (1) update both consumers to stop reading the column, (2) deploy and verify, (3) THEN run this migration in a follow-up. Alternatively, deprecate the column for one release: mark it `nullable=True` and stop writing to it, give consumers a release to migrate off, then drop.

- **[DA2-DATA-LOSS-RISK] migrations/0042_drop_legacy_id.sql:1**: `DROP COLUMN` is irreversible without a backup. The values in `legacy_external_id` are gone the moment this runs. Even after consumers migrate off, archive the values before dropping. → Add a step before the migration: `INSERT INTO archived_user_legacy_ids SELECT id, legacy_external_id FROM users WHERE legacy_external_id IS NOT NULL`. Or document explicitly that no archival is needed and why (legal/compliance signoff).

- **[IN1-PROD-OUTAGE-RISK] migrations/0042_drop_legacy_id.sql:1**: `DROP COLUMN` on a populated table takes an ACCESS EXCLUSIVE lock in PostgreSQL. On a large `users` table this can block all reads/writes for a meaningful window during the deploy. → Schedule for a low-traffic window OR use `ALTER TABLE ... DROP COLUMN IF EXISTS ...` after first marking nullable and waiting one release (per the DA1 recommendation, which subsumes this).

### Important (should fix)

- (none)

### Suggestions (improve when convenient)

- (none)

### Delegations

- (none — no test gap signal because this is a schema-only change)

### Comment lifecycle
- 0 resolved | 0 outdated | 0 won't-fix | 0 possibly addressed | 0 stale | 0 open
- Suppressed: 0 findings.

### What's Good

- The PR description gives context ("haven't used it for new signups since 2023") which is honest and useful for understanding the scope.
- The ORM change is in the same PR as the migration, which is the correct order — many teams ship these in different PRs and end up with a window where the ORM thinks the column exists but the database doesn't (or vice versa).

### Submission preview (local mode)
  gh api -X POST repos/acme/billing/pulls/5013/reviews (create pending review)
  gh api -X POST .../reviews/{id}/comments × 3 (three inline findings)
  gh api -X POST .../reviews/{id}/events -f event=REQUEST_CHANGES -f body=<summary>

Proceed? Type "yes" to submit, "edit" to revise, or "no" to abort.
```

## What this fixture demonstrates

1. **DA persona activates** because `migrations/*.sql` matches the conditional trigger pattern.
2. **The orchestrator escalates to a subagent** for DA — the subagent reads adjacent context (downstream consumers) that the orchestrator wouldn't have fetched on its own.
3. **DA1 and DA2 fire on the same migration** — they have distinct fingerprints (DA1 = downstream-break, DA2 = irreversibility) and don't dedup.
4. **IN1 also fires** because `DROP COLUMN` takes a table lock — that's an *operational* concern that's distinct from DA's schema-correctness concern. Both report independently.
5. **The Confidence section names** which persona escalated to a subagent — useful for users debugging skill behavior.
6. **What's Good is substantive** — names the specific things done well (PR description, atomic schema+ORM change).
