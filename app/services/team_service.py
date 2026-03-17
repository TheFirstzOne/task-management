"""
TeamService — Business logic for team & member management
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.team import Team
from app.models.user import User, UserRole
from app.repositories.team_repo import TeamRepository
from app.repositories.user_repo import UserRepository
from app.utils.exceptions import NotFoundError, DuplicateNameError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TeamService:

    def __init__(self, db: Session) -> None:
        self.db = db
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
        from app.models.task import Task, TaskStatus
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("สมาชิก", user_id)
        # Unassign active tasks so they don't hold a reference to a deleted user
        active_tasks = (
            self.db.query(Task)
            .filter(
                Task.assignee_id == user_id,
                Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED]),
                Task.is_deleted == False,  # noqa: E712
            )
            .all()
        )
        for task in active_tasks:
            task.assignee_id = None
        self.db.commit()
        logger.info("Soft-deleting member id=%s, unassigned %d active task(s)",
                    user_id, len(active_tasks))
        if not self.user_repo.delete(user_id):
            raise NotFoundError("สมาชิก", user_id)

    def toggle_member_active(self, user_id: int) -> User:
        user = self.user_repo.toggle_active(user_id)
        if not user:
            raise NotFoundError("สมาชิก", user_id)
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
