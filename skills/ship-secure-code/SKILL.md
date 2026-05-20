---
name: ship-secure-code
description: >
  Apply application-security principles (auth, input validation, injection,
  XSS/output encoding, CSRF/origin, crypto, secrets, supply chain, PII/logging,
  resource exhaustion, path traversal, deserialization/SSRF) when writing or
  reviewing security-sensitive Python, TypeScript/JavaScript, or Java code.
  Invoke explicitly for security reviews or as the delegation target from
  ship-reviewed-prs SC persona. Do not invoke for pure styling, shell scripts,
  one-off prototypes, or non-security code review (use ship-clean-code).
allowed-tools: Read, Grep, Glob
---

# Secure Code Skill

## Purpose

This skill applies application-security principles to help you write code that resists the OWASP Top 10 + CWE Top 25 attack classes and to review existing code for the same. It operates in **review mode** only — it does not auto-remediate vulnerable code. (Auto-remediation will be added in a future version once the rule set is proven; producing patches for security bugs without a human in the loop is a footgun.) Sibling skills handle non-security concerns: `ship-clean-code` (file quality), `ship-tested-code` (test design), `ship-debugged-code` (root cause), `ship-reviewed-prs` (PR-level orchestration).

## Quickstart (New to Application Security?)

Start with these 3 rules and internalize them before learning the rest:

1. **Trust nothing from outside the trust boundary.** Validate, sanitize, and encode at every system edge — HTTP body, URL, header, file upload, database row, message-queue payload, environment variable, external API response, cookie, postMessage. The skill flags every place data crosses the boundary without validation.
2. **Allowlist beats denylist.** Define what's allowed; reject everything else. A regex that bans `"javascript:"` will be defeated; one that requires `^https?://` won't.
3. **Defense in depth.** No single layer is enough. Even when one defense (CSP, auth middleware, ORM parameterization) is present, an adjacent layer (input validation, output encoding) must also do its job. The skill explicitly checks for missing depth, not just missing primary controls.

The detailed reference files (`reference.md`, `reference-categories.md`) assume familiarity with OWASP Top 10 and the language-specific framework conventions.

## Mode Detection

- **Review mode** (default and currently only mode): Read the target code, analyze against the 12-category rubric below, produce a structured report. Never edit code, never produce patches except as advisory snippets in the report.
- **Triggered explicitly** by: `/ship-secure-code <path|file>`, "security review", "secure code review", "audit this for security", or invocation from `ship-reviewed-prs` SC delegation.

If asked to *write* security-sensitive code (e.g., new auth handler, new crypto wrapper, new input validator), the skill does not apply directly — use `ship-clean-code` with security context, then run this skill to review the output. We separate write from review intentionally: a single mode that does both tends to produce code that looks defended (long, lots of try/catch, lots of validation) without actually being defended.

## Core Principles - Always Apply

These 12 rules apply to ALL security review:

### 1. Trust boundary first.
Identify the trust boundary before reading the code. Anything crossing it (HTTP input, file upload, queue message, env var, external API response, cookie, postMessage payload, IPC) is untrusted. All findings hang off this map. If the code under review doesn't make the boundary explicit, that's the first finding.

### 2. Allowlist, not denylist.
Validators must enumerate what's allowed and reject everything else. A regex that excludes known-bad input is a denylist; rewrite or reject.

### 3. Sanitize at output, not input.
Input validation rejects malformed data. Output encoding makes data safe for the context it lands in (HTML, SQL, shell, header, URL, log). Both are required. If only input validation is present, the code is one input-channel away from compromise.

### 4. Authentication ≠ Authorization.
A user being logged in (AuthN) doesn't mean they have permission for the resource (AuthZ). IDOR/BOLA is the most common security bug: an endpoint that requires login but doesn't check whether the requested resource belongs to the requesting user. SEC1 fires on both.

### 5. Secure defaults.
Choose libraries and configurations that are secure by default. Bcrypt over SHA-256, parameterized queries over string concat, `secrets.token_urlsafe` over `Math.random()`. The skill flags code that opts out of secure defaults without justification.

### 6. Defense in depth.
Even when a primary control is present, an adjacent layer must also work. CSP plus output encoding plus input validation; auth middleware plus per-resource AuthZ plus rate limiting. The skill checks the secondary layer explicitly.

### 7. Least privilege.
Every component (process, service account, IAM role, database user, container) runs with the minimum permissions needed. Findings on over-privileged access live under SEC1.

### 8. Fail closed.
On error, deny access. A try/catch that swallows an auth failure and continues is worse than no try/catch. Same for crypto verify failures, signature checks, allowlist lookups.

### 9. No DIY crypto.
Use the language's standard library or a vetted package (bcrypt, argon2, NaCl, Web Crypto API). Never roll your own cipher, hash construction, or MAC. The skill flags any code under `crypto/` or `security/` that constructs primitives by hand.

### 10. Secrets never in code.
Hardcoded credentials, API keys, tokens, certificates, and connection strings are categorically wrong. SEC7 fires on any literal that matches secret patterns regardless of context.

### 11. Severity is mechanical from finding ID.
SECn.1 findings (must-fix) block merge. SECn.2 findings (should-fix) ship with mitigation plans. SECn.3-5 are advisory. The skill computes tier from the finding ID and the surrounding context (user-controlled input vs. trusted-internal); no LLM negotiation.

### 12. Surface confidence, not opinion.
Include a Confidence section naming what was reviewed, what was not (binaries, generated code, vendored deps), and what's the residual risk. A confident "must fix" pairs with the specific data-flow path that drove the finding.

## The 12-Category Catalog

| ID | Label | Covers | Tier-1 examples (must-fix) |
|----|-------|--------|----------------------------|
| SEC1 | AUTH | Missing AuthN; missing AuthZ on routes; IDOR (missing tenant/owner checks); broken session handling; over-privileged service accounts | Admin route with no auth middleware; `Model.findById(id)` without tenant filter; `jwt.decode(token, verify=False)` |
| SEC2 | INPUT-VALIDATION | Missing parameterization, allowlist patterns, schema validation at boundary | HTTP route accepting `request.body` without `zod.parse` / Pydantic / JSR-380 |
| SEC3 | INJECTION | SQL, NoSQL, OS command, LDAP, XPath, log, header, template (SSTI), prototype pollution | `db.query(f"... {id}")`; `subprocess.run(cmd, shell=True)`; `Object.assign({}, untrusted)` |
| SEC4 | XSS / OUTPUT-ENCODING | `dangerouslySetInnerHTML`; raw HTML in `children`/slot; `javascript:` URLs; unsafe `href`; unescaped Handlebars/EJS/Jinja | `<div dangerouslySetInnerHTML={{__html: userInput}} />`; `{{{userBio}}}` |
| SEC5 | CSRF / ORIGIN | Missing CSRF token; `postMessage` without origin check; iframe without `sandbox`; weak CSP; CORS `*` + `credentials: true` | `window.addEventListener('message', handler)` with no `event.origin` check; `app.use(cors({origin: '*', credentials: true}))` |
| SEC6 | CRYPTO | MD5/SHA1 for passwords; deprecated ciphers; `algorithms: ['none']` JWT; `Math.random()` for security; hardcoded IV; ECB mode | `hashlib.md5(password)`; `Cipher.getInstance("AES")` (ECB default) |
| SEC7 | SECRETS | Hardcoded keys; committed `.env`; token in URL; runtime/lockfile leakage | `const API_KEY = "sk_live_..."`; `.env` not gitignored; `requests.get(f"...?token={TOKEN}")` |
| SEC8 | SUPPLY-CHAIN | New dep age/downloads; `postinstall` scripts; non-registry lockfile sources; peer-dep drift; typosquats | New pkg added 2 weeks ago with `postinstall`; `request` vs `requests` typo |
| SEC9 | PII / LOGGING | `console.log(user)`; unredacted request logging; analytics with PII; error logs leaking response bodies | `logger.info("user: %s", user)` where `user` includes email/SSN |
| SEC10 | RESOURCE-EXHAUSTION | ReDoS (nested-quantifier regex); unbounded `Promise.all`; missing rate limits; missing body-size caps | `/^(a+)+$/`; `Promise.all(items.map(fetch))` on untrusted list |
| SEC11 | PATH-TRAVERSAL / FILE-OPS | `path.join` with user input; `../` not validated; archive extraction (zip slip) | `open(os.path.join(dir, req.body.filename))`; `tar.extractall()` without filter |
| SEC12 | DESERIALIZATION / SSRF | `pickle.loads`/`eval`/`Function`; `fetch(userControlledUrl)`; open redirect; XXE | `pickle.loads(req.body)`; `requests.get(req.GET['url'])` without allowlist |

Full per-category rubric — antipatterns, canonical fixes, false-positive notes, cross-references — lives in `reference-categories.md`.

## Severity Tiers

Each finding ID has a tier sub-tag computed from the data-flow context:

- **Tier 1 (must-fix, REQUEST_CHANGES)** — user-controlled input reaches a dangerous sink with no validation/escaping. The textbook OWASP scenario. Blocks merge.
- **Tier 2 (should-fix, COMMENT)** — secondary defense missing where a primary defense exists, OR the dangerous sink is reachable only via trusted-internal input. Ship with mitigation plan.
- **Tier 3-5 (advisory, COMMENT)** — defense-in-depth suggestions, hardening, telemetry gaps.

The full tier definitions per finding ID are in `reference-categories.md`.

## Decision Matrix

| State | Decision |
|-------|----------|
| Any unsuppressed *.1 (must-fix) finding | `REQUEST_CHANGES` |
| Only *.2 findings | `COMMENT` |
| Only *.3-*.5 findings | `COMMENT` |
| Zero findings | `APPROVE` (or `NO_FINDINGS` when run standalone) |

`ship-secure-code` does not have its own submission semantics — when run standalone, it produces a structured report. When run as the delegation target from `ship-reviewed-prs`, the parent skill maps the report to its own decision matrix (SECn.1 → SC1-AUTH-MISSING/SC2-INJECTION/etc. severity).

## Review Output Format

```
## Security Review: [scope]

### Confidence
<2-4 sentences: trust boundary identified, what was reviewed, what was not
reviewed (binaries, vendored deps, generated code), residual risk.>

### Critical (must fix before merge)
- **[SEC3.1-INJECTION] api/users.ts:42**: <data flow path: source → sink>. → <fix>.
- **[SEC1.1-AUTH-MISSING-AUTHZ] api/orders.ts:18**: <description>. → <fix>.

### Important (should fix)
- **[SEC10.2-REDOS] utils/parser.ts:55**: <regex>. → <fix>.

### Advisory (defense in depth)
- **[SEC5.4-MISSING-CSP] middleware.ts:8**: <description>. → <fix>.

### What's Good
- <substantive observation about a defense done well — not boilerplate>
```

Rules for the output:
- Include the **data flow path** for every Critical finding: identify the source (where untrusted data enters) and the sink (where it lands without protection). A finding without a source-to-sink trace is not actionable.
- Tag every finding with its full ID (`SECn.t-LABEL`) — tier is part of the ID, not a separate field.
- Specific file:line every time.
- "What's Good" is mandatory. Name the defenses that exist (parameterized queries, auth middleware present, CSP configured) so the author trusts the negative findings.
- More than 10 findings: top 10 strictly ordered by severity. Never suppress a tier-1 finding due to the cap.

## Pragmatism Guidelines

- **Test fixtures with fake credentials are OK.** `password: "test1234"` in a `*.test.*` file under the `test` bucket isn't SEC7 if the variable name signals test usage and the file path is a test path.
- **Documented placeholders in markdown are OK.** `YOUR_API_KEY_HERE` in `*.md` is not SEC7.
- **Dev-only code is held to a lower bar.** Code under `scripts/`, `tools/`, `dev/` that explicitly says "dev only" gets advisory-tier findings only — no blocking findings on convenience scripts.
- **Match team conventions.** If the override file disables a category (e.g., the repo has no DB so SEC1's IDOR sub-rule is N/A), respect it.
- **MD5 for non-security checksums is fine.** `crypto.createHash('md5')` on a file content for cache-key purposes is not SEC6. Check the surrounding semantic.
- **Trust signals from the PR description.** If the author wrote "Known issue: X is out of scope, tracked in #N," do not re-flag X.

## Working with Existing Vulnerabilities

If the code under review *already* contains an old vulnerability not introduced by this PR/diff:
- Note it in Advisory tier with a `(pre-existing)` marker.
- Do not block the current PR on it.
- Recommend opening a separate issue.

Newly-introduced vulnerabilities (this PR adds them) are full-tier per the matrix.

## Team Overrides

Before applying security rules, check for override files in this order:

1. `overrides.md` next to this `SKILL.md` (team-wide overrides bundled with the skill)
2. `.claude/ship-secure-code-overrides.md` in the user's project root (project-specific overrides)

Use overrides for:
- Disabled categories (e.g., a repo with no DB doesn't need SEC11 path-traversal depth).
- Severity overrides (e.g., escalate SEC8 to tier 1 for highly-regulated codebases).
- Extra secret patterns (e.g., your org's internal key prefixes).
- Ignored paths.

A template is at `overrides.example.md`.

## Team Adoption

Phased rollout recommended:
- **Weeks 1-4**: Enable SEC1, SEC3, SEC4, SEC7 only — the OWASP-Top-10 core. Build the review habit. Most teams ship at least one of these per quarter.
- **Month 2**: Add SEC2, SEC5, SEC6, SEC11, SEC12 — the broader injection / output-encoding / file-ops surface.
- **Month 3+**: Full SEC1-SEC12. Add SEC8 (supply chain), SEC9 (PII), SEC10 (DoS).

Track: tier-1 findings per PR (should trend toward zero); false-positive rate per category (if any category fires noisily, demote it via overrides).

## Related Skills

- **`ship-reviewed-prs`** — PR-level orchestrator. Its SC persona delegates to this skill for depth. When working a PR end-to-end, run `ship-reviewed-prs` first; it will tell you which files to run this skill on.
- **`ship-clean-code`** — File-level code-quality review (naming, SRP, error handling). P2-SEC is its surface-level security check; this skill is the depth target. Run clean-code first to fix structure, then run secure-code to find vulnerabilities.
- **`ship-tested-code`** — Test design. Security fixes need regression tests; secure-code reviews flag missing tests as advisory, then defer to tested-code.
- **`ship-debugged-code`** — Use when a security bug is being fixed and you want a regression test designed around the root cause.

## Reference Loading

For deeper analysis, load supporting reference files alongside this `SKILL.md`:

- `reference.md` — Methodology, sources (OWASP Top 10, ASVS, CWE), cross-cutting principles, anti-overlap with sibling skills.
- `reference-categories.md` — SEC1-SEC12 deep rubric: antipatterns, canonical fixes, false-positive notes, cross-references.
- `lang-python.md`, `lang-typescript.md`, `lang-java.md` — Language-specific patterns for each SEC category.
- `examples/review-example.md` — End-to-end review output sample on a vulnerable Next.js + Express app.
- `examples/fix-example.md` — Walkthrough of a single finding from identification through fix and test.
- `tests/` — Self-test fixtures (sample vulnerable input + expected report).

Paths are relative to this `SKILL.md`. Load on-demand when doing thorough reviews or when the user asks for detailed guidance on a specific topic.
