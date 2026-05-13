# Expected Review Output — fixture-2-typescript-types

---

## Code Review: input.ts

### Critical (must fix before merge)

- **[P1-BUG] Lines 3-17**: `forEach` does not await async callbacks. The function returns `results` immediately while the async work is still pending, so the array is empty (or partially filled) when returned. → Use `await Promise.all(data.orders.map(async (order) => { ... }))` or a `for...of` loop with `await`.

- **[P1-BUG] Line 5**: `customer.tier == "premium"` uses loose equality. → Use `===`. This is an ESLint rule (`eqeqeq`) and should be enforced project-wide.

### Important (should fix)

- **[P3-ERR] Line 23**: `fetch` is not checked for `response.ok`. A 404 or 500 still returns a Response object and `response.json()` is called on the error body, returning garbage. → Check `if (!response.ok) throw new Error(\`Customer ${id} fetch failed: ${response.status}\`)` before `.json()`.

- **[P3-ERR] Line 22**: Manual URL concatenation: `"/api/customers/" + id`. If `id` contains special characters (e.g., a slash), the URL is malformed. → Use `encodeURIComponent(id)` or a URL builder.

- **[P4-TEST] Line 1**: `processOrders` calls the global `fetch` indirectly via `fetchCustomer`. Cannot test without a real network or module-level mock. → Inject the fetcher (or use MSW for tests).

- **[P5-MAINT] Line 1**: Parameters and locals typed `any` defeat TypeScript's safety. `data`, `order`, `id` could be anything. → Define explicit types: `interface ProcessOrdersInput { orders: Order[] }`, etc.

### Suggestions (improve when convenient)

- **[P6-READ] Line 6**: Magic number `0.1` for premium discount. → Define `const PREMIUM_DISCOUNT_RATE = 0.1`.

- **[P6-READ] Lines 7-15**: Both branches build similar objects. → Compute `discount` (zero for non-premium) once, then push a single shape.

### What's Good

- The function is small, focused on a single transformation, and its return shape is consistent across branches.
- Using `await fetchCustomer(...)` instead of `.then` is the modern idiom and keeps the control flow readable.
