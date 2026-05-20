# Expected Review Output — fixture-2-sqli

The skill should produce a report substantially matching the structure below. The two SEC3.1 tier-1 findings are non-negotiable; wording can vary.

---

```
## Security Review: src/routes/users.ts

### Confidence
Reviewed 1 file (~20 lines). Trust boundary: Express handler reading `req.query.q` and `req.query.sort` from the HTTP layer. AuthN is present via the `requireAuth` middleware. Two tier-1 SQL injection findings on the same SQL statement: the search term `q` and the column name `sort`. Both require different fix patterns (parameterization for values, allowlist for column names).

### Critical (must fix before merge)

- **[SEC3.1-INJECTION-SQL] src/routes/users.ts:11**: `WHERE display_name ILIKE '%${q}%'` interpolates user-controlled `q` into the SQL string. Classic SQL injection — `q = "'; DROP TABLE users; --"` is the textbook payload (and unparameterized LIKE wildcards have additional surface). Data flow: `req.query.q` (HTTP, untrusted) → template literal → `db.query` (SQL parser). → Use parameterized query: `WHERE display_name ILIKE $1` with `['%' + q + '%']`. → Note: the `%` wildcards stay outside the parameter; otherwise the user can inject `%` and `_` to over-match, which is a search-quality issue but not a security one.

- **[SEC3.1-INJECTION-SQL-ORDERBY] src/routes/users.ts:12**: `ORDER BY ${sort}` interpolates user-controlled `sort` into the SQL string. The column name *cannot* be parameterized in standard SQL — the driver only parameterizes values. This is a particularly nasty case: an attacker provides `sort = "(SELECT password FROM secrets LIMIT 1)"` and exfiltrates data via the ORDER BY clause (different DBs allow different shapes; PostgreSQL allows subqueries in ORDER BY). Data flow: `req.query.sort` (HTTP, untrusted) → template literal → SQL parser. → Allowlist the column name: `const ALLOWED_SORT = new Set(['created_at', 'display_name', 'id']); if (!ALLOWED_SORT.has(sort)) sort = 'created_at';` then interpolate the validated value. The allowlist must be exhaustive — any unmatched value falls back to the default.

### Important (should fix)

- **[SEC2.1-NO-SCHEMA-VALIDATION] src/routes/users.ts:8**: `req.query.q` and `req.query.sort` are read with `as string` cast — Express types them as `string | string[] | ParsedQs | ParsedQs[]`, the cast is wrong if the client sends `?q[]=foo`. → Use schema validation: `const QuerySchema = z.object({ q: z.string().min(1).max(100), sort: z.enum(['created_at', 'display_name', 'id']).default('created_at') }); const { q, sort } = QuerySchema.parse(req.query);`. The Zod enum on `sort` also closes the SEC3.1-ORDERBY finding above as a side effect.

- **[SEC10.4-RATE-LIMIT-SEARCH]** advisory: search endpoints are a common DoS vector (expensive query + low cost to caller). → Add `express-rate-limit` to this route at e.g. 60 req/min per user.

### What's Good

- **`requireAuth` middleware is in the middle slot** — the route is correctly gated. The bug is the SQL construction, not the auth boundary.
- **Limit is hardcoded** (`LIMIT 50`) — prevents the search from returning massive result sets. Small but real defense against pagination-abuse DoS.
- **Result-set fields are explicit** — selecting `id, email, display_name` rather than `*`. The team thought about what to expose; a future schema change won't accidentally leak a new sensitive column.
```

## What this fixture demonstrates

1. **Two SQL injection findings on a single statement** — one for the value (`q`) and one for the column name (`sort`). They look similar but have different fixes; the data-flow trace must distinguish them.
2. **ORDER BY can't be parameterized** — the fix is allowlist, not parameterization. Reviewers who default to "use $1" without thinking miss this.
3. **Schema validation closes ORDER BY as a side effect** — the Zod enum for `sort` is itself the allowlist. Single fix for SEC2.1 + SEC3.1-ORDERBY.
4. **"What's Good" calls out the hardcoded `LIMIT` and the explicit field selection** — both are real, substantive defenses, not boilerplate.
