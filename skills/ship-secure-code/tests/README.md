# Self-Test Fixtures — ship-secure-code

These fixtures are regression checks for the skill. Each fixture provides a synthetic vulnerable code sample and the expected security review.

## How to use

1. Open Claude Code with the skill installed.
2. Paste the fixture's `input.md` content as the user message.
3. The skill should produce output substantially matching `expected-output.md`.

Minor wording differences are fine. Watch for: missing tier-1 findings, wrong SEC category attribution, wrong tier, missing data-flow trace, missing "What's Good" section.

## Fixtures

| Fixture | What it tests |
|---|---|
| `fixture-1-xss` | SEC4.1 stored XSS in a React component rendering unsanitized user content via `dangerouslySetInnerHTML`; data-flow trace from API response through prop to render sink. |
| `fixture-2-sqli` | SEC3.1 SQL injection in an Express handler using template-literal query construction; tier-1; expected fix uses parameterized `pg` driver call. |
| `fixture-3-missing-authz` | SEC1.2 IDOR in a Next.js App Router `route.ts` that fetches a resource by id without tenant/owner filtering. AuthN is present; AuthZ is the gap. |
