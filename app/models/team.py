"""
Team model — ทีมงาน
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Team(Base):
    __tablename__ = "teams"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_deleted  = Column(Boolean, default=False, nullable=False, server_default="0")
    created_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    members = relationship("User", back_populates="team", cascade="all, delete-orphan")
    tasks   = relationship("Task", back_populates="team")

    def __repr__(self) -> str:
        return f"<Team id={self.id} name={self.name!r}>"
