"""
TaskService — Business logic for task management & history logging
"""

from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus, TaskPriority
from app.models.history import WorkHistory
from app.repositories.task_repo import TaskRepository
from app.repositories.user_repo import UserRepository


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
            raise ValueError(f"ไม่พบงาน id={task_id}")
        return task

    def get_all_tasks(self) -> List[Task]:
        return self.task_repo.get_all()

    def get_tasks_by_team(self, team_id: int) -> List[Task]:
        return self.task_repo.get_by_team(team_id)

    def get_tasks_by_assignee(self, user_id: int) -> List[Task]:
        return self.task_repo.get_by_assignee(user_id)

    def get_overdue_tasks(self) -> List[Task]:
        return self.task_repo.get_overdue()

    # ── Update ────────────────────────────────────────────────────
    def update_task(self, task_id: int, actor_id: Optional[int] = None,
                    **kwargs) -> Task:
        task = self.get_task(task_id)
        changed = {k: (getattr(task, k), v) for k, v in kwargs.items()
                   if hasattr(task, k) and getattr(task, k) != v}
        updated = self.task_repo.update(task_id, **kwargs)
        for field, (old, new) in changed.items():
            self._log(task_id, f"updated_{field}", detail=f"แก้ไข {field}",
                      old_value=str(old), new_value=str(new), actor_id=actor_id)
        return updated

    def change_status(self, task_id: int, new_status: TaskStatus,
                      actor_id: Optional[int] = None) -> Task:
        task = self.get_task(task_id)
        old_status = task.status
        updated = self.task_repo.change_status(task_id, new_status)
        self._log(task_id, "status_changed",
                  detail=f"เปลี่ยนสถานะ: {old_status} → {new_status}",
                  old_value=old_status, new_value=new_status, actor_id=actor_id)
        return updated

    def assign_task(self, task_id: int, assignee_id: Optional[int],
                    actor_id: Optional[int] = None) -> Task:
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
            raise ValueError(f"ไม่พบงาน id={task_id}")

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
    def get_dashboard_stats(self) -> Dict[str, int]:
        all_tasks = self.task_repo.get_all()
        done      = sum(1 for t in all_tasks if t.status == TaskStatus.DONE)
        cancelled = sum(1 for t in all_tasks if t.status == TaskStatus.CANCELLED)
        overdue   = len(self.task_repo.get_overdue())
        pending   = sum(1 for t in all_tasks if t.status == TaskStatus.PENDING)
        in_prog   = sum(1 for t in all_tasks if t.status == TaskStatus.IN_PROGRESS)
        return {
            "total":       len(all_tasks),
            "done":        done,
            "cancelled":   cancelled,
            "overdue":     overdue,
            "pending":     pending,
            "in_progress": in_prog,
        }
