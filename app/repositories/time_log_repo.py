# -*- coding: utf-8 -*-
"""
TimeLogRepository — DB access layer for TimeLog model.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.time_log import TimeLog


class TimeLogRepository:

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Create ────────────────────────────────────────────────────
    def create(
        self,
        task_id: int,
        started_at: datetime,
        is_running: bool = False,
        ended_at: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
        note: str = "",
        user_id: Optional[int] = None,
    ) -> TimeLog:
        log = TimeLog(
            task_id=task_id,
            user_id=user_id,
            started_at=started_at,
            ended_at=ended_at,
            duration_minutes=duration_minutes,
            note=note,
            is_running=is_running,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    # ── Read ──────────────────────────────────────────────────────
    def get_running(self, task_id: int) -> Optional[TimeLog]:
        return (
            self.db.query(TimeLog)
            .filter(TimeLog.task_id == task_id, TimeLog.is_running == True)  # noqa: E712
            .first()
        )

    def get_by_task(self, task_id: int) -> List[TimeLog]:
        return (
            self.db.query(TimeLog)
            .filter(TimeLog.task_id == task_id, TimeLog.is_running == False)  # noqa: E712
            .order_by(TimeLog.started_at.desc())
            .all()
        )

    def get_all_completed(self) -> List[TimeLog]:
        return (
            self.db.query(TimeLog)
            .options(joinedload(TimeLog.user))
            .filter(TimeLog.is_running == False)  # noqa: E712
            .all()
        )

    def get_all_completed_with_task(self) -> List[TimeLog]:
        return (
            self.db.query(TimeLog)
            .options(joinedload(TimeLog.task))
            .filter(TimeLog.is_running == False)  # noqa: E712
            .all()
        )

    # ── Update ────────────────────────────────────────────────────
    def stop(self, log: TimeLog, ended_at: datetime, duration_minutes: int) -> TimeLog:
        log.ended_at = ended_at
        log.is_running = False
        log.duration_minutes = duration_minutes
        self.db.commit()
        self.db.refresh(log)
        return log

    # ── Delete ────────────────────────────────────────────────────
    def delete(self, log_id: int) -> bool:
        log = self.db.get(TimeLog, log_id)
        if not log:
            return False
        self.db.delete(log)
        self.db.commit()
        return True
