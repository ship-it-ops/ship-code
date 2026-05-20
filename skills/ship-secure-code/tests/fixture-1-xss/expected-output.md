# Expected Review Output — fixture-1-xss

The skill should produce a report substantially matching the structure below. The SEC4.1 tier-1 finding is non-negotiable; wording can vary.

---

```
## Security Review: app/components/MessageView.tsx, app/api/messages/[id]/route.ts

### Confidence
Reviewed 2 files (~30 lines). Trust boundary: HTTP body in the API route (params.id only — already parameterized, no SEC2/SEC3 finding) and the fetch response in the React component. The bodyHtml field is user-written rich text persisted in the database; rendering it without sanitization is stored XSS. AuthN is present on the API route; AuthZ on a per-message basis is not visible — flagged as advisory since the example data model doesn't show ownership.

### Critical (must fix before merge)

- **[SEC4.1-XSS-DANGEROUSLY-SET] app/components/MessageView.tsx:24**: `dangerouslySetInnerHTML={{__html: message.bodyHtml}}` renders the message body as HTML without sanitization. Stored XSS: any user who writes `<script>` (or any of dozens of other XSS vectors) into a message body owns the browser of anyone who views the message. Data flow: previous POST (not shown) writes `bodyHtml` to DB → API GET returns it → React renders as HTML. → Sanitize with DOMPurify before render: `import DOMPurify from 'isomorphic-dompurify';` then `<div dangerouslySetInnerHTML={{__html: DOMPurify.sanitize(message.bodyHtml)}} />`. → Or, if rich-text isn't actually needed, render as plain text: `<div>{message.bodyHtml}</div>` (React escapes by default).

### Important (should fix)

- **[SEC1.2-IDOR-POTENTIAL] app/api/messages/[id]/route.ts:11**: The query fetches a message by id with no visible ownership/tenant filter. If the messages table is multi-tenant or contains private messages, any authenticated user can read any message by id. Reviewer should verify the data model. → If messages are scoped to a tenant: `'SELECT ... FROM messages WHERE id = $1 AND tenant_id = $2', [params.id, session.tenantId]`. If they're scoped to participants in a conversation, the filter is more complex but the principle is the same.

### Advisory (defense in depth)

- **[SEC2.3-VALIDATE-MESSAGE-ID]** advisory: `params.id` is passed to the DB without format validation. The parameterized query prevents injection, but a malformed id (extremely long string, non-UUID) wastes a DB roundtrip. → `z.string().uuid().parse(params.id)` at the top of the handler.

- **[SEC5.4-MISSING-CSP]** advisory (general): no CSP header is shown. CSP is the depth layer for SEC4.1; even after DOMPurify, a properly-configured CSP (`script-src 'self'`) is the second line of defense if a future bug reintroduces unsanitized rendering. → Configure CSP in `middleware.ts` for all HTML responses.

### What's Good

- **AuthN is present** on the API route (`getServerSession()` at the top). The bug pattern (auth-present, authz-missing) is the most common modern shape — bonus points for the team being one step into doing it right.
- **Query is parameterized** — `WHERE id = $1` with `[params.id]`, not template literal. SEC3.1 doesn't fire here even though the code interacts with both untrusted input and SQL. This is the correct pg-driver pattern.
- **`bodyHtml` field naming** is honest — it's clearly user-supplied HTML, which makes the sanitization gap easy to identify in review. Compare to `body` or `content`, which might be either text or HTML and would be harder to reason about.
```

## What this fixture demonstrates

1. **The XSS finding is the tier-1 catch** even though both files look "clean" at first glance (well-typed, parameterized SQL, AuthN present). The vulnerability is the absence of sanitization, not the presence of an obvious flaw.
2. **The data flow trace spans files** — the API route writes `bodyHtml` to the DB; the component reads it back and renders it. Reviewers who only look at one file at a time miss this class of bug.
3. **The advisory IDOR finding requires a reviewer judgment call** — the example doesn't tell us whether messages are private. The skill flags the *potential* without fabricating facts.
4. **CSP is mentioned but advisory** — defense in depth, not a blocker. If the team already has CSP in `middleware.ts`, this advisory is satisfied.
