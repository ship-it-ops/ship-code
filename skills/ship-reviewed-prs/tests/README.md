# Self-Test Fixtures — ship-reviewed-prs

These fixtures are regression checks for the skill. Each fixture provides a synthetic PR (diff + review threads + CI status) and the expected output if the skill is functioning correctly.

## How to use

1. Open Claude Code with the skill installed.
2. Paste the fixture's `input.md` content as the user message.
3. The skill should produce output substantially matching `expected-output.md`.

These are *not* live PRs — they're synthetic inputs designed to exercise specific skill behaviors. The `gh` calls won't actually run; the skill should recognize the structured input and process it as if it had fetched the data.

Minor wording differences in the output are fine. Watch for: missing *1 findings, wrong persona attribution, wrong decision, missing lifecycle suppression, missing "What's Good" section.

## Fixtures

| Fixture | What it tests |
|---|---|
| `fixture-1-security-bug-pr` | SC1 (auth-missing) on a new admin endpoint; clean lifecycle; REQUEST_CHANGES decision; bot-disclosure prefix in CI mode |
| `fixture-2-migration-pr` | DA persona escalation triggered; DA1+IN1 findings on a schema migration; conditional persona activation visible in Confidence |
| `fixture-3-stale-resolved-pr` | Comment lifecycle suppression: 3 resolved + 2 won't-fix threads. Fingerprint dedup drops 3 candidate findings silently (the three that map to resolved threads); the won't-fix threads have no matching candidates in this fixture. |
| `fixture-4-clean-approve-pr` | Zero findings, zero open threads, green CI → APPROVE; `--auto-approve` honored on green path |
| `fixture-5-frontend-pr` | FE persona regression anchor — derived from a real PR the skill missed before FE existed. Diff contains all 10 finding sites; expected output annotates each `# Copilot finding #N` for mechanical coverage scoring. Target: 10/10 caught. |
| `fixture-6-frontend-clean` | FE persona false-positive guard — well-shaped React component (axe-tested, stateless, no controlled-state surface). FE activates but should produce zero findings. APPROVE. |
