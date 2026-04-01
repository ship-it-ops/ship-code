# Python Test Transformations

## Example 1: Implementation-Coupled → Behavior-Based

### Before
```python
import unittest
from unittest.mock import patch, MagicMock

class TestOrderService(unittest.TestCase):
    @patch('app.services.order_service.EmailClient')
    @patch('app.services.order_service.PaymentGateway')
    @patch('app.services.order_service.OrderRepository')
    def test_place_order(self, mock_repo, mock_payment, mock_email):
        mock_repo.return_value.save.return_value = MagicMock(id=1)
        mock_payment.return_value.charge.return_value = {"status": "ok"}
        mock_email.return_value.send.return_value = True

        service = OrderService()
        result = service.place_order({"item": "widget", "amount": 100})

        mock_repo.return_value.save.assert_called_once()
        mock_payment.return_value.charge.assert_called_once_with(100)
        mock_email.return_value.send.assert_called_once()
        self.assertIsNotNone(result)
```

**Problems:**
- Tests mock wiring, not behavior (D6)
- Over-mocking: every dependency patched (M1)
- Weak assertion: `assertIsNotNone` (A1)
- No descriptive test name (N3)
- Tightly coupled to import paths -- renaming a module breaks the test

### After
```python
import pytest
from app.services.order_service import OrderService
from tests.fakes import FakeOrderRepository, FakePaymentGateway, FakeEmailService
from tests.factories import OrderFactory


class TestPlaceOrder:
    def test_saves_order_with_calculated_total(self):
        repo = FakeOrderRepository()
        service = OrderService(repo=repo, payment=FakePaymentGateway(), email=FakeEmailService())

        order = OrderFactory.with_items([("Widget", 2, 25.00), ("Gadget", 1, 50.00)])
        result = service.place_order(order)

        saved = repo.find_by_id(result.id)
        assert saved is not None
        assert saved.total == 100.00
        assert saved.status == "confirmed"

    def test_rejects_order_with_empty_cart(self):
        service = OrderService(
            repo=FakeOrderRepository(),
            payment=FakePaymentGateway(),
            email=FakeEmailService(),
        )

        with pytest.raises(ValidationError, match="Cart cannot be empty"):
            service.place_order(OrderFactory.empty())

    def test_sends_confirmation_email_on_success(self):
        email = FakeEmailService()
        service = OrderService(
            repo=FakeOrderRepository(),
            payment=FakePaymentGateway(),
            email=email,
        )

        order = OrderFactory.standard()
        service.place_order(order)

        assert len(email.sent) == 1
        assert "confirmation" in email.sent[0]["subject"].lower()
```

**Improvements:**
- Fakes instead of mocks — tests real behavior through the system
- Each test verifies one behavior with a descriptive name
- Assertions are specific: exact total, exact status, email content
- Factory pattern for test data — resilient to model changes
- No coupling to import paths or internal implementation

---

## Example 2: Flaky Time-Dependent → Deterministic

### Before
```python
def test_subscription_is_active():
    sub = Subscription(started_at=datetime.now(), duration_days=30)
    assert sub.is_active()

def test_subscription_expires():
    sub = Subscription(
        started_at=datetime.now() - timedelta(days=31),
        duration_days=30
    )
    assert not sub.is_active()
```

**Problems:**
- Depends on `datetime.now()` — can flake near midnight (F3)
- No clear separation of time logic

### After
```python
import time_machine

@time_machine.travel("2025-06-15 12:00:00")
def test_subscription_is_active_within_duration():
    sub = Subscription(
        started_at=datetime(2025, 6, 1),
        duration_days=30,
    )
    assert sub.is_active()

@time_machine.travel("2025-07-15 12:00:00")
def test_subscription_expires_after_duration():
    sub = Subscription(
        started_at=datetime(2025, 6, 1),
        duration_days=30,
    )
    assert not sub.is_active()

@time_machine.travel("2025-07-01 00:00:00")
def test_subscription_is_active_on_last_day():
    sub = Subscription(
        started_at=datetime(2025, 6, 1),
        duration_days=30,
    )
    assert sub.is_active()
```

**Improvements:**
- Time is frozen — completely deterministic
- Boundary condition tested (last day)
- Test names describe the specific scenario
- Dates are explicit and readable

---

## Example 3: Missing Edge Cases → Comprehensive

### Before
```python
def test_calculate_discount():
    assert calculate_discount(100, "SAVE10") == 90
```

**Problems:**
- Only one happy path tested (C1)
- No edge cases: invalid code, expired code, zero amount, negative (TD6)

### After
```python
class TestCalculateDiscount:
    def test_applies_percentage_discount(self):
        assert calculate_discount(100, "SAVE10") == 90.00

    def test_applies_fixed_amount_discount(self):
        assert calculate_discount(100, "FLAT20") == 80.00

    def test_discount_cannot_reduce_below_zero(self):
        assert calculate_discount(10, "FLAT20") == 0.00

    def test_rejects_expired_coupon(self):
        with pytest.raises(CouponExpiredError, match="OLDCODE"):
            calculate_discount(100, "OLDCODE")

    def test_rejects_unknown_coupon(self):
        with pytest.raises(InvalidCouponError):
            calculate_discount(100, "DOESNOTEXIST")

    def test_zero_amount_returns_zero(self):
        assert calculate_discount(0, "SAVE10") == 0.00

    @pytest.mark.parametrize("amount", [-1, -100])
    def test_rejects_negative_amounts(self, amount):
        with pytest.raises(ValueError, match="Amount must be non-negative"):
            calculate_discount(amount, "SAVE10")
```

**Improvements:**
- Happy paths AND sad paths covered
- Edge cases: zero, negative, expired, unknown
- Parametrized test for similar negative cases
- Each test verifies one behavior
