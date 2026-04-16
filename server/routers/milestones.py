# -*- coding: utf-8 -*-
"""Milestone CRUD endpoints — Phase 22"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from server.deps import get_current_user, get_db
from server.serializers import milestone_to_dict, task_to_dict
from app.models.user import User
from app.services.milestone_service import MilestoneService
from app.utils.exceptions import NotFoundError, TaskFlowError, ValidationError

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateMilestoneIn(BaseModel):
    name: str
    description: str = ""
    due_date: Optional[str] = None


class UpdateMilestoneIn(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _handle_exc(exc: Exception):
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, TaskFlowError):
        raise HTTPException(status_code=400, detail=str(exc))
    raise exc


def _parse_date(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"รูปแบบวันที่ไม่ถูกต้อง: {s!r}")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
def list_milestones(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    svc = MilestoneService(db)
    return [milestone_to_dict(m) for m in svc.get_all_milestones()]


@router.post("")
def create_milestone(
    body: CreateMilestoneIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    svc = MilestoneService(db)
    try:
        m = svc.create_milestone(
            name=body.name,
            description=body.description,
            due_date=_parse_date(body.due_date),
        )
        return milestone_to_dict(m)
    except Exception as exc:
        _handle_exc(exc)


@router.get("/{milestone_id}")
def get_milestone(
    milestone_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    svc = MilestoneService(db)
    try:
        m = svc.get_milestone(milestone_id)
        data = milestone_to_dict(m)
        data["tasks"] = [task_to_dict(t) for t in svc.get_tasks(milestone_id)]
        return data
    except Exception as exc:
        _handle_exc(exc)


@router.patch("/{milestone_id}")
def update_milestone(
    milestone_id: int,
    body: UpdateMilestoneIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    svc = MilestoneService(db)
    try:
        data = body.model_dump(exclude_none=True)
        if "due_date" in data:
            data["due_date"] = _parse_date(data["due_date"])
        m = svc.update_milestone(milestone_id, **data)
        return milestone_to_dict(m)
    except Exception as exc:
        _handle_exc(exc)


@router.delete("/{milestone_id}")
def delete_milestone(
    milestone_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    svc = MilestoneService(db)
    try:
        svc.delete_milestone(milestone_id)
        return {}
    except Exception as exc:
        _handle_exc(exc)


@router.post("/{milestone_id}/tasks/{task_id}")
def assign_task(
    milestone_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    svc = MilestoneService(db)
    try:
        task = svc.assign_task(task_id, milestone_id)
        return task_to_dict(task)
    except Exception as exc:
        _handle_exc(exc)


@router.delete("/{milestone_id}/tasks/{task_id}")
def remove_task(
    milestone_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    svc = MilestoneService(db)
    try:
        svc.remove_task(task_id)
        return {}
    except Exception as exc:
        _handle_exc(exc)
