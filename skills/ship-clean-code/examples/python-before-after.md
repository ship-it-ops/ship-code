# Python: Before & After

## Scenario
A data processing module that reads user transaction records, validates them,
computes summary statistics, and returns results.

---

## Before (8 violations)

```python
def proc(d, t=[], fmt="csv"):
    # loop through the data
    res = []
    tot = 0
    cnt = 0
    err = 0

    # old approach - keeping just in case
    # for row in d:
    #     if row[2] > 0:
    #         t.append(row)

    for i in range(len(d)):
        try:
            r = d[i]
            a = float(r["amount"])
            if a > 0 and a < 10000:
                if r["status"] == "active":
                    tot += a
                    cnt += 1
                    x = {
                        "id": r["id"],
                        "a": a,
                        "tax": a * 0.0825,
                        "total": a + (a * 0.0825),
                        "tier": 1 if a < 100 else 2 if a < 500 else 3,
                    }
                    t.append(x)
                    res.append(x)
        except:
            err += 1

    if cnt == 0:
        return None

    avg = tot / cnt
    return {"items": res, "total": tot, "avg": avg, "errors": err}
```

---

## After (Corrected)

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional


TAX_RATE = 0.0825                          # [4] Magic number extracted to named constant
MAX_TRANSACTION_AMOUNT = 10_000            # [4] Magic number extracted
ACTIVE_STATUS = "active"


class SpendingTier(Enum):                  # [4] Magic tier numbers replaced with enum
    STANDARD = "standard"
    PLUS = "plus"
    PREMIUM = "premium"


@dataclass
class ProcessedTransaction:
    id: str
    amount: float
    tax: float
    total: float
    tier: SpendingTier


class EmptyDatasetError(Exception):
    """Raised when no valid transactions are found."""


def classify_tier(amount: float) -> SpendingTier:
    """Determine spending tier based on transaction amount."""
    if amount < 100:                       # [3] Single-responsibility helper
        return SpendingTier.STANDARD
    if amount < 500:
        return SpendingTier.PLUS
    return SpendingTier.PREMIUM


def _build_transaction(record: dict) -> Optional[ProcessedTransaction]:
    """Validate and transform a single transaction record.

    Returns None if the record is invalid or inactive.
    """
    try:                                   # [8] Specific exception type
        amount = float(record["amount"])
    except (ValueError, KeyError) as exc:
        raise ValueError(f"Bad record {record.get('id', '?')}: {exc}") from exc

    is_valid = 0 < amount < MAX_TRANSACTION_AMOUNT
    if not is_valid or record.get("status") != ACTIVE_STATUS:
        return None

    tax = amount * TAX_RATE
    return ProcessedTransaction(
        id=record["id"],
        amount=amount,                     # [1] Descriptive field names
        tax=tax,
        total=amount + tax,
        tier=classify_tier(amount),
    )


def process_transactions(
    records: list[dict],                   # [1] Clear parameter name
) -> dict:                                 # [7] No mutable default argument
    """Process transaction records and return summary statistics.

    Raises:
        EmptyDatasetError: If no valid transactions exist after filtering.
    """
    processed: list[ProcessedTransaction] = []
    errors = 0                             # [5] Commented-out code removed

    for record in records:                 # [6] No redundant comment
        try:
            txn = _build_transaction(record)
            if txn is not None:
                processed.append(txn)
        except ValueError:
            errors += 1

    if not processed:
        raise EmptyDatasetError(           # [4b] Raise instead of returning None
            "No valid transactions found"
        )

    total = sum(t.amount for t in processed)
    average = total / len(processed)       # [1] 'average' not 'avg'

    return {
        "items": processed,
        "total": total,
        "average": average,
        "errors": errors,
    }
```

---

## Annotations

| # | Violation (Before) | Fix (After) |
|---|---|---|
| 1 | **Poor variable names** -- `d`, `r`, `a`, `x`, `tot`, `cnt`, `res` | Renamed to `records`, `record`, `amount`, `processed`, `total`, `errors`, etc. |
| 2 | **Function too long / does multiple things** -- `proc` validates, transforms, classifies tier, and aggregates | Split into `process_transactions`, `_build_transaction`, and `classify_tier` |
| 3 | **Magic numbers** -- `10000`, `0.0825`, `100`, `500`, tier ints `1/2/3` | Extracted to `TAX_RATE`, `MAX_TRANSACTION_AMOUNT`, and `SpendingTier` enum |
| 4 | **Returns None on empty input** -- caller must remember to check | Raises `EmptyDatasetError` with a clear message |
| 5 | **Commented-out code** -- dead `for row in d` block left behind | Removed entirely; version control preserves history |
| 6 | **Redundant comment** -- `# loop through the data` adds no information | Removed; the code is self-documenting with clear names |
| 7 | **Mutable default argument** -- `t=[]` shared across calls | Removed the parameter; accumulation is local to the function |
| 8 | **Bare except** -- `except:` swallows all errors silently | Catches `ValueError` and `KeyError` specifically; re-raises with context |
