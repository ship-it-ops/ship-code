# Expected Review Output — fixture-2-typescript-mock-heavy

---

## Test Review: input.test.ts

### Critical (must fix before merge)

- **[T3-LEVEL] Lines 17-25 and 31-39**: This test mocks every collaborator and verifies that each was called. The test passes whether or not the checkout actually works — it only verifies that the orchestration code calls the orchestrated services. → Use fakes for state-based collaborators (`fakeInventory`, `fakeOrderRepo`) and assert on observable outcomes: `expect(fakeOrderRepo.findById(42)?.total).toBe(99.99)`, `expect(fakeNotifier.sentMessages).toHaveLength(1)`.

- **[T1-COVERAGE] Test file**: Only the happy path is tested. Missing: inventory unavailable, payment declined, repository save fails, partial-failure recovery (e.g., charge succeeded but save failed). → Each error path needs a test. The checkout flow is exactly the kind of code where bugs live in error handling.

### Important (should fix)

- **[T4-DESIGN] Line 31**: Test name `"processes checkout"` is vague. → Use `should_save_order_with_calculated_total_after_successful_payment` or similar behavior-describing name.

- **[T6-MAINT] Lines 5-13, 16-24**: 8 typed-as-`any` collaborators and 16 lines of mock setup for an 8-line test. → If real fakes are too much, use a builder: `CheckoutFixture.standard()` returns the SUT with all dependencies pre-wired and the test can override only what it needs.

- **[T4-DESIGN] Lines 33-39**: Verifying `toHaveBeenCalled()` on every mock without checking arguments is "mock-orchestration testing". → Verify with arguments (`expect(mockPaymentGateway.charge).toHaveBeenCalledWith(99.99, expect.objectContaining({ customerId: "user-1" }))`) or, better, switch to fakes and assert on state.

- **[T5-DATA] Lines 17-23**: Hardcoded magic values (1, 2, 99.99, "ch_123") with no semantic intent. → Define `const STANDARD_ITEM_PRICE = 99.99` and `const STANDARD_CART = [{ id: SKU_WIDGET, qty: 2 }]` to make the scenario obvious.

### Suggestions (improve when convenient)

- **[T6-MAINT] Lines 5-13**: `let mockX: any` with `any` defeats TypeScript. → Type as `Mocked<CartService>` etc., from Vitest's `Mocked` helper, or define test-double types explicitly.

### What's Good

- Uses constructor injection (line 25) for the SUT — testability is built in even if this test does not exploit it. Switching to fakes is straightforward.
- `beforeEach` resets mocks per test — at least there is no state leakage between tests in this file.
