# Java Debugging — Before / After

Concrete examples of systematic debugging applied to common Java bugs.

---

## Example 1: NullPointerException on a deeply chained call

### Bug Report

> Production stack trace:
> ```
> NullPointerException at OrderController.confirm(OrderController.java:42)
> ```

### Poor Investigation

```java
// Quick fix proposed
public ResponseEntity<?> confirm(@PathVariable Long id) {
    Order order = orderService.findById(id);
    if (order == null || order.getCustomer() == null
            || order.getCustomer().getAddress() == null) {
        return ResponseEntity.badRequest().build();
    }
    String city = order.getCustomer().getAddress().getCity();
    // ...
}
```

**Problems:**
- D2: Defensive null checks at the controller treat symptoms, not the root cause.
- I8: Without **Helpful NullPointerException** enabled (Java 14+), the trace doesn't say *which* dereference was null. The fix is speculative.
- D5: No verification that `customer.address` is the null one (vs. `order.customer` or `order` itself).

### Better Investigation

**Step 1: Enable Helpful NullPointerExceptions.**

Run the JVM with `-XX:+ShowCodeDetailsInExceptionMessages` (default-on in Java 15+). Now the stack trace becomes:

```
NullPointerException: Cannot invoke "Address.getCity()" because the return value
of "Customer.getAddress()" is null
    at OrderController.confirm(OrderController.java:42)
```

Specific: `Customer.getAddress()` returned null. Not `order`, not `customer`.

**Step 2: Hypothesis.**

> H1: Some Customer rows have NULL `address_id`. Likely accounts imported from a legacy system that didn't capture addresses.

**Step 3: Verify with data.**

```sql
SELECT count(*) FROM customers WHERE address_id IS NULL;
-- 1247 rows
SELECT min(created_at), max(created_at) FROM customers WHERE address_id IS NULL;
-- 2019-01-15  2021-08-22  (all from the legacy import window)
```

Hypothesis confirmed.

**Step 4: Identify the right layer.**

The bug is **not** "controller didn't check". The bug is "we have legacy customers with no address, and confirm() requires an address". Two options:

- (A) Make `address` mandatory at the data layer — backfill missing addresses or block confirmation upstream.
- (B) Make `confirm()` explicitly handle the "no address" case as a domain concept (return 422 with a "complete your profile" message).

(B) is the right product behavior. The fix lives in the **domain**, not the controller's null-checks:

```java
// Order.java — domain model
public ConfirmationResult confirm() {
    if (!customer.hasCompleteAddress()) {
        return ConfirmationResult.incompleteProfile(customer.getId());
    }
    // ... real confirmation logic
    return ConfirmationResult.confirmed(this);
}

// Customer.java
public boolean hasCompleteAddress() {
    return address != null && address.isComplete();
}
```

```java
// OrderController.java
public ResponseEntity<?> confirm(@PathVariable Long id) {
    Order order = orderService.findByIdOrThrow(id);
    ConfirmationResult result = order.confirm();
    return switch (result.kind()) {
        case CONFIRMED -> ResponseEntity.ok(result.order());
        case INCOMPLETE_PROFILE -> ResponseEntity.status(422)
            .body(Map.of("error", "complete_profile_required",
                         "customerId", result.customerId()));
    };
}
```

**Step 5: Regression tests.**

```java
@Test
@DisplayName("confirm returns INCOMPLETE_PROFILE when customer has no address")
void confirmIncompleteProfile() {
    Customer legacy = CustomerFactory.legacyWithoutAddress();
    Order order = OrderFactory.forCustomer(legacy);

    ConfirmationResult result = order.confirm();

    assertThat(result.kind()).isEqualTo(Kind.INCOMPLETE_PROFILE);
    assertThat(result.customerId()).isEqualTo(legacy.getId());
}

@Test
@DisplayName("controller returns 422 for customer with incomplete profile")
void controllerReturns422() throws Exception {
    Long orderId = seedOrderForLegacyCustomer();

    mockMvc.perform(post("/orders/{id}/confirm", orderId))
        .andExpect(status().isUnprocessableEntity())
        .andExpect(jsonPath("$.error").value("complete_profile_required"));
}
```

**Step 6: Adjacent audit.**

Search for every other place that dereferences `customer.getAddress()`:
```bash
$ rg "customer\.getAddress\(\)" --type java
```
Many will have the same latent bug. Fix or defer with a tracking ticket.

---

## Example 2: Race condition causing duplicate writes

### Bug Report

> About once a week, a customer reports getting two welcome emails. Database shows two `WelcomeEmailSent` rows for that customer.

### Poor Investigation

```java
// Proposed: deduplicate on read
public void sendWelcome(Customer c) {
    if (emailLog.alreadySent(c.getId(), WELCOME)) return;  // <-- check
    emailGateway.send(...);
    emailLog.record(c.getId(), WELCOME);  // <-- act
}
```

**Problems:**
- F1: Symptom patch — the check-then-act is itself the race.
- D6: Intermittent, no investigation of *what* race.
- I3: No hypothesis stated.

### Better Investigation

**Step 1: Hypothesis.**

> H1: `sendWelcome` is being invoked twice concurrently (e.g., from two threads or two service instances), and the `alreadySent` check on both returns false before either `record` call commits.

**Step 2: Verify.**

```sql
-- Find duplicate WelcomeEmailSent rows and inspect timestamps
SELECT customer_id, count(*), array_agg(sent_at)
FROM welcome_email_log
GROUP BY customer_id HAVING count(*) > 1
ORDER BY customer_id DESC LIMIT 10;
```

Result: timestamps for each pair are within 200ms. Two concurrent invocations.

```bash
# Check service logs for two simultaneous calls
$ grep "sendWelcome customer_id=4711" logs/ | sort
2025-04-30T10:01:23.142  pod-a-xyz
2025-04-30T10:01:23.298  pod-b-abc
```

Two pods invoked it. Hypothesis confirmed: the welcome trigger is firing in both consumers of the same Kafka topic (a Kafka consumer group misconfiguration is the cause).

**Step 3: Root cause has two layers.**

1. **Kafka group config** — both pods should be in the same consumer group but were in different ones, causing duplicate delivery. (Infra fix.)
2. **Application code** — even with a correct Kafka config, the check-then-act is not atomic. Must be safe under concurrent invocation. (Application fix.)

**Step 4: Application fix — use a database constraint as the atomicity guarantee.**

```sql
ALTER TABLE welcome_email_log ADD CONSTRAINT uniq_customer UNIQUE (customer_id);
```

```java
public SendResult sendWelcome(Customer c) {
    // Reserve the slot atomically. If we lose the race, we know to skip.
    boolean reserved = emailLog.tryReserve(c.getId(), WELCOME);
    if (!reserved) {
        return SendResult.alreadySent(c.getId());
    }
    try {
        emailGateway.send(...);
        emailLog.markSent(c.getId(), WELCOME);
        return SendResult.sent(c.getId());
    } catch (Exception e) {
        emailLog.releaseReservation(c.getId(), WELCOME);
        throw e;
    }
}

// emailLog.tryReserve uses INSERT ... ON CONFLICT DO NOTHING and returns
// true only if the row was created, leveraging the UNIQUE constraint.
```

**Step 5: Regression test (concurrent stress test).**

```java
@Test
@DisplayName("sendWelcome is safe under concurrent invocation — exactly one email")
void sendWelcomeAtomic() throws InterruptedException {
    Customer c = customers.save(CustomerFactory.standard());
    int threads = 20;
    var latch = new CountDownLatch(threads);
    var sentCount = new AtomicInteger(0);
    var skipCount = new AtomicInteger(0);
    var pool = Executors.newFixedThreadPool(threads);

    for (int i = 0; i < threads; i++) {
        pool.submit(() -> {
            try {
                SendResult r = service.sendWelcome(c);
                if (r.kind() == SendResult.Kind.SENT) sentCount.incrementAndGet();
                else skipCount.incrementAndGet();
            } finally {
                latch.countDown();
            }
        });
    }
    latch.await(10, TimeUnit.SECONDS);

    assertThat(sentCount.get()).isEqualTo(1);
    assertThat(skipCount.get()).isEqualTo(threads - 1);
    assertThat(emailGateway.sentCount()).isEqualTo(1);  // exactly one real send
}
```

---

## Example 3: "Sometimes the application freezes"

### Bug Report

> The application becomes unresponsive after running for several hours. Restart fixes it temporarily.

### Poor Investigation

> Set up a cron job to restart the JVM every 4 hours.

**Problems:**
- D2: Restart-as-fix.
- D6: "Sometimes" never investigated.
- C5: Fatigue fix — settled for the workaround.

### Better Investigation

**Step 1: Get a thread dump while the application is frozen.**

```bash
$ jcmd <pid> Thread.print > /tmp/thread-dump-frozen.txt
# Or use jstack <pid>
```

**Step 2: Search the dump for "deadlock" or many BLOCKED threads.**

```
Found one Java-level deadlock:
=============================
"http-nio-8080-exec-12":
  waiting to lock monitor 0x00007f8a0c003fa8 (object 0x0000000700c00100, a com.example.OrderRepository),
  which is held by "http-nio-8080-exec-7"
"http-nio-8080-exec-7":
  waiting to lock monitor 0x00007f8a0c004288 (object 0x0000000700c00200, a com.example.InventoryRepository),
  which is held by "http-nio-8080-exec-12"
```

Classic deadlock: two threads, two locks, opposite acquisition order.

**Step 3: Trace the source.**

```java
// OrderService.java
public void placeOrder(Order o) {
    synchronized (orderRepo) {
        synchronized (inventoryRepo) {
            // ...
        }
    }
}

// InventoryService.java
public void restock(SKU sku) {
    synchronized (inventoryRepo) {
        synchronized (orderRepo) {  // <-- opposite order!
            // ...
        }
    }
}
```

**Step 4: Root cause and fix.**

Synchronizing on repository instances is the wrong design. The right fix is:
- Use database-level locking with transactions (`SELECT ... FOR UPDATE`).
- Or, if in-memory locking is truly needed, **always acquire locks in the same global order** (e.g., always lock the lower object hash first).

```java
// OrderService.java
@Transactional
public void placeOrder(Order o) {
    // DB locks acquired in a fixed order via PK
    orderRepo.lockForUpdate(o.getId());
    inventoryRepo.lockForUpdate(o.getSkus());
    // ...
}

@Transactional
public void restock(SKU sku) {
    orderRepo.lockForUpdate(sku.getReservedOrderIds());  // same order: orders first
    inventoryRepo.lockForUpdate(List.of(sku));
}
```

**Step 5: Regression test.**

```java
@Test
@DisplayName("placeOrder and restock do not deadlock under concurrent load")
@Timeout(value = 30, unit = TimeUnit.SECONDS)
void noDeadlockUnderConcurrency() throws InterruptedException {
    int N = 50;
    var pool = Executors.newFixedThreadPool(N);
    var latch = new CountDownLatch(N * 2);

    for (int i = 0; i < N; i++) {
        pool.submit(() -> { orderService.placeOrder(randomOrder()); latch.countDown(); });
        pool.submit(() -> { inventoryService.restock(randomSku()); latch.countDown(); });
    }

    // If a deadlock occurs, latch.await times out and JUnit fails the test.
    assertThat(latch.await(20, TimeUnit.SECONDS)).isTrue();
}
```

**Step 6: Document for the team.**

Add to the team's coding conventions doc: "Acquire database locks in a fixed global order — orders → inventory → payments. Never synchronize on repository instances."
