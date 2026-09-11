from datetime import datetime

import pytest

from app.business_hours import calculate_pickup_deadline, validate_business_hours


def test_pickup_deadline_uses_same_day_closing_time():
    created_at = datetime(2026, 9, 11, 12, 30)
    expire_time = datetime(2026, 9, 12, 12, 30)

    assert calculate_pickup_deadline(created_at, expire_time, "22:00") == datetime(
        2026, 9, 11, 22, 0
    )


def test_pickup_deadline_uses_next_closing_after_shop_has_closed():
    created_at = datetime(2026, 9, 11, 23, 30)
    expire_time = datetime(2026, 9, 13, 12, 30)

    assert calculate_pickup_deadline(created_at, expire_time, "22:00") == datetime(
        2026, 9, 12, 22, 0
    )


def test_product_expiry_caps_pickup_deadline():
    created_at = datetime(2026, 9, 11, 12, 30)
    expire_time = datetime(2026, 9, 11, 18, 0)

    assert calculate_pickup_deadline(created_at, expire_time, "22:00") == expire_time


def test_business_hours_reject_matching_open_and_close_times():
    with pytest.raises(ValueError, match="不能相同"):
        validate_business_hours("08:00", "08:00")
