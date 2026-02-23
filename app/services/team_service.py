"""
TeamService — Business logic for team & member management
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.team import Team
from app.models.user import User, UserRole
from app.repositories.team_repo import TeamRepository
from app.repositories.user_repo import UserRepository


class TeamService:

    def __init__(self, db: Session) -> None:
        self.db = db
        self.team_repo = TeamRepository(db)
        self.user_repo = UserRepository(db)

    # ── Teams ─────────────────────────────────────────────────────
    def create_team(self, name: str, description: str = "") -> Team:
        if self.team_repo.get_by_name(name):
            raise ValueError(f"ทีมชื่อ '{name}' มีอยู่แล้ว")
        return self.team_repo.create(name=name, description=description)

    def update_team(self, team_id: int, **kwargs) -> Team:
        team = self.team_repo.update(team_id, **kwargs)
        if not team:
            raise ValueError(f"ไม่พบทีม id={team_id}")
        return team

    def delete_team(self, team_id: int) -> None:
        # Unassign members first
        members = self.user_repo.get_by_team(team_id)
        for m in members:
            self.user_repo.update(m.id, team_id=None)
        if not self.team_repo.delete(team_id):
            raise ValueError(f"ไม่พบทีม id={team_id}")

    def get_all_teams(self) -> List[Team]:
        return self.team_repo.get_all()

    def get_team(self, team_id: int) -> Team:
        team = self.team_repo.get_by_id(team_id)
        if not team:
            raise ValueError(f"ไม่พบทีม id={team_id}")
        return team

    # ── Members ───────────────────────────────────────────────────
    def add_member(self, team_id: int, name: str, role: UserRole,
                   skills: str = "") -> User:
        self.get_team(team_id)   # validate team exists
        return self.user_repo.create(name=name, role=role, skills=skills, team_id=team_id)

    def remove_member(self, user_id: int) -> None:
        user = self.user_repo.update(user_id, team_id=None)
        if not user:
            raise ValueError(f"ไม่พบสมาชิก id={user_id}")

    def toggle_member_active(self, user_id: int) -> User:
        user = self.user_repo.toggle_active(user_id)
        if not user:
            raise ValueError(f"ไม่พบสมาชิก id={user_id}")
        return user

    # ── Workload ──────────────────────────────────────────────────
    def get_workload(self, team_id: int) -> Dict[int, int]:
        """Return {user_id: active_task_count} for team members."""
        from app.models.task import Task, TaskStatus
        members = self.user_repo.get_by_team(team_id, active_only=True)
        result: Dict[int, int] = {}
        for member in members:
            count = (
                self.db.query(Task)
                .filter(
                    Task.assignee_id == member.id,
                    Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED]),
                )
                .count()
            )
            result[member.id] = count
        return result
