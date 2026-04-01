# Python Testing Idioms

## Test Runner & Conventions

- Use **pytest** as the test runner (not unittest)
- Name test files `test_*.py`, test functions `test_should_*` or `test_<behavior>_when_<condition>`
- Group related tests in classes (no inheritance from `unittest.TestCase` needed with pytest)
- Use `conftest.py` for shared fixtures -- fixtures are inherited by all tests in the directory and below

## Fixtures

- Use `@pytest.fixture` for setup. Understand scope hierarchy: `function` (default), `class`, `module`, `session`
- Use `yield` fixtures for setup + teardown in one function
- Compose fixtures: a fixture can request other fixtures as parameters
- Use `@pytest.fixture(autouse=True)` sparingly -- only for truly universal setup (e.g., database transaction rollback)
- Keep fixture scope as narrow as possible. Session-scoped fixtures with mutable state cause test coupling

```python
@pytest.fixture
def active_user(db_session):
    user = UserFactory.active()
    db_session.add(user)
    db_session.flush()
    yield user
    # teardown happens automatically with transaction rollback
```

## Parametrize

- Use `@pytest.mark.parametrize` with `ids=` for readable failure output
- Use tuple unpacking for multi-argument parametrize
- Combine multiple parametrize decorators for cartesian product testing

```python
@pytest.mark.parametrize("input_val, expected", [
    ("valid@email.com", True),
    ("no-at-sign", False),
    ("", False),
    ("a@b.c", True),
], ids=["valid", "missing-at", "empty", "minimal-valid"])
def test_email_validation(input_val, expected):
    assert is_valid_email(input_val) == expected
```

## Exception Testing

- Use `pytest.raises(ExceptionType, match="regex")` -- always include `match` to verify the message
- For custom exceptions, assert on exception attributes

```python
def test_withdraw_exceeding_balance_raises():
    account = Account(balance=50)
    with pytest.raises(InsufficientFundsError, match="Cannot withdraw 100") as exc_info:
        account.withdraw(100)
    assert exc_info.value.available_balance == 50
```

## Mocking & Faking

- **Prefer fakes over `unittest.mock.patch`** for service dependencies. Fakes are explicit and catch more bugs.
- When mocking is necessary: use `unittest.mock.patch` as a context manager or decorator (not `patch.object` on instances)
- Use `monkeypatch` fixture for environment variables and simple attribute overrides
- Use `pytest.raises` for exception paths, not mock side effects when avoidable

```python
# GOOD: Fake for state-based testing
class FakeEmailService:
    def __init__(self):
        self.sent = []

    def send(self, to, subject, body):
        self.sent.append({"to": to, "subject": subject, "body": body})

def test_order_confirmation_sends_email():
    email = FakeEmailService()
    service = OrderService(email_service=email)
    service.place_order(OrderFactory.standard())
    assert len(email.sent) == 1
    assert "confirmation" in email.sent[0]["subject"].lower()
```

## Time & Async

- Use `freezegun` or `time-machine` for time-dependent tests. Prefer `time-machine` (faster, fewer edge cases)
- Use `pytest-asyncio` with `@pytest.mark.asyncio` for async test functions
- Never use `time.sleep()` in tests -- use `asyncio` test patterns or explicit waits

```python
import time_machine

@time_machine.travel("2025-01-15 10:00:00")
def test_subscription_expires_after_30_days():
    sub = Subscription(started_at=datetime(2024, 12, 15))
    assert sub.is_expired()
```

## Property-Based Testing

- Use **hypothesis** for property-based tests. Define strategies with `@given`
- Good properties to test: roundtrip (serialize/deserialize), invariants (sorted output length == input length), idempotence (applying twice == applying once)
- Use `@settings(max_examples=200)` for CI, `@settings(max_examples=1000)` for deep runs

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_preserves_length(lst):
    assert len(sorted(lst)) == len(lst)

@given(st.text())
def test_json_roundtrip(s):
    assert json.loads(json.dumps(s)) == s
```

## Test Data Factories

- Use **factory_boy** or hand-written factories with sensible defaults
- Factory methods should reveal intent: `UserFactory.admin()`, `OrderFactory.with_discount()`
- Use `faker` (via factory_boy's `Faker`) for realistic data with `factory.Faker.override_default_locale("en_US")`

## Integration Testing

- Use **testcontainers-python** for real databases, Redis, Kafka in tests
- Use `@pytest.fixture(scope="session")` for container lifecycle (start once, share across tests)
- Use transaction rollback per test for database isolation (faster than recreating)

```python
@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16") as pg:
        yield pg

@pytest.fixture
def db_session(postgres_container):
    engine = create_engine(postgres_container.get_connection_url())
    with Session(engine) as session:
        yield session
        session.rollback()
```

## Coverage & Mutation Testing

- Use `pytest-cov` for coverage: `pytest --cov=src --cov-branch --cov-report=term-missing`
- Use **mutmut** for mutation testing: `mutmut run --paths-to-mutate=src/domain/`
- Target mutation testing at business logic, not I/O or configuration code

## Common Traps

- **Mutable default in fixtures**: `@pytest.fixture` with mutable default arguments shares state. Use factory functions.
- **Forgetting `await`**: Missing `await` in async tests silently passes. Use strict mode or linting.
- **`conftest.py` scope creep**: A root `conftest.py` with 50 fixtures slows down all tests. Keep fixtures close to where they are used.
- **Testing with SQLite when production uses Postgres**: Behavioral differences in locking, JSON, array types. Use TestContainers.
