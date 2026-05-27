# Expected Review Output — fixture-2-migration-pr

> **Format note (v1.2+):** Under the inline-first protocol the three Critical findings below should be posted as **three inline review comments** on `migrations/0042_drop_legacy_id.sql:1` (the migration script is one logical anchor; co-locating all three findings keeps the diff context coherent). None qualifies for a `suggestion` fence — each fix requires coordination with downstream consumers or a multi-step deploy sequence. The summary body that ships in the review-body step should reduce each Critical bullet to `[DA1-SCHEMA-BREAK] migrations/0042_drop_legacy_id.sql:1 — see inline comment` and so on. The full finding text below is what should appear in the inline-comment bodies.

```
## PR Review — #5013 `Drop legacy_external_id from users table`

**Verdict: Changes requested**

### Confidence
Reviewed 2 files (1 schema migration, 1 ORM model). DA persona escalated to subagent for adjacent-context discovery. The subagent found 2 downstream consumers of the dropped column. CI green. No existing review threads. The DA1 finding is the blocker — this is a one-way schema change with active downstream readers.

### Personas activated

| Persona | Status | Reason |
|---|---|---|
| SE | ✅ pass | ORM change is atomic with the migration; no PR-shaped concerns |
| SC | ✅ pass | no auth / injection / secrets surface touched |
| IN | ✅ active | `DROP COLUMN` takes ACCESS EXCLUSIVE lock — operational risk |
| DA | ✅ active | schema migration with downstream consumers (escalated to subagent) |
| FE | ⏭ skip | no TSX/JSX in diff |
| TS | ⏭ skip | schema-only change; no test gap signal |

### Findings

| Severity | Count | Inline anchors |
|---|---|---|
| Must-fix | 3 | `DA1 migrations/0042_drop_legacy_id.sql:1` · `DA2 migrations/0042_drop_legacy_id.sql:1` · `IN1 migrations/0042_drop_legacy_id.sql:1` |
| Should-fix | 0 | — |
| Nits | 0 | — |

The three Must-fix findings co-locate on the migration script — see inline comments for the full bodies:

- **[DA1-SCHEMA-BREAK]** Dropping `users.legacy_external_id` will break two downstream consumers (`analytics-etl/dbt/models/users_dim.sql:14`, `exports/customer_export_lambda/handler.py:42`). Coordinate with consumers first; run the migration in a follow-up after they've stopped reading.
- **[DA2-DATA-LOSS-RISK]** `DROP COLUMN` is irreversible. Archive the values first (`INSERT INTO archived_user_legacy_ids SELECT id, legacy_external_id FROM users WHERE legacy_external_id IS NOT NULL`), or document the explicit legal/compliance signoff that none is needed.
- **[IN1-PROD-OUTAGE-RISK]** `DROP COLUMN` on a populated table takes an ACCESS EXCLUSIVE lock in PostgreSQL. Schedule for a low-traffic window OR follow the DA1 deprecation sequence (subsumes this).

### Comment lifecycle

| State | Count |
|---|---|
| Resolved | 0 |
| Won't-fix | 0 |
| Outdated | 0 |
| Possibly addressed | 0 |
| Stale | 0 |
| Open | 0 |

Suppressed 0 findings.

### What's solid

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
5. **The Personas-activated table** names which persona escalated to a subagent (DA) — useful for users debugging skill behavior.
6. **What's solid is substantive** — names the specific things done well (PR description, atomic schema+ORM change).
