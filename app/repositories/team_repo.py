"""
TeamRepository — CRUD operations for Team model
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.team import Team
from app.repositories.base import BaseRepository


class TeamRepository(BaseRepository[Team]):

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Create ────────────────────────────────────────────────────
    def create(self, name: str, description: str = "") -> Team:
        team = Team(name=name, description=description)
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team

    # ── Read ──────────────────────────────────────────────────────
    def get_by_id(self, team_id: int) -> Optional[Team]:
        return (self.db.query(Team)
                .filter(Team.id == team_id, Team.is_deleted == False)  # noqa: E712
                .first())

    def get_all(self) -> List[Team]:
        return (self.db.query(Team)
                .filter(Team.is_deleted == False)  # noqa: E712
                .order_by(Team.name)
                .all())

    def get_by_name(self, name: str) -> Optional[Team]:
        return (self.db.query(Team)
                .filter(Team.name == name, Team.is_deleted == False)  # noqa: E712
                .first())

    # ── Update ────────────────────────────────────────────────────
    def update(self, team_id: int, **kwargs) -> Optional[Team]:
        team = self.get_by_id(team_id)
        if not team:
            return None
        for key, value in kwargs.items():
            if hasattr(team, key):
                setattr(team, key, value)
        self.db.commit()
        self.db.refresh(team)
        return team

    # ── Delete ────────────────────────────────────────────────────
    def delete(self, team_id: int) -> bool:
        """Soft-delete a team by setting is_deleted = True."""
        team = self.get_by_id(team_id)
        if not team:
            return False
        team.is_deleted = True
        self.db.commit()
        return True

    def delete_permanent(self, team_id: int) -> bool:
        """Hard delete — permanently removes team from database."""
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return False
        self.db.delete(team)
        self.db.commit()
        return True
