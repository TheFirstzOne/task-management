# -*- coding: utf-8 -*-
"""Dashboard router — Phase 21"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.task_service import TaskService
from server.deps import get_current_user, get_db

router = APIRouter()


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return task count statistics for the dashboard."""
    return TaskService(db).get_dashboard_stats()
