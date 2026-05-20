# Secure Code Overrides — Example

Copy this file to `overrides.md` (next to `SKILL.md`) or to `.claude/ship-secure-code-overrides.md` in your project root, then edit. Anything documented here supersedes the defaults in `SKILL.md`, `reference.md`, and `reference-categories.md`.

> The skill loader reads override files in this order, with later files winning:
> 1. `SKILL.md` defaults
> 2. `overrides.md` (next to `SKILL.md`, team-wide)
> 3. `.claude/ship-secure-code-overrides.md` in the project root (project-specific)

Format is loose `key: value` or `key: [list]`. The skill reads override files as plain text and pattern-matches keys.

---

## Disabled categories

For repos that genuinely don't have a category's surface (e.g., no database = no SEC1.2 IDOR concerns):

```
sec_disabled_categories: [SEC8]    # we handle supply-chain in a dedicated CI job
```

For finer control, disable specific sub-rules:

```
sec_disabled_rules:
  - SEC9.5    # actuator exposure handled by network policy
  - SEC8.5    # peer-dep drift — we use overrides intentionally
```

The skill still scans these but never emits findings.

---

## Severity overrides

Escalate categories for highly-regulated codebases:

```
sec_escalate: [SEC8]    # supply-chain CVEs are tier 1 for us (HIPAA-adjacent)
sec_escalate: [SEC9]    # PII handling is tier 1 (financial data)
```

Demote categories for low-risk codebases:

```
sec_demote: [SEC8]      # internal-only tools repo, supply-chain risk is lower
```

---

## Extra secret patterns

Your organization's internal key prefixes:

```
sec_extra_secret_patterns:
  - "acme_sk_[A-Za-z0-9]{32}"    # internal Acme API keys
  - "acme_int_[A-Za-z0-9-]{40}"  # internal service tokens
```

Pattern matching is regex; the skill flags any literal that matches.

---

## Ignored paths

```
sec_ignored_paths:
  - "src/migrations/legacy/"     # frozen module, no new work
  - "scripts/dev-only/"          # local dev scripts, never deployed
  - "examples/"                  # example code, intentionally simple
```

Findings in these paths are skipped entirely.

---

## Test fixture allowances

By default, files in the `test` bucket get a pass on hardcoded fake credentials. Configure additional patterns:

```
sec_test_fixture_paths:
  - "tests/fixtures/"
  - "**/*.fixture.ts"
  - "spec/integration/"

sec_test_fixture_secret_allowlist:
  - "test1234"
  - "fakeKey"
  - "00000000-0000-0000-0000-000000000000"   # nil UUID used in tests
```

---

## Trust-boundary overrides

Mark internal services as trusted (no SEC1/SEC2 enforcement on the boundary):

```
sec_internal_service_paths:
  - "src/services/internal-rpc/"    # auth handled at the mesh layer
```

Use sparingly — most "internal" services are reachable from somewhere unintended.

---

## Framework-specific notes

```
sec_framework: nextjs-app-router        # the skill tunes Next.js-specific patterns
sec_framework: spring-boot
sec_framework: fastapi
```

If multiple frameworks coexist, list them:

```
sec_framework: [nextjs-app-router, fastapi]
```

---

## Reporting tuning

```
sec_findings_cap: 15    # default: 10 — show more findings before summarizing
sec_include_what_good: true    # default: true — set false for terse output
```

---

## Custom rules

Team-specific concerns appended to the rubric. Each rule maps to an existing SEC category and severity tier.

```
sec_custom_rules:
  - id: SEC1.X-CUSTOM
    description: "Any new endpoint under /api/internal/ must have @InternalOnly annotation. Tier 1."
    fire_on: "new route under /api/internal/ lacking @InternalOnly"
  - id: SEC7.X-CUSTOM
    description: "Any literal matching /acme_dbg_[a-z]{8}/ is a debug-only token. Tier 2."
    fire_on: "regex match in production code"
```

---

## CI-mode tuning

When invoked from `ship-reviewed-prs` SC delegation:

```
sec_max_delegation_decision: REQUEST_CHANGES   # default: full matrix
sec_inline_comment_categories: [SEC1, SEC3, SEC4, SEC7]   # which findings post as inline GitHub comments
```
