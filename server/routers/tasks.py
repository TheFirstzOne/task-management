# -*- coding: utf-8 -*-
"""Tasks, Subtasks, Comments, and Time-logs router — Phase 21"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.task import TaskPriority, TaskStatus
from app.models.user import User
from app.services.task_service import TaskService
from app.services.time_tracking_service import TimeTrackingService
from app.utils.exceptions import NotFoundError, TaskFlowError, ValidationError
from server.deps import get_current_user, get_db
from server.serializers import comment_to_dict, subtask_to_dict, task_to_dict, timelog_to_dict

router = APIRouter()


# ── Request body schemas ──────────────────────────────────────────────────────

class CreateTaskIn(BaseModel):
    title: str
    description: str = ""
    priority: str = "Medium"
    tags: str = ""
    start_date: Optional[str] = None
    due_date: Optional[str] = None
    team_id: Optional[int] = None
    assignee_id: Optional[int] = None
    depends_on_id: Optional[int] = None


class UpdateTaskIn(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[str] = None
    start_date: Optional[str] = None
    due_date: Optional[str] = None
    team_id: Optional[int] = None
    assignee_id: Optional[int] = None
    depends_on_id: Optional[int] = None


class CreateCommentIn(BaseModel):
    body: str


class CreateSubtaskIn(BaseModel):
    title: str
    due_date: Optional[str] = None
    assignee_id: Optional[int] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _handle_exc(exc: Exception):
    """Convert domain exceptions to HTTPExceptions."""
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, TaskFlowError):
        raise HTTPException(status_code=400, detail=str(exc))
    raise exc


# ── Task endpoints ────────────────────────────────────────────────────────────

@router.get("")
def list_tasks(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return all active tasks."""
    svc = TaskService(db)
    return [task_to_dict(t) for t in svc.get_all_tasks()]


@router.get("/deleted")
def list_deleted_tasks(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return all soft-deleted tasks."""
    svc = TaskService(db)
    return [task_to_dict(t) for t in svc.get_deleted_tasks()]


@router.get("/search")
def search_tasks(
    q: str = "",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Full-text search across title, description, and tags."""
    svc = TaskService(db)
    return [task_to_dict(t) for t in svc.search_tasks(q)]


@router.get("/near-due/count")
def near_due_count(
    days: int = 3,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return count of tasks due within the next N days."""
    svc = TaskService(db)
    return {"count": svc.get_near_due_count(days)}


@router.get("/near-due")
def near_due_tasks(
    days: int = 3,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return tasks due within the next N days."""
    svc = TaskService(db)
    return [task_to_dict(t) for t in svc.get_near_due_tasks(days)]


@router.get("/for-dropdown")
def tasks_for_dropdown(
    exclude_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return non-cancelled tasks for dependency dropdown."""
    svc = TaskService(db)
    return [task_to_dict(t) for t in svc.get_tasks_for_depends_dropdown(exclude_id)]


@router.get("/{task_id}")
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return a single task by ID."""
    svc = TaskService(db)
    try:
        return task_to_dict(svc.get_task(task_id))
    except Exception as exc:
        _handle_exc(exc)


@router.get("/{task_id}/dependents")
def get_dependents(
    task_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return tasks that depend on the given task."""
    svc = TaskService(db)
    return [task_to_dict(t) for t in svc.get_dependent_tasks(task_id)]


@router.post("")
def create_task(
    body: CreateTaskIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new task."""
    svc = TaskService(db)
    try:
        task = svc.create_task(
            title=body.title,
            description=body.description,
            priority=TaskPriority(body.priority),
            tags=body.tags,
            start_date=_parse_dt(body.start_date),
            due_date=_parse_dt(body.due_date),
            team_id=body.team_id,
            assignee_id=body.assignee_id,
            created_by_id=current_user.id,
            depends_on_id=body.depends_on_id,
        )
        return task_to_dict(task)
    except Exception as exc:
        _handle_exc(exc)


@router.patch("/{task_id}")
def update_task(
    task_id: int,
    body: UpdateTaskIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update one or more fields on an existing task."""
    svc = TaskService(db)
    kwargs = {}
    data = body.model_dump(exclude_none=True)

    # Handle status separately (uses change_status for history logging)
    new_status = data.pop("status", None)

    # Parse datetime strings
    for dt_field in ("start_date", "due_date"):
        if dt_field in data:
            data[dt_field] = _parse_dt(data[dt_field])

    # Convert priority string to enum
    if "priority" in data:
        data["priority"] = TaskPriority(data["priority"])

    try:
        if data:
            svc.update_task(task_id, actor_id=current_user.id, **data)
        if new_status is not None:
            svc.change_status(task_id, TaskStatus(new_status), actor_id=current_user.id)
        return task_to_dict(svc.get_task(task_id))
    except Exception as exc:
        _handle_exc(exc)


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Soft-delete a task."""
    svc = TaskService(db)
    try:
        svc.delete_task(task_id)
        return {}
    except Exception as exc:
        _handle_exc(exc)


@router.post("/{task_id}/restore")
def restore_task(
    task_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Restore a soft-deleted task."""
    svc = TaskService(db)
    try:
        return task_to_dict(svc.restore_task(task_id))
    except Exception as exc:
        _handle_exc(exc)


# ── Comment endpoints ─────────────────────────────────────────────────────────

@router.get("/{task_id}/comments")
def list_comments(
    task_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return all comments for a task."""
    svc = TaskService(db)
    return [comment_to_dict(c) for c in svc.get_comments(task_id)]


@router.post("/{task_id}/comments")
def add_comment(
    task_id: int,
    body: CreateCommentIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a comment to a task."""
    svc = TaskService(db)
    try:
        comment = svc.add_comment(task_id, body.body, author_id=current_user.id)
        return comment_to_dict(comment)
    except Exception as exc:
        _handle_exc(exc)


# ── Subtask endpoints ─────────────────────────────────────────────────────────

@router.post("/{task_id}/subtasks")
def add_subtask(
    task_id: int,
    body: CreateSubtaskIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Add a subtask to a task."""
    svc = TaskService(db)
    try:
        subtask = svc.add_subtask(
            task_id, body.title,
            due_date=_parse_dt(body.due_date),
            assignee_id=body.assignee_id,
        )
        return subtask_to_dict(subtask)
    except Exception as exc:
        _handle_exc(exc)


# ── Time-log endpoints ────────────────────────────────────────────────────────

@router.get("/{task_id}/time-logs")
def list_time_logs(
    task_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return all time logs for a task."""
    svc = TimeTrackingService(db)
    return [timelog_to_dict(tl) for tl in svc.get_logs_by_task(task_id)]


@router.get("/{task_id}/time-logs/total")
def total_minutes(
    task_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return total tracked minutes for a task."""
    svc = TimeTrackingService(db)
    return {"total_minutes": svc.get_total_minutes(task_id)}


@router.post("/{task_id}/time-logs/start")
def start_timer(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start the timer for a task."""
    svc = TimeTrackingService(db)
    tl = svc.start_timer(task_id, user_id=current_user.id)
    return timelog_to_dict(tl)


@router.post("/{task_id}/time-logs/stop")
def stop_timer(
    task_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Stop the running timer for a task."""
    svc = TimeTrackingService(db)
    tl = svc.stop_timer(task_id)
    if tl is None:
        return {}
    return timelog_to_dict(tl)
