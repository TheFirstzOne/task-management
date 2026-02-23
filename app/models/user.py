"""
User model — สมาชิกทีม
"""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, enum.Enum):
    TECHNICIAN = "Technician"
    ENGINEER   = "Engineer"
    CNC        = "CNC"
    PLC        = "PLC"
    HYDRAULIC  = "Hydraulic"
    OTHER      = "Other"


class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(100), nullable=False)
    role       = Column(Enum(UserRole), nullable=False, default=UserRole.TECHNICIAN)
    skills     = Column(String(255), nullable=True)          # comma-separated tags
    is_active  = Column(Boolean, default=True, nullable=False)
    team_id    = Column(Integer, ForeignKey("teams.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team             = relationship("Team", back_populates="members")
    assigned_tasks   = relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee")
    created_tasks    = relationship("Task", foreign_keys="Task.created_by_id", back_populates="created_by")
    comments         = relationship("TaskComment", back_populates="author")
    history_entries  = relationship("WorkHistory", back_populates="actor")

    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.name!r} role={self.role}>"
