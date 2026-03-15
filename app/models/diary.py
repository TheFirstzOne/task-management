"""
DiaryEntry model — บันทึกการทำงานรายวัน
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime
from app.database import Base


class DiaryEntry(Base):
    __tablename__ = "diary_entries"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    content    = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<DiaryEntry id={self.id} created_at={self.created_at}>"
