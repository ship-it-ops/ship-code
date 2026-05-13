# Systematic Debugging Reference

Detailed rules organized by concern area, combining classical debugging discipline (Zeller, Agans) with modern observability and incident-response practice.

---

## 1. Reproduction

### Principles

1. **Get a reliable repro first.** Without one, every "fix" is a guess. Pause investigation until you have failing input you can run on demand.
2. **Minimize the repro.** Strip everything not essential to triggering the failure. A 5-line repro tells you more than a 500-line one.
3. **Repro becomes the test.** The minimized repro is the seed of the regression test. Capture it in the test framework as you go.
4. **For intermittent bugs, find the determinant.** Race conditions have a window — find it. Data-dependent bugs have a row — find it. Environment bugs have a difference — find it. Intermittent does not mean random; it means you have not identified the variable yet.
5. **Capture the environment.** Repro that works locally but not in CI (or vice versa) is an environment bug, not a phantom. Diff: OS, runtime version, dependency versions, locale, timezone, file system case-sensitivity, container limits.
6. **Capture the input precisely.** Exact request body, headers, query parameters, cookies, session state. Paraphrased descriptions lose the bug.

### Common Violations

- Investigation begins from a vague "users report X" without a captured failing case.
- Repro is a 200-line integration test that fails sometimes — never minimized.
- Bug filed as "intermittent" with no attempt to find the determinant.
- "Cannot reproduce" closed without comparing environments.

### Quick Examples

**Before (no repro):**
> "Login is broken for some users. I tried logging in and it worked, so I am not sure what is happening. Looking at the login code now..."

**After (repro first):**
> "Bug repro: user account ID 4711 (test seed) fails login with password 'correct-horse-battery-staple'. Captured in `tests/auth/test_login_4711_regression.py` — fails on main, hangs on `verify_password` for 30s before timing out. Investigating from the repro now."

---

## 2. Hypothesis-Driven Investigation

### Principles

1. **State the hypothesis before the experiment.** Format: "I believe X because Y. If I am right, doing Z will produce W." Then run Z. Compare actual W to predicted W.
2. **Confirm or eliminate, never both partially.** A hypothesis is either confirmed or it is not. "Maybe" means the experiment was not specific enough.
3. **Falsifiable predictions only.** "There is a problem with the database" is not a hypothesis. "Query Q returns rows in different order than expected because the ORDER BY is missing" is.
4. **One hypothesis per experiment.** If you change two things, the result tells you nothing about either.
5. **Discard refuted hypotheses fast.** When the prediction does not match, the hypothesis is wrong — do not patch it to fit. Form a new one.
6. **Track hypotheses you ruled out.** Future you will be tempted to re-investigate them. Note "X is not the cause because Y" in your scratchpad or PR.

### Common Violations

- "Shotgun debugging": instrumenting everything in the call stack with prints, hoping something reveals itself.
- "Sounds right" reasoning: applying a fix because it looks like a similar past bug, without confirming it is.
- Patching a hypothesis to survive a failed experiment ("well, X is still probably the cause, except when...").
- Investigating until a fix works, then declaring victory without understanding why.

### Quick Examples

**Hypothesis well-stated:**
> H1: The 500 error in `/api/orders` is caused by a null `customer.tier` for legacy users who signed up before 2023-06.
> Prediction: Querying for `customer.tier IS NULL` will return only pre-2023-06 accounts.
> Experiment: `SELECT id, created_at FROM customers WHERE tier IS NULL LIMIT 20`
> Result: All returned accounts have `created_at < 2023-06-01`. ✅ H1 confirmed.

**Hypothesis poorly stated:**
> "I think there is a database problem."

---

## 3. Bisection

### Principles

1. **`git bisect run` is your fastest tool.** When a bug appeared "recently" and you have a script that returns 0 (good) / 1 (bad), `git bisect run` finds the offending commit in O(log n) operations.
2. **Bisect non-git changes too.** Feature flags, dependency versions, config values, environment variables — the same binary search applies. Halve the search space each iteration.
3. **Test the script before bisecting.** Run it on a known-good and known-bad commit first. A bisect with a broken test script gives a false answer.
4. **Skip merges/build-broken commits with `git bisect skip`.** Do not let an unrelated broken commit derail the search.
5. **Bisect to the smallest unit that changed.** Once you have the commit, diff it. Comment out half of the diff. Repeat. The actual bug-introducing change is usually a few lines, not the whole commit.

### Common Violations

- Spending hours reading commits manually when `git bisect run` would have found it in 10 iterations.
- Bisecting without a deterministic test script — flaky results give wrong commits.
- Stopping at the bisected commit without identifying the specific line that caused the regression.

### Quick Examples

**Bisect script pattern:**
```bash
#!/bin/bash
# bisect.sh - returns 0 if the bug is absent, 1 if present
npm install --silent && npm test -- --testPathPattern=login 2>&1 | grep -q "passed" && exit 0 || exit 1
```
```bash
git bisect start HEAD v2.4.0  # known bad ... known good
git bisect run ./bisect.sh
```

---

## 4. Reading Errors and Stack Traces

### Principles

1. **Read the error literally.** The framework wrote that message for a reason. Do not assume it is misleading until you have ruled out the literal interpretation.
2. **Search the exact error string.** Then your codebase, then the framework's issue tracker, then the broader web. Exact strings find duplicates faster than paraphrased problem descriptions.
3. **Find the first frame in your code.** Walk down from the top of the stack — the deepest frame is usually framework internals. The shallowest frame that is *your* code is where to start.
4. **Read both directions.** Top of the trace shows the immediate failure. Bottom shows the entry point. The middle shows the path. All three matter.
5. **The error type matters as much as the message.** `KeyError` vs. `AttributeError` vs. `TypeError` narrow the cause significantly. Do not generalize to "exception".
6. **Look for the cause chain.** Many languages preserve a `cause` or `inner exception`. The visible error often wraps the real one.

### Common Violations

- Skipping the stack trace and going straight to suspect code based on intuition.
- Searching for "error in login" when the actual message is `KeyError: 'tier'` — the specific string would find the bug in seconds.
- Focusing on the framework frames at the top of the stack instead of the first application frame.

---

## 5. State Inspection

### Principles

1. **Verify before assuming.** Every "should" is a hypothesis. Print, log, breakpoint, or query — confirm the actual value.
2. **Inspect at the boundary of the failure.** Where the stack trace points, examine: input arguments, local variables, instance state, return values, side effects.
3. **Check types, not just values.** `1` (int) and `"1"` (str) look identical in a print; the type often is the bug.
4. **Check shape and schema for collections.** Empty list vs. None vs. missing key are different bugs. List of strings vs. list of bytes is a different bug.
5. **Sample real data, not test data.** A bug that only appears in production is a bug about real data shapes. Capture a representative sample (anonymized) for the repro.

### Common Violations

- Adding a fix based on "the variable should contain X" without checking what it actually contains.
- Reading `len(items)` correctly but never inspecting items[0] to confirm the schema.
- Assuming the type from the variable name (`user_id` must be int) without verifying (it could be the string "4711").

---

## 6. Root Cause Analysis

### Principles

1. **Ask "but why?" repeatedly (5 Whys, fishbone, or similar).** Stop only when the answer is a concrete invariant violation, not "the code is wrong on this line".
2. **Find the producer, not the consumer.** A null at the call site usually came from a producer that returned null. The producer is the bug; the call site is the witness.
3. **Find the first violation, not the first crash.** A program can corrupt state at step 1, drift along, and crash at step 50. The crash site is rarely the bug.
4. **Distinguish necessary from sufficient causes.** "Removing X makes the bug go away" does not mean X is the cause — it might just paper over the symptom.
5. **Check for clusters.** Bugs cluster: one missing null check often implies others. One race condition in a module suggests examining the rest.
6. **Look for the latent condition.** Was there a missing invariant, a stale assumption, a contract change? The proximate cause is "the function returned null"; the latent cause is "the API contract changed in v3 and the caller was not updated".

### Common Violations

- Stopping at "Line X throws — add a null check" without asking why X was null.
- Patching the consumer to handle malformed input instead of fixing the producer that should not have produced it.
- Assuming necessary causation from temporal correlation ("the deploy at 10am broke it, so commit Y is the cause" — could be a config change, a data event, a downstream service).

### Quick Examples

**Symptom patch (D2):**
```python
# Bug: KeyError 'tier' for some users
def get_discount(user):
    tier = user.get("tier", "free")  # patch: default to free
    return DISCOUNTS[tier]
```

**Root cause fix:**
```python
# Producer: user serialization was dropping 'tier' for legacy accounts.
# Fix at the producer — guarantee the field exists on all User objects.
def serialize_user(user_row):
    return {
        "id": user_row.id,
        "name": user_row.name,
        "tier": user_row.tier or "free",  # explicit invariant at the boundary
    }
# Add database migration: set tier='free' for legacy NULL rows.
# Add NOT NULL constraint going forward.
```

---

## 7. Fix Design

### Principles

1. **Fix at the right layer.** Closest to the source of the invariant violation, not closest to the crash.
2. **Boundary validation, not interior validation.** Validate input at the parser/deserializer/API edge. Once data is inside the trusted core, it should be valid by construction.
3. **Make invalid states unrepresentable.** Type system, schema, constraints. The best fix prevents the bug from being expressible.
4. **Smallest fix that solves the actual problem.** Do not bundle refactoring, formatting, or unrelated improvements into a bug fix. The diff should be reviewable as a single change.
5. **Reversible fix when possible.** Feature flag, gradual rollout, or canary so you can back out fast if the fix introduces a new bug.
6. **Document the invariant.** Add a comment, type, or test that captures *why* the fix is needed. The next person to read the code should understand the constraint.

### Common Violations

- Adding null checks at every call site instead of fixing the producer.
- Hotfix that grows into a refactor; reviewer cannot tell which change is the bug fix and which is incidental.
- Fix that catches an exception silently and continues with degraded behavior — the bug still happens, you just stopped seeing it.

---

## 8. Logging and Observability for Debugging

### Principles

1. **Structured logs at decision points.** Log INFO at state transitions, request entries/exits, and outcomes. Log WARN at recoverable failures. Log ERROR at unrecoverable failures. Never log secrets.
2. **Correlation IDs end-to-end.** Every request gets an ID. Every log line includes it. Every downstream call propagates it. Without this, distributed debugging is impossible.
3. **Capture context, not just messages.** "Order failed" tells you nothing. "Order failed: order_id=4711, user_id=42, total=99.50, gateway_response={code: 402, message: 'card declined'}" tells you everything.
4. **Use the debugger first, instrument as fallback.** A debugger gives richer information without permanent code changes. Logging is for cases where the debugger cannot reach (production, async, distributed).
5. **Remove debug logging before merging.** Temporary `print` and `console.log` statements pollute production logs. Use the proper log levels or remove.
6. **Tracing for "where is time going" questions.** Distributed tracing (OpenTelemetry) is the right tool for "why is this slow" — not log timestamps.
7. **Metrics for "how often" questions.** Errors, latencies, throughput. Logs answer "what happened in this one case"; metrics answer "how often does this happen".

### Common Violations

- ERROR-level logs for expected conditions ("user not found" during a lookup).
- `print(x)` statements left in production code after debugging.
- Log messages that paraphrase the variable name ("got user") instead of including the value.
- No correlation IDs — bug spans three services, you cannot reconstruct the request path.
- Logging entire request/response bodies (may contain PII).

---

## 9. Regression Test Design

### Principles

1. **Write the test first, then verify it fails.** The test must fail on the broken code; otherwise it does not actually catch the bug.
2. **Test the invariant, not the specific bug.** "User with NULL tier returns 'free' discount" tests the invariant; "Line 42 does not raise KeyError" tests the implementation.
3. **Place the test at the right level.** A bug in a domain function gets a unit test. A bug in a request flow gets an integration test. An E2E user-impacting bug may need an E2E test plus a unit test for the underlying function.
4. **Name the test for the bug it catches.** `test_get_discount_handles_legacy_user_with_null_tier` is searchable, self-documenting, and a paper trail.
5. **Test the cluster, not just the bug.** If the root cause was "missing null check on producer X", test all the consumers of X that might have been vulnerable.
6. **Test the data shape that caused the bug.** Use the minimized repro data as the test input. Do not paraphrase ("a user with no tier"); use the actual shape (`{"id": 4711, "name": "alice", "tier": None}`).

For deeper guidance on test design, defer to the sibling skill `ship-tested-code`.

### Common Violations

- Bug fixed, no test added. ("It's obvious; the test would be trivial.")
- Test added but written against the fixed code — it never failed against the broken version.
- Test verifies the implementation detail ("does not call function X") instead of the behavior ("returns 'free' for users with null tier").
- Test data is invented from scratch rather than minimized from the failing repro.

---

## 10. Postmortems and Documentation

### Principles

1. **Blameless postmortems for incidents.** Focus on systemic causes (missing invariants, gaps in alerting, untested code paths), not "who pushed the bad commit". The goal is learning, not blame.
2. **Document symptom, cause, fix, prevention.** A debugging-session writeup or PR description should answer: what was the symptom, what was the actual cause, why was the cause not caught earlier, what changes prevent recurrence.
3. **Reference the regression test.** The PR or postmortem links to the test file:line that captures this bug. Future engineers searching for related bugs will find it.
4. **Update runbooks.** If an alert fired and the response was non-obvious, update the runbook. If no alert fired but one should have, file a ticket to add it.
5. **Action items have owners and deadlines.** "We should add monitoring" is not an action item. "Alice will add Datadog alert for tier=null orders by 2025-08-01" is.

### Common Violations

- "Postmortem" that is a timeline with no causal analysis.
- Commit message "fixed bug" with no description of what or why.
- Action items without owners — guaranteed to never happen.
- Blame language ("Bob broke the build") instead of systemic language ("the test suite did not cover this path").

---

## Quick-Reference Checklist

Use this for rapid debugging-session and fix review scanning:

| Area | Key Question |
|---|---|
| Reproduction | Can I trigger this bug on demand right now? |
| Hypothesis | Have I stated a falsifiable hypothesis before running this experiment? |
| Bisection | Have I narrowed to the smallest change that caused the regression? |
| Errors | Have I read the exact error message and the full stack trace? |
| State | Have I inspected the actual value, type, and shape — not assumed? |
| Root cause | Can I answer "but why?" with an invariant, not "code is wrong"? |
| Fix layer | Is the fix at the producer / boundary, not the consumer / interior? |
| Regression test | Does a test fail on the broken code and pass on the fixed code? |
| Adjacent bugs | Have I looked for other consumers of the same broken producer? |
| Documentation | Will a future engineer understand the cause from the commit / PR / postmortem? |

---

## Sources

This skill synthesizes principles from established works and modern practice:

- **Why Programs Fail: A Guide to Systematic Debugging** — Andreas Zeller (2nd ed., 2009). The hypothesis-driven framework, delta debugging, and bisection rigor.
- **Debugging: The 9 Indispensable Rules for Finding Even the Most Elusive Software and Hardware Problems** — David J. Agans (2002). "Understand the system", "Make it fail", "Quit thinking and look", and the rest of the timeless rules.
- **The Pragmatic Programmer** — Andy Hunt and Dave Thomas (20th anniv. ed., 2019). Rubber duck debugging, "select isn't broken", and the discipline of trusting nothing you have not verified.
- **Site Reliability Engineering** — Beyer, Jones, Petoff, Murphy (2016). Postmortem culture, blameless incident reviews, action item discipline.
- **The Field Guide to Understanding 'Human Error'** — Sidney Dekker (3rd ed., 2014). Systemic vs. individual causation in incident analysis.
- **Modern debugging ecosystem** — IDE debuggers (PyCharm, VS Code, IntelliJ), Chrome DevTools, OpenTelemetry, structured-logging frameworks: documentation and consensus as of 2025.

The skill's specific rule numbering (D1-D7 priority, ID prefixes in `reference-smells.md`) is original to this repo and chosen for review legibility.
