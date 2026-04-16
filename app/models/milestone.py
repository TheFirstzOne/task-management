"""
Milestone model — เป้าหมายของทีม จัดกลุ่ม tasks
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class Milestone(Base):
    __tablename__ = "milestones"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(100), nullable=False)
    description = Column(Text, default="")
    due_date    = Column(DateTime, nullable=True)
    is_deleted  = Column(Boolean, default=False, nullable=False, server_default="0")
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at  = Column(DateTime,
                         default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
                         onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    # Relationships
    tasks = relationship("Task", back_populates="milestone")

    def __repr__(self) -> str:
        return f"<Milestone id={self.id} name={self.name!r}>"
