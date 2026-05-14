# Self-Test Fixtures — ship-tested-code

These fixtures are regression checks for the skill. Each fixture pairs a sample test file with the expected review output if the skill is functioning correctly.

## How to use

1. Open Claude Code with the skill installed.
2. Run `/ship-tested-code review tests/fixture-N/input.<ext>` (or paste the input).
3. Compare the output against `expected-output.md` in the same fixture directory.

Minor wording differences are fine. Watch for substantive drift: missing T1/T2 findings, wrong priority categorization, missing "What's Good" section, no concrete fix suggestions.

## Fixtures

| Fixture | Language | What it tests |
|---|---|---|
| `fixture-1-python-flaky` | Python | T2 (flaky test via sleep + datetime.now), T4 (multiple concepts in one test), T1 (missing error path) |
| `fixture-2-typescript-mock-heavy` | TypeScript | T3 (over-mocking), T1 (no assertions on actual behavior), T6 (mock setup > test logic) |
| `fixture-3-java-implementation-coupled` | Java | T4 (testing implementation), T3 (E2E for unit-level logic), T5 (hardcoded magic values) |
