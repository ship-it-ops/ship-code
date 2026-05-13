# Expected Review Output — fixture-1-python-bugs

The skill, in review mode, should produce a report substantially matching the structure below. Exact wording may vary; check for: every P1/P2 finding listed, correct priority categorization, concrete fix suggestions, and a non-empty "What's Good" section.

---

## Code Review: input.py

### Critical (must fix before merge)

- **[P1-BUG] Line 13**: `range(0, len(result) + 1)` causes an off-by-one on the final iteration — when `i == len(result)`, `result[i]` raises `IndexError`. → Use `range(len(result))`, or better, iterate directly: `for row in result:`.

- **[P2-SEC] Line 8**: SQL injection via string concatenation: `"SELECT * FROM users WHERE created_at > '" + d + "'"`. A malicious `d` value can execute arbitrary SQL. → Use parameterized query: `c.execute("SELECT id, name FROM users WHERE created_at > ?", (d,))`.

### Important (should fix)

- **[P3-ERR] Lines 17-18**: Bare `except:` catches `KeyboardInterrupt`, `SystemExit`, and silently returns `None`. Callers cannot distinguish "no users" from "database error". → Catch specific exceptions (`sqlite3.DatabaseError`), log with context, and either re-raise or raise a domain-specific error.

- **[P3-ERR] Lines 6-7**: Connection and cursor are not closed; on exception, they leak. → Use `with sqlite3.connect("app.db") as conn:` for automatic cleanup.

- **[P5-MAINT] Line 4**: Function couples concerns — opens connection, builds query, fetches, transforms, handles errors. → Inject the database/connection as a parameter so this function is testable and composable.

### Suggestions (improve when convenient)

- **[P6-READ] Line 4**: Parameter `d` and variables `c`, `q`, `u`, `i` are all single-letter. The docstring "get users" duplicates the function name. → Rename to `since_date`, `cursor`, `query`, `user_row`, and `index` (or eliminate `index` by iterating directly).

- **[P6-READ] Line 8**: SELECT * fetches all columns but the code only uses 2. Magic indices `u[0]` and `u[1]` couple the code to column order. → Use `SELECT id, name FROM users WHERE ...` and unpack named tuples or rows: `for user_id, name in cursor:`.

### What's Good

- The function has a try/except wrapping the database operation — the intent to handle failures is there, just needs better specificity.
- The transformation to a list of dicts (line 14) decouples the database row shape from the function's return type, which is a sound boundary.
