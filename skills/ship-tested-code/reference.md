# Testing Best Practices Reference

Detailed rules organized by concern area, combining established testing principles
from TDD By Example (Beck), Full Stack Testing (Mohan), and modern industry consensus.

---

## 1. Test Design Fundamentals

### Principles

1. **Arrange-Act-Assert (AAA) pattern -- enforced strictly.** Every test has three visually distinct phases. When setup, action, and verification blur together, the test becomes hard to understand and debug.
2. **One concept per test.** Each test verifies a single behavior or scenario. Multiple assertions are fine if they all verify the same concept. If a test can fail for multiple unrelated reasons, split it.
3. **Given-When-Then mental model.** Even without Gherkin syntax, every test answers: given what state, when what action happens, then what is the expected outcome?
4. **Assertion specificity.** Assert the exact thing that proves the behavior. `assertEquals("shipped", order.status)` not `assertNotNull(order)`. Weak assertions give false confidence.
5. **Test boundary identification.** For every unit under test, explicitly decide what is inside the boundary (real) and what is outside (doubled). When this boundary is wrong, tests either break constantly (too wide) or miss real bugs (too narrow).
6. **Behavior-based, not implementation-based testing.** If you refactor the internals of a function and no external behavior changes, zero tests should break. Tests that verify internal state, mock call ordering, or private method behavior are implementation-coupled.
7. **F.I.R.S.T. properties.** Tests must be Fast, Independent (no ordering dependencies), Repeatable (in any environment), Self-validating (boolean pass/fail), and Timely (written alongside production code).

### Common Violations

- Tests with interleaved arrange/act/assert phases.
- A single test verifying five different behaviors with separate act-assert sequences.
- `assertTrue(result != null)` when `assertEquals(expected, actual)` would be more specific.
- Tests that fail when you rename a private method without changing any public behavior.
- Tests that require running other tests first to set up state.

### Quick Examples

**Before:**
```python
def test_account():
    a = Account()
    a.deposit(100)
    a.withdraw(50)
    assert a.balance == 50
    a.withdraw(100)
    assert a.balance == 50  # overdraft blocked
```

**After:**
```python
def test_withdraw_reduces_balance():
    account = Account(balance=100)
    account.withdraw(50)
    assert account.balance == 50

def test_withdraw_exceeding_balance_is_rejected():
    account = Account(balance=50)
    account.withdraw(100)
    assert account.balance == 50
```

---

## 2. Test Strategy & Architecture

### Principles

1. **The test pyramid is architecture-dependent.** There is no universal shape. Monoliths benefit from heavy unit testing (pyramid). Frontend-heavy apps benefit from integration-focused testing (trophy). Microservices need contract tests and integration tests (diamond). Choose based on where your risk concentrates.
2. **Unit tests for business logic.** Pure business rules, calculations, state transitions, and domain logic get fast, isolated unit tests. These form the foundation regardless of architecture.
3. **Integration tests at service boundaries.** Test the seams where your code meets external systems: databases, message brokers, HTTP clients, file systems. Use containerized dependencies (TestContainers) for realism.
4. **Contract tests between services.** For microservices, consumer-driven contract testing (Pact) is more valuable than end-to-end integration tests. The consumer defines what it expects; the provider verifies it can satisfy those expectations.
5. **E2E tests for critical user journeys only.** Limit to 5-10% of your suite. Keep under 30 minutes. Test: signup, login, core transaction, payment flow. Do not try to achieve high coverage with E2E tests.
6. **Static analysis as the foundation.** Linting, type checking, and formatting are the cheapest tests. They catch entire categories of bugs at zero runtime cost. Enforce in CI before any test runs.
7. **CI pipeline layering by speed.** Static analysis (seconds) -> Unit tests (<3 min) -> Integration tests (<10 min) -> E2E tests (<30 min). Fast feedback first, expensive tests later.

### Common Violations

- An E2E test suite of 800 tests taking 45 minutes that nobody waits for.
- Unit tests that spin up a database for simple business logic.
- Microservices without contract tests, relying on manual integration testing.
- No static analysis in CI -- linting done locally (or not at all).
- Integration tests that mock everything, defeating the purpose.

### Quick Examples

**Test strategy for a monolith:**
```
Unit tests (70%): Domain logic, calculations, validation
Integration tests (20%): Database queries, API endpoints, caching
E2E tests (10%): Login → create order → checkout → confirmation
```

**Test strategy for microservices:**
```
Unit tests (40%): Service-internal business logic
Contract tests (30%): Consumer-driven contracts at service boundaries
Integration tests (25%): Service + containerized dependencies
E2E tests (5%): Critical cross-service workflows
```

---

## 3. TDD & Test-First Development

### Principles

1. **Red-Green-Refactor.** Write a failing test (red). Write the minimum code to make it pass (green). Clean up while keeping tests green (refactor). This is one cycle. Repeat.
2. **Fake It ('Til You Make It).** Return a constant to make the test pass, then gradually generalize. This ensures you take the smallest possible step and your test actually fails for the right reason.
3. **Triangulation.** When you have a constant (fake) implementation, write a second test that forces you to generalize. Two data points triangulate toward the real algorithm.
4. **Obvious Implementation.** When the implementation is truly obvious, just type it in. If it turns out you were wrong (test fails unexpectedly), fall back to Fake It.
5. **One Step Test.** Pick the next test that teaches you something and that you are confident you can make pass. Build from known to unknown.
6. **Starter Test.** When stuck, write a degenerate test case -- the simplest possible scenario (empty input, single element, trivial case). This gets you moving.
7. **TDD as design feedback.** Hard-to-test code signals a design problem: too many dependencies, hidden side effects, tight coupling. Listen to the tests. If writing a test requires 60 lines of setup, the production code has too many responsibilities.
8. **When TDD fits vs. when it doesn't.** TDD excels for business logic, domain rules, algorithms, and state machines. It is less useful for exploratory prototyping, UI layout, infrastructure-as-code, and integration glue. Use judgment.
9. **Step size.** Take the smallest step that teaches you something. When confident, take bigger steps. When confused, take smaller steps. After an unexpected failure, revert to the smallest possible step.
10. **Clean Check-in.** Always check in with all tests passing. A broken test in version control breaks everyone's flow. If you must stop mid-work, either fix the test or revert.

### Common Violations

- Writing all production code first, then backfilling tests afterward (misses design feedback).
- Red-green without refactor (accumulating mess).
- Taking steps too large -- writing a full feature before running any test.
- Treating TDD as a religion rather than a tool -- demanding it for trivial getters or config wiring.
- Never deleting tests during refactoring, even when they become redundant.

---

## 4. Mocking, Faking & Test Doubles

### Principles

1. **Choose doubles by purpose.** Fake: replace a slow/external collaborator with a fast in-memory equivalent when you care about state outcomes (repositories, caches, queues). Mock: verify interaction protocols -- use when the assertion IS whether a call was made (e.g., "email sent exactly once"). Stub: provide canned responses to queries.
2. **Prefer fakes over mocks.** Fakes give you realistic behavior and catch more bugs. An in-memory repository that implements the same interface as your real one is more valuable than a mock that returns hardcoded values.
3. **Mock at boundaries only.** External APIs you do not control, clocks, random number generators, file systems in unit tests. Do not mock your own code between layers -- that tests wiring, not behavior.
4. **Contract tests replace mocking between services.** Instead of mocking Service B in Service A's tests, use consumer-driven contracts. Service A's contract defines what it expects; Service B verifies it can deliver.
5. **Never mock value objects or data structures.** A `User` or `Order` object should be the real thing in tests. Mocking data objects adds complexity and hides bugs.
6. **Warning: over-mocking.** When you mock all collaborators, your test verifies that your mocks are wired correctly, not that your code works. If your mock setup is longer than your test logic, reconsider the testing approach.
7. **Mock behavior, not data.** When you must mock, define behavior (`when(repo.findById(1)).thenReturn(user)`) not procedural expectations (`verify(repo).findById(1); then verify(repo).save(user); then verify(notifier).send()`).

### Common Violations

- Every dependency mocked, including simple value objects and domain entities.
- Mock setup spanning 40+ lines with chained `.when().thenReturn()` calls for a 5-line test.
- Verifying exact call sequences (`verify(mock, times(1)).method(arg)`) for non-critical interactions.
- Mocking the system under test itself (testing that a class calls its own methods).
- Using mocks in integration tests where a containerized dependency would be more appropriate.

### Quick Examples

**Before (over-mocked):**
```java
@Test
void testProcessOrder() {
    when(validator.validate(any())).thenReturn(true);
    when(pricer.calculate(any())).thenReturn(new Price(100));
    when(inventory.reserve(any())).thenReturn(true);
    when(repo.save(any())).thenReturn(savedOrder);
    when(notifier.send(any())).thenReturn(true);

    service.processOrder(order);

    verify(validator).validate(order);
    verify(pricer).calculate(order);
    verify(inventory).reserve(order);
    verify(repo).save(any());
    verify(notifier).send(any());
}
```

**After (focused):**
```java
@Test
void processOrder_saves_order_with_calculated_price() {
    var order = OrderFactory.standard();
    var service = new OrderService(realValidator, realPricer, fakeInventory, fakeRepo, stubNotifier);

    service.processOrder(order);

    assertThat(fakeRepo.findById(order.id()))
        .isPresent()
        .hasValueSatisfying(saved -> assertThat(saved.total()).isEqualTo(new Price(100)));
}
```

---

## 5. Test Data Management

### Principles

1. **Factory/Builder pattern always.** Never construct test objects directly with long constructor calls. Use factories that provide sensible defaults and reveal intent through method names.
2. **Test data tells a story.** The data in your test should make the scenario obvious. If testing expired subscriptions, the expiry date should be visibly in the past, not hidden in a factory three files away.
3. **Test data isolation by level.** Unit tests: in-memory objects, no database. Integration tests: transaction rollback per test or dedicated schema per test run. E2E tests: dedicated environment with seed data, each test creates its own entities with unique identifiers.
4. **Realistic data generation.** Use libraries like Faker/Bogus for realistic-looking data, but with seeded randomness for reproducibility. Do not use "test", "asdf", "foo" -- you miss bugs that real data patterns expose (unicode, long strings, special characters).
5. **Never use production data in tests without anonymization.** This is a compliance violation. Generate synthetic data that matches production patterns.
6. **Test edge cases with data.** For every input field, test: null/undefined, empty string, maximum length, unicode characters, special characters, negative numbers, zero, boundary values.
7. **Database state management.** For integration suites: start from a known state, use migrations to keep test schema in sync, prefer programmatic setup over SQL dump files. SQL dumps rot fast.

### Common Violations

- `new User("John", "john@test.com", "password", null, null, true, 0)` in every test -- breaks when fields are added.
- Shared mutable test data: one test inserts a user, another test depends on that user existing.
- Test data that obscures the scenario: five users created but only one matters to the assertion.
- Production database dumps used as test fixtures (PII risk, staleness, large file sizes).
- Hard-coded IDs: `user_id = 42` scattered across tests, colliding when run in parallel.

### Quick Examples

**Before:**
```python
def test_expired_subscription():
    user = User("John", "Doe", "john@test.com", "plan_expired",
                datetime(2023, 1, 1), True, None, 0, "USD")
    assert not user.can_access_premium()
```

**After:**
```python
def test_expired_subscription_blocks_premium_access():
    user = UserFactory.with_expired_subscription()
    assert not user.can_access_premium()

# In factories.py:
class UserFactory:
    @staticmethod
    def with_expired_subscription():
        return User(
            name="Test User",
            email=f"test-{uuid4()}@example.com",
            subscription_expires_at=datetime.now() - timedelta(days=30),
        )
```

---

## 6. Flaky Test Prevention & Management

### Principles

1. **Root causes of flakiness.** Almost always one of: shared mutable state between tests, timing/race conditions, environment differences (local vs CI), non-deterministic data (random values, timestamps, floating point), external service instability.
2. **No `sleep()` in tests.** Use explicit waits with conditions, polling with timeouts, or event-driven synchronization. Every `sleep()` in a test is a flaky test waiting to happen.
3. **Eliminate shared mutable state.** Every test creates its own data, uses its own transaction or isolated context, and cleans up after itself. Tests that share state will eventually run in wrong order.
4. **Deterministic data only.** No `Math.random()` or `datetime.now()` without a seeded generator or injected clock. No reliance on database auto-increment IDs for ordering.
5. **Isolate external dependencies.** If your test calls a real third-party API, it will flake. Use contract tests, service virtualization, or in-process fakes.
6. **Quarantine pattern.** When a test is identified as flaky, move it to a quarantine suite immediately. It still runs but does not block the pipeline. It shows up on a dashboard. Fix within 48 hours or delete.
7. **Rerun-and-track, not rerun-and-forget.** If CI retries failed tests and they pass on retry, log it. Track rerun rate per test. Any test needing reruns more than 2% of the time is flaky.
8. **Randomize test execution order.** If tests pass alphabetically but fail when randomized, you have hidden ordering dependencies. Find them early.
9. **Flaky rate above 2% is an emergency.** At this rate, developers start ignoring CI failures. The safety net is gone. Treat flakiness as a P1 incident.

### Common Violations

- `time.sleep(2)` to "wait for the async operation to complete."
- Tests that pass locally but fail in CI (or vice versa) due to environment differences.
- A "known flaky" tag that grows to 15% of the suite with no fix timeline.
- Tests that depend on a specific database row created by a previous test.
- Random test data without seeding, causing intermittent failures on specific values.

---

## 7. Testing Specific Architectures

### API Testing (REST, GraphQL, gRPC)

1. **Schema validation.** Validate request/response shapes against OpenAPI specs or protobuf definitions. Generate validators from specs, never hand-write them.
2. **Error path testing for every endpoint.** Test: malformed input, missing required fields, unauthorized access, not-found resources, conflict states, rate limiting.
3. **Contract testing for service boundaries.** Consumer defines expectations, provider verifies. This eliminates the need for expensive multi-service integration environments.
4. **GraphQL-specific.** Test query depth limits, N+1 detection, and partial failure responses. Test each resolver in isolation.

### Event-Driven Architecture

1. **Producer tests.** Verify the correct event is published with the correct payload. Use an in-memory or containerized broker. Assert on event shape, not downstream effects.
2. **Consumer tests.** Given a specific event, verify the consumer processes it correctly. Feed events directly to the handler in unit tests.
3. **Dead letter queue testing.** Publish a malformed event. Verify it lands in the DLQ with appropriate metadata.
4. **Idempotency verification.** Deliver the same event twice. Verify the system handles it correctly with no duplicates.
5. **Schema evolution.** Produce a message with schema v2, consume with a consumer expecting v1. Verify backward compatibility.

### Database Testing

1. **Migration testing in CI.** Apply migration to a database with representative data, verify schema correctness and data integrity. Test rollback. Use containerized databases, not SQLite.
2. **Repository tests cover complex queries.** Not just CRUD -- test multi-join queries, pagination edge cases, optimistic locking conflicts, unique constraint violations.
3. **Transaction boundary testing.** Test atomicity explicitly: inject failure between writes and verify neither persisted.
4. **Query performance regression.** For critical queries, capture execution plans. Alert if a migration causes a plan change.

### Async / Concurrent Code

1. **Await with timeout, never sleep.** Poll for the expected condition with a timeout. Use framework-provided async test utilities.
2. **Thread-stress tests.** Run N concurrent operations that should conflict, repeat M times. Non-deterministic but practical for catching races.
3. **Eventual consistency testing.** Publish event, poll read model until it reflects the expected state. Assert on final state, not intermediate states.

### Frontend Testing

1. **Component tests with Testing Library.** Query by role > label > text > testid. Test user-visible behavior, not internal state.
2. **Mock Service Worker (MSW) at the network level.** Do not mock your API client or hooks. Mock the network so real code executes.
3. **Accessibility testing.** Run axe-core in every component test. Supplement with manual screen reader testing quarterly.
4. **Visual regression.** Worth it for design systems and component libraries. Not worth it for rapidly changing UIs.
5. **Performance budgets in CI.** Bundle size limits (size-limit), Lighthouse score thresholds. Treat violations as test failures.

### Data Pipeline Testing

1. **Separate I/O from transformations.** Transformation logic is a pure function that takes input and returns output. Test it with small, deterministic DataFrames. I/O is tested separately at integration level.
2. **Schema validation on every pipeline output.** Column names, types, nullability. Use Great Expectations, Deequ, or dbt tests.
3. **Idempotency.** Run the pipeline twice with the same input. Verify identical output.
4. **Data quality checks.** Completeness (null rates, row counts), accuracy (cross-source validation), consistency (cross-table totals), timeliness (freshness), uniqueness (no duplicate keys).
5. **Test time explicitly.** Freeze time in tests. Test timezone conversions, DST transitions, late-arriving data, leap years.

---

## 8. Security & Performance Testing

### Security Testing

1. **Auth testing as separate concerns.** Authentication tests (valid/expired/malformed/missing tokens). Authorization tests (table-driven: every endpoint x every role x expected status code).
2. **Input validation testing.** For every user-controllable field: SQL injection payloads, XSS payloads, command injection (`; rm -rf /`), path traversal (`../../etc/passwd`).
3. **Mass assignment testing.** Send request bodies with extra fields (`is_admin: true`). Verify they are ignored.
4. **Rate limiting verification.** Exceed the limit, verify 429 response with `Retry-After` header. Verify reset after window.
5. **OWASP Top 10 as test checklist.** Broken access control (A01) and injection (A03) deserve the most investment.
6. **Dependency scanning.** Automated vulnerability scanning of dependencies in CI. Tools: Snyk, OWASP Dependency-Check, npm audit, safety (Python).

### Performance Testing

1. **Performance budgets as CI gates.** P50 response time under X ms, P99 under Y ms, error rate below Z%. Fail the build on violations.
2. **Realistic load profiles.** Ramp-up period, mix of operations reflecting real usage ratios (80% reads, 15% writes), think time between requests, hot spots.
3. **Micro-benchmarks for hot paths.** Critical algorithms and data transformations get benchmark tests that run in CI. Detect regressions before deployment.
4. **Frontend performance.** Core Web Vitals (LCP, CLS, INP) thresholds in Lighthouse CI. Bundle size limits with `size-limit`.
5. **When to test.** Every PR: micro-benchmarks. Weekly: load tests against staging. Before major releases: soak tests (sustained load over hours).

---

## 9. Resilience & Production Testing

### Resilience Testing

1. **Circuit breaker testing.** Test all three states: closed (normal), open (fail fast), half-open (probe). Inject failures to trip the breaker, verify fast-fail, wait for reset, verify recovery.
2. **Retry testing.** Verify: exponential backoff, jitter, maximum retry count, only retries on retryable errors (5xx/timeout, not 4xx), correct error after exhaustion.
3. **Timeout testing.** Inject slow responses. Verify timeout is enforced at the expected duration. Verify cascading timeouts make sense (A > B > C).
4. **Graceful degradation.** Kill a dependency mid-test. Verify the system returns a degraded response, not a 500 error. Verify it recovers when the dependency returns.
5. **Chaos engineering.** Dependency failure injection, latency injection, resource exhaustion (CPU/memory/file descriptors), network partition simulation (Toxiproxy).

### Production Testing (Shift Right)

1. **Canary deployments.** Deploy to a small percentage of traffic. Compare error rates, latency percentiles, and business metrics between canary and baseline.
2. **Feature flags as test boundaries.** Deploy code without activating it. Gradually roll out while monitoring. Testing deployment independently from testing the feature.
3. **Synthetic monitoring.** Run synthetic transactions against production continuously -- login, core workflow, payment flow. Alert immediately when something breaks.
4. **Observability as testing.** If your tests cannot catch it, your observability must. Structured logging, distributed tracing, and metrics are the last line of defense.
5. **Production traffic replay.** Capture production request patterns (sanitized of PII), replay against new versions in shadow mode. Validates real-world edge cases.

---

## 10. Quality Metrics & Culture

### Metrics That Matter

1. **Escaped defect rate.** Bugs that reach production per release. The primary measure of testing effectiveness.
2. **Flaky test rate.** Percentage of suite that is flaky. Above 2-3%, developers stop trusting CI.
3. **DORA metrics.** Deployment frequency, lead time, change failure rate, MTTR. Teams that deploy often tend to have better test suites.
4. **Time to detect.** Where in the pipeline defects are found. Shift left = finding earlier = cheaper.
5. **Branch coverage as a floor.** 70-80% minimum. Track trends, not absolutes. Never set as a target to optimize for.

### Metrics That Mislead

1. **Code coverage as a target.** The moment you incentivize coverage, you get tests that hit lines without verifying behavior. Coverage measures execution, not correctness.
2. **Number of tests.** More tests is not better tests. 200 focused tests beat 2000 unfocused ones.
3. **Bugs found in QA.** If QA finds many bugs, that is development quality being poor, not QA being great.

### Advanced Testing Techniques

1. **Property-based testing.** Define invariants that must hold for all valid inputs. The framework generates hundreds of random inputs. Patterns: roundtrip (encode/decode), commutativity, idempotence, invariant preservation. Tools: hypothesis (Python), fast-check (TS), jqwik (Java).
2. **Mutation testing.** Introduce small code changes (mutants) and verify tests catch them. Reveals holes that coverage cannot. Start with high-impact areas -- business logic, security checks. Tools: Pitest (Java), Stryker (TS/.NET), mutmut (Python).
3. **Architecture testing.** Enforce dependency rules, layer boundaries, and naming conventions with automated tests. Tools: ArchUnit (Java), dependency-cruiser (TS).

### Building Testing Culture

1. **Make the right thing easy.** Fast CI, good fixtures, test templates, local environments that mirror production.
2. **Every PR includes tests.** No exceptions unless explicitly agreed. PRs without tests are not ready for review.
3. **Celebrate quality wins.** When someone catches a bug with a test, call it out. When someone fixes a flaky suite, that is as valuable as shipping a feature.
4. **Tests are not overhead -- they are the prerequisite for sustainable speed.** Every team that skips testing to "move faster" hits a wall within 6-12 months.

---

## Quick-Reference Checklist

Use this for rapid test review scanning:

| Area | Key Question |
|---|---|
| Design | Does each test verify one behavior with a clear name? |
| Strategy | Are tests at the right level (unit/integration/E2E)? |
| Data | Does test data use factories and reveal scenario intent? |
| Isolation | Can all tests run in any order, concurrently? |
| Assertions | Is every assertion specific and meaningful? |
| Flakiness | Are there any `sleep()` calls, shared state, or timing dependencies? |
| Coverage | Are error paths and edge cases tested, not just happy paths? |
| Mocking | Are mocks limited to external boundaries? |
| Speed | Does the suite run fast enough to be used on every commit? |
| Maintenance | Is test code reviewed with the same rigor as production code? |
