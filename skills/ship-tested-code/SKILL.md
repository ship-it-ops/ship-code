---
name: ship-tested-code
description: >
  Apply testing best practices (test design, TDD, test strategy, mocking,
  integration testing, CI/CD testing) when writing or reviewing tests for
  Python, TypeScript/JavaScript, or Java code. Invoke explicitly for test
  reviews or test strategy assessments. Do not invoke for shell scripts,
  config files, or one-off scripts.
allowed-tools: Read, Grep, Glob
---

# Testing Best Practices Skill

## Purpose

This skill applies testing best practices plus modern software engineering principles to help you write effective, maintainable, and reliable tests. It operates in two modes: writing (apply silently) and review (structured report).

## Quickstart (New to Testing Best Practices?)

Start with these 3 rules and internalize them before learning the rest:
1. **Test behavior, not implementation** — if refactoring internals breaks your test, the test is wrong
2. **One test, one reason to fail** — each test verifies a single behavior
3. **Fast feedback is everything** — unit tests in ms, integration tests in seconds, E2E only for critical paths

The detailed reference files (`reference.md`, `reference-smells.md`) assume familiarity with testing frameworks and patterns — build up to those over time.

## Mode Detection

- **Writing mode** (default when generating or modifying test code): Apply all principles
  proactively. Produce well-structured, behavior-focused tests by default without commentary
  unless asked. Do not explain the principles being applied -- just write good tests.

- **Review mode** (when explicitly reviewing tests, using /ship-tested-code, or asked to review):
  Read the target test code, analyze against the rules below, and produce a structured
  report using the Review Output Format defined in this skill.

Trigger review mode when the user says: "review tests", "test review", "check my tests",
"test quality", or invokes the skill explicitly. When in doubt, default to writing mode.

## Core Principles - Always Apply

These 12 rules apply to ALL tests, ALL languages, EVERY time:

### 1. Test behavior, not implementation.
Tests should survive refactoring. Query by role/behavior, not internal state. If changing
internals (without changing behavior) breaks tests, the tests are coupled to implementation.
Do not test private methods, auto-generated code, or framework wiring.

### 2. One test, one behavior, one reason to fail.
Each test verifies a single concept. Multiple assertions are fine if they verify the same
behavior. If a test name needs "and", split it. If a test can fail for five different
reasons, it is five tests pretending to be one.

### 3. Arrange-Act-Assert (AAA) structure.
Every test has three distinct phases: set up the scenario, perform the action, verify the
result. Keep them visually separated. Do not tangle setup with assertions or interleave
multiple act-assert sequences.

### 4. Tests are deterministic or they are deleted.
A test that passes 99% of the time is a flaky test. No `sleep()`, no shared mutable state,
no reliance on execution order, no external service calls without isolation, no
`Math.random()` or `datetime.now()` without controlled injection.

### 5. Test names are specifications.
A failing test name should tell you exactly what broke. Use `should_X_when_Y` or
`test_X_given_Y`. Never `test1`, `testProcess`, or `testHappyPath`. If your tests were the
only documentation, a reader should understand the system's behavior.

### 6. Test the sad paths harder than the happy paths.
Happy paths get validated by usage. Error handling, edge cases, timeouts, empty inputs,
nulls, maximum values, unicode, concurrent access -- test these deliberately. Production
bugs live in the negative paths.

### 7. Right test at the right level.
Unit tests for business logic, integration tests at service boundaries, contract tests
between services, E2E only for critical user journeys. Do not use E2E for what a unit test
can catch. The right distribution depends on your architecture, not a universal shape.

### 8. Isolate by default, share nothing.
Tests must be executable in any order, concurrently. Each test creates its own data and
cleans up after itself. No shared mutable state between tests. If tests cannot run in
parallel, there is a design problem.

### 9. Mock at boundaries, not everywhere.
Mock external APIs, clocks, randomness. Use real (containerized) databases and queues when
practical. Prefer fakes over mocks for state-based tests. Never mock value objects. When
you mock everything, you test that your mocks are wired correctly, not that your code works.

### 10. Every production incident produces a regression test.
If your system failed in a way tests did not predict, fill the gap. This is how you build
a safety net over time. Bugs cluster -- when you find one, test adjacent logic exhaustively.

### 11. Test data uses factories, not fixtures.
Use builder/factory patterns for test data. When a model adds a field, fix one factory,
not 400 tests. Make test data reveal intent: `UserFactory.withExpiredSubscription()`,
not `User("John", "john@test.com", null, null, true, 0)`.

### 12. Delete tests that don't earn their keep.
Tests have maintenance costs. Skipped tests older than 30 days: fix or delete. Tests that
have not failed in 2 years on stable code: evaluate whether they provide value.
Coverage-gaming tests with weak assertions: delete. A fast, reliable suite of 200 tests
beats a slow, flaky suite of 2000.

## Priority Hierarchy for Test Reviews

When reviewing test code, report issues in this priority order:

**T1 - MISSING COVERAGE**: Untested critical paths, missing error/edge case tests, no
regression test for known bugs, business logic without tests.

**T2 - FLAKY/UNRELIABLE**: Timing dependencies (`sleep`), shared mutable state,
non-deterministic data, external service calls without isolation, order-dependent tests.

**T3 - WRONG LEVEL**: E2E test for what a unit test should catch, mocking everything
(testing mocks not code), testing framework internals instead of your code.

**T4 - POOR DESIGN**: Implementation-coupled tests, tests with multiple reasons to fail,
unclear test names, AAA structure violated, testing private methods.

**T5 - TEST DATA**: Hardcoded magic values, shared mutable fixtures, no factories,
production data in tests, missing edge case data (nulls, empty, unicode, boundaries).

**T6 - MAINTAINABILITY**: Duplicate test setup across files, over-abstracted helpers
(5 levels deep), excessive mocking setup longer than test logic, brittle selectors/locators.

**T7 - ASSERTIONS**: Weak assertions (`assertNotNull` when you mean `assertEquals`),
missing assertions (test exercises code but verifies nothing), snapshot abuse on
large/changing components, no assertion messages.

## Pragmatism Guidelines

Rules for when NOT to be strict:

- **Don't demand tests for trivial code.** Getters, setters, simple delegation,
  framework-generated code do not need tests. Test what could break.

- **Legacy code gets the Boy Scout Rule.** When touching untested code: add a test for
  your change. Do not demand full coverage of the file. Leave it slightly better.

- **Prototype code gets a pass.** If the user says "quick hack", "prototype", "spike",
  relax test requirements. If it survives to production, tests come first.

- **Coverage is a floor, not a goal.** 70-80% branch coverage is a healthy baseline.
  Never chase 100% — it incentivizes low-value tests. Use coverage to find gaps, not to
  declare victory.

- **Speed trumps comprehensiveness.** A fast, reliable suite of 200 tests beats a slow,
  flaky suite of 2000. Optimize for feedback speed.

- **Match existing test patterns.** If the project uses a specific test structure, naming
  convention, or framework, follow it. Consistency with the codebase outweighs ideals.

- **Never block on T7 issues.** Assertion style suggestions are just that -- suggestions.

## Language Detection & Routing

Detect the programming language from file extensions and context. Load the appropriate
language-specific reference:

- `.py` files -> Read `${SKILL_DIR}/lang-python.md`
- `.ts`, `.tsx`, `.js`, `.jsx` files -> Read `${SKILL_DIR}/lang-typescript.md`
- `.java` files -> Read `${SKILL_DIR}/lang-java.md`

Apply universal principles first, then layer language-specific idioms on top. When the
language is ambiguous or not covered, apply only universal principles.

## Review Output Format

When in review mode, produce this structured output:

```
## Test Review: [filename or scope]

### Critical (must fix before merge)
- **[T1-COVERAGE] Line XX**: [Missing test description]. -> [What to test and how].
- **[T2-FLAKY] Line XX**: [Flakiness source]. -> [Specific fix].

### Important (should fix)
- **[T3-LEVEL] Line XX**: [Problem]. -> [Better approach].
- **[T4-DESIGN] Line XX**: [Problem]. -> [Fix suggestion with code snippet].
- **[T5-DATA] Line XX**: [Problem]. -> [Fix suggestion].

### Suggestions (improve when convenient)
- **[T6-MAINT] Line XX**: [Problem]. -> [Fix suggestion].
- **[T7-ASSERT] Line XX**: [Problem]. -> [Fix suggestion].

### What's Good
- [Substantive positive observations about test design, coverage strategy, or patterns done well.]
```

Rules for the output:
- Always include "What's Good" -- never be purely negative. Name specific patterns done well.
- Tag every finding with its priority category (T1-T7).
- Include specific line numbers.
- Every finding must include a concrete fix suggestion, not just a description of the problem.
- Group by severity, not by category.
- If there are more than 10 findings, show the top 10 strictly ordered by priority
  (T1 before T2, etc.). Never suppress a T1 or T2 finding due to the cap. Summarize
  remaining T6/T7 findings as a count.

## Working with Legacy / Untested Code

- **Boy Scout Rule**: Add tests for the code you touch. Do not demand full coverage of the
  surrounding file.
- Prioritize T1-T2 findings in legacy code. T5-T7 findings are deferred unless you own the module.
- Write characterization tests first (capture current behavior) before refactoring.
- If existing tests use a different style, match the file's convention for new tests in that file.

## Team Overrides

Before applying testing rules, check if `${SKILL_DIR}/overrides.md` exists. If it does,
read it and apply its overrides. Team overrides supersede defaults. Use this for: test
framework preferences, coverage thresholds, naming convention deviations, disabled rules.

If a project has a `.claude/ship-tested-code-overrides.md` file, read it as well —
project-level overrides take precedence over skill-level overrides.

## Team Adoption

Phased rollout recommended:
- **Weeks 1-4**: Enable T1 (missing coverage) and T2 (flaky tests) only. Build the review habit.
- **Month 2**: Add T3 (wrong level) and T4 (poor design).
- **Month 3+**: Full T1-T7 reviews.

Track: T1/T2 findings per PR (should trend toward zero), flaky test rate, escaped defect rate.

## Reference Loading

For deeper analysis, load supporting reference files:

- Detailed rules by concern: `${SKILL_DIR}/reference.md`
- Test smells checklist (~50 items): `${SKILL_DIR}/reference-smells.md`
- Language-specific testing idioms: `${SKILL_DIR}/lang-{language}.md`
- Before/after examples: `${SKILL_DIR}/examples/`

Load these on-demand when doing thorough reviews or when the user asks for detailed
guidance on a specific testing topic.
