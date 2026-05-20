# Synthetic Input for Fixture 2: SQL Injection

You are reviewing the following Express handler. Apply the `ship-secure-code` rubric.

## File: `src/routes/users.ts`

```ts
import { Router } from 'express';
import { db } from '../lib/db';
import { requireAuth } from '../middleware/auth';

const router = Router();

router.get('/users/search', requireAuth, async (req, res) => {
  const q = req.query.q as string;
  const sort = (req.query.sort as string) || 'created_at';

  const rows = await db.query(
    `SELECT id, email, display_name FROM users
     WHERE display_name ILIKE '%${q}%'
     ORDER BY ${sort} DESC
     LIMIT 50`,
  );

  res.json(rows);
});

export default router;
```

---

Apply the ship-secure-code rubric and produce a structured review.
