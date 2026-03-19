---
name: ship-clean-code
description: >
  Apply clean code principles (naming, functions, classes, error handling,
  testing, formatting) when writing or reviewing production-quality Python,
  TypeScript/JavaScript, or Java code. Invoke explicitly for PR reviews or
  code quality assessments. Do not invoke for shell scripts, SQL queries,
  config files, quick prototypes, or single-expression snippets.
allowed-tools: Read, Grep, Glob
---

# Clean Code Skill

## Purpose

This skill applies clean code principles plus modern software engineering best practices to help you write readable, maintainable, and debuggable code. It operates in two modes: writing (apply silently) and review (structured report).

## Quickstart (New to Clean Code?)

Start with these 3 rules and internalize them before learning the rest:
1. **Name everything clearly** — if you need a comment to explain a variable, rename it instead
2. **Keep functions small** — if a function does two things, split it into two functions
3. **Single Responsibility** — each file/class/module should have one job

The detailed reference files (`reference.md`, `reference-smells.md`) assume familiarity with design patterns and SOLID principles — build up to those over time.

## Mode Detection

- **Writing mode** (default when generating or modifying code): Apply all principles
  proactively. Produce clean code by default without commentary unless asked. Do not
  explain the principles being applied -- just write good code.

- **Review mode** (when explicitly reviewing, using /ship-clean-code, or asked to review):
  Read the target code, analyze against the rules below, and produce a structured
  report using the Review Output Format defined in this skill.

Trigger review mode when the user says: "review", "clean code review", "code quality",
"check this code", or invokes the skill explicitly. When in doubt, default to writing
mode.

## Core Principles - Always Apply

These 12 rules apply to ALL code, ALL languages, EVERY time:

### 1. Names reveal intent.
Name every variable, function, and class to reveal its purpose. If a name requires a
comment, rename it. No single-letter names except loop counters (i, j, k). No
abbreviations unless universally understood (url, id, http).

### 2. Functions do one thing and are small.
Target under 20 lines. Hard ceiling at 50. If you can describe what a function does
only by using "and" or "or", split it. Extract blocks in if/else/while into
well-named functions.

### 3. Functions take few arguments.
Zero is ideal, one is good, two is OK, three requires justification. Group related
parameters into objects/dataclasses/interfaces. Never use boolean flag arguments --
split into two functions instead.

### 4. No side effects.
A function named `checkPassword` must not initialize a session. If a function has side
effects, its name must say so (`checkPasswordAndInitSession` or better: split into two
calls).

### 5. Errors use exceptions/idiomatic patterns, never null.
Don't return null -- use Optional/Maybe types, empty collections, or throw exceptions.
Don't pass null as an argument. Provide context when throwing exceptions (what
operation, what input).

### 6. No commented-out code.
Delete it. Version control has the history. Commented-out code confuses readers who
don't know if it's safe to delete.

### 7. Comments explain WHY, never WHAT.
If code needs a comment explaining what it does, refactor the code to be
self-documenting. Good comments: intent explanations, warnings about consequences,
TODO with ticket numbers.

### 8. DRY -- Don't Repeat Yourself.
Extract repeated logic into named functions. But apply the Rule of Three: wait for
three instances before abstracting. Premature abstraction is worse than duplication.

### 9. One level of abstraction per function.
Don't mix high-level orchestration with low-level details. Follow the Stepdown Rule:
read the code top-to-bottom like a narrative, each function calling functions one
abstraction level below.

### 10. Encapsulate conditionals.
Replace `if (timer.hasExpired() && !timer.isRecurrent())` with
`if (shouldBeDeleted(timer))`. Extract complex boolean expressions into well-named
functions.

### 11. No magic numbers or strings.
Every literal value with domain meaning must be a named constant.
`if (age >= 18)` becomes `if (age >= LEGAL_DRINKING_AGE)`. This applies to array
indices, timeout values, status codes, and configuration values.

### 12. Single Responsibility Principle.
Each class/module has one and only one reason to change. If you can think of more than
one motive for changing a class, it has more than one responsibility. Split it.

## Priority Hierarchy for Reviews

When reviewing code, report issues in this priority order:

**P1 - BUGS**: Logic errors, off-by-one, null dereference, race conditions, resource
leaks, unreachable code, infinite loops.

**P2 - SECURITY**: Injection vulnerabilities (SQL, XSS, command), hardcoded secrets,
insecure deserialization, path traversal, missing auth checks, unvalidated external
input.

**P3 - ERROR HANDLING**: Swallowed exceptions, missing error paths, null returns, bare
except/catch blocks, missing resource cleanup.

**P4 - TESTABILITY**: Untestable code (hidden dependencies, global state, static
coupling), missing boundary handling.

**P5 - MAINTAINABILITY**: SRP violations, high coupling, missing abstractions,
hardcoded config, backward-compatibility breaks.

**P6 - READABILITY**: Bad names, long functions (>50 lines), deep nesting (>3 levels),
unclear intent, misleading comments, magic numbers.

**P7 - STYLE**: Formatting inconsistencies, import order, whitespace. Report ONLY if
egregious or inconsistent within the file.

## Pragmatism Guidelines

Rules for when NOT to be strict:

- **Don't rewrite untouched code.** If the user asks to add a feature, don't
  simultaneously rename all variables in the file. Focus on the requested change.

- **Don't lecture.** In writing mode, apply principles silently. Only explain when the
  user asks "why" or when in review mode.

- **Prototype code gets a pass.** If the user says "quick hack", "prototype", "spike",
  or "just try this", relax all rules except: no hardcoded secrets, no injection
  vulnerabilities, no obvious security holes.

- **Consistency with existing codebase outweighs ideals.** If the project uses
  snake_case in TypeScript, follow that convention. Match the surrounding code's style.

- **Performance-critical code can be ugly.** When the user explicitly prioritizes
  performance, allow longer functions, less abstraction, and inline code. Note the
  trade-off in a comment.

- **Rule of Three for abstractions.** Don't extract a shared function/class until the
  pattern appears three times. Two instances of similar code is not yet a pattern.

- **Never block on style.** In review mode, style issues (P7) are suggestions only,
  never "must fix".

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
## Code Review: [filename or scope]

### Critical (must fix before merge)
- **[P1-BUG] Line XX**: [Problem description]. -> [Specific fix suggestion with code snippet].
- **[P2-SEC] Line XX**: [Problem description]. -> [Specific fix suggestion].

### Important (should fix)
- **[P3-ERR] Line XX**: [Problem description]. -> [Fix suggestion].
- **[P4-TEST] Line XX**: `ServiceClass` instantiates `Dependency` internally via `new Dependency()`, making it impossible to test without the real implementation. -> Inject via constructor parameter; provide a fake in tests.
- **[P5-MAINT] Line XX**: [Problem description]. -> [Fix suggestion].

### Suggestions (improve when convenient)
- **[P6-READ] Line XX**: [Problem description]. -> [Fix suggestion].

### What's Good
- [Substantive positive observation about architecture, error handling, or test coverage -- not surface-level compliments. Name specific patterns done well.]
```

Rules for the output:
- Always include "What's Good" -- never be purely negative. Include substantive observations about architecture, error handling, or patterns done well.
- Tag every finding with its priority category (P1-P7).
- Include specific line numbers.
- Every finding must include a concrete fix suggestion, not just a description of the problem.
- Group by severity, not by category.
- If there are more than 10 findings, show the top 10 strictly ordered by priority
  (P1 before P2, etc.). Never suppress a P1 or P2 finding due to the cap. Summarize
  remaining P6/P7 findings as a count.

## Working in Legacy / Brownfield Code

- **Boy Scout Rule**: Leave the code you touch slightly cleaner than you found it. Rename one variable, extract one long block, remove one dead comment — do not rewrite the surrounding file.
- Prioritize P1-P3 findings in legacy code. P5-P7 findings are deferred unless you own the module.
- If existing code uses a different convention, match the file's convention for new code in that file. Flag the inconsistency in the review but do not block the PR.
- **Strangler Fig pattern**: When replacing a legacy module, introduce the clean version alongside the old one behind an interface. Do not rewrite in place.

## Team Overrides

Before applying clean code rules, check if `${SKILL_DIR}/overrides.md` exists. If it does, read it and apply its overrides. Team overrides supersede defaults. Use this for: agreed naming deviations, relaxed line-length limits, project-specific idioms, disabled rules.

If a project has a `.claude/ship-clean-code-overrides.md` file, read it as well — project-level overrides take precedence over skill-level overrides.

## Team Adoption

Phased rollout recommended:
- **Weeks 1-4**: Enable P1 (bugs) and P2 (security) only. Build the review habit.
- **Month 2**: Add P3 (error handling) and P4 (testability).
- **Month 3+**: Full P1-P7 reviews.

Track: P1/P2 findings per PR (should trend toward zero), team friction reports.

## Reference Loading

For deeper analysis, load supporting reference files:

- Detailed rules by concern: `${SKILL_DIR}/reference.md`
- Code smells checklist (66 items): `${SKILL_DIR}/reference-smells.md`
- Language-specific idioms: `${SKILL_DIR}/lang-{language}.md`
- Before/after examples: `${SKILL_DIR}/examples/`

Load these on-demand when doing thorough reviews or when the user asks for detailed
guidance on a specific topic.
