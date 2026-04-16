"""
Tests for MilestoneService — Phase 22
"""

import pytest
from datetime import datetime, timedelta

from app.services.milestone_service import MilestoneService
from app.services.task_service import TaskService
from app.utils.exceptions import ValidationError, NotFoundError


# ── Helpers ───────────────────────────────────────────────────────────────────

def _svc(db) -> MilestoneService:
    return MilestoneService(db)


def _make_task(db, title="งานทดสอบ"):
    svc = TaskService(db)
    return svc.create_task(title=title, created_by_id=None)


# ── Create ────────────────────────────────────────────────────────────────────

def test_create_milestone_basic(db):
    svc = _svc(db)
    m = svc.create_milestone("Release v2.2")
    assert m.id is not None
    assert m.name == "Release v2.2"
    assert m.is_deleted is False


def test_create_milestone_with_due_date(db):
    svc = _svc(db)
    due = datetime(2026, 5, 1)
    m = svc.create_milestone("Demo Day", due_date=due)
    assert m.due_date == due


def test_create_milestone_empty_name_raises(db):
    with pytest.raises(ValidationError):
        _svc(db).create_milestone("")


def test_create_milestone_whitespace_name_raises(db):
    with pytest.raises(ValidationError):
        _svc(db).create_milestone("   ")


def test_create_milestone_name_too_long_raises(db):
    with pytest.raises(ValidationError):
        _svc(db).create_milestone("x" * 101)


# ── Read ──────────────────────────────────────────────────────────────────────

def test_get_all_milestones_empty(db):
    assert _svc(db).get_all_milestones() == []


def test_get_all_milestones_ordered_by_due_date(db):
    svc = _svc(db)
    svc.create_milestone("Later",  due_date=datetime(2026, 6, 1))
    svc.create_milestone("Earlier", due_date=datetime(2026, 4, 1))
    milestones = svc.get_all_milestones()
    assert milestones[0].name == "Earlier"
    assert milestones[1].name == "Later"


def test_get_milestone_not_found_raises(db):
    with pytest.raises(NotFoundError):
        _svc(db).get_milestone(999)


# ── Update ────────────────────────────────────────────────────────────────────

def test_update_milestone_name(db):
    svc = _svc(db)
    m = svc.create_milestone("Old Name")
    updated = svc.update_milestone(m.id, name="New Name")
    assert updated.name == "New Name"


def test_update_milestone_empty_name_raises(db):
    svc = _svc(db)
    m = svc.create_milestone("Valid")
    with pytest.raises(ValidationError):
        svc.update_milestone(m.id, name="")


def test_update_milestone_not_found_raises(db):
    with pytest.raises(NotFoundError):
        _svc(db).update_milestone(999, name="X")


# ── Delete ────────────────────────────────────────────────────────────────────

def test_delete_milestone_soft_delete(db):
    svc = _svc(db)
    m = svc.create_milestone("To Delete")
    svc.delete_milestone(m.id)
    assert svc.get_all_milestones() == []


def test_delete_milestone_unlinks_tasks(db):
    svc = _svc(db)
    m = svc.create_milestone("M1")
    task = _make_task(db)
    svc.assign_task(task.id, m.id)
    assert task.milestone_id == m.id
    svc.delete_milestone(m.id)
    db.refresh(task)
    assert task.milestone_id is None


# ── Task assignment ───────────────────────────────────────────────────────────

def test_assign_task_to_milestone(db):
    svc = _svc(db)
    m = svc.create_milestone("M1")
    task = _make_task(db)
    svc.assign_task(task.id, m.id)
    tasks = svc.get_tasks(m.id)
    assert len(tasks) == 1
    assert tasks[0].id == task.id


def test_remove_task_from_milestone(db):
    svc = _svc(db)
    m = svc.create_milestone("M1")
    task = _make_task(db)
    svc.assign_task(task.id, m.id)
    svc.remove_task(task.id)
    assert svc.get_tasks(m.id) == []


def test_assign_task_invalid_milestone_raises(db):
    task = _make_task(db)
    with pytest.raises(NotFoundError):
        _svc(db).assign_task(task.id, 999)


# ── Progress ──────────────────────────────────────────────────────────────────

def test_get_progress_no_tasks(db):
    svc = _svc(db)
    m = svc.create_milestone("Empty")
    progress = svc.get_progress(m.id)
    assert progress == {"total": 0, "done": 0, "percent": 0.0}


def test_get_progress_partial_done(db):
    svc = _svc(db)
    task_svc = TaskService(db)
    m = svc.create_milestone("M1")
    t1 = _make_task(db, "Task 1")
    t2 = _make_task(db, "Task 2")
    svc.assign_task(t1.id, m.id)
    svc.assign_task(t2.id, m.id)
    task_svc.update_task(t1.id, status="Done", actor_id=None)
    progress = svc.get_progress(m.id)
    assert progress["total"] == 2
    assert progress["done"] == 1
    assert progress["percent"] == 0.5
