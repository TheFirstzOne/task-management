# -*- coding: utf-8 -*-
"""Diary router — Phase 21"""

import os
import tempfile

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.diary_service import DiaryService
from app.utils.exceptions import TaskFlowError
from server.deps import get_current_user, get_db
from server.serializers import diary_to_dict

router = APIRouter()


class CreateDiaryIn(BaseModel):
    content: str


def _handle_exc(exc: Exception):
    if isinstance(exc, TaskFlowError):
        raise HTTPException(status_code=400, detail=str(exc))
    raise exc


@router.post("")
def create_diary_entry(
    body: CreateDiaryIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Create a new diary entry."""
    svc = DiaryService(db)
    try:
        entry = svc.create_entry(body.content)
        return diary_to_dict(entry)
    except Exception as exc:
        _handle_exc(exc)


@router.get("/grouped")
def get_diary_grouped(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return diary entries grouped by date string."""
    svc = DiaryService(db)
    grouped = svc.get_entries_grouped()
    # Convert DiaryEntry objects to dicts in each group
    return {date_str: [diary_to_dict(e) for e in entries]
            for date_str, entries in grouped.items()}


@router.get("/export/word")
def export_word(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Export diary entries as a Word document."""
    svc = DiaryService(db)
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        path = f.name
    try:
        svc.export_to_word(path)
    except Exception as exc:
        if os.path.exists(path):
            os.unlink(path)
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="job_diary.docx",
    )


@router.get("/export/pdf")
def export_pdf(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Export diary entries as a PDF document."""
    svc = DiaryService(db)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        path = f.name
    try:
        svc.export_to_pdf(path)
    except Exception as exc:
        if os.path.exists(path):
            os.unlink(path)
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename="job_diary.pdf",
    )
