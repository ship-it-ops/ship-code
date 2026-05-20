# Secure Code Review Example

End-to-end demonstration of `ship-secure-code` running on a small Next.js + Express service. The vulnerable codebase is synthetic but representative — each finding maps to a real-world bug class. The review output shows the structure the skill produces when invoked standalone.

---

## The codebase under review

Three files, ~80 lines total. Imagine this is a slice of a larger Next.js app.

### `app/api/orders/[id]/route.ts`

```ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { getServerSession } from 'next-auth';

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const session = await getServerSession();
  if (!session) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  const order = await db.query(
    `SELECT * FROM orders WHERE id = '${params.id}'`,
  );
  return NextResponse.json(order);
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const created = await db.query(
    `INSERT INTO orders (user_id, amount, notes) VALUES ('${body.userId}', ${body.amount}, '${body.notes}')`,
  );
  return NextResponse.json(created);
}
```

### `app/components/OrderConfirmation.tsx`

```tsx
'use client';

import DOMPurify from 'isomorphic-dompurify';

export function OrderConfirmation({ order }: { order: { id: string; notes: string } }) {
  return (
    <div className="order">
      <h2>Order {order.id} confirmed</h2>
      <div dangerouslySetInnerHTML={{ __html: order.notes }} />
      <a href={`/orders/${order.id}/receipt?token=${order.id}`}>Download receipt</a>
    </div>
  );
}
```

### `lib/db.ts`

```ts
import { Pool } from 'pg';

const STRIPE_KEY = 'sk_live_51KQpZeEXAMPLEFAKEKEY';

export const db = new Pool({
  connectionString: 'postgresql://app:db_pass_change_me@db.internal/orders',
});

export async function chargeOrder(amount: number, token: string) {
  const res = await fetch(`https://api.stripe.com/v1/charges?token=${STRIPE_KEY}`, {
    method: 'POST',
    body: JSON.stringify({ amount, source: token }),
  });
  return res.json();
}
```

---

## Review Output (what the skill produces)

```
## Security Review: app/api/orders/, app/components/OrderConfirmation.tsx, lib/db.ts

### Confidence
Reviewed 3 files (~80 lines). Trust boundary identified: Next.js App Router route handlers (HTTP body, URL params) and the `chargeOrder` outbound fetch (server-side URL construction). Skipped 0 generated/vendored files. The AuthN layer is present on GET but AuthZ is missing (IDOR); the POST handler has neither auth nor validation; output rendering uses `dangerouslySetInnerHTML` with unsanitized data; the database connection string and Stripe key are hardcoded. Five tier-1 findings drive the REQUEST_CHANGES decision.

### Critical (must fix before merge)

- **[SEC1.2-IDOR] app/api/orders/[id]/route.ts:10**: `db.query(... WHERE id = '${params.id}')` fetches an order by id with no ownership/tenant check. Any authenticated user can read any order. → Add a join/filter on the requesting user: `WHERE id = $1 AND user_id = $2` with `[params.id, session.user.id]`. → Verify: an authenticated user requesting an order belonging to a different user should receive 403 or 404 (do not 401 — that leaks existence).

- **[SEC1.1-AUTH-MISSING] app/api/orders/[id]/route.ts:15**: POST handler exports `POST` without `getServerSession()` — anyone can create an order on any user's behalf, including non-authenticated requests. → Add `const session = await getServerSession(); if (!session) return NextResponse.json({error: 'unauthorized'}, {status: 401});` at the top of the handler.

- **[SEC3.1-INJECTION-SQL] app/api/orders/[id]/route.ts:10**: SQL string interpolation: `\`... WHERE id = '${params.id}'\``. A malicious `id` value (e.g., `' OR '1'='1`) executes arbitrary SQL. Data flow: `req.params.id` (HTTP, untrusted) → template literal → `db.query` parser. → Use parameterized query: `db.query('SELECT * FROM orders WHERE id = $1 AND user_id = $2', [params.id, session.user.id])`.

- **[SEC3.1-INJECTION-SQL] app/api/orders/[id]/route.ts:18**: SQL string interpolation in INSERT: `\`INSERT INTO orders (user_id, amount, notes) VALUES ('${body.userId}', ${body.amount}, '${body.notes}')\``. Three injection vectors (userId, amount, notes). Data flow: `req.body.*` (HTTP, untrusted) → template literal → `db.query` parser. → Use parameterized: `db.query('INSERT INTO orders (user_id, amount, notes) VALUES ($1, $2, $3)', [body.userId, body.amount, body.notes])`. Note: also add schema validation per SEC2.1.

- **[SEC4.1-XSS-DANGEROUSLY-SET] app/components/OrderConfirmation.tsx:9**: `dangerouslySetInnerHTML={{__html: order.notes}}` renders order notes (user-controlled, stored via the POST handler above) as HTML without sanitization. Stored XSS — an attacker creates an order with HTML/JS in `notes`, anyone viewing that order's confirmation runs the attacker's JS. Data flow: `req.body.notes` → DB → `order.notes` → `dangerouslySetInnerHTML` (HTML parser sink). → Sanitize before render: `dangerouslySetInnerHTML={{__html: DOMPurify.sanitize(order.notes)}}` (DOMPurify is already imported in the file). Or, if rich content isn't actually needed, render as text: `<div>{order.notes}</div>`.

- **[SEC7.1-SECRET-HARDCODED] lib/db.ts:3**: Hardcoded Stripe live key (`sk_live_...`) in source. The key has been committed to git history and is now leaked permanently regardless of fix; rotate immediately. → Move to env var: `const STRIPE_KEY = process.env.STRIPE_KEY` with non-null assertion at app boot. → Add `STRIPE_KEY` to your secrets manager (AWS Secrets Manager / HashiCorp Vault / etc.). → Rotate the leaked key via the Stripe dashboard.

### Important (should fix)

- **[SEC2.1-NO-SCHEMA-VALIDATION] app/api/orders/[id]/route.ts:17**: POST handler reads `body.userId`, `body.amount`, `body.notes` without schema validation. Even after parameterization (above), `amount` could be a string, an array, or an object — runtime behavior depends on PostgreSQL coercion. → Add `import { z } from 'zod'; const OrderSchema = z.object({ userId: z.string().uuid(), amount: z.number().int().positive(), notes: z.string().max(500) }).strict(); const body = OrderSchema.parse(await req.json());`. The `.strict()` rejects extra fields.

- **[SEC7.3-TOKEN-IN-URL] lib/db.ts:9**: Stripe key passed as URL query parameter (`?token=${STRIPE_KEY}`). Tokens in URLs leak via referrer headers, server access logs (Stripe's, yours, and any proxy in between), and browser history. → Pass via `Authorization: Bearer ${STRIPE_KEY}` header instead. → Stripe's API expects `Authorization: Bearer <key>`, not a query parameter — the current code is wrong on two axes (insecure + non-functional).

- **[SEC7.1-SECRET-HARDCODED] lib/db.ts:6**: Hardcoded database password (`db_pass_change_me`) in connection string. Lower severity because the password value suggests a non-production placeholder, but in code review it should be replaced regardless. → Use env: `connectionString: process.env.DATABASE_URL`.

### Advisory (defense in depth)

- **[SEC4.3-UNSAFE-URL] app/components/OrderConfirmation.tsx:11**: `<a href={`/orders/${order.id}/receipt?token=${order.id}`}>` constructs a URL with the order id in the token slot — looks like a placeholder. If `order.id` is ever attacker-controlled (it isn't directly here since the DB controls ids, but defense-in-depth), this could become a vector. → Use a separate, signed download token rather than reusing the order id.

- **[SEC9.4-ERROR-LEAK]** (general): no error handler shown — Next.js App Router's default error handling can leak stack traces in development mode. → Configure a route-level error boundary that returns sanitized error responses in production.

### What's Good

- **AuthN is present on GET** (`getServerSession()` at the top of the handler). The bug is the missing AuthZ, not missing auth entirely — this is the most common modern pattern and means the team understands auth basics.
- **DOMPurify is already imported** in `OrderConfirmation.tsx`. The fix for the XSS finding is a one-line change to actually call it — the team already pulled in the right library.
- **Database access is wrapped in a `Pool`** (not a fresh connection per request) — good operational hygiene independent of security.
```

---

## What this example demonstrates

1. **Data flow is explicit in every Critical finding** — each lists the source (where untrusted data enters), the sink (where it lands without protection), and the path between them. A reviewer can verify the finding without reading the full file.
2. **Tier-1 is reserved for textbook OWASP** — five tier-1 findings here: missing AuthZ, missing AuthN, SQL injection (×2), stored XSS, hardcoded secret. Each of these would appear in any introductory app-sec curriculum.
3. **Tier-2 covers the secondary defense** — schema validation, token-in-URL, placeholder DB password. These all matter but they're not the kind of finding that makes a security engineer's hair stand up.
4. **Advisory tier is hardening** — token reuse for download URLs, error handler. These are improvements to make later, not blockers.
5. **"What's Good" names specific defenses** that exist. The team gets credit for AuthN being present, for already importing DOMPurify, for using a connection pool. This isn't padding — it's evidence the reviewer engaged with the code rather than running a checklist.
6. **Fix suggestions are specific and actionable** — code snippets, env-var names, library calls. A reader can copy-paste and verify.
