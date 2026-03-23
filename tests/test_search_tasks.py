# -*- coding: utf-8 -*-
"""
Tests for TaskService.search_tasks (app/services/task_service.py).
"""
import pytest
from app.services.task_service import TaskService
from app.models.task import TaskStatus


def _svc(db) -> TaskService:
    return TaskService(db)


def _create(svc, title="Task", description="", tags="", status=TaskStatus.PENDING):
    task = svc.create_task(title=title, description=description, tags=tags)
    if status != TaskStatus.PENDING:
        svc.change_status(task.id, status)
    return task


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_search_by_title(db):
    svc = _svc(db)
    _create(svc, title="Fix hydraulic pump issue")
    _create(svc, title="Weekly report")

    results = svc.search_tasks("hydraulic")
    assert len(results) == 1
    assert results[0].title == "Fix hydraulic pump issue"


def test_search_by_description(db):
    svc = _svc(db)
    _create(svc, title="Task A", description="CNC machine maintenance")
    _create(svc, title="Task B", description="Routine check")

    results = svc.search_tasks("CNC")
    assert len(results) == 1
    assert results[0].title == "Task A"


def test_search_by_tags(db):
    svc = _svc(db)
    _create(svc, title="Weld job", tags="welding,urgent")
    _create(svc, title="Other task", tags="routine")

    results = svc.search_tasks("welding")
    assert len(results) == 1
    assert results[0].title == "Weld job"


def test_search_empty_query_returns_empty(db):
    svc = _svc(db)
    _create(svc, title="Some task")

    assert svc.search_tasks("") == []
    assert svc.search_tasks("   ") == []


def test_search_excludes_cancelled(db):
    svc = _svc(db)
    _create(svc, title="Cancelled pump task", status=TaskStatus.CANCELLED)

    results = svc.search_tasks("pump")
    assert results == []


def test_search_excludes_deleted(db):
    svc = _svc(db)
    task = _create(svc, title="Deleted pump task")
    svc.delete_task(task.id)

    results = svc.search_tasks("pump")
    assert results == []


def test_search_respects_limit(db):
    svc = _svc(db)
    for i in range(25):
        _create(svc, title=f"Pump task {i}")

    results = svc.search_tasks("Pump", limit=10)
    assert len(results) == 10


def test_search_case_insensitive(db):
    svc = _svc(db)
    _create(svc, title="PLC Controller Check")

    assert len(svc.search_tasks("plc")) == 1
    assert len(svc.search_tasks("PLC")) == 1
    assert len(svc.search_tasks("Plc")) == 1
