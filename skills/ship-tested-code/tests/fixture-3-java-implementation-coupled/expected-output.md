# Expected Review Output — fixture-3-java-implementation-coupled

---

## Test Review: DiscountCalculatorTest.java

### Critical (must fix before merge)

- **[T3-LEVEL] Lines 12-23**: A full Selenium E2E test, including `Thread.sleep(1000)` and `Thread.sleep(2000)`, to verify that 10% off 100 equals 90. This is unit-test logic dressed up as E2E. → Test the calculator directly: `assertThat(new DiscountCalculator().apply(100.0, "SAVE10")).isEqualTo(new BigDecimal("90.00"))`. Reserve E2E for full checkout flows.

- **[T2-FLAKY] Lines 16, 20**: `Thread.sleep(1000)` and `Thread.sleep(2000)` are timing-dependent waits that flake on slow CI. → Use Selenium's `WebDriverWait` with explicit conditions: `wait.until(ExpectedConditions.textToBe(By.id("total"), "90.00"))`.

- **[T4-DESIGN] Lines 27-35**: `testCalcInternal` uses `Mockito.spy` to verify that the calculator calls `lookupCouponInDatabase` and `multiplyByRate` — both private implementation details. Refactoring the internal helpers will break this test even when behavior is unchanged. → Test the observable behavior: `assertThat(calc.apply(100.0, "SAVE10")).isEqualTo(new BigDecimal("90.00"))`. Remove the spy.

### Important (should fix)

- **[T1-COVERAGE] File**: Missing tests for: unknown coupon, expired coupon, coupon for different category, zero total, negative total, very large total, multiple coupons. → Add parameterized test with `@CsvSource` covering each case.

- **[T5-DATA] Line 22**: Magic value `"90.00"` with no derivation. A reader cannot tell whether the test is asserting "10% off 100 = 90" or "fixed 10 off = 90". → Use named constants: `static final BigDecimal SAVE10_DISCOUNTED_TOTAL = new BigDecimal("90.00");` or inline the calculation: `assertEquals(BASE_TOTAL.multiply(SAVE10_RATE), result)`.

- **[N1 — Naming] Lines 12, 27**: `test1` and `testCalcInternal` describe nothing. → Use behavior-describing names: `applies_save10_coupon_reduces_total_by_ten_percent` and `apply_unknown_coupon_returns_original_total`.

### Suggestions (improve when convenient)

- **[T6-MAINT] Line 14**: Hardcoded URL `"http://localhost:8080"` couples the test to a specific environment. → Use a test profile / configuration source. Better: skip the E2E entirely per T3 above.

- **[A1 — Assertion strength] Line 22**: `assertEquals` with String comparison on a numeric field is brittle to formatting changes ("90", "90.0", "90.00" are all numerically equal but string-different). → Compare as `BigDecimal` with `isEqualByComparingTo`.

### What's Good

- The test file at least targets the calculation logic — the *intent* of `testCalcInternal` is to verify discount math. After rewriting per T4, it becomes a clean, focused unit test in 3 lines.
