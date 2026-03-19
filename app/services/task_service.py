"""
TaskService — Business logic for task management & history logging
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, TypedDict
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus, TaskPriority
from app.models.history import WorkHistory
from app.repositories.task_repo import TaskRepository
from app.repositories.user_repo import UserRepository
from app.utils.exceptions import (
    NotFoundError, CircularDependencyError, SelfDependencyError, ValidationError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DashboardStats(TypedDict):
    total: int
    pending: int
    in_progress: int
    review: int
    done: int
    cancelled: int
    overdue: int


class TaskService:

    def __init__(self, db: Session) -> None:
        self.db = db
        self.task_repo = TaskRepository(db)
        self.user_repo = UserRepository(db)

    # ── Internal: log history ─────────────────────────────────────
    def _log(self, task_id: int, action: str, detail: str = "",
             old_value: str = "", new_value: str = "",
             actor_id: Optional[int] = None) -> None:
        entry = WorkHistory(
            task_id=task_id,
            actor_id=actor_id,
            action=action,
            detail=detail,
            old_value=old_value,
            new_value=new_value,
        )
        self.db.add(entry)
        self.db.commit()

    # ── Dependency validation ──────────────────────────────────────
    def _validate_dependency(self, task_id: Optional[int],
                             depends_on_id: Optional[int]) -> None:
        """Raise TaskFlowError if dependency is invalid (self-ref or circular)."""
        if depends_on_id is None:
            return
        target = self.task_repo.get_by_id(depends_on_id)
        if not target:
            raise NotFoundError("Task", depends_on_id)
        if task_id is not None and task_id == depends_on_id:
            raise SelfDependencyError(task_id)
        if task_id is not None:
            chain = self.task_repo.get_dependency_chain(depends_on_id)
            if task_id in chain:
                raise CircularDependencyError(task_id, depends_on_id)

    def check_dependency_warning(self, task_id: int) -> Optional[str]:
        """Return warning string if dependency is not Done, else None."""
        task = self.get_task(task_id)
        if not task.depends_on_id:
            return None
        dep = self.task_repo.get_by_id(task.depends_on_id)
        if not dep:
            return None
        if dep.status != TaskStatus.DONE:
            return f"งาน \"{dep.title}\" (สถานะ: {dep.status.value}) ยังไม่เสร็จ"
        return None

    def get_dependent_tasks(self, task_id: int) -> List[Task]:
        return self.task_repo.get_dependent_tasks(task_id)

    def get_tasks_for_depends_dropdown(
        self, exclude_id: Optional[int] = None
    ) -> List[Task]:
        """Return non-cancelled tasks for dependency dropdown, excluding the task being edited.
        Views should call this instead of filtering tasks inline."""
        return [
            t for t in self.task_repo.get_all()
            if t.id != exclude_id and t.status != TaskStatus.CANCELLED
        ]

    # ── Input validation ──────────────────────────────────────────
    def _validate_task_input(self, title: str,
                              start_date: Optional[datetime],
                              due_date: Optional[datetime]) -> None:
        if not title or not title.strip():
            raise ValidationError("ชื่องานต้องไม่ว่าง")
        if start_date and due_date and start_date > due_date:
            raise ValidationError("วันเริ่มต้องไม่อยู่หลังวันครบกำหนด")

    # ── Create ────────────────────────────────────────────────────
    def create_task(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        tags: str = "",
        start_date: Optional[datetime] = None,
        due_date: Optional[datetime] = None,
        team_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        created_by_id: Optional[int] = None,
        depends_on_id: Optional[int] = None,
    ) -> Task:
        """Create a new task after validating input and dependency.
        Raises ValidationError, SelfDependencyError, CircularDependencyError."""
        self._validate_task_input(title, start_date, due_date)
        self._validate_dependency(None, depends_on_id)
        task = self.task_repo.create(
            title=title,
            description=description,
            priority=priority,
            tags=tags,
            start_date=start_date,
            due_date=due_date,
            team_id=team_id,
            assignee_id=assignee_id,
            created_by_id=created_by_id,
            depends_on_id=depends_on_id,
        )
        self._log(task.id, "created", detail=f"สร้างงาน: {title}", actor_id=created_by_id)
        return task

    # ── Read ──────────────────────────────────────────────────────
    def get_task(self, task_id: int) -> Task:
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task", task_id)
        return task

    def get_all_tasks(self) -> List[Task]:
        return self.task_repo.get_all()

    def get_task_or_none(self, task_id: int) -> Optional[Task]:
        """Return task by id without raising — returns None if not found."""
        return self.task_repo.get_by_id(task_id)

    def get_deleted_tasks(self) -> List[Task]:
        """Return all soft-deleted tasks."""
        return self.task_repo.get_deleted()

    def get_comments(self, task_id: int):
        """Return comments for a task ordered by created_at asc."""
        return self.task_repo.get_comments(task_id)

    def get_tasks_by_team(self, team_id: int) -> List[Task]:
        return self.task_repo.get_by_team(team_id)

    def get_tasks_by_assignee(self, user_id: int) -> List[Task]:
        return self.task_repo.get_by_assignee(user_id)

    def get_overdue_tasks(self) -> List[Task]:
        return self.task_repo.get_overdue()

    def get_near_due_tasks(self, days_ahead: int = 3) -> List[Task]:
        """Return active tasks due within the next `days_ahead` days (not yet overdue)."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        cutoff = now + timedelta(days=days_ahead)
        return (
            self.db.query(Task)
            .filter(
                Task.is_deleted == False,  # noqa: E712
                Task.due_date >= now,
                Task.due_date <= cutoff,
                Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED]),
            )
            .order_by(Task.due_date.asc())
            .all()
        )

    def get_near_due_count(self, days_ahead: int = 3) -> int:
        """Return count of active tasks due within `days_ahead` days."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        cutoff = now + timedelta(days=days_ahead)
        return (
            self.db.query(func.count(Task.id))
            .filter(
                Task.is_deleted == False,  # noqa: E712
                Task.due_date >= now,
                Task.due_date <= cutoff,
                Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED]),
            )
            .scalar() or 0
        )

    # ── Update ────────────────────────────────────────────────────
    def update_task(self, task_id: int, actor_id: Optional[int] = None,
                    **kwargs) -> Task:
        """Update task fields; validates changed title/dates and dependency.
        Logs a history entry for each changed field."""
        # Validate input fields if being changed
        if "title" in kwargs or "start_date" in kwargs or "due_date" in kwargs:
            task = self.get_task(task_id)
            title      = kwargs.get("title",      task.title)
            start_date = kwargs.get("start_date", task.start_date)
            due_date   = kwargs.get("due_date",   task.due_date)
            self._validate_task_input(title, start_date, due_date)
        # Validate dependency if being changed
        if "depends_on_id" in kwargs:
            self._validate_dependency(task_id, kwargs["depends_on_id"])

        task = self.get_task(task_id)
        changed = {k: (getattr(task, k), v) for k, v in kwargs.items()
                   if hasattr(task, k) and getattr(task, k) != v}
        updated = self.task_repo.update(task_id, **kwargs)
        for field, (old, new) in changed.items():
            if field == "depends_on_id":
                old_t = self.task_repo.get_by_id(old) if old else None
                new_t = self.task_repo.get_by_id(new) if new else None
                old_name = old_t.title if old_t else (f"#{old}" if old else "ไม่มี")
                new_name = new_t.title if new_t else (f"#{new}" if new else "ไม่มี")
                self._log(task_id, "dependency_changed",
                          detail=f"เปลี่ยนงานที่ต้องทำก่อน: {old_name} → {new_name}",
                          old_value=str(old), new_value=str(new), actor_id=actor_id)
            else:
                self._log(task_id, f"updated_{field}", detail=f"แก้ไข {field}",
                          old_value=str(old), new_value=str(new), actor_id=actor_id)
        return updated

    def change_status(self, task_id: int, new_status: TaskStatus,
                      actor_id: Optional[int] = None) -> Task:
        """Change task status and log the transition to history."""
        task = self.get_task(task_id)
        old_status = task.status
        updated = self.task_repo.change_status(task_id, new_status)
        self._log(task_id, "status_changed",
                  detail=f"เปลี่ยนสถานะ: {old_status.value} → {new_status.value}",
                  old_value=old_status.value, new_value=new_status.value,
                  actor_id=actor_id)
        return updated

    def assign_task(self, task_id: int, assignee_id: Optional[int],
                    actor_id: Optional[int] = None) -> Task:
        """Assign (or unassign) a task to a user; logs to history."""
        task = self.get_task(task_id)
        old_assignee = task.assignee_id
        updated = self.task_repo.update(task_id, assignee_id=assignee_id)
        self._log(task_id, "assigned",
                  detail="มอบหมายงาน",
                  old_value=str(old_assignee), new_value=str(assignee_id),
                  actor_id=actor_id)
        return updated

    # ── Delete ────────────────────────────────────────────────────
    def delete_task(self, task_id: int) -> None:
        if not self.task_repo.delete(task_id):
            raise NotFoundError("Task", task_id)

    def restore_task(self, task_id: int) -> Task:
        """Restore a soft-deleted task."""
        task = self.task_repo.restore(task_id)
        if not task:
            raise NotFoundError("Task", task_id)
        self._log(task_id, "restored", detail="กู้คืนงานที่ถูกลบ")
        return task

    # ── SubTasks ──────────────────────────────────────────────────
    def add_subtask(self, task_id: int, title: str):
        return self.task_repo.add_subtask(task_id, title)

    def toggle_subtask(self, subtask_id: int):
        return self.task_repo.toggle_subtask(subtask_id)

    def delete_subtask(self, subtask_id: int) -> None:
        self.task_repo.delete_subtask(subtask_id)

    # ── Comments ──────────────────────────────────────────────────
    def add_comment(self, task_id: int, body: str,
                    author_id: Optional[int] = None):
        comment = self.task_repo.add_comment(task_id, body, author_id)
        self._log(task_id, "commented", detail=body[:80], actor_id=author_id)
        return comment

    # ── Summary / Dashboard ───────────────────────────────────────
    def get_dashboard_stats(self) -> DashboardStats:
        """Return task counts using SQL COUNT queries — avoids loading all rows."""
        base = (
            self.db.query(func.count(Task.id))
            .filter(Task.is_deleted == False)
        )
        def _count_status(status: TaskStatus) -> int:
            return base.filter(Task.status == status).scalar() or 0

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        overdue = (
            self.db.query(func.count(Task.id))
            .filter(
                Task.is_deleted == False,
                Task.due_date < now,
                Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED]),
            )
            .scalar() or 0
        )
        return {
            "total":       base.scalar() or 0,
            "done":        _count_status(TaskStatus.DONE),
            "cancelled":   _count_status(TaskStatus.CANCELLED),
            "overdue":     overdue,
            "pending":     _count_status(TaskStatus.PENDING),
            "in_progress": _count_status(TaskStatus.IN_PROGRESS),
            "review":      _count_status(TaskStatus.REVIEW),
        }
