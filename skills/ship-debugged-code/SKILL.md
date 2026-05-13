---
name: ship-debugged-code
description: >
  Apply systematic debugging practices (reproduction, hypothesis-driven
  investigation, bisection, root-cause analysis, regression-test design) when
  investigating, isolating, or fixing bugs in Python, TypeScript/JavaScript, or
  Java code. Invoke explicitly for bug investigations, incident postmortems, or
  debugging reviews. Do not invoke for greenfield feature work or pure
  refactoring with no failure signal.
allowed-tools: Read, Grep, Glob, Bash
---

# Systematic Debugging Skill

## Purpose

This skill applies hypothesis-driven debugging practices to help you find the root cause of bugs quickly, fix them at the right layer, and prevent recurrence. It operates in two modes: investigation (work through a bug) and review (audit a fix or postmortem for soundness).

## Quickstart (New to Systematic Debugging?)

Start with these 3 rules and internalize them before learning the rest:
1. **Reproduce before you investigate** — without a reliable repro, you are guessing
2. **Change one thing at a time** — random parallel edits make it impossible to know what fixed the bug (or what made it worse)
3. **Every confirmed bug ships with a regression test** — a fix without a test will return

The detailed reference files (`reference.md`, `reference-smells.md`) assume familiarity with debuggers and logging — build up to those over time.

## Mode Detection

- **Investigation mode** (default when a bug is described or a failure is presented): Drive the debugging process. Start with reproduction, form hypotheses, narrow the search, identify the root cause, propose a fix at the right layer, and produce a regression test. Surface assumptions explicitly and check them before acting.

- **Review mode** (when explicitly reviewing a fix, a debugging session, a postmortem, or invoking `/ship-debugged-code`): Read the proposed fix and the surrounding context, analyze against the rules below, and produce a structured report using the Review Output Format defined in this skill.

Trigger investigation mode when the user says: "I have a bug", "this is failing", "why does X happen", "help me debug", "reproduce this issue". Trigger review mode when the user says: "review this fix", "audit this debugging session", "review my postmortem", or invokes the skill explicitly. When in doubt, ask whether the user wants you to debug or review.

## Core Principles - Always Apply

These 12 rules apply to ALL debugging, ALL languages, EVERY time:

### 1. Reproduce before you investigate.
A bug you cannot reproduce is a bug you cannot fix with confidence. Get a reliable repro — failing test, recorded session, exact request — before forming any hypothesis. If a bug is intermittent, your first job is to make it deterministic (find the timing window, the data dependency, the environment difference). Until then, do not guess at fixes.

### 2. Hypothesis-driven debugging.
State your hypothesis explicitly before testing it: "I believe the bug is in X because Y; if I am right, then Z will happen when I do W." Each experiment confirms or eliminates a hypothesis. Random instrumentation without a hypothesis is "shotgun debugging" and wastes time.

### 3. Change one thing at a time.
Bisection — both in the code and in the version history — is the fastest path to a root cause. Run `git bisect` for regressions. Comment out one block at a time. Toggle one flag. Parallel edits mean you cannot attribute the result.

### 4. Read the actual error, then read it again.
Stack traces, error messages, and log entries usually contain the answer. Read them top-to-bottom AND bottom-to-top. The first frame in your code, not the deepest framework frame, is usually where to start. Search the exact error string before searching paraphrased descriptions.

### 5. Trust no assumption — verify state.
Print the value, inspect with the debugger, log the type, check the schema, query the database. The bug is almost always in the assumption you did not check. "It should be X" is a hypothesis, not a fact.

### 6. Root cause, not symptom.
Stop at the first plausible fix and you will see the same bug re-emerge through another path. Ask "but why?" at least three times. Patching a `null` check at the call site leaves the root cause — a producer that returns null when it should not — untouched.

### 7. Fix at the right layer.
A bug surfaces where it crashes but lives where the invariant was first violated. Fix at the producer, not the consumer. Validate at the boundary (parser, deserializer, API gateway), not in every downstream function. Fix data at the source, not in formatters.

### 8. Never trust an intermittent failure that "went away".
A test that fails 1% of the time will fail in production. A bug that disappears after a retry is hiding a race condition, a resource leak, or a timing dependency. Investigate until you understand WHY it stopped failing.

### 9. Every confirmed bug produces a regression test.
The deliverable of debugging is not the fix — it is the fix plus a test that fails without the fix and passes with it. A bug that recurs because no test was added is a debugging session that was never finished.

### 10. Bisect ruthlessly when the cause is unclear.
`git bisect run <script>` automates regression-finding across hundreds of commits. Manual binary search across config flags, feature toggles, or dependency versions follows the same logic. When you do not know what changed, isolate the change.

### 11. Use the debugger before adding `print()`.
A debugger lets you inspect state without code changes, set conditional breakpoints, step through the actual execution, and walk the call stack at the moment of failure. Print-debugging is a fallback for environments where attaching a debugger is impractical (production, async, distributed systems). Use the right tool.

### 12. Document the investigation, not just the fix.
The commit message, PR description, or postmortem should explain: what was the symptom, what was the actual cause, why was that cause not caught earlier, and what was done to prevent recurrence. "Fixed bug" is not documentation. Investigation notes are how you teach the team and your future self.

## Priority Hierarchy for Debugging Reviews

When reviewing a bug investigation, fix, or postmortem, report issues in this priority order:

**D1 - CANNOT REPRODUCE**: No reliable reproduction case captured; fix is being applied speculatively. The investigation cannot be trusted without a repro.

**D2 - SYMPTOM PATCH**: Fix addresses where the bug surfaced, not where it originated. Same root cause will manifest through another path.

**D3 - WRONG LAYER**: Fix is at the consumer when it should be at the producer (or vice versa). Validation duplicated downstream instead of centralized at the boundary.

**D4 - MISSING REGRESSION TEST**: Fix shipped without a test that fails without the fix. Bug will recur silently.

**D5 - UNVERIFIED HYPOTHESIS**: Fix is based on an unstated or unverified assumption about why the bug occurred. No experiment confirmed the hypothesis.

**D6 - HIDDEN INTERMITTENT**: Bug was "fixed" by retry, restart, or workaround without understanding why it failed. Race conditions, leaks, or timing bugs left in place.

**D7 - DOCUMENTATION**: Commit message, PR, or postmortem does not explain the cause, only the change. Future debuggers cannot learn from this incident.

## Pragmatism Guidelines

Rules for when NOT to be strict:

- **Production incident: stop the bleeding first.** When a bug is actively burning, ship the symptom patch, then immediately open a follow-up to investigate the root cause. Do not block the rollback or hotfix on a clean root-cause analysis.

- **Cosmetic UI bugs may skip the regression test.** A one-pixel CSS bug does not need a test if visual regression testing is not set up. Use judgment for low-risk surface issues.

- **Third-party bugs you cannot fix.** When the bug is in a vendored library or external API and you cannot patch it, document the workaround clearly and add a comment with the upstream issue link.

- **"It works on my machine" is not a fix.** Environment differences are bugs in your repro, not bugs that go away. Containerize, capture the environment, or escalate — never close as "could not reproduce" without trying.

- **Stop investigating when the cost exceeds the value.** A single edge-case bug affecting one user once a month, with no security or data-integrity impact, may be deferred. Track it explicitly; do not silently drop it.

- **Match team postmortem conventions.** If the team uses a specific incident-report template (5 Whys, fishbone, blameless postmortem), follow it. Consistency outweighs ideals.

## Language Detection & Routing

Detect the programming language from file extensions and context. Load the appropriate language-specific reference:

- `.py` files → Read `lang-python.md`
- `.ts`, `.tsx`, `.js`, `.jsx` files → Read `lang-typescript.md`
- `.java` files → Read `lang-java.md`

Apply universal principles first, then layer language-specific debugging tools and idioms on top. When the language is ambiguous or not covered, apply only universal principles.

## Investigation Mode Workflow

When working an active bug, follow this sequence:

1. **Capture the symptom precisely.** What was expected? What happened? Exact error message, stack trace, request/response, screenshot. No paraphrasing.

2. **Establish a reproduction.** Minimal failing test or exact-steps repro. If intermittent, identify the conditions that make it deterministic (specific input, sequence, environment).

3. **State the first hypothesis explicitly.** Format: "I believe X is the cause because Y. To test: I will do Z and expect W."

4. **Run one experiment.** Change one thing. Re-run the repro. Did the result match the prediction? If yes, you have narrowed the search; if no, the hypothesis is wrong — discard and form a new one.

5. **Bisect when stuck.** If hypotheses are not converging, run `git bisect` over the regression range, or binary-search through feature flags / config changes / dependency versions.

6. **Identify the root cause.** Stop when you can answer: "Why did this happen?" with a concrete invariant violation, not just "code on line X is wrong".

7. **Design the fix at the correct layer.** Producer, not consumer. Boundary, not interior. Source, not symptom.

8. **Write the regression test BEFORE applying the fix.** Verify the test fails on the broken code, then apply the fix and verify it passes.

9. **Document.** Commit message includes: symptom, cause, fix layer, why this code path was uncovered. Reference the test added.

10. **Look for adjacent bugs.** Bugs cluster. If the root cause is "missing null check on producer X", audit all callers of X.

## Review Output Format

When in review mode, produce this structured output:

```
## Debug Review: [bug/PR/incident name]

### Critical (must fix before merge / before closing the incident)
- **[D1-REPRO] Section**: [Problem description]. → [What is missing and how to establish it].
- **[D2-SYMPTOM] Line XX**: [Problem]. → [Where the root cause actually lives and how to fix there].

### Important (should fix)
- **[D3-LAYER] Line XX**: [Problem]. → [Suggested layer and rationale].
- **[D4-TEST] Section**: [Missing regression test description]. → [Test to add, with assertion sketch].
- **[D5-HYPOTHESIS] Section**: [Unverified assumption]. → [Experiment to run].

### Suggestions (improve when convenient)
- **[D6-INTERMITTENT] Section**: [Hidden timing/race issue]. → [Investigation path].
- **[D7-DOC] Commit/PR/postmortem**: [Documentation gap]. → [What to add].

### What's Good
- [Substantive positive observation: reproduction quality, layer choice, test design, hypothesis discipline, or adjacent-bug audit. Not surface-level compliments.]
```

Rules for the output:
- Always include "What's Good" — never be purely negative. Good debugging is hard and deserves recognition for specific moves done well.
- Tag every finding with its priority category (D1-D7).
- Include specific line numbers, section headings, or commit references.
- Every finding must include a concrete next step, not just a description of the problem.
- Group by severity, not by category.
- If there are more than 10 findings, show the top 10 strictly ordered by priority (D1 before D2, etc.). Never suppress a D1 or D2 finding due to the cap. Summarize remaining D6/D7 findings as a count.

## Working with Legacy / Unfamiliar Code

- **Characterization tests before changes.** When debugging in a poorly tested module, write tests that capture current behavior first. This protects against introducing new bugs while fixing the original one.
- **Seams over rewrites.** When the bug requires changes in tightly coupled code, introduce a seam (extracted interface, dependency injection, wrapper) at the minimum extent needed. Do not refactor adjacent code in a bug fix.
- **Prioritize D1-D4 findings in legacy code.** D5-D7 findings are deferred unless you own the module.

## Related Skills

This skill produces fixes. For the broader code lifecycle, defer to siblings:

- **Cleaning up the code path you touched during debugging** → invoke `ship-clean-code`. Bugs often surface design problems (hidden dependencies, oversized functions); use the Boy Scout Rule rather than rewriting the file.
- **Designing the regression test you write** → invoke `ship-tested-code`. This skill insists a test exists; `ship-tested-code` ensures it tests behavior at the right level with deterministic data.
- **Reviewing the bugfix PR end-to-end** → invoke `ship-reviewed-prs`. That skill orchestrates a multi-persona review of the entire PR and will route the "root cause of the bug being fixed" question back here. When you've finished a bugfix and are ready for review, `ship-reviewed-prs` is the entry point.

When debugging across all three concerns, run this skill first to find and fix the bug, then `ship-tested-code` on the regression test you wrote, then `ship-clean-code` if you cleaned anything up.

## Team Overrides

Before applying debugging rules, check for override files in this order (later files win on conflicts):

1. `overrides.md` next to this `SKILL.md` (team-wide overrides bundled with the skill)
2. `.claude/ship-debugged-code-overrides.md` in the user's project root (project-specific overrides)

Read whichever exist and apply their rules on top of the defaults below. Use overrides for: postmortem template conventions, incident severity policy, debugger setup specifics, disabled rules, custom additions.

A template is available at `overrides.example.md` — copy and edit. Do not modify `overrides.example.md` directly; it is reference material.

## Team Adoption

Phased rollout recommended:
- **Weeks 1-4**: Enable D1 (cannot reproduce) and D4 (missing regression test) only. Build the habit of "no fix without a repro and a test".
- **Month 2**: Add D2 (symptom patch) and D3 (wrong layer).
- **Month 3+**: Full D1-D7 reviews.

Track: bug recurrence rate (target: declining), repro-to-fix lead time, percentage of bugs shipping with a regression test.

## Reference Loading

For deeper analysis, load supporting reference files alongside this `SKILL.md`:

- `reference.md` — Detailed rules by concern (reproduction, hypotheses, bisection, observability, root-cause patterns, fix design, postmortems)
- `reference-smells.md` — Debugging anti-patterns catalog with detection and remediation
- `lang-python.md`, `lang-typescript.md`, `lang-java.md` — Language-specific debugger tools, profilers, common bug patterns
- `examples/python-before-after.md`, `examples/typescript-before-after.md`, `examples/java-before-after.md` — Concrete debugging walkthroughs
- `examples/review-output-example.md` — End-to-end debug review output sample
- `tests/` — Self-test fixtures (sample bug report + expected investigation/review output)

Paths are relative to this `SKILL.md`. Load on-demand when doing thorough investigations or when the user asks for detailed guidance on a specific topic.
