# TypeScript / JavaScript Secure-Code Patterns

Per-SEC-category detection patterns for TS/JS, organized by framework. These are grep-able antipatterns — each bullet is something an in-context pass can detect on a diff or directory scan. For per-pattern rubric depth (anti-overlap, false-positive notes), see `reference-categories.md`.

---

## SEC1 — AUTH

### SEC1.1 — Missing AuthN

**Express:**
- New `app.get|post|put|patch|delete('/path', handler)` or `router.x('/path', handler)` with no auth middleware between path and handler. Search for project's middleware name: `authenticate`, `requireAuth`, `passport.authenticate`, `isAuthenticated`, `requireUser`. Confirm with `grep -B 5 "app\.\(get\|post\|put\|patch\|delete\)" <file>`.

**Next.js App Router:**
- New `app/api/**/route.ts` exporting `GET`/`POST`/etc. without `await auth()` (NextAuth v5), `getServerSession(authOptions)`, `await getSession()`, or a `middleware.ts` matcher covering the path.
- `middleware.ts` `config.matcher` array doesn't include a newly-added `/api/...` route.

**Next.js Pages Router:**
- New `pages/api/...` handler without `getSession()` / `getServerSession()` at the top of the handler.

**NestJS:**
- New `@Get|@Post|@Put|@Patch|@Delete` controller method without `@UseGuards(AuthGuard)` / `@UseGuards(JwtAuthGuard)` either on the method or on the class.

**tRPC:**
- New procedure declared as `publicProcedure` where the operation is state-changing or returns user-scoped data — should be `protectedProcedure`.

**GraphQL (Apollo, Mercurius, Yoga):**
- New resolver without an `@auth` directive or a `context.user` check at the top of the resolver body.

### SEC1.2 — IDOR / Missing AuthZ

- `prisma.user.findUnique({ where: { id: input.id } })` (or `findFirst`, `findById`) without `AND` clause filtering by `tenantId` / `ownerId` / `userId`. Search for `findUnique\({ where:` patterns where the where clause uses a user-supplied id without a tenant/owner field.
- TypeORM: `repository.findOne({ where: { id } })` instead of `repository.findOne({ where: { id, ownerId: ctx.user.id } })`.
- Drizzle: `db.select().from(documents).where(eq(documents.id, id))` without `and(eq(documents.tenantId, ctx.tenantId), ...)`.
- Sequelize: `Model.findByPk(id)` without scoped finder.
- Manual: `db.query('SELECT * FROM documents WHERE id = $1', [id])` without `WHERE id = $1 AND tenant_id = $2`.

### SEC1.3 — Broken session

- Session token stored in `localStorage.setItem('token', ...)` (JS-readable, XSS-stealable). Should be `HttpOnly` cookie.
- `cookie.serialize('session', token, { /* no httpOnly */ })` — flag missing `httpOnly: true, secure: true, sameSite: 'lax'|'strict'`.
- Logout that only clears `localStorage` without server-side session invalidation.

### SEC1.5 — JWT misuse

- `jwt.decode(token, { complete: true })` (decode != verify — does not check signature).
- `jwt.verify(token, key)` without `algorithms: ['RS256']` / `['HS256']` — algorithm confusion vulnerability.
- `jose.jwtVerify(token, key)` without `algorithms`.

---

## SEC2 — INPUT-VALIDATION

### SEC2.1 — No schema validation at boundary

**Express / Fastify / Next.js API:**
- Handler accesses `req.body.x` / `req.query.x` / `req.params.x` without a preceding `zod.parse(req.body)` / `Type.Check(...)` / `ajv.validate(...)` / `valibot.parse(...)` / `yup.validateSync(...)` / `joi.validate(...)`.
- TypeBox / Zod schema present but with `.partial()` / `.passthrough()` / `additionalProperties: true` accepting unknown fields.

**tRPC:**
- Procedure missing `.input(z.object({...}))` chain.

**NestJS:**
- Controller method with `@Body() payload: any` instead of `@Body() payload: PaymentDto` paired with `class-validator` decorators.
- Missing `@UsePipes(new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true }))`.

### SEC2.2 — Denylist patterns

- `if (input.includes('javascript:'))` — denylist on URL scheme. Use allowlist: `if (!url.startsWith('https://'))`.
- `input.replace(/<script>/g, '')` — naive HTML stripping; use a sanitizer or escape.
- `filename.endsWith('.exe')` — denylist; allowlist permitted extensions.

### SEC2.3 — Partial validation

- Schema parses some fields but the handler reads more. Cross-reference `z.object({a: ..., b: ...})` against `req.body.<field>` reads elsewhere in the file.

---

## SEC3 — INJECTION

### SEC3.1 — SQL injection

- Template literal in DB call: `` db.query(`SELECT ... ${x}`) ``. Search for `db\.query\(`/`db\.execute\(`/`pool\.query\(`/`connection\.query\(` followed by backtick-delimited string with `${...}`.
- Prisma `prisma.$queryRawUnsafe(query)`, `prisma.$executeRawUnsafe(query)` — by name, these are the unsafe variants. Use `$queryRaw\`...\`` tagged-template variant.
- TypeORM: `.query('... ' + x)`.
- Drizzle: `sql\`... ${unsafe}\`` where `unsafe` is not wrapped in `sql.placeholder` / `sql.raw`-with-allowlist.
- Knex: `.raw('... ' + x)` instead of `.raw('... ?', [x])`.
- Dynamic ORDER BY: `\`ORDER BY ${userColumn}\`` without column-name allowlist.

### SEC3.2 — NoSQL injection

- Mongoose: `Model.find(req.body)` — spreads user-controlled query operators. Should narrow: `Model.find({ email: String(req.body.email) })`.
- MongoDB native: `collection.find({ email: req.body.email })` where `req.body.email = { $ne: null }`.

### SEC3.3 — OS command injection

- `child_process.exec(\`cmd ${x}\`)` — string command with interpolation. Use `execFile`/`spawn` with args array.
- `child_process.execSync(userInput)`.
- `shelljs.exec(userInput)`.

### SEC3.4 — LDAP injection

- `ldapClient.search(base, { filter: \`(uid=${x})\` })` — escape with `ldapjs`-style escape function or `ldap-filter`.

### SEC3.5 — XPath injection

- `xpath.select(\`//user[@name='${x}']\`, doc)`.

### SEC3.6 — Log injection

- `logger.info(\`User: ${userInput}\`)` where `userInput` may contain `\n` / `\r`. Strip CRLF before logging user-controlled strings.

### SEC3.7 — Header injection

- `res.setHeader('X-Foo', userInput)` without newline-stripping.

### SEC3.8 — Template injection (SSTI)

- `Handlebars.compile(userInput)` — user controls the template, not just the data.
- `pug.render(userInput, locals)` — same.
- React: `React.createElement(userInput, ...)` where userInput is a string component name.

### SEC3.9 — Prototype pollution

- `Object.assign({}, ...untrusted)` where untrusted entries may include `__proto__` / `constructor.prototype`.
- `lodash.merge(safe, untrusted)`, `lodash.set(obj, userPath, value)`.
- `qs.parse(querystring, { plainObjects: false })` — set `plainObjects: true` to use null-prototype objects.
- Custom recursive merge that copies all own properties without filtering `__proto__`.

---

## SEC4 — XSS / OUTPUT-ENCODING

### SEC4.1 — Unsafe HTML rendering

**React:**
- `<div dangerouslySetInnerHTML={{ __html: userInput }} />` — must sanitize with DOMPurify first: `DOMPurify.sanitize(userInput)`.
- `<div ref={(el) => el.innerHTML = userInput}>` — direct DOM access bypasses React's escaping.

**Vue:**
- `v-html="userInput"`.

**Angular:**
- `[innerHTML]="userInput"` without `DomSanitizer.sanitize(SecurityContext.HTML, userInput)`.

**Templates:**
- Handlebars `{{{userInput}}}` (triple-brace).
- EJS `<%- userInput %>` (`<%-` unescaped, `<%=` escaped).
- Markdown renderer with `sanitize: false`: `marked.parse(userMd, { sanitize: false })`, `markdown-it().render(userMd)` without DOMPurify post-process.

### SEC4.2 — DOM XSS

- `element.innerHTML = userInput`.
- `element.outerHTML = userInput`.
- `document.write(userInput)`.
- `eval(userInput)`, `Function(userInput)()`, `setTimeout(userInput, 0)` (string form), `setInterval(userInput, ...)` (string form).

### SEC4.3 — Unsafe URL contexts

- `<a href={userUrl}>` — check `userUrl` against scheme allowlist (`http:`, `https:`, optionally `mailto:`). Reject `javascript:`, `data:` for href.
- `<iframe src={userSrc}>` — same scheme allowlist + host allowlist + always include `sandbox`.
- `window.location.href = userUrl`, `window.open(userUrl)`.
- `<form action={userAction}>` — POST destination should be allowlisted.

### SEC4.4 — CSS injection

- `style={{ background: userBg }}` — `userBg` can include `}` to break out of inline style.
- `el.style.cssText = userCss`.

### SEC4.5 — Markdown without sanitization

- `marked.parse(userMd)` (recent versions default to no sanitization).
- `markdown-it().render(userMd)` (no built-in sanitization).
- `react-markdown` is safe by default; flag if `rehypePlugins` includes `rehype-raw` without `rehype-sanitize`.

---

## SEC5 — CSRF / ORIGIN

### SEC5.1 — Missing CSRF token

**Express:**
- POST/PUT/PATCH/DELETE routes without `csurf` middleware (or equivalent).

**Next.js:**
- Server Actions in App Router get framework-level origin checks; document this in the review. Pages Router API routes need explicit CSRF if using cookie auth.

**Note:** APIs that exclusively authenticate via `Authorization: Bearer ...` headers (not cookies) are not vulnerable to classical CSRF. Don't fire SEC5.1 on bearer-token APIs.

### SEC5.2 — postMessage without origin verification

- `window.addEventListener('message', (e) => { ... })` whose handler reads `e.data` without first checking `e.origin === '<known>'`.
- Same for `useEffect` hook subscribing to `'message'`.

### SEC5.3 — Iframe without sandbox

- `<iframe src={userContent}>` without `sandbox=""` (start empty and add specific permissions as needed).
- Embedded user-generated content frames without origin isolation.

### SEC5.4 — Weak CSP

- `Content-Security-Policy: ... 'unsafe-inline' ...` in `script-src`.
- `Content-Security-Policy: ... 'unsafe-eval' ...` in `script-src`.
- `script-src: *` or `connect-src: *`.
- Next.js middleware setting CSP without nonces, when nonces are available (Next.js 13.4+).

### SEC5.5 — CORS misconfiguration

- `cors({ origin: '*', credentials: true })` — invalid combo, but the misconfig still indicates confusion. Flag.
- `cors({ origin: req.headers.origin, credentials: true })` — reflects any origin, equivalent to `*` with credentials.
- Spring (cross-ref `lang-java.md`): `@CrossOrigin(origins = "*", allowCredentials = "true")`.

---

## SEC6 — CRYPTO

### SEC6.1 — Weak password hash

- `crypto.createHash('md5'|'sha1'|'sha256'|'sha512').update(password).digest()` for password storage. Use `bcrypt`, `argon2`, or `scrypt`.
- Browser: `btoa(password)` / `Buffer.from(password).toString('base64')` for "hashing".

### SEC6.2 — Math.random for security

- `Math.random()` used to generate: session ID, password-reset token, CSRF token, email-verification token, API key, anything security-relevant. Use `crypto.randomUUID()` / `crypto.randomBytes(N)`.

### SEC6.3 — Deprecated ciphers

- `crypto.createCipher` (deprecated since Node 10, removed in newer; uses default IV derivation). Use `crypto.createCipheriv(algorithm, key, iv)`.
- `crypto.createCipheriv('aes-256-ecb', ...)` — ECB mode.
- `crypto.createCipheriv('des-cbc', ...)`, `'des-ede-cbc'`.

### SEC6.4 — Hardcoded IV / salt / key

- `crypto.createCipheriv(alg, key, Buffer.from('1234567812345678'))` — literal IV.
- `bcrypt.hash(password, hardcodedSalt)`.

### SEC6.5 — JWT misuse

- `jsonwebtoken.verify(token, key)` without `algorithms` option.
- `jsonwebtoken.sign(payload, key, { algorithm: 'none' })`.
- `jose.jwtVerify` without `algorithms` constraint.

### SEC6.6 — TLS misconfiguration

- Node: `https.request({ rejectUnauthorized: false })` / `agent: new https.Agent({ rejectUnauthorized: false })` — disables cert validation.
- `tls.connect({ rejectUnauthorized: false })`.
- Setting `NODE_TLS_REJECT_UNAUTHORIZED=0` in code (rather than as a dev-only env var).

---

## SEC7 — SECRETS

### SEC7.1 — Hardcoded secret literal

- String literals matching:
  - `sk_live_[A-Za-z0-9]{24,}` (Stripe live key)
  - `sk_test_[A-Za-z0-9]{24,}` (Stripe test key — still flag, may indicate prod-key adjacent code)
  - `AKIA[A-Z0-9]{16}` (AWS access key)
  - `ASIA[A-Z0-9]{16}` (AWS session token)
  - `ghp_[A-Za-z0-9]{36}` (GitHub personal access)
  - `gho_[A-Za-z0-9]{36}` (GitHub OAuth)
  - `xox[bpoa]-[A-Za-z0-9-]{10,}` (Slack)
  - `eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+` (JWT token literal)
  - `-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----` (inline private key)
  - `mongodb://[^:]+:[^@]+@`, `postgres://[^:]+:[^@]+@` (DB URL with embedded password — flag if password isn't `password`/`changeme`/`local`)

### SEC7.2 — Committed .env

- `.env`, `.env.local`, `.env.production`, `.env.development` present in repo (not in `.gitignore`).

### SEC7.3 — Token in URL

- Template literals constructing URLs with a token query parameter: `\`https://api.example.com/?token=${TOKEN}\``.
- `fetch(\`...?api_key=${KEY}\`)`.

### SEC7.4 — CI YAML literal secret

- `.github/workflows/*.yml` with `KEY: sk_live_...` or `TOKEN: ghp_...` instead of `KEY: ${{ secrets.KEY }}`.

### SEC7.5 — Runtime lockfile committed

- `.claude/*.lock` (Claude scheduled-task lockfile).
- `.next/cache/` tracked.
- `npm-debug.log`, `yarn-error.log`.

---

## SEC8 — SUPPLY-CHAIN

### SEC8.1 — Suspicious new dep

When `package.json` adds a new dependency, check:

- `npm view <pkg> time.created` — if < 3 months ago, yellow flag.
- `npm view <pkg> downloads` (or check npmjs.com weekly downloads) — if very low (< 1000/week), yellow flag.
- Name is a typosquat of a popular package — yellow flag. Examples to watch: `request` (popular) vs `requests` (typo); `react-dom` vs `react-doom`; `node-fetch` vs `node-fetchh`; `cross-fetch` vs `crossfetch`.
- `package.json` has new `postinstall` / `preinstall` / `install` script entries. Cross-check whether they were added by adding a new dep (transitive postinstall) — install graph diff shows this.

Combining 2+ yellow flags → tier 1.

### SEC8.2 — Non-registry dependency source

- `package.json` dependency value matches `git+ssh://...`, `git+https://...`, `git://...` without a commit-hash pin (e.g., `#abc123` suffix).
- `package.json` dependency value matches a local `file:` or `link:` outside the workspace.

### SEC8.3 — Lockfile drift

- `package-lock.json` / `pnpm-lock.yaml` / `yarn.lock` change that introduces a `resolved:` URL pointing to a non-registry host.
- Lockfile change without a corresponding `package.json` change (could indicate dep tampering).

### SEC8.4 — Known CVE

- `npm audit` reports a high/critical in a direct or transitive dep added by this PR.

---

## SEC9 — PII / LOGGING

### SEC9.1 — PII in logs

- `console.log("User:", user)` / `console.log({ user })` where `user` object has `email` / `phone` / `address` / `ssn` / `dob`.
- `logger.info("user logged in", user)` (Pino/Winston) — same risk.
- Template literals: `\`User logged in: ${user.email}\``.

### SEC9.2 — Unredacted request logging

- `app.use(morgan('common'))` without a `skip` or token customization that redacts `Authorization`/`Cookie`.
- Pino HTTP without `redact: ['req.headers.authorization', 'req.headers.cookie']`.
- Custom middleware logging `req.body` without redaction.

### SEC9.3 — Analytics with PII

- `analytics.track('event', { email: user.email, phone: user.phone })`.
- `Sentry.init(...)` without `beforeSend` scrubbing.
- `Sentry.init(...)` with `sendDefaultPii: true`.

### SEC9.4 — Error responses leaking PII / internals

- Express `err.stack` returned in response body to clients.
- Validation error response with full `req.body` echo (some Zod error formatters do this — `zod-error-handler` configs).

---

## SEC10 — RESOURCE-EXHAUSTION

### SEC10.1 — ReDoS

- Regex literals with nested quantifiers in production code paths that match user input. Patterns to flag:
  - `/^(\w+)*$/`, `/^(a+)+$/`, `/^(\d|\d\d)+$/` (overlapping alternatives), `/^(.*)+$/`.
  - Alternation with overlap: `/(abc|abd)+/` (shared prefix).
- Use safe-regex or re2 to verify. For known-bad patterns from CVE feeds (e.g., the old `marked` ReDoS, the `validator.js` email ReDoS), flag immediately.

### SEC10.2 — Unbounded concurrency

- `Promise.all(arr.map(fn))` where `arr` is user-controlled and `fn` is I/O-bound. Use `p-limit(N)` to bound concurrency.
- `await Promise.allSettled(arr.map(fn))` — same.

### SEC10.3 — Missing request size cap

- Express `app.use(express.json())` without `{ limit: '<size>' }` — defaults to 100kb but should be explicit; for upload routes the limit must match expected payload size.
- Fastify: no `bodyLimit` option.
- Next.js App Router: `route.ts` parsing `request.body` without size check.
- `formidable` / `multer` without `limits.fileSize`.

### SEC10.4 — Missing rate limit

- Routes that should be rate-limited (auth, password reset, signup, search, expensive computations, email/SMS sending) without `express-rate-limit` / `fastify-rate-limit` / NextJS middleware-level limiter.

### SEC10.5 — Large file / JSON processing

- `JSON.parse(largeString)` without size cap on the string.
- `sharp(buffer)` / `Jimp.read(buffer)` without checking max dimensions.

---

## SEC11 — PATH-TRAVERSAL / FILE-OPS

### SEC11.1 — Path traversal

- `path.join(uploadDir, req.body.filename)` / `path.join(uploadDir, req.params.file)` followed by `fs.readFile`/`fs.createReadStream`/`fs.writeFile` without:
  ```ts
  const resolved = path.resolve(uploadDir, filename);
  if (!resolved.startsWith(path.resolve(uploadDir) + path.sep)) throw new Error('escape');
  ```
- `new URL(userPath, 'file://').pathname` — file URL parser doesn't validate boundary.

### SEC11.2 — Archive extraction

- `tar.extract({ file, cwd })` without `filter` / `onentry` validating entry paths.
- `unzipper.Extract({ path })` reading user-uploaded zips — vulnerable to zip slip.
- `adm-zip.extractAllTo(path)` — same.

### SEC11.3 — Unsafe file ops

- `fs.symlinkSync(target, userPath)` where target is sensitive.
- `fs.chmodSync(userPath, mode)`.
- `fs.unlinkSync(userPath)` without validating userPath is inside an allowed directory.

### SEC11.4 — Filename sanitization

- Storing uploaded file with the user-provided name: `fs.writeFile(path.join(dir, file.originalname), buffer)`. Use UUID-based filenames server-side.

---

## SEC12 — DESERIALIZATION / SSRF

### SEC12.1 — Unsafe deserialization

- `eval(userInput)`, `Function(userInput)()`, `vm.runInNewContext(userInput)`, `vm.runInThisContext(userInput)`.
- `serialize-javascript` parse on untrusted input.
- `node-serialize`'s `unserialize()` — well-known RCE library; do not use on untrusted input.

### SEC12.2 — XXE

- `libxmljs.parseXml(userXml, { resolveExternals: true })` — should be `false`.
- `xml2js.Parser({ explicitArray: false })` without disabling external entities — confirm with xml2js docs.
- DOMParser in browser parsing untrusted XML.

### SEC12.3 — SSRF

- `fetch(userUrl)` server-side without:
  - Scheme allowlist (`url.protocol === 'https:' || url.protocol === 'http:'`).
  - Host resolution + private-IP block (use `dns.lookup` then check against `ipaddr.js` `range()` for private/loopback/link-local).
- `axios.get(userUrl)`, `got(userUrl)`, `node-fetch(userUrl)`, `superagent.get(userUrl)`.
- Image/PDF generators with user-controlled URLs (Puppeteer `page.goto(userUrl)`, headless Chrome to PDF).
- `request(userUrl)` (deprecated `request` lib).

### SEC12.4 — Open redirect

- `res.redirect(req.query.next)` / `res.redirect(req.body.returnUrl)` without validating the destination.
- `next/navigation` `redirect(userUrl)` server action without validation.
- Client-side: `window.location = querystring.next`.

---

## Quick triage for diff reviews

For a new file or major addition, scan in this order:

1. **Boundary first** — locate every route handler / queue consumer / webhook receiver. Confirm AuthN (SEC1.1) and validation (SEC2.1).
2. **Sinks second** — for each `db.query`, `child_process.exec`, `fs.read*`, `fetch`, `eval`, JWT verify, look back to where the data came from.
3. **Output third** — for each `dangerouslySetInnerHTML`, `innerHTML`, `href={...}`, `Markup(...)`, confirm the source is sanitized.
4. **Layer fourth** — check for CSP, CORS, CSRF, rate limit, request-size cap — the defense-in-depth layer.
5. **Crypto/secrets fifth** — scan the diff for hash function names, hardcoded API key shapes, JWT calls.

Most real bugs are caught in steps 1-3. Steps 4-5 are advisory unless something is obviously wrong.
