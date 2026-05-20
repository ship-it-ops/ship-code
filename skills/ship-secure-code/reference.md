# Secure Code Reference

Methodology, sources, cross-cutting principles, and anti-overlap with sibling skills. The per-category rubric (antipatterns, fixes, false-positives) lives in `reference-categories.md`.

---

## 1. Methodology

### Threat modeling at review time

Every review begins with an implicit threat-model question: **what data crosses the trust boundary, and where does it land?** The reviewer maps:

1. **Sources** — points where untrusted data enters: HTTP request body/query/headers/cookies, file uploads, queue messages, environment variables, external API responses, browser `postMessage`, IPC, cross-origin form posts, browser-extension content scripts.
2. **Sinks** — places where untrusted data has security-relevant effect: SQL/NoSQL queries, OS commands, file paths, HTML output, JS evaluation, URL navigation, redirects, deserialization, regex evaluation, log lines, response bodies.
3. **Paths** — for each (source, sink) pair, whether the data flows directly, transformed, validated, or sanitized.

A finding fires when a source-to-sink path lacks an appropriate defense. Output format requires the path to be explicit.

### Severity is a function of two things

- **Reachability**: is the sink reachable from a source under attacker control? Internet-facing HTTP body → very reachable. Internal RPC from a trusted service → less reachable. Local dev script → not reachable. Severity scales with reachability.
- **Impact**: what does compromising the sink achieve? RCE > data exfiltration > information disclosure > denial of service. Severity scales with impact.

The skill's tier-1/tier-2/tier-3-5 split is the codification of these two axes. Tier-1 = reachable + high impact; tier-2 = secondary defense missing OR reachable but lower impact; tier-3-5 = hardening / depth.

### What gets reviewed, what doesn't

| Reviewed | Skipped |
|----------|---------|
| Application code (`*.py`, `*.ts`, `*.tsx`, `*.js`, `*.jsx`, `*.java`) | Generated code (`*.generated.*`, `*.pb.go`, files with `@generated` header) |
| Framework integration points (middleware, routers, ORM, view templates) | Vendored deps (`vendor/`, `node_modules/`, `third_party/`) |
| Build/CI files that touch security (`.github/workflows/*.yml`, `Dockerfile*`) | Pure styling, formatting, lint config |
| Schema/migration files (for IDOR-relevant column additions) | Binary blobs |
| Config files for security settings (`next.config.*`, `vite.config.*`, `application.properties`, etc.) | Lockfiles (read for supply-chain signal only, not full-text review) |
| Tests for security-relevant code (regression coverage check) | Documentation that doesn't contain code samples |

Skipped categories are noted in the Confidence section with counts.

---

## 2. The 12 categories — high-level boundaries

### SEC1 — AUTH

Owns: who-can-do-what. Covers AuthN (logged in) and AuthZ (allowed to access this resource), plus broken session management, over-privileged service accounts, IDOR/BOLA.

- **Tier 1**: Public endpoint with no auth check; authenticated endpoint without per-resource AuthZ check (IDOR); session token reuse without verification; service account with `*` permission.
- **Tier 2**: Missing rate-limiting on auth endpoints; weak password policy; session timeout too long; missing CSRF on state-changing routes (SEC5 cross-ref).
- **Tier 3-5**: Auth logging gaps; missing MFA support; missing account lockout.

Does NOT own: SC encryption misuse (SEC6), session-token storage in JS-accessible cookie (SEC5 origin), broken CSRF (SEC5).

### SEC2 — INPUT-VALIDATION

Owns: data crossing the trust boundary is parsed, validated, and normalized before use. Schema validation at the API boundary, type coercion with explicit failure handling, normalization (Unicode, path canonicalization).

- **Tier 1**: HTTP route accepts `req.body` and uses fields directly without `zod.parse` / Pydantic model / JSR-380 / Joi / Valibot.
- **Tier 2**: Validation exists but uses denylist patterns instead of allowlist; partial validation (some fields validated, some not).
- **Tier 3-5**: Validator error responses leak internal structure; validator slow path.

Cross-ref: SEC3 (injection) often co-occurs with missing SEC2. SEC4 (XSS) is the output-side analog.

### SEC3 — INJECTION

Owns: untrusted data interpreted as code by a downstream parser. The big category — covers SQL, NoSQL, OS command, LDAP, XPath, log, header (CRLF), template (SSTI), prototype pollution.

- **Tier 1**: User-controlled string interpolated into a query/command/template that gets parsed. The classic `db.query(f"SELECT * FROM x WHERE y = {user}")`.
- **Tier 2**: Parameterization present but partial (most queries parameterized, some not — code-quality drift but each unparameterized query is still tier-1).
- **Tier 3-5**: Defense-in-depth (parameterized queries + stored procedures), allowlist on column names.

### SEC4 — XSS / OUTPUT-ENCODING

Owns: untrusted data rendered to a browser without context-appropriate encoding. Covers reflected/stored/DOM XSS, `dangerouslySetInnerHTML`, raw HTML in slot/children props, `javascript:` URLs, unsafe `href`/`src`, unescaped template tags.

- **Tier 1**: User-controlled string rendered as HTML/JS without escaping; `<a href={userUrl}>` without scheme allowlist.
- **Tier 2**: Output-encoded but the template lib's default escape is off (`Jinja2(autoescape=False)`, `Handlebars` triple-braces in a partial); CSP missing but other defenses present.
- **Tier 3-5**: CSP not nonce-based; SRI missing on scripts.

### SEC5 — CSRF / ORIGIN

Owns: cross-origin trust. Covers CSRF (state-changing requests without origin verification), `postMessage` (browser cross-frame), iframe sandboxing, CSP origin clauses, CORS misconfig, cross-origin SSO.

- **Tier 1**: State-changing route without CSRF token AND served from the same origin as JS; `postMessage` handler without `event.origin` check; CORS `origin: '*' + credentials: true`.
- **Tier 2**: CSRF protection present but excluded for some paths; iframe without `sandbox` on a route that embeds user content; weak CSP.
- **Tier 3-5**: Missing `SameSite=Strict` cookies; `referrer-policy` not set.

### SEC6 — CRYPTO

Owns: cryptographic primitive misuse. Hash function choice for passwords; cipher/mode/padding selection; random source; key/IV/salt management; signature/HMAC verification.

- **Tier 1**: MD5/SHA1 for passwords; `Math.random()` for security tokens; `algorithms: ['none']` JWT; `verify=false` on JWT decode; AES-ECB; hardcoded IV.
- **Tier 2**: TLS protocol version too old (`TLSv1.0`); SHA-256 for password storage (better than MD5, still weaker than bcrypt/argon2); custom signature verification.
- **Tier 3-5**: Argon2 parameters too low; no key rotation strategy documented.

### SEC7 — SECRETS

Owns: credentials and key material outside of secret-management. Hardcoded API keys/tokens/connection strings; `.env` committed; tokens in URLs or logs; runtime artifacts (lock files, debug dumps) committed.

- **Tier 1**: Hardcoded API key with a recognizable prefix (`sk_live_`, `AKIA`, `ghp_`, `xoxb-`); `.env` (not `.env.example`) tracked; CI YAML with secret in plain text.
- **Tier 2**: Token in URL (visible in referrer/proxy logs); password in log line; AWS keys hardcoded in a "dev only" comment.
- **Tier 3-5**: No secret-rotation documentation; secrets not scoped to env (prod and staging share keys).

### SEC8 — SUPPLY-CHAIN

Owns: dependency-graph trust. New dep age, weekly downloads, typosquats, `postinstall` scripts, non-registry sources, peer-dep drift, transitive deps with known CVEs.

- **Tier 1**: New dep with `postinstall` script from an unknown publisher; dep pulled from a git URL without commit pinning; lockfile pulls a package from a non-registry source unexpectedly.
- **Tier 2**: New dep is very new (< 3 months on registry) with low download count; transitive dep has a known CVE in `npm audit`/`pip-audit`/`mvn dependency:tree`.
- **Tier 3-5**: Lockfile missing entirely; `^` range specifier on a security-sensitive dep.

### SEC9 — PII / LOGGING

Owns: personally identifiable information leaking through logs, analytics, error responses. Covers `console.log(user)`, unredacted request logging, analytics with PII fields, error logs containing fetched response bodies, Sentry without PII redaction.

- **Tier 1**: PII logged at INFO/DEBUG level in production code path; CSV export endpoint exposing email/SSN/DOB without authorization (also SEC1.1); analytics event tagged with email/phone.
- **Tier 2**: Sentry init without `send_default_pii=False`; logger redaction config missing fields (`authorization`, `cookie`, `set-cookie`); session ID logged.
- **Tier 3-5**: No retention policy documented for PII columns/logs; DEBUG logs may leak PII in non-prod.

### SEC10 — RESOURCE-EXHAUSTION

Owns: denial-of-service via resource consumption. ReDoS (catastrophic-backtracking regex), unbounded concurrency, missing request-size caps, missing rate limits, large-file extraction.

- **Tier 1**: Regex with nested quantifiers matched against user-controlled input; `Promise.all(items.map(fetch))` on unbounded `items`; no `bodyParser` size cap; no rate limit on auth/expensive endpoints.
- **Tier 2**: Thread pool unbounded; queue without capacity; pagination without `limit` cap.
- **Tier 3-5**: No request timeout configured; no circuit breaker.

### SEC11 — PATH-TRAVERSAL / FILE-OPS

Owns: filesystem access through user input. `path.join` without normalization + boundary check; archive extraction (zip slip / tar slip); symlink-following file ops.

- **Tier 1**: `open(os.path.join(dir, user_filename))` without normalize + `startswith(dir)` check; `tar.extractall()` without `filter='data'` on Python 3.12+; `zipfile.extractall()` without entry-name validation.
- **Tier 2**: `Files.move` with user-controlled destination; `shutil.move(src, dst)` with user dst.
- **Tier 3-5**: Missing `chroot`/`namespace`/`container` isolation around file ops.

### SEC12 — DESERIALIZATION / SSRF

Owns: two related risk surfaces — untrusted serialization (pickle/`ObjectInputStream`/YAML.load/Jackson polymorphic), and server-side request forgery (`fetch(userUrl)` server-side without allowlist + private-IP block). Also: XXE (XML external entity), open redirect.

- **Tier 1**: `pickle.loads(bytes_from_user)`; `ObjectInputStream.readObject()` on untrusted input; `requests.get(req.body.url)` without scheme allowlist + private-IP block; `XMLDecoder` for untrusted XML; `Function(userInput)`/`eval(userInput)`.
- **Tier 2**: Jackson polymorphic deserialization without allowlist; YAML.load with default loader; XXE-vulnerable parser config (`DocumentBuilderFactory` without `disallow-doctype-decl`); `response.sendRedirect(userUrl)` without host allowlist.
- **Tier 3-5**: Deserialization of trusted-but-old format without versioning.

---

## 3. Decision matrix (full)

Compute from the merged finding list:

| Condition | Decision (standalone run) | When invoked via ship-reviewed-prs SC delegation |
|-----------|---------------------------|--------------------------------------------------|
| Any tier-1 finding | `REQUEST_CHANGES` | Maps to SC1/SC2/SC3 (etc.) priority-1 at the parent level |
| Only tier-2 findings | `COMMENT` | Maps to SC*.3 (priority-3) at parent |
| Only tier-3-5 findings | `COMMENT` | Maps to SC*.5+ (priority-5+) at parent |
| Zero findings | `APPROVE` (or `NO_FINDINGS`) | SC persona reports clean |

The skill never APPROVEs on a tier-1 finding regardless of overrides. `ci_max_decision: COMMENT` is honored for parent-skill submission but the skill's own report still names the finding as Critical.

---

## 4. Cross-cutting principles (expanded)

### 4.1 Input validation: where to validate

Validate at the **trust boundary** — typically the HTTP request handler / queue consumer / file upload endpoint / cross-origin message receiver. Validate exactly once, with a schema (Zod / Pydantic / JSR-380 / Joi / Valibot). Downstream code consumes the validated, narrowly-typed value, not the raw input.

Common mistakes:
- Validating in the service layer instead of the controller — the validator runs twice in some paths and zero times in others.
- Re-validating in the database layer "just in case" — defense-in-depth in theory, but in practice the second validator drifts and produces inconsistencies.
- Validating only the fields the current code path uses — adding a new field next year picks up unvalidated data from the same input.

Rule: schema validation at the boundary, with `strict()` / `forbid_extra_keys()` / `additionalProperties: false`. New fields are explicit, not implicit.

### 4.2 Output encoding: where to encode

Encode at the **output sink**, using the encoding appropriate for the sink:
- HTML output → HTML-encode (most templates do this automatically; the failure mode is `|safe`/`{{{}}}`/`dangerouslySetInnerHTML`).
- SQL → parameterize (not "escape").
- Shell → don't shell out; if you must, pass args separately.
- URL → use the framework's URL builder; if you can't, percent-encode.
- Log line → newline-strip (`replace('\n', '\\n')`) to prevent CRLF log injection.
- Header value → newline-strip + scheme/value allowlist.
- Filename → strip path separators + null-byte + control characters.

### 4.3 Defense in depth: when one layer isn't enough

The "principle of layered defenses" sounds vague but means something specific: each layer mitigates a different failure mode. CSP mitigates inline-script execution if output encoding fails. Output encoding mitigates XSS if input validation accepts a string that turns out to be HTML. Input validation mitigates everything downstream when it works.

Findings:
- **Two layers present, one weak** → tier 2 (the weak layer should be fixed).
- **One layer present** → tier 1 (especially if it's the input-validation layer, which is the easiest to bypass with a novel attack).
- **No layers** → tier 1, capital letters.

### 4.4 Fail closed

On error, deny. Specifically:
- Auth verification throws → return 401, do NOT continue with `user = null`.
- Signature verification throws → reject the request, do NOT log and continue.
- Allowlist lookup misses → reject, do NOT fall through to default.
- Permission check returns ambiguous (database error during permission lookup) → deny, do NOT grant.

The catch-and-continue antipattern is one of the most common security bugs in code that *looks* defended.

### 4.5 Least privilege at every layer

- Database users: per-service accounts with table-level grants, not `GRANT ALL`.
- Service accounts (cloud IAM): per-task roles, not broad ones.
- Container/process: non-root user, read-only root filesystem, dropped capabilities.
- Frontend JS access: cookies marked `HttpOnly` and `Secure` and `SameSite=Strict` (or `Lax` with justification).
- File-system: dedicated upload directory, no shell access, no write access to code.

SEC1 owns this; findings reference the specific layer.

---

## 5. Anti-overlap with sibling skills

### vs. `ship-clean-code` P2-SEC

`ship-clean-code` has a P2-SEC tier covering "obvious" security (SQL string concatenation, hardcoded secrets, missing auth on new endpoint). It's the surface-level check; this skill is the depth target. The boundary:

- `ship-clean-code` P2-SEC: detection-only, single-line patterns, generic framing ("looks like SQL injection"). Suitable as a fast pass during normal code review.
- `ship-secure-code`: full SECn rubric, data-flow trace, framework-specific patterns, defense-in-depth check. Suitable when security is the primary goal.

On overlap, ship-secure-code wins. The two should not be run together as a redundant pass; ship-clean-code defers to ship-secure-code when invoked, per its `SKILL.md:230` Related Skills section.

### vs. `ship-tested-code`

Security review surfaces test gaps as **advisory** findings:
- New auth handler has no test for the unauthenticated path → advisory.
- Regex with potential ReDoS has no test for malicious input → advisory.

The skill does not write tests. It points at the gap and delegates depth to `ship-tested-code`.

### vs. `ship-reviewed-prs`

`ship-reviewed-prs` SC persona is the **detection** orchestrator: it scans the diff with high-precision regex patterns for SC1-SC7 hits, then delegates depth to this skill. Specifically:
- Hits that the SC orchestrator emits directly (high-confidence single-line patterns): hardcoded secret literal, `dangerouslySetInnerHTML` with `userInput`, `eval(userInput)`, missing auth middleware on new route.
- Hits that the SC orchestrator turns into a delegation bullet: anything requiring data-flow trace, framework knowledge, or multi-file context.

The delegation is one-way: `ship-reviewed-prs` SC → `ship-secure-code`. Running `ship-secure-code` does not back-invoke `ship-reviewed-prs`.

### vs. `ship-debugged-code`

When a security CVE is being fixed, run `ship-debugged-code` to design the regression test, then `ship-secure-code` to review the fix. The two don't conflict; they sequence.

---

## 6. Triage: file-bucketing for the skill

When invoked on a directory or PR diff, classify files first:

| Bucket | Heuristic | Action |
|--------|-----------|--------|
| `code-security-relevant` | Touches auth/crypto/input-handling/output-rendering | Full review |
| `code` | Application code, not obviously security-touching | Quick scan for SEC3/SEC4/SEC7 hits |
| `config-security-relevant` | `next.config.*`, `middleware.ts`, `Dockerfile*`, `*.yml` for CI | Full review |
| `infra-security-relevant` | IAM, network ACLs, security groups | Full review |
| `test` | Test files | Light scan — used to verify regression coverage on security findings |
| `docs` | Markdown, RST | Scan for leaked secrets/URLs only |
| `generated`, `vendor` | Excluded | Skip; count in Confidence |
| `lockfile` | `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `Pipfile.lock`, `poetry.lock`, `Cargo.lock` | Read for supply-chain signal (SEC8) |

---

## 7. Output schema (machine-readable, for delegation)

When invoked from `ship-reviewed-prs`, the skill returns a structured object:

```json
{
  "scope": "packages/api/src/users.ts",
  "summary": {
    "tier_1": 2,
    "tier_2": 1,
    "tier_3_5": 0
  },
  "findings": [
    {
      "id": "SEC3.1-INJECTION-SQL",
      "tier": 1,
      "path": "packages/api/src/users.ts",
      "line": 42,
      "source": "req.body.email (untrusted, HTTP)",
      "sink": "db.query template literal (SQL parser)",
      "data_flow": "req.body.email → email variable → query string interpolation",
      "fix": "db.query('... WHERE email = $1', [email])"
    }
  ],
  "what_good": [
    "Parameterized queries used in 8/9 places",
    "JWT verify includes algorithms allowlist"
  ],
  "confidence": "Reviewed 1 file (220 lines). Skipped node_modules/ (vendor). Trust boundary identified as Express route handlers."
}
```

The parent skill maps this into its own decision matrix.

---

## 8. Quick-Reference Checklist

| Area | Key Question |
|------|--------------|
| Trust boundary | Did I identify every place untrusted data enters? |
| AuthN | Does every non-public route require a logged-in user? |
| AuthZ | Does every per-resource route check ownership/tenant? |
| Input validation | Is there a schema at the boundary that fails on extra/wrong-typed fields? |
| Output encoding | Is data context-encoded at every output sink (HTML, SQL, shell, header, URL, log)? |
| CSRF/origin | Are state-changing requests authenticated AND origin-verified? |
| Crypto | Are passwords hashed with bcrypt/argon2, signatures verified, RNG from `secrets`/`SecureRandom`? |
| Secrets | Are all credentials in env vars / secret manager, not the repo? |
| Supply chain | Are new deps verified (age, downloads, postinstall, source)? |
| PII | Are logs/analytics free of email/phone/SSN/session tokens? |
| Resource | Are regex/loops/uploads/queries bounded? |
| Path | Is every file path normalized and constrained to an expected directory? |
| Deserialization | Is every parser using a safe loader / allowlist? |

---

## 9. Sources

- **OWASP Top 10** (2021). The 10 categories map roughly to SEC1-SEC4 plus parts of SEC6/SEC7/SEC9/SEC11/SEC12. We split injection, XSS, CSRF, and IDOR into separate IDs because they need separate detection logic.
- **OWASP API Security Top 10** (2023). Source for the SEC1 emphasis on AuthZ-not-AuthN (BOLA/BOPLA is API1/API3 in that list).
- **OWASP ASVS** (Application Security Verification Standard) v4. Source for the tier definitions and the "trust boundary" framing.
- **CWE Top 25** (2024). Source for SEC10 (CWE-1333 ReDoS), SEC11 (CWE-22 path traversal), SEC12 (CWE-502 deserialization, CWE-918 SSRF).
- **MDN Web Security** — XSS contexts, CSP, postMessage origin patterns.
- **Building Secure and Reliable Systems** — Adkins et al. (Google, 2020). Source for the layered-defense and fail-closed framing.
- **The Tangled Web** — Michal Zalewski (2011). Source for browser-trust-model patterns (SEC5).
- **Cryptography Engineering** — Ferguson, Schneier, Kohno (2010). Source for the SEC6 primitive-choice rubric.
- **PortSwigger Web Security Academy**, **HackerOne disclosed reports**, **GitHub Security Lab advisories** — modern attack patterns, language-specific gadgets.

The skill's specific organization (12-category catalog, tier sub-tags, data-flow-trace output requirement) is original to this repo and chosen for review legibility.
