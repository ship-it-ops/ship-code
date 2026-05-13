# Expected Review Output — fixture-1-python-flaky

---

## Test Review: input.py

### Critical (must fix before merge)

- **[T2-FLAKY] Line 11**: `time.sleep(2)` is a timing-dependent wait that will eventually flake under slow CI runners and is wasted time on fast ones. → Use explicit synchronization: poll for `s.status == "active"` with a timeout, or restructure `activate()` to return only after the state transition completes.

- **[T2-FLAKY] Lines 8 and 17**: Both `datetime.now()` calls are uncontrolled. If the test runs across midnight UTC on Dec 31 → Jan 1, the year-comparison fails. → Inject a clock or freeze time with `freezegun` / `time-machine`: `@time_machine.travel("2025-06-15")`.

### Important (should fix)

- **[T4-DESIGN] Lines 7-18**: `test_subscription` verifies three distinct concepts in one test: activation succeeds, charging succeeds, and the charge timestamp reflects current year. Failure of any one will mask the others. → Split into `test_activate_transitions_status_to_active`, `test_charge_customer_records_positive_amount`, `test_charge_customer_records_timestamp`.

- **[T1-COVERAGE] Test file**: Only the happy path is tested. Missing: what if `activate()` is called on an already-active subscription? What if `charge_customer` is called on a deactivated subscription? What if payment fails? → Add tests for each error path. Bugs live in negative paths.

- **[T5-DATA] Line 8**: Constructed directly with positional plan="pro" but no factory. Adding a field to `Subscription` will require updating this test. → Use a `SubscriptionFactory.pro()` factory method.

### Suggestions (improve when convenient)

- **[T7-ASSERT] Line 17**: `s.charged_amount > 0` is a weak assertion. We presumably know the exact expected amount for a "pro" subscription. → Assert the exact value: `assert s.charged_amount == PRO_PLAN_PRICE`.

- **[N4 — Naming] Line 7**: `test_subscription` does not describe what aspect of subscription is verified. → Rename per the split above (`test_activate_transitions_status_to_active`, etc.).

### What's Good

- The test exercises a realistic user-facing scenario (create → activate → charge) rather than testing a single method in isolation. After splitting, each sub-test still verifies a real outcome.
- Direct assertions on observable state (status, charged_amount, last_charged_at) rather than mocking and verifying internal call sequences.
