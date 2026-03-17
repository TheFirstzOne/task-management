"""
Tests for TaskService — business logic layer.
Covers: create, get, update, delete, dependency validation, status change.
"""

import pytest
from app.services.task_service import TaskService
from app.models.task import TaskStatus, TaskPriority
from app.utils.exceptions import NotFoundError, CircularDependencyError, SelfDependencyError


# ── Helpers ────────────────────────────────────────────────────────────────

def _svc(db) -> TaskService:
    return TaskService(db)


def _task(db, title="งานทดสอบ", **kwargs):
    return _svc(db).create_task(title=title, **kwargs)


# ── Create ─────────────────────────────────────────────────────────────────

def test_create_task_basic(db):
    task = _task(db, title="งานแรก")
    assert task.id is not None
    assert task.title == "งานแรก"
    assert task.status == TaskStatus.PENDING
    assert task.priority == TaskPriority.MEDIUM


def test_create_task_with_priority(db):
    task = _task(db, title="งานด่วน", priority=TaskPriority.URGENT)
    assert task.priority == TaskPriority.URGENT


def test_create_multiple_tasks(db):
    svc = _svc(db)
    svc.create_task("งาน A")
    svc.create_task("งาน B")
    svc.create_task("งาน C")
    assert len(svc.get_all_tasks()) == 3


# ── Read ───────────────────────────────────────────────────────────────────

def test_get_task_found(db):
    created = _task(db, title="ค้นหาได้")
    fetched = _svc(db).get_task(created.id)
    assert fetched.title == "ค้นหาได้"


def test_get_task_not_found_raises(db):
    with pytest.raises(NotFoundError):
        _svc(db).get_task(9999)


# ── Update ─────────────────────────────────────────────────────────────────

def test_update_task_title(db):
    task = _task(db, title="เก่า")
    updated = _svc(db).update_task(task.id, title="ใหม่")
    assert updated.title == "ใหม่"


def test_change_status(db):
    task = _task(db)
    updated = _svc(db).change_status(task.id, TaskStatus.IN_PROGRESS)
    assert updated.status == TaskStatus.IN_PROGRESS


# ── Delete ─────────────────────────────────────────────────────────────────

def test_delete_task(db):
    task = _task(db)
    _svc(db).delete_task(task.id)
    with pytest.raises(NotFoundError):
        _svc(db).get_task(task.id)


def test_delete_nonexistent_raises(db):
    with pytest.raises(NotFoundError):
        _svc(db).delete_task(9999)


# ── Dependency Validation ──────────────────────────────────────────────────

def test_self_dependency_raises(db):
    task = _task(db, title="งาน self-ref")
    with pytest.raises(SelfDependencyError):
        _svc(db).update_task(task.id, depends_on_id=task.id)


def test_dependency_not_found_raises(db):
    task = _task(db)
    with pytest.raises(NotFoundError):
        _svc(db).update_task(task.id, depends_on_id=9999)


def test_circular_dependency_raises(db):
    svc = _svc(db)
    a = svc.create_task("A")
    b = svc.create_task("B", depends_on_id=a.id)
    # A → B would be circular (B already depends on A)
    with pytest.raises(CircularDependencyError):
        svc.update_task(a.id, depends_on_id=b.id)


def test_valid_dependency_accepted(db):
    svc = _svc(db)
    a = svc.create_task("A")
    b = svc.create_task("B")
    updated = svc.update_task(b.id, depends_on_id=a.id)
    assert updated.depends_on_id == a.id


# ── Dashboard Stats ────────────────────────────────────────────────────────

def test_dashboard_stats_empty(db):
    stats = _svc(db).get_dashboard_stats()
    assert stats["total"] == 0
    assert stats["done"] == 0
    assert stats["overdue"] == 0


def test_dashboard_stats_counts(db):
    svc = _svc(db)
    svc.create_task("A")
    t = svc.create_task("B")
    svc.change_status(t.id, TaskStatus.DONE)
    stats = svc.get_dashboard_stats()
    assert stats["total"] == 2
    assert stats["done"] == 1
    assert stats["pending"] == 1
