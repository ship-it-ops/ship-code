# Secure Code Categories — Deep Rubric

For each of SEC1-SEC12: antipatterns, canonical fixes, common false-positives, cross-references to related categories.

---

## SEC1 — AUTH

Who can do what. AuthN = logged in; AuthZ = allowed to access this resource.

### SEC1.1 — Missing AuthN (must-fix)

**Antipatterns:**
- New HTTP route handler without auth middleware. Express: `app.get('/path', handler)` with no `requireAuth` middleware between path and handler. Next.js App Router: new `route.ts` exporting `GET`/`POST`/etc. without `await auth()` / `getServerSession()` / middleware-matcher coverage. NestJS: controller method without `@UseGuards(AuthGuard)`. tRPC: `publicProcedure` where `protectedProcedure` is needed.
- Servlet `@WebServlet`/`@WebFilter` without security constraint declared.
- Spring controller without `SecurityFilterChain` covering the path (check `application-security.yml` or `WebSecurityConfigurerAdapter`).

**Fix:** wrap with the framework's auth middleware/guard/decorator. Verify: `curl` the route without credentials should return 401.

### SEC1.2 — Missing AuthZ / IDOR / BOLA (must-fix)

**Antipatterns:** the most common modern security bug.
- `Model.findById(req.params.id)` returning a resource without first verifying the requesting user owns/can-access it.
- `repository.findById(id)` (JPA) instead of `findByIdAndOwnerId(id, currentUser.id)`.
- Tenant-scoped resource served without tenant scope: `db.documents.findOne({ id })` instead of `db.documents.findOne({ id, tenantId: ctx.tenant })`.
- Role check at the wrong layer: middleware checks "logged in" but the controller doesn't check "is admin" for an admin-only operation.
- `@PreAuthorize("isAuthenticated()")` instead of `@PreAuthorize("hasRole('ADMIN')")` on an admin endpoint.

**Fix:** check ownership/tenant/role at the controller level (or service if it's the call site). Database queries that fetch resources owned by users must always include the owner/tenant in the WHERE clause.

### SEC1.3 — Broken session management

- Session token stored in `localStorage` (XSS-readable) instead of `HttpOnly` cookie.
- Session ID re-issuance missing after login (session fixation).
- Logout doesn't actually invalidate the session server-side.
- Session timeout too long (default > 24h for sensitive apps).

### SEC1.4 — Over-privileged service account

- DB connection string uses `root`/`postgres` superuser instead of a per-service account.
- Cloud IAM role with `*` permissions or `AdministratorAccess`.
- Container running as root (`USER root` or no `USER` directive in Dockerfile).
- Kubernetes service account with cluster-admin role.

### SEC1.5 — JWT misuse

- `jwt.decode(token, verify=False)` — accepts forged tokens.
- `jwt.decode(token, key, algorithms=None)` — algorithm confusion attack (HS256 vs RS256).
- `Jwts.parser().setSigningKey(key).parseClaimsJws(jwt)` without an algorithm allowlist.
- `algorithms: ['none']` accepted.

### False positives

- A public health endpoint (`/health`, `/ping`, `/metrics`) is intentionally open — verify the path is in the framework's exempt list.
- A webhook receiver verifies signature instead of session auth — that's still authentication, just not the usual session flavor. Check for `verifyStripeSignature`, `verifyGitHubSignature`, HMAC-based webhook patterns.
- Public-read endpoints (read-only data deliberately public) are valid; SEC1.1 only fires on state-changing routes when documented as public.

### Cross-refs

- SEC5 (CSRF/origin) — state-changing routes need origin verification *in addition to* AuthN.
- SEC9 (PII/logging) — IDOR often reveals PII.
- SEC10 (rate limiting) — auth endpoints without rate limiting are a credential-stuffing surface.

---

## SEC2 — INPUT-VALIDATION

Data crossing the trust boundary is parsed, validated, and normalized before use.

### SEC2.1 — No schema validation at the boundary (must-fix when downstream sink is dangerous)

**Antipatterns:**
- Express `req.body` accessed directly without a `zod.parse` / `joi.validate` / `class-validator` / Yup pass.
- FastAPI endpoint missing a Pydantic model in its signature: `def handler(request: Request)` instead of `def handler(payload: PaymentPayload)`.
- Spring controller `@RequestBody Map<String, Object> payload` (untyped, unvalidated) instead of `@Valid @RequestBody PaymentDto payload`.
- DRF (Django REST Framework) `Serializer` not called with `is_valid(raise_exception=True)`.
- Schema validation present but with `additionalProperties: true` / `strict=False` / no `extra='forbid'` — accepts unknown fields, which can collide with downstream merge logic.

**Fix:** schema at the boundary, `strict()` mode, fail-closed on unknown fields. The validated value's type is narrow; downstream code consumes the narrow type, never the raw body.

### SEC2.2 — Denylist instead of allowlist

- `if "javascript:" in url:` — defeated by `JavaScript:`, `java\tscript:`, `&#x6a;avascript:`, etc.
- `re.sub(r"<script>", "", input)` — defeated by case variations, attribute-context injection, `<scr<script>ipt>`.
- `if filename.endswith('.exe') or filename.endswith('.bat'):` — denylist; allowlist of permitted extensions is correct.

**Fix:** allowlist. `if not re.match(r'^https?://', url)`. `if file_ext not in {'png', 'jpg', 'jpeg', 'pdf'}`.

### SEC2.3 — Partial validation

Validation exists but doesn't cover the fields used downstream. E.g., the schema validates `email` and `name` but the handler also reads `req.body.adminOverride`, which is unvalidated.

**Fix:** schema must cover every field the handler reads. `strict()` / `forbid_extra_keys` catches this automatically.

### SEC2.4 — Normalization missing before comparison

- Unicode: `"café"` vs `"café"` (composed vs decomposed) — both render identically but compare unequally. Normalize with NFC before allowlist check.
- Path: equivalent strings like `foo/bar`, `foo/bar/`, and `foo/./bar` can refer to the same file but compare unequally. Normalize with `os.path.normpath` / `Path.resolve` before allowlist.
- URL: `https://example.com:443/` vs `https://example.com/` — normalize before host allowlist.

### False positives

- Internal-only RPC services that trust their caller may legitimately skip validation. Tier-1 fires only when the input source is on the wrong side of the trust boundary.
- Single-field endpoints (e.g., `/healthz?token=...`) may use direct string comparison instead of schema validation — fine.

### Cross-refs

- SEC3 (injection) — almost always co-occurs with missing SEC2.
- SEC11 (path traversal) — same root cause.

---

## SEC3 — INJECTION

Untrusted data interpreted as code by a downstream parser.

### SEC3.1 — SQL injection (must-fix)

**Antipatterns:**
- String concat / template literal: `` db.query(`SELECT * FROM users WHERE email = '${email}'`) ``. JS, Python f-strings, Java `String.format`, Go `fmt.Sprintf` — all the same antipattern.
- ORM `.raw()` / `.unsafe()` / `$queryRawUnsafe` / `Model.objects.extra(where=[f"... {x}"])` / `em.createQuery("... '" + x + "'")` with user input.
- Stored procedures that themselves use `EXEC(@sql)` with concatenated SQL.
- Dynamic ORDER BY: `ORDER BY ${userInput}` — same risk, harder to spot.

**Fix:** parameterized queries. `db.query('SELECT * FROM users WHERE email = $1', [email])` (node-postgres). `db.execute(text(":id"), {"id": id})` (SQLAlchemy). `em.createQuery("...").setParameter("name", name)` (JPA). For ORDER BY: allowlist column names.

### SEC3.2 — NoSQL injection (must-fix)

- MongoDB: `db.users.find({ email: req.body.email })` where `req.body.email` is `{ $ne: null }` — operator injection. Coerce to string before query.
- Mongoose: `findOne(req.body)` — spread user input as query.

**Fix:** explicit field coercion: `db.users.find({ email: String(req.body.email) })`. Or schema validation upstream.

### SEC3.3 — OS command injection (must-fix)

**Antipatterns:**
- `subprocess.run(f"ls {user_input}", shell=True)`.
- `os.system(user_input)`, `os.popen(user_input)`.
- `Runtime.getRuntime().exec("ls " + userInput)`.
- `child_process.exec(`ls ${userInput}`)` (Node).

**Fix:** `subprocess.run(['ls', user_input], shell=False)` — pass args as a list, never as a string. `child_process.execFile('ls', [userInput])`. `ProcessBuilder("ls", userInput)` (Java).

### SEC3.4 — LDAP injection

- `ldap.search_s(base, scope, f"(uid={user_input})")` — escape with `ldap.dn.escape_dn_chars`.
- Java: `DirContext.search(base, "(uid=" + userInput + ")", controls)` — use `Filter.escape`.

### SEC3.5 — XPath injection

- `xpath.compile("//user[@name='" + name + "']")` — use parameterized XPath.

### SEC3.6 — Log injection (CRLF)

- `logger.info("user logged in: " + userInput)` — `userInput` containing `\n` injects fake log lines. Strip newlines from any user input that lands in a log.

### SEC3.7 — Header injection (CRLF)

- `response.setHeader('X-Foo', userInput)` — same as log injection, but the consequence is HTTP response splitting.

### SEC3.8 — Template injection / SSTI

- Jinja2: `Template(user_input).render()` — RCE via `{{config.__class__.__init__.__globals__['os'].popen('id').read()}}`.
- Velocity: `Velocity.evaluate(context, writer, "tag", userTemplate)`.
- Handlebars: compiling a user-supplied template string.

**Fix:** never accept template strings from users. Templates are code.

### SEC3.9 — Prototype pollution

- `Object.assign({}, ...untrusted)` where `untrusted` is `[{"__proto__": {"isAdmin": true}}]`.
- `lodash.merge(safe, untrusted)` — patched in lodash 4.17.21 but the pattern is still risky for chained merges.
- Node: `qs.parse('?__proto__[admin]=true')`.

**Fix:** use `Object.create(null)` for maps that hold untrusted keys. Use `Map` instead of object literal. For libraries: pin to fixed versions.

### Cross-refs

- SEC2 (input validation) — primary defense; SEC3 fires regardless because parameterization is mandatory, not a substitute.
- SEC4 (XSS) — template injection vs XSS context differs; template injection runs server-side code, XSS runs client-side.

---

## SEC4 — XSS / OUTPUT-ENCODING

Untrusted data rendered to a browser without context-appropriate encoding.

### SEC4.1 — Stored / reflected XSS (must-fix)

**Antipatterns:**
- React: `<div dangerouslySetInnerHTML={{ __html: userInput }} />` — RCE in browser.
- Vue: `v-html="userInput"`.
- Angular: `[innerHTML]="userInput"` without `DomSanitizer.bypassSecurityTrustHtml`.
- Handlebars: `{{{userBio}}}` (triple-braces bypass escape).
- EJS: `<%- userBio %>` (`<%-` is unescaped, `<%=` is escaped).
- Jinja2 with `|safe` filter on user input, or `Markup(user_input)`.
- Django template `{% autoescape off %}`.

**Fix:**
- React: render as text (`{userInput}`) — React escapes by default. If HTML is needed, sanitize with `DOMPurify.sanitize(userInput)` first.
- Other frameworks: drop the unsafe form, use the escaped variant. If the output truly must be HTML (rare), sanitize with DOMPurify / Bleach / Jsoup before render.

### SEC4.2 — DOM XSS

- `element.innerHTML = userInput` in JS.
- `document.write(userInput)`.
- `eval(userInput)` / `Function(userInput)` / `setTimeout(userInput)` (string form).

### SEC4.3 — Unsafe URL contexts

- `<a href={userUrl}>` without scheme allowlist — `userUrl = "javascript:alert(1)"` is XSS via click.
- `<iframe src={userSrc}>` without scheme + host allowlist.
- `<img src={userSrc}>` with `userSrc = "javascript:..."` (older browsers).
- `window.location = userUrl` or `window.open(userUrl)`.

**Fix:** validate scheme against `{'http:', 'https:', 'mailto:'}` (or your app's allowlist).

### SEC4.4 — CSS injection

- `<div style={{ background: userBg }}>` — `userBg = "url(javascript:alert(1))"` (old browsers); more commonly, `userBg` can inject `}` to break out of the style scope.
- `style.cssText = userCss` — same.

### SEC4.5 — Markdown rendering without sanitization

- `marked.parse(userInput)` with `sanitize: false` (the default in recent marked versions).
- `markdown-it.render(userInput)` without sanitization.

**Fix:** pass output through DOMPurify; or use a hardened renderer; or render markdown server-side with an allowlist.

### False positives

- A static string `"<b>bold</b>"` from a constants file is not user-controlled; SEC4.1 doesn't fire.
- React text children are auto-escaped — `<div>{userInput}</div>` is safe.
- `dangerouslySetInnerHTML` with a value that comes from a trusted, sanitized source (with the sanitizer call visible in the file) is fine.

### Cross-refs

- SEC5 (CSP) — CSP is the defense-in-depth layer for XSS.
- SEC2 (input validation) — primary; XSS fires regardless because output encoding is mandatory.

---

## SEC5 — CSRF / ORIGIN

Cross-origin trust.

### SEC5.1 — Missing CSRF token on state-changing route (must-fix)

**Antipatterns:**
- Django: `@csrf_exempt` decorator added without justification.
- Flask: missing `CSRFProtect()` from Flask-WTF.
- Express: missing `csurf` middleware on state-changing routes (POST/PUT/PATCH/DELETE).
- Spring Security: `.csrf().disable()` without justification.

**Fix:** enable framework-default CSRF protection; document any exemptions.

Exception: APIs that authenticate via `Authorization: Bearer ...` header (not via cookie) are not vulnerable to CSRF in the classical sense. Don't fire SEC5.1 on bearer-token APIs.

### SEC5.2 — postMessage without origin verification (must-fix)

**Antipatterns:**
- `window.addEventListener('message', (e) => handler(e.data))` — accepts messages from any origin.

**Fix:** `if (event.origin !== 'https://known-parent.example.com') return;` at the top of the handler.

### SEC5.3 — Iframe without sandbox

- `<iframe src={userContent}>` without `sandbox=""` (start with empty sandbox and add specific permissions).
- Embedded user-generated content frames without origin isolation.

### SEC5.4 — Weak or missing CSP (should-fix; advisory if other defenses present)

- No `Content-Security-Policy` header on HTML responses.
- `script-src 'unsafe-inline' 'unsafe-eval'` — disables CSP's main defense.
- `*` in `script-src` / `connect-src`.

**Fix:** nonce-based CSP. `script-src 'self' 'nonce-${nonce}'`.

### SEC5.5 — CORS misconfiguration

- `Access-Control-Allow-Origin: *` AND `Access-Control-Allow-Credentials: true` — browsers block this combo, but the misconfig is still wrong and may indicate confusion. Fire SEC5.5 on the combination.
- Reflected origin without allowlist: `res.setHeader('Access-Control-Allow-Origin', req.headers.origin)` — equivalent to `*` with credentials.
- Pre-flight allowed `Authorization` from arbitrary origins.

### Cross-refs

- SEC1 (auth) — origin verification complements AuthN/AuthZ for state-changing routes.
- SEC4 (XSS) — CSP is the depth layer for XSS.

---

## SEC6 — CRYPTO

Cryptographic primitive misuse.

### SEC6.1 — Weak hash for passwords (must-fix)

**Antipatterns:**
- `hashlib.md5(password.encode())` / `sha1` / `sha256` / `sha512` for password storage.
- `MessageDigest.getInstance("MD5")` / `"SHA-1"` for passwords.
- `crypto.createHash('md5').update(password).digest()` (Node).
- Custom hash construction: `sha256(sha256(password + salt))`.

**Fix:** use a password-hashing function: `bcrypt`, `argon2` (preferred for new code), `scrypt`, or `pbkdf2` with high iterations (>= 600k for SHA-256).

### SEC6.2 — Weak RNG for security tokens

**Antipatterns:**
- `Math.random()` for session IDs, password-reset tokens, CSRF tokens.
- Python `random.random()`, `random.randint()`, `random.choices()` for security tokens.
- Java `new Random()` for security tokens.

**Fix:** `crypto.randomBytes()` / `crypto.randomUUID()` (Node). `secrets.token_urlsafe()` / `secrets.token_hex()` (Python). `SecureRandom` (Java). Web Crypto API (browser).

### SEC6.3 — Deprecated / weak ciphers

- `Cipher.getInstance("DES")` / `"AES"` (defaults to ECB) / `"AES/ECB/PKCS5Padding"`.
- `crypto.createCipher` (deprecated, fixed IV) — use `createCipheriv` with random IV.
- RC4, Blowfish for new code.

**Fix:** `AES-GCM` for new code: `crypto.createCipheriv('aes-256-gcm', key, iv)`. Or `chacha20-poly1305`.

### SEC6.4 — Hardcoded IV / salt / key

- `cipher = AES.new(key, AES.MODE_CBC, iv=b'1234567812345678')` — same IV for every encryption is catastrophic for CBC.
- `bcrypt.hashpw(password, salt='constant')` — defeats bcrypt's salting.
- Hardcoded encryption key in source (also SEC7).

**Fix:** generate IV from `secrets.token_bytes(16)` / `secureRandom.nextBytes(iv)`. Generate salt per record. Store keys in a secret manager.

### SEC6.5 — JWT misuse

- `jwt.decode(token, verify=False)` — covered in SEC1.5.
- `jwt.decode(token, key)` without `algorithms=[...]` — algorithm confusion.
- `algorithms: ['none']` accepted.
- HS256 with a public key (algorithm confusion: HS256 expects a secret, RS256 expects a public key).

### SEC6.6 — TLS misconfiguration

- `ssl.SSLContext(ssl.PROTOCOL_TLSv1)` — TLS 1.0 deprecated.
- `SSLContext.getInstance("TLSv1")` (Java).
- `TrustManager` that returns `null` / accepts all certs — disables validation entirely.
- `verify=False` on `requests.get()`.
- Node: `rejectUnauthorized: false`.

### False positives

- MD5 / SHA1 for cache keys / file checksums (not security). Fine.
- `Math.random()` for non-security randomness (animation, color jitter). Fine.

### Cross-refs

- SEC7 — hardcoded crypto material is also a secret leak.
- SEC1 — JWT misuse maps to both SEC6 (crypto) and SEC1 (auth).

---

## SEC7 — SECRETS

Credentials, keys, and tokens outside of secret-management.

### SEC7.1 — Hardcoded secret literal (must-fix)

**Antipatterns:**
- `const API_KEY = "sk_live_..."` (Stripe).
- `AWS_SECRET_ACCESS_KEY = "..."` (AWS access keys begin with `AKIA` or `ASIA`, 20 chars).
- `GITHUB_TOKEN = "ghp_..."`.
- Slack: `xoxb-` / `xoxp-` / `xoxa-`.
- Database URL with embedded password: `postgresql://user:realpassword@host/db`.
- Private key file content inline: `-----BEGIN RSA PRIVATE KEY-----`.

**Fix:** `process.env.API_KEY` / `os.environ['API_KEY']` / `@Value("${api.key}")`. Use a secret manager (AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager) for production.

### SEC7.2 — Committed `.env` file

- `.env`, `.env.local`, `.env.production`, `.env.development` tracked by git.

**Fix:** add to `.gitignore`; commit `.env.example` with placeholder values only.

### SEC7.3 — Token in URL

- `requests.get(f"https://api.example.com/?token={TOKEN}")` — tokens in URLs leak via referrer headers, server access logs, browser history.

**Fix:** pass via `Authorization` header.

### SEC7.4 — CI YAML with literal secret

- `.github/workflows/*.yml` containing `STRIPE_KEY: sk_live_...` instead of `STRIPE_KEY: ${{ secrets.STRIPE_KEY }}`.

### SEC7.5 — Runtime artifacts / lock files committed

- `.claude/scheduled_tasks.lock` (PID + timestamp).
- `.next/`, `.nuxt/`, `dist/`, `build/` tracked.
- `npm-debug.log`, `yarn-error.log`.

These don't leak literal secrets directly but they leak runtime state (PIDs, paths, sometimes env-var values via error dumps). Treat as SEC7.5 advisory.

### SEC7.6 — Secrets in code comments

- `// API key from staging: sk_test_...`
- Old debug code: `console.log("Connecting with", TOKEN)`.

### False positives

- `.env.example` with placeholder values (`SECRET_KEY=changeme`).
- Test fixtures: `password: "test1234"` in a `*.test.*` file.
- Documentation placeholders: `YOUR_API_KEY_HERE` in `*.md`.

### Cross-refs

- SEC6 — hardcoded crypto material.
- SEC8 — secrets pulled by `postinstall` scripts.

---

## SEC8 — SUPPLY-CHAIN

Dependency-graph trust.

### SEC8.1 — New dep with suspicious profile

**Signals (any one is yellow; combine for tier 1):**
- First-published date on registry < 3 months ago.
- Weekly download count very low.
- Name is a typo of a popular package: `request` vs `requests`, `python-dateutils` vs `python-dateutil`, `colors` vs `color`, `log4j-cor` vs `log4j-core`.
- `postinstall` / `preinstall` / `install` script (npm) or `cmdclass`-with-code (Python `setup.py`) — arbitrary code at install time.
- Publisher unknown / never previously seen.
- Package contains an obfuscated payload (long base64 strings in `index.js`).

### SEC8.2 — Non-registry dependency source

- `npm install` from a git URL without commit pinning.
- `pip install` from a git URL.
- Maven repository with `http://` (no TLS).
- `requirements.txt` with `-e git+https://...` (editable installs).

### SEC8.3 — Lockfile drift

- `package-lock.json` / `pnpm-lock.yaml` / `yarn.lock` / `Pipfile.lock` / `poetry.lock` change that introduces a package from a non-registry source unexpectedly.
- Lockfile missing entirely on a repo that should have one.

### SEC8.4 — Transitive vulnerability

- `npm audit` / `pip-audit` / `mvn dependency-check-maven` reports a high/critical CVE in a transitive dep.

### SEC8.5 — Peer-dep drift

- New dep declares incompatible peer dep that conflicts with existing graph — may force unsafe overrides.

### False positives

- A new dep from a trusted publisher (organization-tagged, > 1M downloads/week) with no postinstall — usually fine; advisory only.
- Internal monorepo deps via workspace: protocol — fine.

### Cross-refs

- SEC7 — postinstall script may steal secrets from env.

---

## SEC9 — PII / LOGGING

Personally identifiable information leaking through logs, analytics, error responses.

### SEC9.1 — PII in production logs (must-fix when at INFO/lower level)

**Antipatterns:**
- `console.log("User:", user)` where `user` is an object with `email`/`phone`/`ssn`.
- `logger.info(f"User: {user}")` (Python, with model `__repr__` exposing PII).
- SLF4J: `logger.info("user: {}", user)` where `user.toString()` includes PII.
- Java Lombok `@ToString` on a user entity without `exclude = {"email", "ssn"}`.

**Fix:** log the user ID only: `logger.info("user.action", { userId: user.id })`.

### SEC9.2 — Unredacted request/response logging

- Morgan / Pino HTTP middleware logging full body.
- Spring Boot `logging.level.org.springframework.web=DEBUG` in prod.
- Sentry / Bugsnag init without `send_default_pii=False` / scrub config.

### SEC9.3 — Analytics with PII

- `analytics.track('event', { email: user.email })`.
- Mixpanel / Segment / Amplitude with email/phone as identifying property when the destination doesn't have a PII-handling agreement.

### SEC9.4 — Error responses leaking PII

- 500 error returns full stack trace + request body to the client.
- Validation error reveals which field failed AND the user-provided value verbatim.

### SEC9.5 — Spring actuator over-exposure

- `/actuator/env` endpoint exposed without auth — leaks env-var values including secrets.
- `/actuator/heapdump` exposed.

### False positives

- Logging a user ID is fine and useful for tracing.
- Logging email at WARN/ERROR level for a specific user-impact event is sometimes acceptable; check team policy.

### Cross-refs

- SEC1.2 — IDOR often surfaces as PII leakage when an attacker views someone else's resource.

---

## SEC10 — RESOURCE-EXHAUSTION

Denial of service via resource consumption.

### SEC10.1 — ReDoS (catastrophic backtracking)

**Antipatterns:**
- Regex with nested quantifiers: `/^(a+)+$/`, `/^(\w+)*$/`, `/^(.*)+$/`.
- Alternation with overlapping subpatterns: `/(a|aa)+$/`.
- Greedy quantifiers around capturing groups followed by another quantifier.

**Fix:** rewrite without nested quantifiers; use atomic groups (some engines) or possessive quantifiers; run regex against user input with a timeout.

Test with safe-regex / re2 / a polynomial-time regex engine.

### SEC10.2 — Unbounded concurrency

- `Promise.all(items.map((u) => fetch(u)))` on an unbounded `items` list.
- `asyncio.gather(*[fetch(u) for u in untrusted_list])`.
- `items.parallelStream().map(...)` on user-list input.

**Fix:** bound concurrency with `p-limit` (Node), `asyncio.Semaphore` (Python), `ForkJoinPool` with explicit parallelism (Java).

### SEC10.3 — Missing request-size cap

- Express `app.use(express.json())` without `{ limit: '100kb' }` — default is 100kb but should be explicit; for upload routes, the limit must match expected payload, not just the default.
- FastAPI: no `Body(..., max_length=...)`.
- Spring: no `spring.servlet.multipart.max-file-size`.

### SEC10.4 — Missing rate limit on expensive endpoints

- Auth (login, password reset, signup) — credential stuffing surface.
- Search / GraphQL — query-complexity attacks.
- Email/SMS sending — billing surface.

**Fix:** rate-limit middleware (express-rate-limit, FastAPI-limiter, Spring Cloud Gateway).

### SEC10.5 — Large-file processing

- `JSON.parse(huge_string)` without size cap.
- Image processing with no max-dimension check (Pillow zip bomb).
- XML parser with entity expansion not limited.

### Cross-refs

- SEC11 — archive extraction is a resource-exhaustion vector too (zip bomb).

---

## SEC11 — PATH-TRAVERSAL / FILE-OPS

Filesystem access through user input.

### SEC11.1 — Path traversal (must-fix)

**Antipatterns:**
- `open(os.path.join(uploads_dir, request.GET['file']))` without normalization + boundary check.
- `pathlib.Path(uploads) / filename` where filename is user-controlled — `Path('..') / '..' / 'etc' / 'passwd'` escapes.
- `new File(uploadDir, userFilename)` (Java).
- `path.join(uploadDir, req.body.filename)` (Node).

**Fix:**
```python
safe_path = (Path(uploads_dir) / user_filename).resolve()
if not safe_path.is_relative_to(Path(uploads_dir).resolve()):
    raise ValueError("path escapes upload dir")
```

### SEC11.2 — Archive extraction (zip slip / tar slip)

- `zipfile.ZipFile.extractall(path)` — entries can contain `..` and escape.
- `tarfile.TarFile.extractall(path)` — same, plus symlink risk. On Python 3.12+, use `filter='data'`.
- Java: `new ZipInputStream(...)`'s entry-name loop without checking for `..`.

**Fix:** iterate archive entries; reject any entry name containing `..` or starting with `/` or with absolute Windows path components; resolve and verify each path is inside the target directory.

### SEC11.3 — Unsafe file operations

- `shutil.move(src, dst)` / `Files.move()` with user-controlled `dst`.
- Symlink following: `open(...)` on a path that resolves to a symlink pointing outside the expected directory.
- `os.chmod` on user-controlled paths.

### SEC11.4 — Filename sanitization

- Filenames with null bytes (`upload.pdf\x00.jpg`) — older code may truncate at null and treat as `.pdf`.
- Path separators in filename: `../etc/passwd`.
- Control characters.

**Fix:** allowlist characters (`[\w.-]+`), or generate UUID-based filenames server-side.

### Cross-refs

- SEC10 — zip bomb is a path/archive vector too.
- SEC2 — input validation primary defense.

---

## SEC12 — DESERIALIZATION / SSRF

Two related risk surfaces grouped for catalog brevity.

### SEC12.1 — Unsafe deserialization (must-fix)

**Antipatterns:**
- Python: `pickle.loads(bytes_from_user)` — RCE.
- Python: `yaml.load(yaml_str)` (without `Loader=SafeLoader`) — RCE via Python tags.
- Python: `marshal.loads()`, `shelve.open(user_path)`, `dill.loads()`.
- Java: `ObjectInputStream.readObject()` on untrusted input — gadget-chain RCE.
- Java: `XMLDecoder` for untrusted XML.
- Jackson polymorphic deserialization: `@JsonTypeInfo(use=Id.CLASS)` without allowlist.
- XStream: `XStream.fromXML(untrusted)` without `XStream.setupDefaultSecurity` + allowlist.
- Node: `eval(serialized)`, `Function(serialized)`.

**Fix:** use JSON with schema validation (Zod / Pydantic / Jackson `@JsonTypeInfo` with allowlist). For YAML, `yaml.safe_load`. For Python, prefer JSON over pickle for any cross-trust-boundary data.

### SEC12.2 — XXE (XML External Entity)

- `ElementTree.parse(user_xml)` — Python's stdlib XML is vulnerable to XXE.
- Java: `DocumentBuilderFactory.newInstance()` without `setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)`.

**Fix:** `defusedxml.ElementTree` (Python). For Java, set the disable-doctype feature.

### SEC12.3 — SSRF (must-fix)

**Antipatterns:**
- `requests.get(user_url)` server-side without scheme + host allowlist + private-IP block.
- `fetch(user_url)` server-side.
- Apache HttpClient: `HttpGet(userUrl)`.
- Java: `URL(userUrl).openConnection()`.
- `<image src={url}>` server-rendered to PDF generators (e.g., headless Chrome) — same risk.

**Fix:** allowlist scheme to `{http, https}`; resolve the host and check it's not in private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `169.254.0.0/16`, `fc00::/7`); fetch via a proxy that enforces the policy.

### SEC12.4 — Open redirect

- `response.sendRedirect(req.GET['next'])` without validating the destination.
- Frontend: `window.location = querystring.next`.

**Fix:** allowlist destination paths/hosts; default to `/` if validation fails.

### Cross-refs

- SEC2 — input validation is the primary defense for all SEC12 sub-rules.
- SEC10 — SSRF often combined with internal-service brute force = DoS.

---

## Quick-Reference Severity Mapping

| Finding ID | Tier 1 (must-fix) trigger | Tier 2 trigger |
|------------|----------------------------|----------------|
| SEC1 | Public state-changing route w/ no auth; IDOR | Missing rate limit on auth; session storage weakness |
| SEC2 | No schema validation, downstream sink is SQL/shell/template | Denylist instead of allowlist; partial validation |
| SEC3 | User-controlled string into SQL/shell/template/eval | ORM `.raw()` w/ partial trust; log injection on internal logs |
| SEC4 | User string in `dangerouslySetInnerHTML` / `|safe` / triple-brace | CSP missing but output-encoding present; markdown render w/o sanitization |
| SEC5 | `postMessage` no origin check; CORS `*` + credentials | CSP weak; iframe no sandbox on UGC routes |
| SEC6 | MD5/SHA1 for passwords; `Math.random` for tokens; JWT `none` | TLS 1.0 enabled; SHA-256 for passwords (better than MD5, still bad) |
| SEC7 | Literal API key / `.env` committed / CI YAML literal secret | Token in URL; secret in log line |
| SEC8 | Typosquat dep w/ postinstall; git-URL dep w/o pin | New dep < 3mo old; transitive CVE |
| SEC9 | Full user object logged at INFO; PII in analytics | Sentry init w/o PII scrub; session ID logged |
| SEC10 | Nested-quantifier regex on user input; unbounded `Promise.all` | Unbounded thread pool; no request body cap |
| SEC11 | Path-traversal-vulnerable upload handler; `extractall` w/o filter | Symlink-following ops; weak filename allowlist |
| SEC12 | `pickle.loads`/`ObjectInputStream`/SSRF unbounded; `eval(userInput)` | Jackson polymorphic w/o allowlist; XXE-vulnerable parser; open redirect |
