# -*- coding: utf-8 -*-
"""History router — Phase 21"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.history import WorkHistory
from app.models.user import User
from server.deps import get_current_user, get_db
from server.serializers import history_to_dict

router = APIRouter()

PAGE_SIZE = 50


@router.get("")
def list_history(
    search: str = "",
    action: str = "",
    actor_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = 0,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return history entries with optional filters, paginated 50 per page."""
    query = db.query(WorkHistory).order_by(WorkHistory.created_at.desc())

    if search:
        query = query.filter(
            WorkHistory.action.contains(search) | WorkHistory.new_value.contains(search)
        )
    if action:
        query = query.filter(WorkHistory.action == action)
    if actor_id is not None:
        query = query.filter(WorkHistory.actor_id == actor_id)
    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
            query = query.filter(WorkHistory.created_at >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to)
            query = query.filter(WorkHistory.created_at <= dt_to)
        except ValueError:
            pass

    results = query.offset(page * PAGE_SIZE).limit(PAGE_SIZE).all()
    return [history_to_dict(h) for h in results]


@router.get("/actions")
def list_actions(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return distinct action types for filter dropdown."""
    rows = db.query(WorkHistory.action).distinct().order_by(WorkHistory.action).all()
    return [r[0] for r in rows if r[0]]
