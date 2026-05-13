# Debug Review Output Example

This demonstrates the structured review format produced in review mode.

## Context

A pull request titled **"Fix login crash for legacy users (#4711)"** is up for review. The PR body says:

> Login was crashing for some users. Added a null check in `verify_password` to handle the case. Tested locally.

The diff:

```python
# auth/login.py
 def verify_password(user, password):
-    return bcrypt.checkpw(password.encode(), user.password_hash.encode())
+    if user.password_hash is None:
+        return False
+    return bcrypt.checkpw(password.encode(), user.password_hash.encode())
```

No tests added. No incident reference. Commit message: `"fix login"`.

## Review Output

```
## Debug Review: PR #4811 — "Fix login crash for legacy users"

### Critical (must fix before merge)

- **[D1-REPRO] PR description**: No reproduction case is captured. The PR
  says "some users" but does not identify which users, which environment,
  or how to trigger the crash. → Add to the PR: the exact user ID(s) that
  hit the bug, the request that failed, the stack trace, and the
  conditions that produce a NULL `password_hash`. Without this, we cannot
  verify the fix actually addresses the original failure.

- **[D2-SYMPTOM] auth/login.py:3**: The fix is at the consumer
  (`verify_password`), but a NULL `password_hash` is a producer bug. A user
  account with NULL `password_hash` should not exist — that violates the
  invariant that authenticated accounts have a hash. → Investigate why
  `password_hash` is NULL: is it a migration bug, a partial signup state,
  legacy accounts? Fix at the source. The consumer check papers over a
  data-integrity bug elsewhere.

- **[D4-TEST] PR**: No regression test added. → Add a test that fails
  without this change and passes with it. Suggested location:
  `tests/auth/test_login.py::test_login_handles_legacy_account_with_null_hash`.
  Use the exact failing user fixture from the bug report.

### Important (should fix)

- **[D5-HYPOTHESIS] PR description**: The PR does not state the hypothesis
  behind the fix. Why does returning False (instead of raising) match the
  intended behavior for legacy accounts? Could this silently lock users
  out who should have been migrated? → State the hypothesis: "Legacy
  accounts created before 2023-06 have NULL password_hash because they
  used SSO-only. Returning False prevents the crash; these users will
  receive a 'try Google sign-in' prompt downstream." Confirm this matches
  the actual data.

- **[D6-INTERMITTENT] PR description**: "Tested locally" but the bug only
  reproduces with production-shaped data. → Either reproduce in a
  staging-like environment (with anonymized production data) or load the
  specific failing fixture into the local test.

### Suggestions (improve when convenient)

- **[D7-DOC] Commit message**: "fix login" tells future debuggers
  nothing. → Rewrite: "Fix login crash for legacy accounts with NULL
  password_hash (#4711). Cause: SSO-only accounts created before 2023-06
  have no password hash; verify_password tried to encode NULL. Fix at the
  consumer for now; producer-side cleanup tracked in #4812."

### What's Good

- The fix correctly avoids broadening the exception handler — it does not
  swallow other errors from `bcrypt.checkpw`. Many fixes for "login
  crash" turn into bare `except:` blocks that hide real problems.
- The change is minimal and reviewable as a single concept. Easy to
  revert if the producer-side fix supersedes it.
```
