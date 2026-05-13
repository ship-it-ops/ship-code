# TypeScript / JavaScript PR-Review Idioms

PR-review-specific patterns for TS/JS. For file-level idioms (type safety, async, React), defer to `ship-clean-code/lang-typescript.md`. This file covers what each persona looks for in a *PR* context.

---

## SC — Senior Security Engineer (TS/JS patterns)

### Auth/Authz (SC1)

- **Express**: new `app.get('/...', handler)` or `router.post('/...', handler)` without an auth middleware. Look for the project's middleware: `authenticate`, `requireAuth`, `passport.authenticate`, `isAuthenticated`. Verify with `grep -B 2 "router\.\|app\." <file>`.
- **Next.js (App Router)**: new `route.ts` exporting `GET`/`POST`/etc. without auth check. Look for `await auth()` (NextAuth v5), `getServerSession`, or middleware in `middleware.ts`.
- **Next.js (Pages Router)**: new `pages/api/...` without `getSession()` or equivalent.
- **NestJS**: new `@Get`/`@Post` controller method without `@UseGuards(AuthGuard)`.
- **tRPC**: new `publicProcedure` where it should be `protectedProcedure`. Check the router file for the pattern.
- **GraphQL**: new resolver without an auth directive (`@auth`) or `context.user` check.

### Injection (SC2)

- **SQL via template literals**: `` db.query(`SELECT * FROM users WHERE id = ${id}`) `` — injection. Use parameterized: `` db.query('SELECT * FROM users WHERE id = $1', [id]) ``.
- **Prisma raw**: `prisma.$queryRawUnsafe(query)` — injection. Use `prisma.$queryRaw\`...\`` tagged template.
- **MongoDB**: object query with user input that includes `$gt`, `$ne` operators — NoSQL injection if not sanitized.
- **`eval()`, `Function()`, `setTimeout(string, ...)`**: dynamic code execution with user input.
- **XSS in React**: `dangerouslySetInnerHTML={{ __html: userInput }}` — sanitize with DOMPurify or use `react-html-parser` with allowlist.
- **XSS in templates**: Handlebars `{{{var}}}` (triple-braces), EJS `<%- var %>` — unescaped output.
- **SSRF**: `fetch(userControlledUrl)` server-side. Validate against an allowlist; block private IP ranges.

### Secrets (SC3)

- API keys, tokens hardcoded: `const API_KEY = "sk_live_..."`. Use `process.env.API_KEY`.
- `.env` committed: `.env`, `.env.local`, `.env.production` should be in `.gitignore`.
- `package.json` with a Git URL containing a token.
- Secret in CI YAML body (not in `secrets:` reference): `GITHUB_ACTIONS_TOKEN: gha_...`.

### Crypto misuse (SC4)

- `crypto.createHash('md5')` or `'sha1'` for security purposes. For passwords: `bcrypt`, `argon2`, `scrypt`.
- `crypto.createCipher` (deprecated, fixed IV) — use `createCipheriv` with random IV.
- JWT verify with `algorithms: ['none']` or no `algorithms` array.
- `Math.random()` used for security-sensitive randomness (tokens, IDs). Use `crypto.randomBytes()` or `crypto.randomUUID()`.

### Supply chain (SC5)

- New entry in `package.json` dependencies — check:
  - First-published date on `npm view <pkg> time.created`. < 3 months is suspicious.
  - Weekly downloads on `npm view <pkg>` or `npmjs.com`. Very low + recently uploaded = typosquat signal.
  - `npm audit` output, GitHub Advisory Database.
- `package.json` with `"postinstall"`, `"preinstall"`, `"install"` script that wasn't there before (especially when added by adding a new dep — check if a transitive dep added it via the new install graph).
- `package-lock.json` / `pnpm-lock.yaml` / `yarn.lock` change that pulls a package from a non-registry source.

### PII / log leakage (SC6, SC7)

- `console.log(req.body)`, `console.log(user)` — pulls in everything including PII and secrets.
- `logger.error(err)` where `err` is a fetch response that might contain the request body.
- Sending PII via analytics: `analytics.track('event', { email: user.email })` — verify the analytics destination respects retention.
- Request logging middleware (Morgan, Pino HTTP) that doesn't redact `authorization`, `cookie`, `set-cookie`.

---

## SE — Senior Engineer (TS/JS patterns)

### Breaking changes (SE1)

- Exported function in a package's `index.ts` removed or renamed.
- Required parameter added to an exported function.
- Type narrowing on an exported type that breaks consumers.
- React component prop removed or renamed when the component is part of a public component library.

### Contract drift (SE2)

- `T` → `T | undefined` (or `T?`) on an exported interface field.
- Discriminated union: a variant removed.
- `zod` / `yup` / `valibot` schema's `default()` changed.
- Response type from a public API endpoint narrowed (field made optional) — consumers will break silently.

### Rollout risk (SE3)

- New feature in a service with a feature-flag framework (LaunchDarkly, Statsig, Unleash, Vercel Edge Config) but no flag wrapped around it.
- `process.env.NODE_ENV === 'production'` guarding behavior that should be flag-controlled.

### Deprecation missing (SE5)

- An exported symbol removed in this PR; `git log` shows no prior commit adding `@deprecated` JSDoc tag.

---

## IN — Senior Infra/SRE (TS/JS patterns)

### Network call hygiene (IN1)

- `fetch(url)` without `signal: AbortSignal.timeout(N)` — `fetch` has no default timeout in Node 18+. Always pass an `AbortSignal`.
- `axios.get(url)` without `{ timeout: N }`. Axios defaults to 0 (no timeout).
- `node-fetch` without timeout. Same issue as native fetch.
- New HTTP client without retry policy. Look for the project's standard wrapper (`lib/http.ts`, `clients/base.ts`).

### Observability (IN2)

- New endpoint without a metric (look for `prom-client`, `pino` with a transport, OpenTelemetry imports).
- New cron job / queue worker without start/finish/error logs.
- Background promise (`fire-and-forget`) without an error handler. Unhandled rejections crash the process in modern Node.

### Resource limits (IN3)

- `Promise.all(items.map(...))` on an unbounded `items` — concurrent unbounded I/O. Use `p-limit` or bounded chunking.
- No `bodyParser` limit on Express: `app.use(express.json())` defaults to 100kb but should be explicit.
- Reading entire response body unboundedly: `await response.text()` on a streaming endpoint.

### Idempotency (IN4)

- New webhook receiver without signature verification (Stripe, GitHub, Twilio all have signature schemes).
- New POST that mutates state without an `Idempotency-Key` header pattern (for retryable client requests).
- Queue job that mutates state without an idempotency key.

### CI/CD (IN5)

- `.github/workflows/*.yml` with an `uses:` line that references an action by tag (`@v3`) rather than SHA (`@a1b2c3...`). Tags are mutable; pin to SHA for supply-chain safety.
- New secret reference: `${{ secrets.X }}` where `X` wasn't previously used.
- Workflow `pull_request_target` instead of `pull_request` — runs with secrets on fork PRs. Almost always wrong; flag for review.

### Performance hot path (IN7)

- React component re-rendering on every parent render due to a new inline object/array prop (`prop={{...}}`, `prop={[...]}`).
- `useEffect` with no dependency array running on every render.
- Server: regex compiled in a hot path (`new RegExp(pattern)` inside a request handler) — hoist to module level.
- `JSON.parse(JSON.stringify(x))` for cloning in a hot path — use `structuredClone`.

---

## DA — Senior Data Engineer (TS/JS patterns)

### Schema break (DA1, DA2, DA3)

- **Prisma migration**: `migration.sql` with `DROP COLUMN`, `DROP TABLE`. Verify the dropped artifact isn't referenced in:
  - Other Prisma models (`schema.prisma`)
  - Application code (`grep -r "<column>" --include="*.ts"`)
  - dbt models, ETL pipelines (out-of-band)
- **TypeORM migration**: same. Look for `await queryRunner.dropColumn(...)`.
- **Drizzle**: schema diff that removes a column.
- **NOT NULL + no backfill**: `ALTER TABLE ... ADD COLUMN ... NOT NULL` without preceding update.

### Type precision (DA5)

- `Float` for money in Prisma — use `Decimal`.
- `Int` for timestamps that need milliseconds or timezone — use `DateTime` with timezone.
- `VarChar(N)` where N is too short for real-world data.

### Event contract (DA6)

- Removing a field from a Zod schema published as an event contract.
- Changing field types on a `kafkajs` producer message schema.

### Retention / PII (DA7)

- New PII field on a model without a corresponding retention-policy entry.

---

## TS — Test Reviewer (TS/JS patterns)

### Test file detection

A file is in the `test` bucket if its path matches:
- `*.test.ts`, `*.test.tsx`, `*.test.js`, `*.test.jsx`
- `*.spec.ts`, `*.spec.tsx`, `*.spec.js`, `*.spec.jsx`
- `__tests__/`, `tests/`, `test/`, `e2e/`
- Vitest setup files: `vitest.setup.ts`, `vitest.config.ts`

### Production file detection

`code` bucket: `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs` outside test paths and outside `node_modules/`, `dist/`, `build/`.

### Coverage gap signal (TS1)

If ≥ 30 net added lines across `code` bucket files AND zero `test` bucket files added or modified, fire TS1.

### Regression test signal (TS2)

If PR description matches `(fixes|closes|resolves) #\d+` AND zero `test` bucket files added or modified, fire TS2.

Both findings delegate to `ship-tested-code` for depth.
