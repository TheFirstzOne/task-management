"""
Date helper utilities
"""

from datetime import datetime, date
from typing import Optional
from dateutil import tz


def now_local() -> datetime:
    return datetime.now(tz=tz.tzlocal())


def format_date(dt: Optional[datetime], fmt: str = "%d/%m/%Y") -> str:
    if not dt:
        return "-"
    return dt.strftime(fmt)


def format_datetime(dt: Optional[datetime]) -> str:
    return format_date(dt, "%d/%m/%Y %H:%M")


def is_overdue(due: Optional[datetime]) -> bool:
    if not due:
        return False
    return due < datetime.utcnow()


def days_until(due: Optional[datetime]) -> Optional[int]:
    if not due:
        return None
    delta = due.date() - date.today()
    return delta.days
