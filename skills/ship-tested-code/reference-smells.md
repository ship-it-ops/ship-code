# Test Smells and Heuristics Quick Reference

A comprehensive checklist of common test smells and how to fix them.

## Design

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| D1 | Testing Implementation, Not Behavior | Test breaks when internals change but behavior doesn't | Rewrite to assert on outputs/side effects, not internal state or call order |
| D2 | Multiple Concepts in One Test | Test name needs "and"; multiple unrelated assertions | Split into separate tests, one concept each |
| D3 | Order-Dependent Tests | Tests fail when run in different order or in parallel | Eliminate shared state; each test creates its own data |
| D4 | Tangled AAA Phases | Setup, action, and assertion interleaved | Restructure into clear Arrange, Act, Assert sections |
| D5 | Testing Private Methods | Test accesses private/internal methods directly | Test through the public API; if you can't, the class needs refactoring |
| D6 | Test Verifies Mock Wiring | Test only asserts that mocks were called in order | Assert on observable outcomes (return values, state changes, side effects) |
| D7 | Fragile Test | Test breaks on any code change, even cosmetic | Loosen coupling: test behavior contracts, not implementation details |

## Data

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| TD1 | Hardcoded Magic Values | `assert result == 42` with no explanation of why 42 | Use named constants or make the derivation obvious in the test |
| TD2 | Shared Mutable Fixtures | Tests modify shared data structures | Give each test its own fresh data; use factory methods |
| TD3 | Production Data in Tests | Real customer data used as test fixtures | Generate synthetic data matching production patterns |
| TD4 | Non-Deterministic Data | `random()`, `datetime.now()`, `UUID` without seed/injection | Use seeded generators, injectable clocks, deterministic IDs |
| TD5 | Data Obscures Scenario | 50 lines of setup but only 1 field matters | Make the relevant data prominent; use factory defaults for the rest |
| TD6 | Missing Edge Case Data | Only "normal" values tested | Add: null, empty, max length, unicode, negative, zero, boundary values |
| TD7 | Brittle Constructor Calls | `new User("a","b","c",null,null,true,0)` everywhere | Use factory/builder: `UserFactory.active()` |

## Assertions

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| A1 | Weak Assertions | `assertNotNull(result)` when specific value is known | Use `assertEquals(expected, actual)` with the exact expected value |
| A2 | No Assertions at All | Test exercises code but never asserts | Add specific assertions for expected outcomes |
| A3 | Snapshot Abuse | `toMatchSnapshot()` on large, frequently changing components | Replace with behavioral assertions; use snapshots only for small, stable outputs |
| A4 | Asserting Implementation Details | `verify(mock).internalMethod()` | Assert on external behavior: return values, persisted state, emitted events |
| A5 | Missing Error Message | Assertion fails with "expected true got false" | Add descriptive failure messages: `assertEquals(expected, actual, "Order should be cancelled after refund")` |
| A6 | Over-Assertion | Test asserts on 15 different properties when only 2 matter | Assert only on the properties relevant to the behavior being tested |

## Mocking

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| M1 | Over-Mocking | Every dependency mocked; test verifies mock orchestration | Use fakes for state-based tests; only mock external boundaries |
| M2 | Mocking Value Objects | Domain objects (User, Order, Price) are mocked | Use real domain objects; they are cheap to construct |
| M3 | Mock Setup > Test Logic | 40 lines of `when().thenReturn()` for a 5-line test | Simplify the system under test or use fakes |
| M4 | Mocking What You Own | Internal service classes mocked instead of external deps | Use real implementations or fakes for internal code |
| M5 | Verification Overload | `verify(mock, times(1))` for every mock interaction | Only verify critical interactions (e.g., "email was sent") |
| M6 | Mock Returns Mock | `when(a.getB()).thenReturn(mockB); when(mockB.getC()).thenReturn(mockC)` | Simplify the object graph or use real objects |

## Flakiness

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| F1 | Sleep-Based Waits | `sleep(2000)`, `Thread.sleep(500)`, `time.sleep(1)` | Use explicit waits with conditions: `waitFor()`, `eventually()`, polling |
| F2 | Shared State Between Tests | Test A sets data that Test B depends on | Each test creates and destroys its own data |
| F3 | Timing-Dependent Assertions | `assert result.timestamp == datetime.now()` | Inject a clock; assert within a tolerance or on a frozen time |
| F4 | External Service Calls | Test hits real third-party API | Use contract tests, service virtualization, or in-process fakes |
| F5 | Environment-Dependent | Passes locally, fails in CI (or vice versa) | Use containers for dependencies; avoid OS-specific assumptions |
| F6 | Floating Point Comparison | `assertEquals(0.1 + 0.2, 0.3)` fails | Use `assertAlmostEqual` or tolerance-based comparison |
| F7 | Port Collision | Tests bind to hardcoded ports | Use dynamic port allocation (port 0) |

## Naming

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| N1 | Numeric Names | `test1`, `test2`, `testCase3` | Rename to describe behavior: `test_rejects_expired_token` |
| N2 | Implementation-Describing Names | `test_calls_repository_save` | Rename to describe outcome: `test_persists_new_order` |
| N3 | Vague Names | `testProcess`, `testHandleData`, `testHappyPath` | Specify what is processed, what data, what makes it happy |
| N4 | Missing Condition | `testLogin` — what about login? | Add condition: `test_login_succeeds_with_valid_credentials` |

## Structure

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| S1 | Giant Setup | 60+ lines of setup per test | Extract into factories/fixtures; simplify the system under test |
| S2 | Copy-Paste Tests | Same 30-line setup duplicated across tests, one value changed | Use parameterized tests for variations; extract shared setup |
| S3 | Over-Abstracted Helpers | 5 levels of helper methods to understand what a test does | Flatten; some duplication in tests is acceptable for readability |
| S4 | Missing Teardown | Tests leave files, database rows, or processes behind | Add cleanup in teardown/afterEach; use temp directories and transactions |
| S5 | Ignored Without Reason | `@Ignore`, `skip`, `xit` with no comment explaining why | Either fix the test, add a ticket reference, or delete it |
| S6 | Test File Mirrors Source File | `UserServiceTest` with one test per method, no behavioral grouping | Organize tests by behavior/scenario, not by source method |

## Coverage

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| C1 | Happy Path Only | Only successful scenarios tested | Add tests for errors, edge cases, boundary conditions |
| C2 | Missing Error Paths | No test for what happens when the database is down, API returns 500, input is null | Test each error path explicitly |
| C3 | Coverage-Gaming Tests | `new MyClass(); assertNotNull(...)` — hits lines, tests nothing | Write meaningful assertions that verify behavior |
| C4 | Testing Framework Code | Tests verify ORM saves, HTTP framework parses JSON | Test YOUR logic, not the framework's correctness |
| C5 | Redundant Tests | 5 integration tests and 8 unit tests all covering the same happy path | Remove redundancy; each test should cover a unique scenario |
| C6 | No Regression Test for Bug | Bug was fixed but no test prevents recurrence | Add a test that fails without the fix, passes with it |
