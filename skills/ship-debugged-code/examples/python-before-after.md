# Python Debugging — Before / After

Concrete examples of systematic debugging applied to common Python bugs. Each example shows the bug, the initial (poor) investigation, and the corrected investigation that finds the root cause and produces a regression test.

---

## Example 1: KeyError in a serialization path

### Bug Report

> Production logs show `KeyError: 'tier'` thrown intermittently from `/api/users/{id}`. About 0.5% of requests, mostly older users.

### Poor Investigation

```python
# Quick fix proposed in the first PR
def get_user_response(user):
    return {
        "id": user["id"],
        "name": user["name"],
        "tier": user.get("tier", "free"),  # symptom patch
    }
```

**Problems:**
- D1: No repro captured. The fix is speculative.
- D2: Symptom patch — the consumer compensates for malformed data instead of fixing the producer.
- D4: No regression test.
- D5: Hypothesis ("`tier` is missing for some users") was never verified against the database.

### Better Investigation

**Step 1: Repro.**

```bash
# From the production log, the failing user ID is 4711.
$ ./scripts/fetch_anonymized_user.py 4711 > tests/fixtures/user_4711.json
$ cat tests/fixtures/user_4711.json
{"id": 4711, "name": "alice", "email": "alice@example.com"}
# Note: no 'tier' key at all
```

**Step 2: Confirm the hypothesis with data.**

```sql
SELECT id, created_at, tier FROM users WHERE tier IS NULL LIMIT 20;
-- All 20 results have created_at < 2023-06-01.
-- Hypothesis confirmed: legacy accounts pre-2023-06 have no tier.
```

**Step 3: Trace the producer.**

```python
# users/serialization.py — this is where the dict is built.
def serialize_user(user_row):
    d = {"id": user_row.id, "name": user_row.name}
    if user_row.tier is not None:  # <-- THIS is the bug. Drops the key entirely.
        d["tier"] = user_row.tier
    return d
```

**Step 4: Fix at the producer.**

```python
# users/serialization.py
def serialize_user(user_row):
    return {
        "id": user_row.id,
        "name": user_row.name,
        "tier": user_row.tier or "free",  # invariant: tier is always present
    }
```

Plus a backfill migration:
```sql
UPDATE users SET tier = 'free' WHERE tier IS NULL;
ALTER TABLE users ALTER COLUMN tier SET NOT NULL;
ALTER TABLE users ALTER COLUMN tier SET DEFAULT 'free';
```

**Step 5: Regression test (written BEFORE the fix is applied, verified to fail).**

```python
# tests/users/test_serialization.py
def test_serialize_legacy_user_with_null_tier_defaults_to_free():
    user = UserFactory.legacy(tier=None)  # legacy() sets created_at < 2023-06
    result = serialize_user(user)
    assert result["tier"] == "free"
    # Ensure the key always exists, even for new users
    assert "tier" in result
```

**Step 6: Adjacent audit.**

```bash
$ rg "user_row\." src/  # find every other consumer of user_row
# Check each one for similar "drop the key if None" bugs.
```

**Step 7: Commit message.**

> Fix KeyError 'tier' for legacy users (#4711)
>
> Symptom: `KeyError: 'tier'` from `/api/users/{id}` for accounts created
> before 2023-06. Affected ~0.5% of requests.
>
> Cause: `serialize_user()` dropped the `tier` key when the database value
> was NULL. Pre-2023-06 accounts had NULL `tier` because the column was
> added later without backfilling.
>
> Fix: serializer now defaults to "free" at the boundary. Migration
> backfills existing rows and sets NOT NULL + DEFAULT on the column.
>
> Regression test: tests/users/test_serialization.py::test_serialize_legacy_user_with_null_tier_defaults_to_free

---

## Example 2: Intermittent test failure ("flaky")

### Bug Report

> `test_email_delivery_order` passes locally but fails ~3% of the time in CI. Marked as `@pytest.mark.flaky` and retried.

### Poor Investigation

```python
@pytest.mark.flaky(reruns=3)  # accepted as-is
def test_email_delivery_order():
    ...
```

**Problems:**
- D6: Hidden intermittent. The retry hides a race condition that will surface in production.
- I1: No repro determinant identified.
- I3: No hypothesis stated.

### Better Investigation

**Step 1: Find the determinant.**

```bash
# Run the test in a loop until it fails.
$ for i in {1..200}; do pytest tests/email/test_delivery.py::test_email_delivery_order -x || break; done
# Fails after 47 iterations.
# Re-run with `-p no:randomly` to disable random ordering.
$ for i in {1..200}; do pytest tests/email/test_delivery.py -p no:randomly -x || break; done
# Passes 200/200. So it IS test ordering. Find the dependency.
```

**Step 2: Bisect the test order.**

```bash
# Capture the failing order.
$ pytest tests/email/ --collect-only -q > /tmp/all_tests.txt
# Add `-p random_seed:12345` (the failing seed from CI). Split tests in half. Re-run.
```

After bisecting, the dependency is found: `test_email_queue_flush` (run earlier) leaves a job in the global `EMAIL_QUEUE` because it doesn't clean up. `test_email_delivery_order` then sees an extra job and the count is off.

**Step 3: Root cause.**

```python
# email/queue.py
EMAIL_QUEUE = []  # <-- module-level global. Shared state across tests.
```

**Step 4: Fix.**

The minimal fix is per-test cleanup, but the **right** fix is removing the global:

```python
# email/queue.py
class EmailQueue:
    def __init__(self):
        self._queue = []
    def push(self, msg): self._queue.append(msg)
    def flush(self): return self._queue[:]

# Inject EmailQueue where needed. No module-level state.
```

**Step 5: Regression test for the isolation property itself.**

```python
def test_email_queue_is_test_isolated(email_queue):
    """Reads back empty even if another test pushed earlier — fixture is fresh."""
    assert email_queue.flush() == []
```

**Step 6: Remove the `@pytest.mark.flaky` decorator.**

Never re-add it. A 3% failure rate that "retries pass" is a 3% production-bug rate hidden by retries.

---

## Example 3: "It works on my machine"

### Bug Report

> `pdf_generator.render(...)` produces a corrupted PDF when run in CI but is fine locally.

### Poor Investigation

> Closed as "could not reproduce". Workaround: re-run the CI job; it eventually passes.

**Problems:**
- C1: "It works on my machine" — the environment difference IS the bug.
- D6: Re-run as a fix.

### Better Investigation

**Step 1: Capture both environments.**

```bash
$ python --version && pip freeze > /tmp/local-env.txt
# In CI runner:
$ python --version && pip freeze > /tmp/ci-env.txt
$ diff /tmp/local-env.txt /tmp/ci-env.txt
# Only difference: locale.
$ locale
LANG=en_US.UTF-8   # local
LANG=C             # CI
```

**Step 2: Hypothesis.**

> H1: PDF generation depends on locale-sensitive number formatting; under `LANG=C`, decimal separators may differ and corrupt the binary PDF stream.

**Step 3: Verify.**

```bash
$ LANG=C python -m pytest tests/pdf/ -x
# Reproduces locally with LANG=C. Confirmed.
```

**Step 4: Fix.**

```python
# pdf/generator.py
import locale

def render(data):
    with _locale_context("C.UTF-8"):  # explicit, predictable
        return _render_inner(data)
```

**Step 5: Regression test.**

```python
@pytest.mark.parametrize("lang", ["C", "en_US.UTF-8", "de_DE.UTF-8"])
def test_pdf_render_is_locale_independent(lang, monkeypatch):
    monkeypatch.setenv("LANG", lang)
    pdf = render(sample_data())
    assert pdf.startswith(b"%PDF-")
    assert _checksum(pdf) == EXPECTED_CHECKSUM
```

Plus a CI fix: pin `LANG=C.UTF-8` explicitly so this kind of difference is documented and stable.
