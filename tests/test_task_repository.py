"""
Tests for TaskRepository — data access layer.
Covers: soft-delete, restore, get_overdue, dependency chain,
        subtask CRUD, edge cases (empty title validation in service).
"""

import pytest
from datetime import datetime, timedelta, timezone

from app.repositories.task_repo import TaskRepository
from app.services.task_service import TaskService
from app.models.task import TaskStatus, TaskPriority
from app.utils.exceptions import ValidationError


# ── Helpers ────────────────────────────────────────────────────────────────

def _repo(db) -> TaskRepository:
    return TaskRepository(db)


def _svc(db) -> TaskService:
    return TaskService(db)


def _task(db, title="งานทดสอบ", **kwargs):
    return _repo(db).create(title=title, **kwargs)


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ══════════════════════════════════════════════════════════════════════════════
#  SOFT DELETE & RESTORE
# ══════════════════════════════════════════════════════════════════════════════

def test_delete_soft_deletes(db):
    task = _task(db)
    result = _repo(db).delete(task.id)
    assert result is True
    # get_by_id excludes soft-deleted
    assert _repo(db).get_by_id(task.id) is None


def test_delete_nonexistent_returns_false(db):
    assert _repo(db).delete(9999) is False


def test_soft_deleted_excluded_from_get_all(db):
    t1 = _task(db, title="งาน 1")
    t2 = _task(db, title="งาน 2")
    _repo(db).delete(t1.id)
    tasks = _repo(db).get_all()
    ids = [t.id for t in tasks]
    assert t1.id not in ids
    assert t2.id in ids


def test_restore_task_makes_visible_again(db):
    task = _task(db, title="ลบแล้วคืน")
    _svc(db).delete_task(task.id)
    # confirm deleted
    assert _repo(db).get_by_id(task.id) is None
    # restore
    restored = _svc(db).restore_task(task.id)
    assert restored.is_deleted is False
    assert _repo(db).get_by_id(task.id) is not None


def test_delete_permanent_removes_from_db(db):
    task = _task(db)
    _repo(db).delete_permanent(task.id)
    # Even querying with raw filter should return nothing
    from app.models.task import Task as TaskModel
    row = db.query(TaskModel).filter(TaskModel.id == task.id).first()
    assert row is None


# ══════════════════════════════════════════════════════════════════════════════
#  OVERDUE
# ══════════════════════════════════════════════════════════════════════════════

def test_get_overdue_empty(db):
    assert _repo(db).get_overdue() == []


def test_get_overdue_returns_past_due_pending(db):
    past = _now() - timedelta(days=3)
    task = _task(db, title="เกินกำหนด", due_date=past)
    overdue = _repo(db).get_overdue()
    assert any(t.id == task.id for t in overdue)


def test_get_overdue_excludes_done(db):
    past = _now() - timedelta(days=2)
    task = _task(db, title="เกินแต่เสร็จ", due_date=past)
    _repo(db).change_status(task.id, TaskStatus.DONE)
    overdue = _repo(db).get_overdue()
    assert not any(t.id == task.id for t in overdue)


def test_get_overdue_excludes_cancelled(db):
    past = _now() - timedelta(days=2)
    task = _task(db, title="ยกเลิก", due_date=past)
    _repo(db).change_status(task.id, TaskStatus.CANCELLED)
    overdue = _repo(db).get_overdue()
    assert not any(t.id == task.id for t in overdue)


def test_get_overdue_excludes_future_due(db):
    future = _now() + timedelta(days=5)
    _task(db, title="ยังไม่ถึง", due_date=future)
    assert _repo(db).get_overdue() == []


# ══════════════════════════════════════════════════════════════════════════════
#  DEPENDENCY CHAIN
# ══════════════════════════════════════════════════════════════════════════════

def test_dependency_chain_empty_for_no_dep(db):
    task = _task(db)
    chain = _repo(db).get_dependency_chain(task.id)
    assert chain == []


def test_dependency_chain_single_level(db):
    a = _task(db, title="A")
    b = _task(db, title="B", depends_on_id=a.id)
    chain = _repo(db).get_dependency_chain(b.id)
    assert a.id in chain


def test_dependency_chain_multi_level(db):
    a = _task(db, title="A")
    b = _task(db, title="B", depends_on_id=a.id)
    c = _task(db, title="C", depends_on_id=b.id)
    chain = _repo(db).get_dependency_chain(c.id)
    assert b.id in chain
    assert a.id in chain


def test_get_dependent_tasks_reverse_lookup(db):
    a = _task(db, title="A")
    b = _task(db, title="B", depends_on_id=a.id)
    c = _task(db, title="C", depends_on_id=a.id)
    dependents = _repo(db).get_dependent_tasks(a.id)
    dep_ids = [t.id for t in dependents]
    assert b.id in dep_ids
    assert c.id in dep_ids


def test_get_dependent_tasks_empty(db):
    a = _task(db, title="A")
    assert _repo(db).get_dependent_tasks(a.id) == []


# ══════════════════════════════════════════════════════════════════════════════
#  SUBTASK CRUD
# ══════════════════════════════════════════════════════════════════════════════

def test_add_subtask(db):
    task = _task(db)
    subtask = _repo(db).add_subtask(task.id, "sub 1")
    assert subtask.id is not None
    assert subtask.title == "sub 1"
    assert subtask.is_done is False


def test_toggle_subtask(db):
    task = _task(db)
    sub = _repo(db).add_subtask(task.id, "sub")
    toggled = _repo(db).toggle_subtask(sub.id)
    assert toggled.is_done is True
    toggled_back = _repo(db).toggle_subtask(sub.id)
    assert toggled_back.is_done is False


def test_toggle_nonexistent_subtask_returns_none(db):
    assert _repo(db).toggle_subtask(9999) is None


def test_delete_subtask_soft_deletes(db):
    task = _task(db)
    sub = _repo(db).add_subtask(task.id, "sub")
    result = _repo(db).delete_subtask(sub.id)
    assert result is True
    # Sub should now be invisible (is_deleted = True)
    from app.models.task import SubTask
    row = db.query(SubTask).filter(SubTask.id == sub.id).first()
    assert row.is_deleted is True


# ══════════════════════════════════════════════════════════════════════════════
#  EDGE CASES — validation in service layer
# ══════════════════════════════════════════════════════════════════════════════

def test_create_task_empty_title_raises(db):
    with pytest.raises(ValidationError):
        _svc(db).create_task(title="")


def test_create_task_whitespace_title_raises(db):
    with pytest.raises(ValidationError):
        _svc(db).create_task(title="   ")


def test_create_task_start_after_due_raises(db):
    start = _now() + timedelta(days=5)
    due   = _now() + timedelta(days=1)   # before start
    with pytest.raises(ValidationError):
        _svc(db).create_task(title="งาน", start_date=start, due_date=due)


def test_update_task_empty_title_raises(db):
    task = _svc(db).create_task(title="งาน")
    with pytest.raises(ValidationError):
        _svc(db).update_task(task.id, title="")


def test_update_task_start_after_due_raises(db):
    task = _svc(db).create_task(title="งาน")
    start = _now() + timedelta(days=10)
    due   = _now() + timedelta(days=2)
    with pytest.raises(ValidationError):
        _svc(db).update_task(task.id, start_date=start, due_date=due)


def test_create_task_valid_dates_accepted(db):
    start = _now()
    due   = _now() + timedelta(days=7)
    task = _svc(db).create_task(title="งาน OK", start_date=start, due_date=due)
    assert task.id is not None


def test_create_task_same_start_and_due_accepted(db):
    d = _now() + timedelta(days=1)
    task = _svc(db).create_task(title="งาน Same", start_date=d, due_date=d)
    assert task.id is not None
