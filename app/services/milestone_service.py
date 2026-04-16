"""
MilestoneService — Business logic สำหรับ Milestone
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.milestone import Milestone
from app.models.task import Task
from app.repositories.milestone_repo import MilestoneRepository
from app.repositories.task_repo import TaskRepository
from app.utils.exceptions import ValidationError, NotFoundError


class MilestoneService:

    def __init__(self, db: Session) -> None:
        self.db = db
        self.milestone_repo = MilestoneRepository(db)
        self.task_repo = TaskRepository(db)

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def create_milestone(
        self,
        name: str,
        description: str = "",
        due_date: Optional[datetime] = None,
    ) -> Milestone:
        if not name or not name.strip():
            raise ValidationError("ชื่อ Milestone ต้องไม่ว่าง")
        if len(name.strip()) > 100:
            raise ValidationError("ชื่อ Milestone ต้องไม่เกิน 100 ตัวอักษร")
        return self.milestone_repo.create(
            name=name, description=description, due_date=due_date
        )

    def get_all_milestones(self) -> List[Milestone]:
        return self.milestone_repo.get_all()

    def get_milestone(self, milestone_id: int) -> Milestone:
        m = self.milestone_repo.get_by_id(milestone_id)
        if not m:
            raise NotFoundError("Milestone", milestone_id)
        return m

    def update_milestone(self, milestone_id: int, **kwargs) -> Milestone:
        self.get_milestone(milestone_id)  # raises NotFoundError if not found
        name = kwargs.get("name")
        if name is not None and not str(name).strip():
            raise ValidationError("ชื่อ Milestone ต้องไม่ว่าง")
        if name is not None and len(str(name).strip()) > 100:
            raise ValidationError("ชื่อ Milestone ต้องไม่เกิน 100 ตัวอักษร")
        if "name" in kwargs and kwargs["name"]:
            kwargs["name"] = kwargs["name"].strip()
        return self.milestone_repo.update(milestone_id, **kwargs)

    def delete_milestone(self, milestone_id: int) -> None:
        m = self.get_milestone(milestone_id)
        # Unlink tasks before deleting
        for task in m.tasks:
            if not task.is_deleted:
                task.milestone_id = None
        self.db.commit()
        self.milestone_repo.delete(milestone_id)

    # ── Task assignment ───────────────────────────────────────────────────────

    def assign_task(self, task_id: int, milestone_id: int) -> Task:
        self.get_milestone(milestone_id)  # verify milestone exists
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task", task_id)
        task.milestone_id = milestone_id
        self.db.commit()
        self.db.refresh(task)
        return task

    def remove_task(self, task_id: int) -> Task:
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Task", task_id)
        task.milestone_id = None
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_tasks(self, milestone_id: int) -> List[Task]:
        self.get_milestone(milestone_id)
        return (
            self.db.query(Task)
            .filter(Task.milestone_id == milestone_id, Task.is_deleted == False)
            .order_by(Task.due_date.asc().nullslast(), Task.created_at.asc())
            .all()
        )

    # ── Progress ──────────────────────────────────────────────────────────────

    def get_progress(self, milestone_id: int) -> dict:
        tasks = self.get_tasks(milestone_id)
        total = len(tasks)
        done  = sum(1 for t in tasks if t.status and t.status.value == "Done")
        return {
            "total":   total,
            "done":    done,
            "percent": round(done / total, 2) if total > 0 else 0.0,
        }
