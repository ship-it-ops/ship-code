# Expected Review Output — fixture-4-non-reversible-migration

The skill should produce a report substantially matching the structure below. The **DEV8.1 tier-1 finding is non-negotiable**; wording can vary.

---

```
## DevOps Review: migrations/2026_06_02_drop_user_legacy_email.sql, services/api/src/users.ts

### Confidence
Reviewed 2 files (~25 lines). Deploy path: `migration applied as part of release → app code stops reading legacy_email → release ships`. The migration drops a column in the same release that removes the only reader. On rollback, the previous app version comes back and queries a column that no longer exists. One tier-1 finding drives the REQUEST_CHANGES decision.

### Critical (must fix before merge)

- **[DEV8.1-NON-REVERSIBLE-MIGRATION] migrations/2026_06_02_drop_user_legacy_email.sql + services/api/src/users.ts**: This PR drops `users.legacy_email` *and* ships the app version that depends on the drop. Deploy path: `apply migration → release new app → (later) rollback releases the OLD app, which queries SELECT ... legacy_email FROM users — column no longer exists, query fails, prod down`. → Two-phase migration: 1) Release N stops writing `legacy_email` (already true per PR's claim), and stops reading it (this PR's code change) — but the schema still has the column. 2) Release N+1 (a separate PR, shipped one release cycle later) drops the column. Each step is reversible alone. If you need to drop it now, verify (a) no other service reads it, (b) the rollback procedure includes restoring the column from backup, and (c) document the rollback procedure in `docs/runbooks/`.

### Important (should fix)

- **[DEV8.4-FORWARD-ONLY-MIGRATION] migrations/2026_06_02_drop_user_legacy_email.sql**: no `down` migration / reverse SQL block. Down-migrations should at minimum re-add the column nullable (data is lost, but schema reversible). → Add a down step or use a tool (Alembic, Flyway with undo) that requires it. CI should run `up → down → up` against a representative dataset.

- **[DEV2.1-NO-ROLLBACK] (compound)**: the combination of an irreversible migration and a code change that depends on it means the release as a whole has no rollback. Even if the migration framework supported it (it doesn't here), data is destructively removed. → As above: two-phase. Make rollback safe before shipping.

### Advisory (hygiene)

- **[DEV8.X-LOCK-DURATION] migrations/2026_06_02_drop_user_legacy_email.sql** (advisory): `ALTER TABLE ... DROP COLUMN` on PostgreSQL acquires `ACCESS EXCLUSIVE`, briefly blocking concurrent reads/writes. For a hot `users` table this is usually fine (DROP COLUMN is metadata-only in modern Postgres), but verify on staging with realistic concurrency. → If concerns, schedule during a low-traffic window and time the operation; document expected duration in the PR description.

### What's Good

- **Parameterized SELECT** — `WHERE id = $1` with `[id]`, not template literal. No SQL injection surface introduced.
- **Single-concern migration** — one `ALTER TABLE` per file, named clearly with date prefix. Easy to bisect if needed.
- **TypeScript type updated** — the `User` interface dropped `legacy_email`; runtime and type are consistent (good for compile-time confidence, irrelevant to the rollback risk).
- **Reasoning in migration comment** — the `-- Reasoning:` comment helps the next reviewer understand intent. (It does not, by itself, make the operation safe.)
```
