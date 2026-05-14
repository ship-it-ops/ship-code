# Self-Test Fixtures — ship-clean-code

These fixtures are regression checks for the skill itself. Each fixture pairs a sample code file with the expected review output if the skill is functioning correctly. If the skill prompt is changed and the output drifts substantially from the expected report, the change either regressed the skill or warrants a fixture update.

## How to use

1. Open Claude Code with the skill installed.
2. Run `/ship-clean-code review tests/fixture-N/input.<ext>` (or paste the input).
3. Compare the output against `expected-output.md` in the same fixture directory.

The expected output is illustrative — minor wording differences are fine. Look for substantive drift: missing P1/P2 findings, wrong priority categorization, missing "What's Good" section, no concrete fix suggestions.

## Fixtures

| Fixture | Language | What it tests |
|---|---|---|
| `fixture-1-python-bugs` | Python | P1 (off-by-one), P2 (SQL injection), P3 (bare except), P6 (naming) all caught in one pass |
| `fixture-2-typescript-types` | TypeScript | `any` abuse, missing null safety, floating promises, language idioms |
| `fixture-3-java-srp` | Java | SRP violation (god class), constructor-injected dependencies, equals/hashCode contract |
