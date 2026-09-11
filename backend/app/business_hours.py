from __future__ import annotations

from datetime import datetime, time, timedelta


DEFAULT_BUSINESS_OPEN_TIME = "08:00"
DEFAULT_BUSINESS_CLOSE_TIME = "22:00"
BUSINESS_TIME_FORMAT = "%H:%M"


def parse_business_time(value: str) -> time:
    return datetime.strptime(value, BUSINESS_TIME_FORMAT).time()


def validate_business_hours(open_time: str, close_time: str) -> None:
    opening = parse_business_time(open_time)
    closing = parse_business_time(close_time)
    if opening == closing:
        raise ValueError("开门时间和关门时间不能相同")


def calculate_pickup_deadline(
    created_at: datetime,
    product_expire_time: datetime,
    close_time: str,
) -> datetime:
    """Return the next shop closing time, capped by the food expiry time."""

    closing = datetime.combine(created_at.date(), parse_business_time(close_time))
    if closing <= created_at:
        closing += timedelta(days=1)
    return min(closing, product_expire_time)
