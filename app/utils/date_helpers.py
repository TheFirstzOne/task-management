"""
Date helper utilities
"""

from datetime import datetime, date, timezone
from typing import Optional
from dateutil import tz


def now_local() -> datetime:
    return datetime.now(tz=tz.tzlocal())


def parse_date_input(s: str) -> Optional[datetime]:
    """Parse a date string (dd/mm/yyyy or yyyy-mm-dd) into datetime.
    Returns None if empty; raises ValueError on invalid format.
    Used by task_view.py for start_date / due_date fields."""
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"รูปแบบวันที่ไม่ถูกต้อง: {s!r}  (ใช้ dd/mm/yyyy)")


def parse_date_field(s: str) -> Optional[date]:
    """Parse a date string into date (supports dd/mm/yyyy, yyyy-mm-dd, Buddhist Era).
    Returns None on empty or invalid input (never raises).
    Used by history_view.py and summary_view.py for filter date fields."""
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    # Buddhist Era support: dd/mm/yyyy where yyyy > 2500
    try:
        d, m, y_be = s.split("/")
        return date(int(y_be) - 543, int(m), int(d))
    except Exception:
        return None


def format_date(dt: Optional[datetime], fmt: str = "%d/%m/%Y") -> str:
    if not dt:
        return "-"
    return dt.strftime(fmt)


def format_datetime(dt: Optional[datetime]) -> str:
    return format_date(dt, "%d/%m/%Y %H:%M")


def is_overdue(due: Optional[datetime]) -> bool:
    if not due:
        return False
    return due < datetime.now(timezone.utc).replace(tzinfo=None)


def days_until(due: Optional[datetime]) -> Optional[int]:
    if not due:
        return None
    delta = due.date() - date.today()
    return delta.days
