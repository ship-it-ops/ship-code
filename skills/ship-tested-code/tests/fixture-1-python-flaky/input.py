import time
from datetime import datetime

from billing import Subscription, charge_customer


def test_subscription():
    s = Subscription(plan="pro", started_at=datetime.now())
    s.activate()

    time.sleep(2)  # let the activation propagate

    charge_customer(s)

    assert s.status == "active"
    assert s.charged_amount > 0
    assert s.last_charged_at.year == datetime.now().year
