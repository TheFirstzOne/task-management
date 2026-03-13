"""
TaskRepository — CRUD operations for Task, SubTask, TaskComment
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.task import Task, SubTask, TaskComment, TaskStatus, TaskPriority


class TaskRepository:

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Task Create ───────────────────────────────────────────────
    def create(
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
        task = Task(
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
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    # ── Task Read ─────────────────────────────────────────────────
    def get_by_id(self, task_id: int) -> Optional[Task]:
        return self.db.query(Task).filter(Task.id == task_id).first()

    def get_all(self) -> List[Task]:
        return self.db.query(Task).order_by(Task.created_at.desc()).all()

    def get_by_team(self, team_id: int) -> List[Task]:
        return (
            self.db.query(Task)
            .filter(Task.team_id == team_id)
            .order_by(Task.due_date.asc())
            .all()
        )

    def get_by_assignee(self, user_id: int) -> List[Task]:
        return (
            self.db.query(Task)
            .filter(Task.assignee_id == user_id)
            .order_by(Task.due_date.asc())
            .all()
        )

    def get_by_status(self, status: TaskStatus) -> List[Task]:
        return self.db.query(Task).filter(Task.status == status).all()

    def get_overdue(self) -> List[Task]:
        now = datetime.utcnow()
        return (
            self.db.query(Task)
            .filter(Task.due_date < now, Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED]))
            .all()
        )

    # ── Dependency queries ──────────────────────────────────────────
    def get_dependent_tasks(self, task_id: int) -> List[Task]:
        """Return tasks whose depends_on_id == task_id (reverse lookup)."""
        return (
            self.db.query(Task)
            .filter(Task.depends_on_id == task_id)
            .order_by(Task.created_at.desc())
            .all()
        )

    def get_dependency_chain(self, task_id: int) -> List[int]:
        """Walk the depends_on chain upward and return all ancestor IDs."""
        chain: List[int] = []
        current_id = task_id
        for _ in range(100):                        # safety limit
            task = self.get_by_id(current_id)
            if not task or not task.depends_on_id:
                break
            chain.append(task.depends_on_id)
            current_id = task.depends_on_id
        return chain

    # ── Task Update ───────────────────────────────────────────────
    def update(self, task_id: int, **kwargs) -> Optional[Task]:
        task = self.get_by_id(task_id)
        if not task:
            return None
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        self.db.commit()
        self.db.refresh(task)
        return task

    def change_status(self, task_id: int, status: TaskStatus) -> Optional[Task]:
        return self.update(task_id, status=status)

    # ── Task Delete ───────────────────────────────────────────────
    def delete(self, task_id: int) -> bool:
        task = self.get_by_id(task_id)
        if not task:
            return False
        self.db.delete(task)
        self.db.commit()
        return True

    # ── SubTask ───────────────────────────────────────────────────
    def add_subtask(self, task_id: int, title: str) -> SubTask:
        subtask = SubTask(task_id=task_id, title=title)
        self.db.add(subtask)
        self.db.commit()
        self.db.refresh(subtask)
        return subtask

    def toggle_subtask(self, subtask_id: int) -> Optional[SubTask]:
        subtask = self.db.query(SubTask).filter(SubTask.id == subtask_id).first()
        if not subtask:
            return None
        subtask.is_done = not subtask.is_done
        self.db.commit()
        self.db.refresh(subtask)
        return subtask

    def delete_subtask(self, subtask_id: int) -> bool:
        subtask = self.db.query(SubTask).filter(SubTask.id == subtask_id).first()
        if not subtask:
            return False
        self.db.delete(subtask)
        self.db.commit()
        return True

    # ── Comments ──────────────────────────────────────────────────
    def add_comment(self, task_id: int, body: str, author_id: Optional[int] = None) -> TaskComment:
        comment = TaskComment(task_id=task_id, body=body, author_id=author_id)
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def get_comments(self, task_id: int) -> List[TaskComment]:
        return (
            self.db.query(TaskComment)
            .filter(TaskComment.task_id == task_id)
            .order_by(TaskComment.created_at.asc())
            .all()
        )
