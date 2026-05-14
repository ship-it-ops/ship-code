# Clean Code Overrides — Example

Copy this file to `overrides.md` (next to `SKILL.md`) or to `.claude/ship-clean-code-overrides.md` in your project root, then edit. Anything documented here supersedes the defaults in `SKILL.md` and `reference.md`.

> The skill loader reads override files in this order, with later files winning:
> 1. `SKILL.md` defaults
> 2. `overrides.md` (next to `SKILL.md`, team-wide)
> 3. `.claude/ship-clean-code-overrides.md` in the project root (project-specific)

Keep entries short — they should be one-liners with a brief justification.

---

## Naming

- **Allow Hungarian notation in COM interop code.** Files under `src/interop/` are exempt from rule N6 (encoding-free names) because Win32/COM types require the prefix convention.
- **Permit single-letter ML variables.** `X`, `y`, `W`, `b` are conventional in ML notebooks under `notebooks/`. Skip rule N1 there.

## Functions

- **Allow 5 arguments for HTTP request handlers.** Route handlers in `src/api/handlers/` may accept up to 5 args (request, response, params, body, context). Rule F1 (max 3 args) does not apply.

## Formatting

- **Line length is 100 characters, not 120.** Set by team agreement; configured in `pyproject.toml`.

## Disabled rules

- **Disable G24 (Follow Standard Conventions) for legacy module `src/legacy/`.** Scheduled for rewrite in Q3; do not flag.
- **Disable J1 (long imports).** Our IDE config auto-organizes; the rule produces noise.

## Custom additions

- **Require docstrings on all public functions** in `src/api/` and `src/sdk/`. We publish API docs from these.
- **Forbid `print()` and `console.log()` outside `scripts/` and `tests/`.** Production code must use the configured logger.
