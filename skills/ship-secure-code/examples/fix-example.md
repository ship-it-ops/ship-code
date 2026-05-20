# Fix Example: SEC3.1 SQL Injection

Walkthrough of a single finding from identification through fix and regression test. Uses the SQL injection from `examples/review-example.md` as the worked example. The skill produces this kind of trace when asked "how do I fix [finding]?" interactively, but never auto-applies the patch.

---

## The finding

```
[SEC3.1-INJECTION-SQL] app/api/orders/[id]/route.ts:10:
SQL string interpolation: `... WHERE id = '${params.id}'`.
A malicious id value (e.g., ' OR '1'='1) executes arbitrary SQL.
Data flow: req.params.id (HTTP, untrusted) → template literal → db.query parser.
→ Use parameterized query.
```

## 1. Identify

The vulnerable line:

```ts
const order = await db.query(
  `SELECT * FROM orders WHERE id = '${params.id}'`,
);
```

The pattern: `params.id` is untrusted (it's whatever the client puts in the URL path), and it's being concatenated into a SQL string. The pg driver doesn't parse it as data — it parses the entire string as SQL. An attacker provides:

```
GET /api/orders/x'%20OR%20'1'='1
```

The query becomes:

```sql
SELECT * FROM orders WHERE id = 'x' OR '1'='1'
```

Which returns every row in the `orders` table.

Worse: with UNION SELECT, an attacker exfiltrates arbitrary data. With stacked queries (if the driver allows them), an attacker writes to other tables.

## 2. Confirm the data flow

The skill's data-flow trace was:

```
req.params.id (HTTP, untrusted)
  → params.id (handler signature destructure)
  → template literal in db.query (SQL parser sink)
```

Three steps. Each adds no transformation — no validation, no sanitization, no escaping. The untrusted value lands in the parser intact.

To confirm there's no protection upstream:
- `grep -B 10 "db.query" route.ts` — any validation/sanitization before line 10? No.
- Check the middleware layer (`middleware.ts`) — any param validation? No.
- Check the framework — does Next.js sanitize URL params by default? No.

The data flow is real and the sink is exploitable.

## 3. Apply the fix

The canonical fix is parameterization. The `pg` driver accepts `$N` placeholders:

```ts
const order = await db.query(
  'SELECT * FROM orders WHERE id = $1 AND user_id = $2',
  [params.id, session.user.id],
);
```

Note we added two changes:

1. **Parameterization** (`$1` instead of `'${params.id}'`). The driver passes `params.id` as a *value* to the database; the parser never sees it as part of the SQL string. The SEC3.1 finding is resolved.

2. **AuthZ filter** (`AND user_id = $2`). This is the SEC1.2-IDOR fix — even with parameterization, a logged-in user can still read any order if there's no ownership check. Both fixes belong in the same patch.

The combined fix:

```ts
export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const session = await getServerSession();
  if (!session) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  const order = await db.query(
    'SELECT * FROM orders WHERE id = $1 AND user_id = $2',
    [params.id, session.user.id],
  );

  if (order.rowCount === 0) {
    return NextResponse.json({ error: 'not found' }, { status: 404 });
  }

  return NextResponse.json(order.rows[0]);
}
```

A few details worth noting:

- We return 404 (not 403) when the order isn't found OR isn't owned. Distinguishing 403 from 404 would leak existence: an attacker learns that order id `12345` exists even if they can't read it. Always return 404 for ownership failures on resource-lookup routes.
- We index into `order.rows[0]` instead of returning the whole result object. The raw `Result` object includes metadata (row count, command tag, oid) that's leaky in this context.

## 4. Regression test

A fix without a regression test will recur. Add a test that explicitly verifies the attacker payload no longer works:

```ts
import { describe, it, expect, beforeEach } from 'vitest';
import { GET } from './route';

describe('GET /api/orders/[id]', () => {
  beforeEach(async () => {
    // ... seed two users (alice, bob) and one order owned by alice
  });

  it("returns alice's order to alice", async () => {
    const req = mockRequest({ session: { user: { id: 'alice' } } });
    const res = await GET(req, { params: { id: 'order-1' } });
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.id).toBe('order-1');
  });

  it("returns 404 when bob requests alice's order", async () => {
    const req = mockRequest({ session: { user: { id: 'bob' } } });
    const res = await GET(req, { params: { id: 'order-1' } });
    expect(res.status).toBe(404);    // not 403 — never reveal existence
  });

  it("rejects SQL injection in the id parameter", async () => {
    const req = mockRequest({ session: { user: { id: 'alice' } } });
    const res = await GET(req, { params: { id: "x' OR '1'='1" } });
    expect(res.status).toBe(404);    // the literal id "x' OR '1'='1" doesn't exist
    // If parameterization is broken, the query returns all rows and we'd get 200.
  });

  it('returns 401 without a session', async () => {
    const req = mockRequest({ session: null });
    const res = await GET(req, { params: { id: 'order-1' } });
    expect(res.status).toBe(401);
  });
});
```

The third test (`rejects SQL injection in the id parameter`) is the key one. It's the regression: if a future refactor reintroduces string interpolation, the literal `x' OR '1'='1` returns 200 instead of 404 and the test fails.

## 5. Verify

After applying the fix and adding tests, verify:

1. **Run the test suite** — all four cases pass.
2. **Manually try the exploit** against a local instance:
   ```
   curl 'http://localhost:3000/api/orders/x%27%20OR%20%271%27%3D%271' -H "Cookie: session=..."
   ```
   Should return 404, not 200-with-data.
3. **Re-run the skill** on the patched file:
   ```
   /ship-secure-code app/api/orders/[id]/route.ts
   ```
   The SEC3.1 finding on line 10 should be gone. SEC1.2 on the same line should also be gone (single fix resolved both).

If the skill still flags SEC3.1, the fix is incomplete — re-check the data flow trace and look for another interpolation site.

---

## Why "no auto-remediation"

The skill could have produced the patch above mechanically. We don't, for three reasons:

1. **The fix often spans more than one finding** — here, SEC3.1 and SEC1.2 share the patch. An auto-remediation that fixes only SEC3.1 would leave the IDOR open and *look* fixed in the next review pass.
2. **The fix sometimes changes behavior in subtle ways** — returning 404 vs 403 vs 401 is a policy choice, and the right answer depends on the team's privacy stance.
3. **The test is part of the fix** — a patch without a regression test is half a fix. We surface the regression test in the walkthrough, but writing it requires the team's test scaffolding (`mockRequest`, fixture seeding, vitest vs jest) which the skill can't infer reliably.

So: the skill identifies, traces, and recommends. The human applies and tests.
