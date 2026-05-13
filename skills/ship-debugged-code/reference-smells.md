# Debugging Smells and Anti-Patterns

A catalog of common failure modes in debugging sessions, fixes, and postmortems.

## Investigation

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| I1 | No Reproduction | Investigation begins from a verbal description, no captured failing case | Stop. Build a minimal repro before any code change |
| I2 | Shotgun Debugging | Prints/logs scattered across many files with no targeting hypothesis | Form one hypothesis at a time; instrument only the relevant code path |
| I3 | Hypothesis Not Stated | Fix is applied with no documented reasoning about why this is the cause | Write the hypothesis explicitly in the commit/PR before fixing |
| I4 | Unfalsifiable Hypothesis | "There is a problem with X" with no testable prediction | Restate as: "I believe X because Y. If true, Z will happen when W." |
| I5 | Hypothesis Survives Refutation | Failed experiment is explained away rather than discarded | When the prediction does not match, the hypothesis is wrong — form a new one |
| I6 | Confirmation Bias | Investigation latches onto first plausible cause, ignores contradicting evidence | Actively look for evidence that would refute the current hypothesis |
| I7 | Investigation Without Bisection | Manually reading commits to find a regression that affects 1000+ commits | Use `git bisect run` with a deterministic test script |
| I8 | Skipping the Stack Trace | Investigating without reading the error message and full stack | Read top-to-bottom AND bottom-to-top before forming hypotheses |

## Reproduction

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| R1 | Vague Repro | "Sometimes the form doesn't submit" with no specific input | Capture exact request, headers, body, environment |
| R2 | Repro Not Minimized | 200-line integration test that fails intermittently | Strip until only the failing assertion remains |
| R3 | Intermittent Accepted As-Is | Bug filed as "race condition, hard to reproduce" with no investigation | Find the determinant — the window, the data, the env difference |
| R4 | Environment Mismatch Ignored | Works locally, fails in CI (or vice versa) closed as "could not reproduce" | Diff: OS, runtime version, deps, locale, timezone, container limits |
| R5 | Repro Lost After Fix | Original failing case is not captured in a regression test | The minimized repro becomes the test — paste it in before fixing |

## Fix Design

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| F1 | Symptom Patch | Fix is at the crash site, not the source of the invariant violation | Trace back to the producer; fix there |
| F2 | Wrong Layer | Validation added in 10 call sites instead of at the boundary | Centralize at the parser/deserializer/API edge |
| F3 | Bundled Refactor | Bug-fix PR also renames, reformats, or restructures unrelated code | Split into separate PRs: bug fix first, cleanup second |
| F4 | Exception Silenced | `try/except: pass` or `catch(e) {}` added "to avoid the error" | Catch only what you can handle; let the rest propagate |
| F5 | Retry As Fix | Adding a retry around a flaky operation without understanding why it fails | Investigate why it fails first; retry is for transient infra issues, not bugs |
| F6 | Stale Workaround | Fix is documented as "temporary" but no follow-up to address the real cause | Open a tracked ticket with owner; comment in code with link |
| F7 | Fix Without Repro Verification | Fix shipped without re-running the original failing case | Always verify: test fails on broken code, passes on fixed code |
| F8 | Fix Without Adjacent Audit | Single bug fixed, no check for other consumers of the same broken producer | Bugs cluster — search for all callers/uses of the broken contract |

## Testing

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| T1 | No Regression Test | Fix shipped without a test that fails without the fix | Write the test first; verify it fails; then apply the fix |
| T2 | Test Written After Fix Without Failure Check | Test added but never verified to fail on broken code | Revert the fix temporarily, confirm the test fails, then reapply |
| T3 | Test of Implementation, Not Behavior | "Test does not call function X" instead of "returns expected output" | Test the invariant: given input, expect output or state |
| T4 | Test at Wrong Level | E2E test for a bug in a pure function (or unit test for an integration issue) | Match test scope to bug scope; unit for logic, integration for I/O |
| T5 | Paraphrased Test Data | "A user with no tier" instead of `{"id": 4711, "tier": None}` | Use the minimized repro data as test input verbatim |

## Observability

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| O1 | Print Debugging Left Behind | `print()` / `console.log()` / `System.out.println()` in committed code | Remove or convert to proper structured logging |
| O2 | No Correlation IDs | Distributed bug, logs from three services cannot be correlated | Propagate request/trace ID end-to-end |
| O3 | Context-Free Error Logs | "Order failed" with no IDs, no input, no upstream response | Include: operation, input, state, downstream response, correlation ID |
| O4 | Logs at Wrong Level | ERROR logged for expected conditions (e.g., 404 on lookup) | INFO for state changes, WARN for recoverable, ERROR for actionable failures |
| O5 | Sensitive Data in Logs | Passwords, tokens, PII visible in log output | Mask at source; never trust review to catch this later |
| O6 | No Metrics for Recurring Question | Repeatedly grep-ing logs to count occurrences of an event | Add a metric; logs answer "what happened once", metrics answer "how often" |

## Postmortem / Documentation

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| P1 | Timeline Without Causation | Postmortem lists events but never explains why the bug occurred | Add: root cause, contributing factors, why detection was late |
| P2 | Blame Language | "Bob's commit caused..." instead of "the change passed review despite missing test coverage for X" | Rewrite in systemic terms; the goal is learning, not accountability |
| P3 | Action Items Without Owners | "We should add monitoring" with no name attached | Every action item: owner, deadline, tracking link |
| P4 | "Fixed Bug" Commit Message | Commit message describes the change but not the cause | Include: symptom, cause, fix layer, regression test reference |
| P5 | No Runbook Update | Same incident type recurs; the responder has no documented playbook | Update or create a runbook for the alert/symptom |

## Cognitive

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| C1 | "It Works on My Machine" | Investigator dismisses a CI failure as environmental | Capture the environment difference; reproduce in the failing environment |
| C2 | "Should Be Impossible" | Investigator stops looking when something appears to contradict the model | The model is wrong. Inspect actual state, do not reason from invariants |
| C3 | "Select Isn't Broken" (Pragmatic Programmer) | Blaming the library/OS/network before exhausting your own code | Assume the bug is in your code until proven otherwise |
| C4 | Recency Bias | Suspecting the last thing changed without evidence | Use bisection or actual stack trace, not "what did I change recently" |
| C5 | Fatigue Fix | Investigator stops at first working theory after hours of debugging | Take a break, sleep on it, or have a colleague verify before merging |
| C6 | Rubber Duck Skipped | Stuck for hours, never explained the bug out loud to anyone or anything | Explain the problem from scratch to a colleague (or a duck) — most bugs reveal themselves |
