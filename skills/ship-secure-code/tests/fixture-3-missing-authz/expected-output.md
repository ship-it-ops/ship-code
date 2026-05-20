# Expected Review Output — fixture-3-missing-authz

The skill should produce a report substantially matching the structure below. The two SEC1.2 tier-1 findings are non-negotiable; wording can vary.

---

```
## Security Review: app/api/documents/[id]/route.ts

### Confidence
Reviewed 1 route file + schema reference (~30 lines). Trust boundary: Next.js App Router GET and DELETE handlers reading `params.id`. AuthN is present on both handlers; AuthZ is missing on both — classic IDOR. The Prisma schema confirms the resource is tenant-scoped (`tenantId` column) and has an author (`authorId`). Any authenticated user can read or delete any document by id, regardless of tenant or ownership. Two tier-1 findings drive REQUEST_CHANGES.

### Critical (must fix before merge)

- **[SEC1.2-IDOR] app/api/documents/[id]/route.ts:11**: GET fetches `prisma.document.findUnique({ where: { id: params.id } })` with no tenant or owner filter. The schema shows `tenantId` and `authorId` columns; this query returns any document by id regardless of whether the requesting user is in the right tenant or is the author. Cross-tenant data leak. Data flow: `req.params.id` (HTTP, untrusted) → Prisma `where` clause → DB returns row from any tenant. → Add tenant scope: `where: { id: params.id, tenantId: session.user.tenantId }`. → If documents have a sharing model beyond simple ownership, add an explicit permission check before returning the document (e.g., the document is shared with a group the user is in).

- **[SEC1.2-IDOR-DESTRUCTIVE] app/api/documents/[id]/route.ts:27**: DELETE removes a document by id with no ownership/tenant check. Any authenticated user can delete any document. Worse than the GET case because the action is destructive and irreversible. Data flow: `req.params.id` → `prisma.document.delete({ where: { id } })` → row deleted from any tenant. → Two-step fix: first verify ownership, then delete. → `const doc = await prisma.document.findUnique({ where: { id: params.id, tenantId: session.user.tenantId, authorId: session.user.id } }); if (!doc) return NextResponse.json({ error: 'not found' }, { status: 404 }); await prisma.document.delete({ where: { id: doc.id } });`. → Return 404 (not 403) on the ownership miss to avoid leaking existence.

### Important (should fix)

- **[SEC9.1-PII-RESPONSE] app/api/documents/[id]/route.ts:18**: GET returns the full document via `NextResponse.json(document)`, which includes the entire `bodyMd` (potentially long, potentially containing sensitive content) and the author relation. The author select limits the exposed user fields, which is good; flag remains because the body contents are not filtered. → If the route is supposed to return a summary view, narrow the select; if it's the full-document view, the current shape may be intentional but document it.

- **[SEC10.4-RATE-LIMIT-DELETE]** advisory: destructive endpoints should be rate-limited per user to mitigate accidental or malicious mass-deletion. → Add `express-rate-limit` equivalent (Next.js middleware) at low requests/min on DELETE.

### Advisory (defense in depth)

- **[SEC2.1-VALIDATE-PARAM-ID]** advisory: `params.id` isn't validated to be a cuid before being passed to Prisma. Prisma will reject non-cuid values at the type layer but a malformed long string still costs a DB roundtrip. → `z.string().cuid().parse(params.id)` at the top of each handler.

### What's Good

- **AuthN present on both handlers** — the team understands authentication. The IDOR is a missing-AuthZ pattern, not missing-auth-entirely.
- **`findUnique` returns null on miss, handled correctly** — the `if (!document)` branch returns 404 rather than crashing. The fix builds on this — same 404 response for "not yours" preserves the existence-non-disclosure behavior.
- **Author select is narrowed** to `{ id: true, displayName: true }` — the team thought about not over-exposing user data in the join. Same pattern should apply to the top-level document body.
- **CUID for primary key** rather than incrementing integer — makes enumeration attacks meaningfully harder (an attacker can't iterate `id=1, 2, 3...` to discover documents). Doesn't replace AuthZ, but raises the cost of exploitation.
```

## What this fixture demonstrates

1. **IDOR is missed when AuthN is present** — the most common modern security bug pattern. A reviewer who sees `getServerSession()` at the top might check the box and miss the AuthZ gap.
2. **Destructive vs read-only IDOR have different framings** — both tier-1, but the destructive case (DELETE) is worse and the fix is two-step (verify, then delete) rather than one-step (add WHERE clause).
3. **Schema-as-evidence** — the Prisma schema confirms the resource has `tenantId` and `authorId`, so the IDOR isn't speculative. Reviewers who can read the schema produce sharper findings.
4. **Return 404 for ownership miss** — never 403. This is a policy detail the skill names explicitly.
5. **"What's Good" calls out CUID** — a real defense-in-depth choice (raises enumeration cost) that's separate from the AuthZ fix. Recognizing it makes the criticism trustworthy.
