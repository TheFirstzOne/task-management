"""
Task model — งาน, sub-tasks, comments
"""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean,
    DateTime, Enum, ForeignKey, BigInteger
)
from sqlalchemy.orm import relationship
from app.database import Base


class TaskStatus(str, enum.Enum):
    PENDING     = "Pending"
    IN_PROGRESS = "In Progress"
    REVIEW      = "Review"
    DONE        = "Done"
    CANCELLED   = "Cancelled"


class TaskPriority(str, enum.Enum):
    LOW    = "Low"
    MEDIUM = "Medium"
    HIGH   = "High"
    URGENT = "Urgent"


class Task(Base):
    __tablename__ = "tasks"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    title          = Column(String(200), nullable=False)
    description    = Column(Text, nullable=True)
    status         = Column(Enum(TaskStatus),   nullable=False, default=TaskStatus.PENDING)
    priority       = Column(Enum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM)
    tags           = Column(String(255), nullable=True)   # comma-separated
    start_date     = Column(DateTime, nullable=True)
    due_date       = Column(DateTime, nullable=True)

    # FK
    team_id        = Column(Integer, ForeignKey("teams.id"),      nullable=True, index=True)
    assignee_id    = Column(Integer, ForeignKey("users.id"),      nullable=True, index=True)
    created_by_id  = Column(Integer, ForeignKey("users.id"),      nullable=True)
    depends_on_id  = Column(Integer, ForeignKey("tasks.id"),      nullable=True, index=True)
    milestone_id   = Column(Integer, ForeignKey("milestones.id"), nullable=True, index=True)

    created_at     = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at     = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted     = Column(Boolean, default=False, nullable=False, server_default="0", index=True)

    # Relationships
    milestone   = relationship("Milestone", back_populates="tasks")
    team        = relationship("Team", back_populates="tasks")
    assignee    = relationship("User", foreign_keys=[assignee_id],   back_populates="assigned_tasks")
    created_by  = relationship("User", foreign_keys=[created_by_id], back_populates="created_tasks")
    depends_on  = relationship("Task", remote_side="Task.id", foreign_keys=[depends_on_id])
    subtasks    = relationship("SubTask",     back_populates="task", cascade="all, delete-orphan")
    comments    = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan",
                               order_by="TaskComment.created_at")
    history     = relationship("WorkHistory", back_populates="task", cascade="all, delete-orphan",
                               order_by="WorkHistory.created_at")
    time_logs   = relationship("TimeLog",     back_populates="task", cascade="all, delete-orphan",
                               order_by="TimeLog.started_at")

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title!r} status={self.status}>"


class SubTask(Base):
    __tablename__ = "subtasks"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    task_id     = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    title       = Column(String(200), nullable=False)
    is_done     = Column(Boolean, default=False, nullable=False)
    is_deleted  = Column(Boolean, default=False, nullable=False, server_default="0")
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    due_date    = Column(DateTime, nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    task     = relationship("Task", back_populates="subtasks")
    assignee = relationship("User", foreign_keys=[assignee_id])

    def __repr__(self) -> str:
        return f"<SubTask id={self.id} title={self.title!r} done={self.is_done}>"


class TaskComment(Base):
    __tablename__ = "task_comments"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    task_id    = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    author_id  = Column(Integer, ForeignKey("users.id"), nullable=True)
    body       = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

    # Relationships
    task   = relationship("Task", back_populates="comments")
    author = relationship("User", back_populates="comments")

    def __repr__(self) -> str:
        return f"<TaskComment id={self.id} task_id={self.task_id}>"
