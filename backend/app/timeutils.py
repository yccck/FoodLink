from datetime import datetime
from typing import Optional

from app.config import SHANGHAI_TZ

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def now_shanghai_naive() -> datetime:
    return datetime.now(SHANGHAI_TZ).replace(tzinfo=None, microsecond=0)


def format_datetime(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is not None:
        value = value.astimezone(SHANGHAI_TZ).replace(tzinfo=None)
    return value.strftime(DATETIME_FORMAT)
