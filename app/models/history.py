"""
WorkHistory model — Action log ทุกการเปลี่ยนแปลง
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class WorkHistory(Base):
    __tablename__ = "work_history"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    task_id     = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    actor_id    = Column(Integer, ForeignKey("users.id"), nullable=True)

    # e.g. "created", "status_changed", "assigned", "commented", "due_date_changed"
    action      = Column(String(64), nullable=False)

    # Human-readable description of the change
    detail      = Column(Text, nullable=True)

    # JSON snapshot (old_value → new_value) — stored as plain text
    old_value   = Column(Text, nullable=True)
    new_value   = Column(Text, nullable=True)

    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

    # Relationships
    task  = relationship("Task", back_populates="history")
    actor = relationship("User", back_populates="history_entries")

    def __repr__(self) -> str:
        return f"<WorkHistory id={self.id} action={self.action!r} task_id={self.task_id}>"
