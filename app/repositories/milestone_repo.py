"""
MilestoneRepository — CRUD + soft-delete สำหรับ Milestone
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.milestone import Milestone
from app.repositories.base import BaseRepository


class MilestoneRepository(BaseRepository[Milestone]):

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── BaseRepository interface ──────────────────────────────────────────────

    def get_by_id(self, id: int) -> Optional[Milestone]:
        return (
            self.db.query(Milestone)
            .filter(Milestone.id == id, Milestone.is_deleted == False)
            .first()
        )

    def get_all(self) -> List[Milestone]:
        return (
            self.db.query(Milestone)
            .filter(Milestone.is_deleted == False)
            .order_by(Milestone.due_date.asc().nullslast(), Milestone.created_at.asc())
            .all()
        )

    def delete(self, id: int) -> bool:
        m = self.get_by_id(id)
        if not m:
            return False
        m.is_deleted = True
        self.db.commit()
        return True

    # ── Extra methods ─────────────────────────────────────────────────────────

    def create(self, name: str, description: str = "", due_date=None) -> Milestone:
        m = Milestone(name=name.strip(), description=description.strip(), due_date=due_date)
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return m

    def update(self, id: int, **kwargs) -> Optional[Milestone]:
        m = self.get_by_id(id)
        if not m:
            return None
        for key, value in kwargs.items():
            if hasattr(m, key):
                setattr(m, key, value)
        self.db.commit()
        self.db.refresh(m)
        return m
