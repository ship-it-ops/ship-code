# Self-Test Fixtures — ship-debugged-code

These fixtures cover both investigation mode (given a bug report, the skill should guide the user through a systematic process) and review mode (given a proposed fix or postmortem, the skill should flag missing steps).

## How to use

1. Open Claude Code with the skill installed.
2. For investigation fixtures: paste `input.md` and verify the skill drives the right early steps.
3. For review fixtures: run `/ship-debugged-code review` against `input.md` and compare to `expected-output.md`.

Minor wording differences are fine. Watch for: missing D1 (reproduction) prompts in investigation mode, missing D2/D4 findings in review mode, no concrete next steps.

## Fixtures

| Fixture | Mode | What it tests |
|---|---|---|
| `fixture-1-bug-report` | Investigation | Skill demands reproduction before forming hypotheses; resists the urge to jump to a fix |
| `fixture-2-pr-review` | Review | Skill catches symptom-patch fix, missing regression test, vague commit message |
| `fixture-3-postmortem-review` | Review | Skill catches blame language, action items without owners, missing systemic causation |
