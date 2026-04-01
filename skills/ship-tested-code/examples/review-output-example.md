# Review Output Example

This demonstrates the structured review format produced in review mode.

## Source Code Under Review

```python
# test_user_service.py
import time
import pytest
from unittest.mock import patch, MagicMock
from app.services.user_service import UserService

users_db = []

class TestUserService:
    def setup_method(self):
        users_db.clear()

    @patch('app.services.user_service.EmailClient')
    @patch('app.services.user_service.UserRepository')
    def test_create_user(self, mock_repo, mock_email):
        mock_repo.return_value.save.return_value = MagicMock(id=1)
        mock_repo.return_value.find_by_email.return_value = None
        mock_email.return_value.send.return_value = True

        service = UserService()
        result = service.create_user("John", "john@test.com", "password123")

        mock_repo.return_value.save.assert_called_once()
        mock_email.return_value.send.assert_called_once()
        assert result is not None

    @patch('app.services.user_service.UserRepository')
    def test_get_user(self, mock_repo):
        mock_repo.return_value.find_by_id.return_value = {"name": "John", "email": "john@test.com"}
        service = UserService()
        user = service.get_user(1)
        assert user["name"] == "John"

    def test_user_login(self):
        users_db.append({"email": "john@test.com", "password": "hashed"})
        service = UserService()
        service.authenticate("john@test.com", "hashed")
        time.sleep(1)  # wait for session to be created
        assert service.is_authenticated

    def test_process(self):
        service = UserService()
        result = service.process_users([
            {"name": "A", "status": "active"},
            {"name": "B", "status": "inactive"},
            {"name": "C", "status": "active"},
        ])
        assert len(result) == 2
        assert result is not None

    @patch('app.services.user_service.UserRepository')
    def test_delete(self, mock_repo):
        mock_repo.return_value.delete.return_value = True
        service = UserService()
        service.delete_user(1)
        mock_repo.return_value.delete.assert_called_once_with(1)
```

## Review Output

```
## Test Review: test_user_service.py

### Critical (must fix before merge)

- **[T1-COVERAGE] Lines 1-50**: No tests for error paths. Missing: what happens when
  `create_user` is called with a duplicate email? When `get_user` is called with a
  non-existent ID? When `authenticate` fails? When `delete_user` targets a non-existent
  user?
  → Add tests: `test_create_user_rejects_duplicate_email`,
  `test_get_user_raises_for_unknown_id`, `test_authenticate_rejects_wrong_password`,
  `test_delete_nonexistent_user_raises`.

- **[T2-FLAKY] Line 34**: `time.sleep(1)` waits for session creation. This is
  timing-dependent and will flake in slow CI environments.
  → Make session creation synchronous in tests, or use an explicit wait with a condition:
  `await_condition(lambda: service.is_authenticated, timeout=2.0)`. Better yet, redesign
  `authenticate` to return when the session is ready.

- **[T2-FLAKY] Line 6**: Module-level `users_db = []` is shared mutable state across
  tests. If tests run in parallel or `setup_method` fails, state leaks between tests.
  → Each test should create its own data via dependency injection. Pass the repository
  to `UserService` as a constructor parameter.

### Important (should fix)

- **[T3-LEVEL] Lines 12-22**: `test_create_user` mocks both the repository and email
  client, then only verifies that mocks were called. This tests mock wiring, not behavior.
  → Use fakes: `FakeUserRepository` (in-memory dict) and `FakeEmailService` (captures
  sent messages). Assert on persisted state and email content, not mock calls.

- **[T4-DESIGN] Line 39**: `test_process` — name describes implementation, not behavior.
  What does "process" mean? What are the expected outcomes?
  → Rename to `test_filters_active_users_from_list` and assert on the returned users'
  names and statuses, not just the count.

- **[T4-DESIGN] Lines 12-22**: `test_create_user` tests saving AND emailing in one test.
  If the save assertion fails, the email assertion is never reached.
  → Split: `test_create_user_persists_with_correct_fields` and
  `test_create_user_sends_welcome_email`.

- **[T5-DATA] Lines 12-22**: User data is hardcoded strings ("John", "john@test.com",
  "password123"). When the User model adds a required field, this test breaks.
  → Use a factory: `UserFactory.standard()` or `UserFactory.with_email("john@test.com")`.

### Suggestions (improve when convenient)

- **[T7-ASSERT] Line 21**: `assert result is not None` — this is the weakest possible
  assertion. What should `result` actually be?
  → Assert on specific properties: `assert result.name == "John"` and
  `assert result.email == "john@test.com"`.

- **[T7-ASSERT] Lines 42-43**: `assert len(result) == 2` and `assert result is not None`
  (in that order — the not-None check is redundant after len check). Neither assertion
  verifies the correct users were returned.
  → Assert: `assert [u["name"] for u in result] == ["A", "C"]`.

- **[T6-MAINT] Line 46**: `test_delete` only verifies the mock was called with the right
  argument. It does not test what happens when deletion succeeds or fails.
  → Use a fake repository. Assert the user no longer exists after deletion.

### What's Good

- Test file structure uses a class to group related tests, which provides clear organization.
- The `setup_method` shows awareness of test isolation (clearing shared state), even though
  the approach should be replaced with dependency injection.
- Tests cover the main CRUD operations (create, read, delete), providing a foundation to
  build upon. The test for `process_users` shows intent to test filtering logic.
```
