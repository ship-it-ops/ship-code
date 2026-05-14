# Debugging Overrides — Example

Copy this file to `overrides.md` (next to `SKILL.md`) or to `.claude/ship-debugged-code-overrides.md` in your project root, then edit. Anything documented here supersedes the defaults in `SKILL.md` and `reference.md`.

> The skill loader reads override files in this order, with later files winning:
> 1. `SKILL.md` defaults
> 2. `overrides.md` (next to `SKILL.md`, team-wide)
> 3. `.claude/ship-debugged-code-overrides.md` in the project root (project-specific)

---

## Incident response

- **Use the company-standard postmortem template** at `docs/postmortems/TEMPLATE.md` instead of the freeform format suggested in `reference.md` §10.
- **Severity policy**: SEV-1 incidents block all other work until resolved; SEV-2 within 24h; SEV-3 by end of sprint. Defined in `docs/oncall/SEVERITY.md`.
- **Blameless language is mandatory.** Any postmortem with names assigned to causes (not action items) gets blocked at review.

## Reproduction expectations

- **Production data may be replayed in `staging-shadow` environment.** Anonymization tooling is at `tools/anonymize/`. Never load raw prod data into a developer laptop.
- **Cypress is the only sanctioned tool for capturing frontend repros.** Save the trace under `e2e/repros/` and link it from the bug ticket.

## Debugger / tooling specifics

- **PyCharm Pro is the standard Python debugger.** VS Code's Python debug adapter has been unreliable with our async stack; expect setup help from #dev-experience.
- **Datadog APM is the source of truth for distributed traces.** Do not rely on application logs alone for cross-service debugging.
- **Sentry is the error tracker.** Source maps must be uploaded via the CI step (see `.github/workflows/deploy.yml`).

## Disabled / softened rules

- **Disable D7 (Documentation) for hotfixes during active incidents.** The full writeup happens in the postmortem; the commit can be terse to ship fast.
- **Relax D4 (regression test) for one-line config changes.** A regression test for "the timeout was 5s and should be 30s" is low-value churn.

## Custom additions

- **Every fix touching `payments/` must include a chaos-test scenario.** See `tests/chaos/payments/README.md` for the format.
- **Cross-team incidents (>1 team affected) require a coordination doc opened in `incidents/`** before the fix is merged.
- **Database hotfixes require a peer-pair attestation** — at least one other engineer must explicitly approve in the PR body, not just the PR review.
