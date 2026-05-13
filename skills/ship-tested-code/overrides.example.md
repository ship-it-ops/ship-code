# Testing Overrides — Example

Copy this file to `overrides.md` (next to `SKILL.md`) or to `.claude/ship-tested-code-overrides.md` in your project root, then edit. Anything documented here supersedes the defaults in `SKILL.md` and `reference.md`.

> The skill loader reads override files in this order, with later files winning:
> 1. `SKILL.md` defaults
> 2. `overrides.md` (next to `SKILL.md`, team-wide)
> 3. `.claude/ship-tested-code-overrides.md` in the project root (project-specific)

---

## Test framework choices

- **Use `unittest` instead of `pytest`** in `services/legacy-billing/`. Migration to pytest is scheduled but not blocking PRs.
- **Vitest is the standard**, not Jest. Snapshot APIs and mock module syntax differ — flag Jest imports as T6 (maintenance).

## Coverage thresholds

- **Branch coverage floor is 85%** for `src/domain/` (business logic). Default 70% applies elsewhere.
- **No coverage requirement** for `src/migrations/` (DB schema migrations are tested via integration runs).

## Mocking policy

- **Allow `requests-mock` in `services/payment-gateway/`** as a transition off real-API tests. Goal is contract tests with Pact by Q4 — track in `tests/CONTRACTS_TODO.md`.
- **Mocking `Clock` is mandatory** anywhere a function reads `datetime.now()`. Catch as T2 (flaky) on review.

## Test data

- **Use `polyfactory` factories**, not the project-rolled `TestDataBuilder` helpers (deprecated).
- **Postgres TestContainers required** for any test importing from `db/`. SQLite in-memory is not equivalent.

## Disabled rules

- **Disable T7 (assertion style)** entirely — we use Hamcrest-style matchers and the lint rule produces false positives.

## Custom additions

- **Every PR touching `src/auth/` must include a regression test** referencing a security incident or threat-model entry.
- **E2E tests live in `e2e/`, are limited to 30**, and any new addition requires lead sign-off (see `e2e/POLICY.md`).
