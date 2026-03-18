"""
TeamService — Business logic for team & member management
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.team import Team
from app.models.user import User, UserRole
from app.repositories.task_repo import TaskRepository
from app.repositories.team_repo import TeamRepository
from app.repositories.user_repo import UserRepository
from app.utils.exceptions import NotFoundError, DuplicateNameError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TeamService:

    def __init__(self, db: Session) -> None:
        self.db = db
        self.task_repo = TaskRepository(db)
        self.team_repo = TeamRepository(db)
        self.user_repo = UserRepository(db)

    # ── Teams ─────────────────────────────────────────────────────
    def create_team(self, name: str, description: str = "") -> Team:
        if self.team_repo.get_by_name(name):
            raise DuplicateNameError("ทีม", name)
        return self.team_repo.create(name=name, description=description)

    def update_team(self, team_id: int, **kwargs) -> Team:
        team = self.team_repo.update(team_id, **kwargs)
        if not team:
            raise NotFoundError("ทีม", team_id)
        return team

    def delete_team(self, team_id: int) -> None:
        # Unassign members first
        members = self.user_repo.get_by_team(team_id)
        for m in members:
            self.user_repo.update(m.id, team_id=None)
        if not self.team_repo.delete(team_id):
            raise NotFoundError("ทีม", team_id)

    def get_all_teams(self) -> List[Team]:
        return self.team_repo.get_all()

    def get_team(self, team_id: int) -> Team:
        team = self.team_repo.get_by_id(team_id)
        if not team:
            raise NotFoundError("ทีม", team_id)
        return team

    # ── Members ───────────────────────────────────────────────────
    def add_member(self, team_id: int, name: str, role: UserRole,
                   skills: str = "") -> User:
        self.get_team(team_id)   # validate team exists
        return self.user_repo.create(name=name, role=role, skills=skills, team_id=team_id)

    def remove_member(self, user_id: int) -> None:
        """Unassign member from team (keeps user in system)."""
        user = self.user_repo.update(user_id, team_id=None)
        if not user:
            raise NotFoundError("สมาชิก", user_id)

    def delete_member(self, user_id: int) -> None:
        """Soft-delete a member: unassign their active tasks, then mark deleted."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("สมาชิก", user_id)
        # Unassign active tasks so they don't hold a reference to a deleted user
        count = self.task_repo.unassign_user(user_id)
        logger.info("Soft-deleting member id=%s, unassigned %d active task(s)",
                    user_id, count)
        if not self.user_repo.delete(user_id):
            raise NotFoundError("สมาชิก", user_id)

    def get_members_for_dropdown(self, team_id: Optional[int] = None) -> List[User]:
        """Return active users for assignee dropdown, optionally filtered by team_id.
        Views should call this instead of accessing user_repo directly."""
        if team_id is not None:
            return self.user_repo.get_by_team(team_id, active_only=True)
        return self.user_repo.get_all(active_only=True)

    def toggle_member_active(self, user_id: int) -> User:
        user = self.user_repo.toggle_active(user_id)
        if not user:
            raise NotFoundError("สมาชิก", user_id)
        return user

    # ── Workload ──────────────────────────────────────────────────
    def get_workload(self, team_id: int) -> Dict[int, int]:
        """Return {user_id: active_task_count} for team members."""
        members = self.user_repo.get_by_team(team_id, active_only=True)
        return {
            member.id: self.task_repo.count_active_by_assignee(member.id)
            for member in members
        }
