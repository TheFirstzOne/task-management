"""
TeamRepository — CRUD operations for Team model
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.team import Team


class TeamRepository:

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
        return self.db.query(Team).filter(Team.id == team_id).first()

    def get_all(self) -> List[Team]:
        return self.db.query(Team).order_by(Team.name).all()

    def get_by_name(self, name: str) -> Optional[Team]:
        return self.db.query(Team).filter(Team.name == name).first()

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
        team = self.get_by_id(team_id)
        if not team:
            return False
        self.db.delete(team)
        self.db.commit()
        return True
