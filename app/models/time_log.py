"""
TimeLog model — บันทึกเวลาทำงานต่องาน
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class TimeLog(Base):
    __tablename__ = "time_logs"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    task_id          = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    started_at       = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    ended_at         = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)   # computed on stop
    note             = Column(Text, nullable=True)
    is_running       = Column(Boolean, nullable=False, default=True, index=True)
    created_at       = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    task = relationship("Task", back_populates="time_logs")
    user = relationship("User", foreign_keys=[user_id])
