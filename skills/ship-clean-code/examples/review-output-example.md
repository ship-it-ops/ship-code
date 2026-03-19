# Review Output Example

This demonstrates the structured review format produced in review mode.

## Source Code Under Review

```python
# user_service.py
import os
import requests

db_pass = "hunter2"

class UserService:
    def __init__(self):
        self.db = DatabaseConnection(os.environ["DB_HOST"], db_pass)
        self.cache = {}

    def get_user_and_update_cache(self, id):
        # get user from database
        try:
            result = self.db.query(f"SELECT * FROM users WHERE id = {id}")
            if result:
                u = result[0]
                u["last_accessed"] = datetime.now()
                self.cache[id] = u
                if u["status"] == 1:
                    self.send_welcome(u)
                return u
            else:
                return None
        except:
            print("error")
            return None

    def send_welcome(self, user):
        requests.post("http://email-service:3000/send", json={"to": user["email"]})
```

## Review Output

```
## Code Review: user_service.py

### Critical (must fix before merge)

- **[P1-BUG] Line 23**: `get_user_and_update_cache` mutates the database result
  object by setting `last_accessed`, causing side effects in what appears to be a
  read operation. If the same object is referenced elsewhere, this mutation
  propagates silently.
  → Split into `find_user(user_id)` (pure read) and `record_user_access(user_id)`
  (explicit write).

- **[P2-SEC] Line 4**: Database password hardcoded as string literal `"hunter2"`.
  → Load from environment variable or secrets manager:
  `db_pass = os.environ["DB_PASS"]`. Fail fast at startup if not set.

- **[P2-SEC] Line 20**: SQL injection via f-string interpolation:
  `f"SELECT * FROM users WHERE id = {id}"`.
  → Use parameterized query:
  `self.db.query("SELECT * FROM users WHERE id = %s", (user_id,))`.

### Important (should fix)

- **[P3-ERR] Lines 30-32**: Bare `except:` catches all exceptions including
  `KeyboardInterrupt` and `SystemExit`. The error message `"error"` provides no
  diagnostic value.
  → Catch specific exceptions: `except DatabaseError as e:` and log with context:
  `logger.error("Failed to fetch user", extra={"user_id": user_id, "error": str(e)})`.

- **[P3-ERR] Lines 29, 32**: Returns `None` for both "not found" and "error"
  cases — callers cannot distinguish between a missing user and a database failure.
  → Raise `UserNotFoundError` for missing users; let database errors propagate or
  wrap in `ServiceError`.

- **[P4-TEST] Line 14**: `UserService.__init__` creates its own
  `DatabaseConnection`, making it impossible to test without a live database.
  → Inject the dependency:
  `def __init__(self, db: DatabaseConnection, cache: dict | None = None)`.

- **[P5-MAINT] Line 26**: `get_user_and_update_cache` also sends a welcome email,
  violating Single Responsibility. A getter should not trigger side effects in
  external services.
  → Move welcome email logic to the caller or an event handler.

### Suggestions (improve when convenient)

- **[P6-READ] Line 17**: Parameter `id` shadows Python builtin `id()`. Variable
  `u` on line 22 is a single-letter name for a user object.
  → Rename to `user_id` and `user` respectively.

- **[P6-READ] Line 25**: Magic number `1` for status check. What does status 1 mean?
  → Define `USER_STATUS_ACTIVE = 1` or use an enum: `UserStatus.ACTIVE`.

- **[P6-READ] Line 31**: Using `print()` instead of structured logging.
  → Use `logger.error(...)` with the `logging` module.

### What's Good

- The caching strategy (line 24) shows awareness of read performance. The basic
  structure of query → process → cache is a sound pattern that just needs the
  mutations and side effects extracted.
- Method naming attempt `get_user_and_update_cache` at least tries to be honest
  about what the function does — many codebases would just call this `get_user`
  and hide the cache update entirely.
```
