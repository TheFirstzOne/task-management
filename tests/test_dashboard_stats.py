# -*- coding: utf-8 -*-
"""
Tests for TaskService.get_dashboard_stats (app/services/task_service.py).
"""
from datetime import datetime, timezone, timedelta

import pytest

from app.services.task_service import TaskService
from app.models.task import TaskPriority, TaskStatus


# ── Helpers ───────────────────────────────────────────────────────────────────

def _svc(db) -> TaskService:
    return TaskService(db)


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _create(svc, title="Task", status=TaskStatus.PENDING, due_date=None):
    task = svc.create_task(title=title, due_date=due_date)
    if status != TaskStatus.PENDING:
        svc.change_status(task.id, status)
        task = svc.get_task(task.id)
    return task


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_dashboard_stats_empty_db(db):
    stats = _svc(db).get_dashboard_stats()
    assert stats["total"] == 0
    assert stats["pending"] == 0
    assert stats["in_progress"] == 0
    assert stats["review"] == 0
    assert stats["done"] == 0
    assert stats["cancelled"] == 0
    assert stats["overdue"] == 0


def test_dashboard_stats_includes_review(db):
    svc = _svc(db)
    _create(svc, title="Review Task", status=TaskStatus.REVIEW)

    stats = svc.get_dashboard_stats()
    assert stats["review"] == 1
    assert stats["total"] == 1


def test_dashboard_stats_total_excludes_deleted(db):
    svc = _svc(db)
    task = _create(svc, title="To Be Deleted")
    svc.delete_task(task.id)

    stats = svc.get_dashboard_stats()
    assert stats["total"] == 0


def test_dashboard_stats_overdue_count(db):
    svc = _svc(db)
    past_due = _now() - timedelta(days=2)
    _create(svc, title="Overdue Task", status=TaskStatus.PENDING, due_date=past_due)

    stats = svc.get_dashboard_stats()
    assert stats["overdue"] == 1


def test_dashboard_stats_overdue_excludes_done_and_cancelled(db):
    svc = _svc(db)
    past_due = _now() - timedelta(days=1)
    _create(svc, title="Done Overdue",      status=TaskStatus.DONE,      due_date=past_due)
    _create(svc, title="Cancelled Overdue", status=TaskStatus.CANCELLED, due_date=past_due)

    stats = svc.get_dashboard_stats()
    assert stats["overdue"] == 0


def test_dashboard_stats_all_statuses(db):
    svc = _svc(db)
    _create(svc, title="Pending Task",     status=TaskStatus.PENDING)
    _create(svc, title="In Progress Task", status=TaskStatus.IN_PROGRESS)
    _create(svc, title="Review Task",      status=TaskStatus.REVIEW)
    _create(svc, title="Done Task",        status=TaskStatus.DONE)
    _create(svc, title="Cancelled Task",   status=TaskStatus.CANCELLED)

    stats = svc.get_dashboard_stats()
    assert stats["total"] == 5
    assert stats["pending"] == 1
    assert stats["in_progress"] == 1
    assert stats["review"] == 1
    assert stats["done"] == 1
    assert stats["cancelled"] == 1


def test_dashboard_stats_total_counts_all_non_deleted(db):
    svc = _svc(db)
    for i in range(4):
        _create(svc, title=f"Task {i}")

    stats = svc.get_dashboard_stats()
    assert stats["total"] == 4


def test_dashboard_stats_overdue_counts_in_progress(db):
    """In-progress tasks past due date should count as overdue."""
    svc = _svc(db)
    past_due = _now() - timedelta(days=3)
    _create(svc, title="Overdue In Progress", status=TaskStatus.IN_PROGRESS, due_date=past_due)

    stats = svc.get_dashboard_stats()
    assert stats["overdue"] == 1
