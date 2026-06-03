# Synthetic Input for Fixture 4: Non-reversible migration paired with code drop

You are reviewing the following two files. Apply the `ship-devops` rubric.

## File: `migrations/2026_06_02_drop_user_legacy_email.sql`

```sql
-- Migration: drop the legacy_email column from users.
-- Reasoning: we migrated to the new email field two releases ago.

ALTER TABLE users DROP COLUMN legacy_email;
```

## File: `services/api/src/users.ts`

```ts
import { db } from './db';

export interface User {
  id: string;
  email: string;          // canonical
  // legacy_email removed in this PR
  createdAt: Date;
}

export async function getUser(id: string): Promise<User | null> {
  const rows = await db.query<User>(
    `SELECT id, email, created_at AS "createdAt" FROM users WHERE id = $1`,
    [id],
  );
  return rows[0] ?? null;
}

export async function listUsers(): Promise<User[]> {
  const rows = await db.query<User>(
    `SELECT id, email, created_at AS "createdAt" FROM users ORDER BY created_at DESC LIMIT 100`,
  );
  return rows;
}
```

(Same PR also removes the previous `legacy_email` references from the codebase.)

---

Apply the ship-devops rubric and produce a structured review.
