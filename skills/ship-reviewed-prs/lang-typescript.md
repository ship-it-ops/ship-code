# TypeScript / JavaScript PR-Review Idioms

PR-review-specific patterns for TS/JS. For file-level idioms (type safety, async, React), defer to `ship-clean-code/lang-typescript.md`. This file covers what each persona looks for in a *PR* context.

---

## SC — Senior Security Engineer (TS/JS patterns)

> SC owns **detection** at the PR-review level. The patterns below are the high-precision single-line shapes that fire as direct SC findings. For data-flow trace, multi-file context, framework-specific depth (Spring/Django/NestJS/etc.), or any of the SEC4-SEC12 categories in the sibling skill, emit `Run /ship-secure-code on <file>` under Delegations instead of writing a deep finding here. The detailed per-category rubric lives in `/Users/.../ship-secure-code/lang-typescript.md`.

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

---

## FE — Senior Frontend Engineer (TS/JS patterns)

These are detection-shaped patterns — each is something a single grep / scan pass can find on a diff. The rubric depth (false-positive notes, framing) is in `reference-personas.md`.

### A11Y contract (FE1)

- **Dangling ARIA target**: grep for `aria-errormessage="<expr>"` or `aria-describedby="<expr>"` or `aria-labelledby="<expr>"`. For each, locate the literal id value (or the template-string id like `${rest.id ?? 'inline-edit'}-error`) and grep the same component file for `id={` matching that value. If no rendered element matches, fire FE1. Pay special attention to id values that depend on a state variable (`error`) — the rendered element must be conditional on the *same* state.
- **Accessible-name carryover on DOM swap**: identify components that branch the return JSX based on a state variable (e.g. `if (!editing) return <button .../>` followed by a different return `<input .../>`). If the first branch has an accessible name (`aria-label`, `aria-labelledby`, visible text child) and the second branch is an `<input>`/`<textarea>` without `aria-label`/`aria-labelledby`, fire FE1.
- **`role="img"` without label**: grep for `role="img"`. If the same element lacks `aria-label`, `aria-labelledby`, or a child element exposing an accessible name, fire FE1. Exception: SVG with `<title>` is fine.

### Controlled-state desync (FE2)

- **Effect resetting refs/history on every prop change**: grep for `useEffect(\([^)]*\) =>` whose body contains both a `setState` (or ref mutation) AND a `.reset()` / `.clear()` / re-initialization call, AND whose dep array includes a prop. Fire FE2.
- **Callback emits a subset of internal state**: grep for `on[A-Z]\w+?\?\.\(` or `on[A-Z]\w+?\(` invocations inside an internal handler. If the surrounding code generates an id (`Date.now()`, `crypto.randomUUID()`, `nanoid()`, `${prefix}-${counter}`) into a local variable BUT the callback only receives a subset of that variable, fire FE2. Common shape: `const newEdge = { id: gen(), ...params }; applyCommand(...); onConnect?.(params);` — the consumer can't reconstruct the id.
- **Internal command stores more than callback emits**: cross-check `applyCommand({ kind: '...', node: { id, position, data } })` with `onNodeAdd?.(position)` shapes — if the internal command has more fields than the outward callback, fire FE2 on the callback site.

### Command-history incomplete (FE3)

- **Bypassing dispatch**: grep for two paths to the same state mutation. Heuristic: locate every `set<Capitalized>(`/`baseOn<Capitalized>Change(` call and every `applyCommand(`/`dispatch(` call in the same file. If a keyboard/imperative handler (`useKeyboard`, `onKeyDown`, `useGraphEditorKeyboard`, etc.) calls the raw setter while click/menu/drag handlers go through dispatch, fire FE3.
- **Overlapping command entries**: identify command actions whose inverse already covers a related entity. Specifically: `delete-node` whose inverse restores incident edges, paired with a separate `delete-edge` for those same edges in the same user action (search for two consecutive `applyCommand(... 'delete-node' ...)` and `applyCommand(... 'delete-edge' ...)` in the same handler). Fire FE3.

### No-op prop value (FE4)

- For each TypeScript prop typed as a union of string literals (`'a' \| 'b' \| 'c'`), grep the same file for `=== '<variant>'`, `case '<variant>':`, or destructured branching on the variant. If a variant has no matching branch, fire FE4. Tolerate variants annotated `/** @experimental */` or `/** @deprecated */` on the type declaration.

### SSR / global-CSS (FE5)

- **Global CSS import in non-entry module**: grep for `^import ['"]\..*\.css['"]` or `^import ['"][^./].*\.css['"]` in any file whose path is not `layout.tsx`, `_app.tsx`, `page.tsx`, `main.tsx`, `index.tsx`, or `root.tsx`. Fire FE5. Exception: CSS Modules (`.module.css`) are not global; do not fire.
- **`window`/`document` at module top-level without `'use client'`**: grep for `^const \w+ = window\.` or `^window\.` or `^document\.` at module-top level. If the file doesn't open with `'use client'` and the project is Next.js App Router (heuristic: `app/` directory + `next.config.*`), fire FE5.

### Range clamp missing (FE6)

- For each function/method that returns or passes a `{ x, y, width, height }`-shaped object (or `{ left, top, right, bottom }`, `{ start, end }`) to a consumer documented to accept normalized 0..1 fractions, check whether the producer applies `Math.max(0, Math.min(1, x))` (or a `clamp01` helper) to each field. Common consumers: `Minimap`, `GraphMinimap`, `Slider`, `Progress`, normalized scroll, normalized viewport rects. If neither producer nor consumer clamps, fire FE6.

### Changeset drift (FE7)

- For each `.changeset/*.md` file in the diff, parse the body. Phrases that indicate "scope smaller than diff": `lands in next iteration`, `follow-up PR`, `to be added`, `not yet implemented`, `coming soon`, `placeholder for`. Cross-check against the diff — if any of the named behaviors are present in the diff, fire FE7. Phrases that indicate "scope larger than diff": describe behaviors not detectable in the diff. Optional secondary check.

### Redundant internal import (FE8)

- For each `import` line inside `packages/<pkg>/src/`, check if the import specifier starts with the package's own published name (read `packages/<pkg>/package.json` `name` field). If yes, fire FE8 — a package should not self-import its own published path. Common offender: `import '@scope/pkg/styles.css'` from inside `packages/pkg/src/`.
