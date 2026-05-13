# TypeScript / JavaScript Debugging — Before / After

Concrete examples of systematic debugging applied to common JS/TS bugs.

---

## Example 1: React component "sometimes shows stale data"

### Bug Report

> The `OrderSummary` component sometimes shows the previous order's total after navigating from one order to another. Refreshing the page fixes it.

### Poor Investigation

```tsx
// Quick fix proposed
function OrderSummary({ orderId }: Props) {
  const [order, setOrder] = useState<Order | null>(null);
  useEffect(() => {
    fetchOrder(orderId).then(setOrder);
  }, [orderId]);
  return <div>{order?.total ?? "Loading..."}</div>;
}
```

> "Maybe it's a React rendering issue. Added `key={orderId}` to force remount."

**Problems:**
- D1: No repro captured. Speculative fix.
- D2: `key={orderId}` papers over the symptom (force remount), doesn't address why state is stale.
- D5: No hypothesis about *why* the state is stale.

### Better Investigation

**Step 1: Repro.**

Open Chrome DevTools, network throttling set to "Slow 3G". Navigate from order #1 → order #2 rapidly. Bug reproduces 100% under slow network.

**Step 2: Hypothesis.**

> H1: `fetchOrder(orderId)` is racing — the first request (slow) resolves after the second (fast), and `setOrder` is called with the stale data last.

**Step 3: Verify.**

Add temporary logging:
```tsx
useEffect(() => {
  console.log("fetching", orderId);
  fetchOrder(orderId).then(o => {
    console.log("resolved", o.id, "current prop was", orderId);
    setOrder(o);
  });
}, [orderId]);
```

Output when reproducing:
```
fetching 1
fetching 2
resolved 2  current prop was 2
resolved 1  current prop was 2   <-- BUG: stale response wins
```

Hypothesis confirmed.

**Step 4: Fix at the right layer.**

The bug is not in React — it's that the fetch is not cancelled when the component re-runs the effect. Fix with `AbortController`:

```tsx
function OrderSummary({ orderId }: Props) {
  const [order, setOrder] = useState<Order | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchOrder(orderId, { signal: controller.signal })
      .then(setOrder)
      .catch((e) => {
        if (e.name !== "AbortError") throw e;
      });
    return () => controller.abort();
  }, [orderId]);

  return <div>{order?.total ?? "Loading..."}</div>;
}
```

**Step 5: Regression test.**

```tsx
test("displays current order even when previous fetch resolves later", async () => {
  const slowFirst = deferred<Order>();
  const fastSecond = Promise.resolve(ORDER_2);

  vi.mocked(fetchOrder)
    .mockImplementationOnce(() => slowFirst.promise)
    .mockImplementationOnce(() => fastSecond);

  const { rerender } = render(<OrderSummary orderId={1} />);
  rerender(<OrderSummary orderId={2} />);

  // Resolve the slow first fetch AFTER navigating to #2.
  slowFirst.resolve(ORDER_1);

  await waitFor(() => {
    expect(screen.getByText("99.99")).toBeInTheDocument(); // ORDER_2 total
  });
  // Crucially: ORDER_1's total never appears.
  expect(screen.queryByText("42.00")).not.toBeInTheDocument();
});
```

**Step 6: Adjacent audit.**

`rg "useEffect.*fetch" src/` — find every other component that fetches in an effect without cancellation. Many will have the same bug latent.

---

## Example 2: Unhandled promise rejection in Node.js

### Bug Report

> The Node service crashes once a day with no clear error. Logs show `(node:1234) UnhandledPromiseRejectionWarning` but no useful stack.

### Poor Investigation

> Added `process.on("uncaughtException", () => process.exit(1))` to "ensure clean restart".

**Problems:**
- D2: Restart-as-fix hides the actual bug.
- D6: Intermittent dismissed.
- O2: No correlation — the warning lacks the request that triggered it.

### Better Investigation

**Step 1: Capture the full stack.**

```js
// Catch unhandled rejections globally during investigation
process.on("unhandledRejection", (reason, promise) => {
  console.error("UNHANDLED REJECTION", {
    reason,
    stack: reason instanceof Error ? reason.stack : "no stack",
    promise,
  });
});
```

Deploy. Wait for the next occurrence. Now the log has:
```
UNHANDLED REJECTION  TypeError: Cannot read properties of undefined (reading 'id')
  at processPayment (services/payments.ts:47:23)
  at async retryHandler (services/queue.ts:122:9)
```

**Step 2: Hypothesis.**

> H1: `processPayment` accesses `customer.id` without checking that `customer` exists. The retry handler must be passing undefined when the customer was deleted between enqueue and dequeue.

**Step 3: Verify.**

```bash
# Search for cases where customer is deleted but jobs are still queued.
$ grep -A 2 "deleted.*customer" logs/audit.log | head -20
```

Found: 3 deleted customers had pending payment retries.

**Step 4: Root cause.**

Two problems:
1. Producer: payment-retry jobs don't cancel when the customer is deleted.
2. Consumer: `processPayment` assumes the customer still exists.

Fix both layers:

```typescript
// services/payments.ts — consumer fix (defensive)
export async function processPayment(customerId: string, amount: number) {
  const customer = await customers.findById(customerId);
  if (!customer) {
    logger.warn("Skipping payment for deleted customer", { customerId });
    return { skipped: true, reason: "customer_deleted" };
  }
  // ...
}

// services/customers.ts — producer fix (root cause)
export async function deleteCustomer(id: string) {
  await db.transaction(async (tx) => {
    await tx.customers.delete(id);
    await paymentQueue.cancelByCustomer(id); // <-- cancel pending retries
  });
}
```

**Step 5: Regression tests.**

```typescript
test("processPayment skips gracefully when customer is deleted", async () => {
  const result = await processPayment("deleted-id", 100);
  expect(result.skipped).toBe(true);
  expect(result.reason).toBe("customer_deleted");
});

test("deleteCustomer cancels pending payment retries", async () => {
  await paymentQueue.enqueue({ customerId: "c1", amount: 100 });
  await deleteCustomer("c1");
  expect(await paymentQueue.pending()).toEqual([]);
});
```

---

## Example 3: Source map missing → useless production error

### Bug Report

> Sentry shows `Uncaught TypeError: r is not a function at https://cdn/app.min.js:1:48273`. No stack, no context. Recurs 50x per day.

### Poor Investigation

> "Minified — impossible to debug. Try reproducing locally."

(One week passes. Cannot reproduce locally. Ticket stalls.)

### Better Investigation

**Step 1: The repro is in production telemetry; the missing piece is source maps.**

```bash
# Verify the build produces source maps.
$ ls dist/
app.min.js  # no app.min.js.map
```

Fix the build:
```js
// vite.config.ts
export default defineConfig({
  build: {
    sourcemap: true,
  },
});
```

**Step 2: Upload source maps to Sentry on every deploy.**

```bash
$ sentry-cli releases new "$VERSION"
$ sentry-cli releases files "$VERSION" upload-sourcemaps dist/
$ sentry-cli releases finalize "$VERSION"
```

**Step 3: Re-deploy. Wait for the next occurrence.**

Now Sentry shows:
```
Uncaught TypeError: emitDelta is not a function
  at handleEvent (src/realtime/socket.ts:142:11)
  at WebSocket.onmessage (src/realtime/socket.ts:88:7)
```

**Step 4: Inspect the actual code.**

```typescript
// src/realtime/socket.ts:142
function handleEvent(event: ServerEvent) {
  const handler = handlers[event.type];
  handler.emitDelta(event.payload);  // <-- handler is undefined when event.type is unknown
}
```

**Step 5: Hypothesis.**

> H1: The server is occasionally sending event types the client doesn't know about (e.g., after a server-side feature deploy precedes the client deploy).

**Step 6: Verify with logs.**

Add temporary logging of unknown event types — confirm. Server deployed a new event type two days ago; clients with older bundles cached.

**Step 7: Fix at the right layer.**

```typescript
function handleEvent(event: ServerEvent) {
  const handler = handlers[event.type];
  if (!handler) {
    logger.warn("Unknown event type from server", { type: event.type });
    return;  // ignore, don't crash
  }
  handler.emitDelta(event.payload);
}
```

Plus a process fix: client and server protocol versions are now negotiated on connect; the server downgrades for older clients.

**Step 8: Regression test.**

```typescript
test("handleEvent ignores unknown event types without crashing", () => {
  const warn = vi.spyOn(logger, "warn");
  expect(() => handleEvent({ type: "future_event_type", payload: {} })).not.toThrow();
  expect(warn).toHaveBeenCalledWith("Unknown event type from server", { type: "future_event_type" });
});
```

**Lesson:** "Cannot debug minified code" was a tooling gap, not a fundamental obstacle. Always ship source maps. Always upload them to your error tracker.
