"""
UserRepository — CRUD operations for User model
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user import User, UserRole


class UserRepository:

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Create ────────────────────────────────────────────────────
    def create(self, name: str, role: UserRole, skills: str = "",
               team_id: Optional[int] = None) -> User:
        user = User(name=name, role=role, skills=skills, team_id=team_id)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    # ── Read ──────────────────────────────────────────────────────
    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_all(self, active_only: bool = False) -> List[User]:
        q = self.db.query(User)
        if active_only:
            q = q.filter(User.is_active == True)  # noqa: E712
        return q.order_by(User.name).all()

    def get_by_team(self, team_id: int, active_only: bool = False) -> List[User]:
        q = self.db.query(User).filter(User.team_id == team_id)
        if active_only:
            q = q.filter(User.is_active == True)  # noqa: E712
        return q.order_by(User.name).all()

    # ── Update ────────────────────────────────────────────────────
    def update(self, user_id: int, **kwargs) -> Optional[User]:
        user = self.get_by_id(user_id)
        if not user:
            return None
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def toggle_active(self, user_id: int) -> Optional[User]:
        user = self.get_by_id(user_id)
        if not user:
            return None
        user.is_active = not user.is_active
        self.db.commit()
        self.db.refresh(user)
        return user

    # ── Delete ────────────────────────────────────────────────────
    def delete(self, user_id: int) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            return False
        self.db.delete(user)
        self.db.commit()
        return True
