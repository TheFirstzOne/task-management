# -*- coding: utf-8 -*-
"""
TimeTrackingService — Phase 13 (C)
Handles: start/stop timer, manual log, query logs, summary per task/member.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List, Dict, TypedDict

from sqlalchemy.orm import Session

from app.models.time_log import TimeLog
from app.repositories.time_log_repo import TimeLogRepository


class MemberSummary(TypedDict):
    name: str
    total_minutes: int
    task_count: int
    hours: float


class TaskTimeSummary(TypedDict):
    title: str
    total_minutes: int


class TimeTrackingService:

    def __init__(self, db: Session):
        self.db = db
        self.time_log_repo = TimeLogRepository(db)

    # ── Timer control ─────────────────────────────────────────────
    def start_timer(self, task_id: int, user_id: Optional[int] = None) -> TimeLog:
        """Start a new running timer for a task.
        Stops any previously running timer for the same task first."""
        self._stop_running(task_id)
        return self.time_log_repo.create(
            task_id=task_id,
            user_id=user_id,
            started_at=datetime.now(timezone.utc).replace(tzinfo=None),
            is_running=True,
        )

    def stop_timer(self, task_id: int) -> Optional[TimeLog]:
        """Stop the running timer for a task; compute duration."""
        log = self.time_log_repo.get_running(task_id)
        if not log:
            return None
        ended_at = datetime.now(timezone.utc).replace(tzinfo=None)
        delta = ended_at - log.started_at
        duration = max(1, int(delta.total_seconds() / 60))
        return self.time_log_repo.stop(log, ended_at, duration)

    def is_running(self, task_id: int) -> bool:
        return self.time_log_repo.get_running(task_id) is not None

    def get_running_log(self, task_id: int) -> Optional[TimeLog]:
        return self.time_log_repo.get_running(task_id)

    # ── Manual log ────────────────────────────────────────────────
    def add_manual_log(
        self,
        task_id: int,
        duration_minutes: int,
        note: str = "",
        user_id: Optional[int] = None,
        started_at: Optional[datetime] = None,
    ) -> TimeLog:
        now = started_at or datetime.now(timezone.utc).replace(tzinfo=None)
        return self.time_log_repo.create(
            task_id=task_id,
            user_id=user_id,
            started_at=now,
            ended_at=now,
            duration_minutes=max(1, duration_minutes),
            note=note,
            is_running=False,
        )

    def delete_log(self, log_id: int) -> None:
        self.time_log_repo.delete(log_id)

    # ── Query ─────────────────────────────────────────────────────
    def get_logs_by_task(self, task_id: int) -> List[TimeLog]:
        return self.time_log_repo.get_by_task(task_id)

    def get_total_minutes(self, task_id: int) -> int:
        logs = self.get_logs_by_task(task_id)
        return sum(log.duration_minutes or 0 for log in logs)

    def get_summary_by_member(self) -> List[MemberSummary]:
        """Return [{name, total_minutes, task_count, hours}] for all members.
        Uses joinedload to avoid N+1 queries on user relationship."""
        rows = self.time_log_repo.get_all_completed()
        agg: Dict[Optional[int], Dict] = {}
        for row in rows:
            uid  = row.user_id
            name = row.user.name if row.user else "ไม่ระบุ"
            if uid not in agg:
                agg[uid] = {"name": name, "total_minutes": 0, "task_ids": set()}
            agg[uid]["total_minutes"] += row.duration_minutes or 0
            agg[uid]["task_ids"].add(row.task_id)

        result = []
        for v in sorted(agg.values(), key=lambda x: x["total_minutes"], reverse=True):
            result.append({
                "name":          v["name"],
                "total_minutes": v["total_minutes"],
                "task_count":    len(v["task_ids"]),
                "hours":         v["total_minutes"] / 60,
            })
        return result

    def get_summary_by_task(self) -> List[TaskTimeSummary]:
        """Return [{title, total_minutes}] sorted desc.
        Uses joinedload to avoid N+1 queries on task relationship."""
        rows = self.time_log_repo.get_all_completed_with_task()
        agg: Dict[int, Dict] = {}
        for row in rows:
            tid = row.task_id
            if tid not in agg:
                title = row.task.title if row.task else f"Task #{tid}"
                agg[tid] = {"title": title, "total_minutes": 0}
            agg[tid]["total_minutes"] += row.duration_minutes or 0

        return sorted(agg.values(), key=lambda x: x["total_minutes"], reverse=True)

    # ── Private ───────────────────────────────────────────────────
    def _stop_running(self, task_id: int) -> None:
        log = self.time_log_repo.get_running(task_id)
        if log:
            ended_at = datetime.now(timezone.utc).replace(tzinfo=None)
            delta = ended_at - log.started_at
            duration = max(1, int(delta.total_seconds() / 60))
            self.time_log_repo.stop(log, ended_at, duration)
