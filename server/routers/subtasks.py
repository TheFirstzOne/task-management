# -*- coding: utf-8 -*-
"""Subtasks and time-log (non-task-scoped) router — Phase 21/23"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.task import SubTask
from app.models.user import User
from app.services.task_service import TaskService
from app.services.time_tracking_service import TimeTrackingService
from app.utils.exceptions import NotFoundError, TaskFlowError, ValidationError
from server.deps import get_current_user, get_db
from server.serializers import subtask_to_dict, timelog_to_dict


class UpdateSubtaskIn(BaseModel):
    title: str
    due_date: Optional[str] = None
    assignee_id: Optional[int] = None


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value)

router = APIRouter()


def _handle_exc(exc: Exception):
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, TaskFlowError):
        raise HTTPException(status_code=400, detail=str(exc))
    raise exc


@router.patch("/subtasks/{subtask_id}")
def update_subtask(
    subtask_id: int,
    body: UpdateSubtaskIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Update a subtask's title, due_date, and assignee."""
    svc = TaskService(db)
    try:
        subtask = svc.update_subtask(
            subtask_id,
            title=body.title,
            due_date=_parse_dt(body.due_date),
            assignee_id=body.assignee_id,
        )
        return subtask_to_dict(subtask)
    except HTTPException:
        raise
    except Exception as exc:
        _handle_exc(exc)


@router.patch("/subtasks/{subtask_id}/toggle")
def toggle_subtask(
    subtask_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Toggle a subtask's completion state."""
    svc = TaskService(db)
    try:
        subtask = svc.toggle_subtask(subtask_id)
        if subtask is None:
            raise HTTPException(status_code=404, detail=f"ไม่พบ Subtask (id={subtask_id})")
        return subtask_to_dict(subtask)
    except HTTPException:
        raise
    except Exception as exc:
        _handle_exc(exc)


@router.delete("/subtasks/{subtask_id}")
def delete_subtask(
    subtask_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Delete a subtask."""
    svc = TaskService(db)
    try:
        svc.delete_subtask(subtask_id)
        return {}
    except Exception as exc:
        _handle_exc(exc)


@router.delete("/time-logs/{log_id}")
def delete_time_log(
    log_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Delete a time log entry."""
    svc = TimeTrackingService(db)
    try:
        svc.delete_log(log_id)
        return {}
    except Exception as exc:
        _handle_exc(exc)
