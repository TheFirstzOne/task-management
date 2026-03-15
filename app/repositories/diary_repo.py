"""
DiaryRepository — CRUD operations for DiaryEntry
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.diary import DiaryEntry


class DiaryRepository:

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Create ───────────────────────────────────────────────────
    def create(self, content: str) -> DiaryEntry:
        entry = DiaryEntry(content=content)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    # ── Read ─────────────────────────────────────────────────────
    def get_by_id(self, entry_id: int) -> Optional[DiaryEntry]:
        return self.db.query(DiaryEntry).filter(DiaryEntry.id == entry_id).first()

    def get_all(self) -> List[DiaryEntry]:
        return self.db.query(DiaryEntry).order_by(DiaryEntry.created_at.desc()).all()

    def get_by_date(self, date: datetime) -> List[DiaryEntry]:
        """Get entries for a specific date (ignoring time)."""
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return (
            self.db.query(DiaryEntry)
            .filter(DiaryEntry.created_at >= start, DiaryEntry.created_at < end)
            .order_by(DiaryEntry.created_at.desc())
            .all()
        )

    def get_grouped_by_date(self) -> Dict[str, List[DiaryEntry]]:
        """Return all entries grouped by date string (DD/MM/YYYY), newest first."""
        entries = self.get_all()
        grouped: Dict[str, List[DiaryEntry]] = {}
        for entry in entries:
            date_key = entry.created_at.strftime("%d/%m/%Y")
            grouped.setdefault(date_key, []).append(entry)
        return grouped

    # ── Update ───────────────────────────────────────────────────
    def update(self, entry_id: int, content: str) -> Optional[DiaryEntry]:
        entry = self.get_by_id(entry_id)
        if not entry:
            return None
        entry.content = content
        self.db.commit()
        self.db.refresh(entry)
        return entry

    # ── Delete ───────────────────────────────────────────────────
    def delete(self, entry_id: int) -> bool:
        entry = self.get_by_id(entry_id)
        if not entry:
            return False
        self.db.delete(entry)
        self.db.commit()
        return True
