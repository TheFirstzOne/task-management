"""
Tests for Phase 16 additions to TaskService and TaskRepository.
Covers: get_task_or_none, get_deleted_tasks, get_comments, restore_task,
        get_near_due_tasks, get_near_due_count, and the new Repository methods.
"""

import pytest
from datetime import datetime, timezone, timedelta

from app.services.task_service import TaskService
from app.repositories.task_repo import TaskRepository
from app.models.task import TaskStatus, TaskPriority, TaskComment
from app.models.history import WorkHistory
from app.utils.exceptions import NotFoundError


# ── Helpers ─────────────────────────────────────────────────────────────────

def _svc(db) -> TaskService:
    return TaskService(db)


def _repo(db) -> TaskRepository:
    return TaskRepository(db)


def _task(db, title="งานทดสอบ", **kwargs):
    return _svc(db).create_task(title=title, **kwargs)


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ═══════════════════════════════════════════════════════════════════
#  TaskService.get_task_or_none
# ═══════════════════════════════════════════════════════════════════

def test_get_task_or_none_returns_task_when_exists(db):
    t = _task(db, title="มีอยู่")
    result = _svc(db).get_task_or_none(t.id)
    assert result is not None
    assert result.title == "มีอยู่"


def test_get_task_or_none_returns_none_when_not_found(db):
    result = _svc(db).get_task_or_none(9999)
    assert result is None


def test_get_task_or_none_returns_none_for_deleted_task(db):
    t = _task(db, title="ลบแล้ว")
    _svc(db).delete_task(t.id)
    result = _svc(db).get_task_or_none(t.id)
    assert result is None


# ═══════════════════════════════════════════════════════════════════
#  TaskService.get_deleted_tasks
# ═══════════════════════════════════════════════════════════════════

def test_get_deleted_tasks_empty_when_none_deleted(db):
    _task(db, title="งานปกติ")
    result = _svc(db).get_deleted_tasks()
    assert result == []


def test_get_deleted_tasks_returns_only_deleted(db):
    t1 = _task(db, title="งานปกติ")
    t2 = _task(db, title="งานลบแล้ว")
    _svc(db).delete_task(t2.id)
    result = _svc(db).get_deleted_tasks()
    ids = [t.id for t in result]
    assert t2.id in ids
    assert t1.id not in ids


def test_get_deleted_tasks_multiple(db):
    t1 = _task(db, title="A")
    t2 = _task(db, title="B")
    t3 = _task(db, title="C")
    _svc(db).delete_task(t1.id)
    _svc(db).delete_task(t3.id)
    result = _svc(db).get_deleted_tasks()
    assert len(result) == 2


# ═══════════════════════════════════════════════════════════════════
#  TaskService.get_comments
# ═══════════════════════════════════════════════════════════════════

def test_get_comments_empty_initially(db):
    t = _task(db, title="ไม่มี comment")
    result = _svc(db).get_comments(t.id)
    assert result == []


def test_get_comments_returns_added_comments(db):
    t = _task(db, title="งานที่มี comment")
    _svc(db).add_comment(t.id, "comment แรก")
    _svc(db).add_comment(t.id, "comment สอง")
    result = _svc(db).get_comments(t.id)
    assert len(result) == 2


def test_get_comments_ordered_by_created_at(db):
    t = _task(db, title="ลำดับ comment")
    _svc(db).add_comment(t.id, "ก่อน")
    _svc(db).add_comment(t.id, "หลัง")
    result = _svc(db).get_comments(t.id)
    assert result[0].body == "ก่อน"
    assert result[1].body == "หลัง"


# ═══════════════════════════════════════════════════════════════════
#  TaskService.restore_task
# ═══════════════════════════════════════════════════════════════════

def test_restore_task_makes_it_active_again(db):
    t = _task(db, title="กู้คืน")
    _svc(db).delete_task(t.id)
    assert _svc(db).get_task_or_none(t.id) is None
    _svc(db).restore_task(t.id)
    restored = _svc(db).get_task(t.id)
    assert restored.is_deleted is False


def test_restore_task_not_found_raises(db):
    with pytest.raises(NotFoundError):
        _svc(db).restore_task(9999)


def test_restore_task_logs_history(db):
    t = _task(db, title="บันทึกประวัติ")
    _svc(db).delete_task(t.id)
    _svc(db).restore_task(t.id)
    logs = db.query(WorkHistory).filter(WorkHistory.task_id == t.id).all()
    actions = [l.action for l in logs]
    assert "restored" in actions


# ═══════════════════════════════════════════════════════════════════
#  TaskService.get_near_due_tasks
# ═══════════════════════════════════════════════════════════════════

def test_get_near_due_tasks_empty_when_no_tasks(db):
    result = _svc(db).get_near_due_tasks(days_ahead=3)
    assert result == []


def test_get_near_due_tasks_returns_tasks_within_window(db):
    soon = _now() + timedelta(days=2)
    t = _task(db, title="ใกล้ครบกำหนด", due_date=soon)
    result = _svc(db).get_near_due_tasks(days_ahead=3)
    ids = [r.id for r in result]
    assert t.id in ids


def test_get_near_due_tasks_excludes_overdue(db):
    past = _now() - timedelta(days=1)
    t = _task(db, title="เกินกำหนดแล้ว", due_date=past)
    result = _svc(db).get_near_due_tasks(days_ahead=3)
    ids = [r.id for r in result]
    assert t.id not in ids


def test_get_near_due_tasks_excludes_done_tasks(db):
    soon = _now() + timedelta(days=1)
    t = _task(db, title="เสร็จแล้ว", due_date=soon)
    _svc(db).change_status(t.id, TaskStatus.DONE)
    result = _svc(db).get_near_due_tasks(days_ahead=3)
    ids = [r.id for r in result]
    assert t.id not in ids


def test_get_near_due_tasks_excludes_cancelled_tasks(db):
    soon = _now() + timedelta(days=1)
    t = _task(db, title="ยกเลิก", due_date=soon)
    _svc(db).change_status(t.id, TaskStatus.CANCELLED)
    result = _svc(db).get_near_due_tasks(days_ahead=3)
    ids = [r.id for r in result]
    assert t.id not in ids


def test_get_near_due_tasks_excludes_deleted_tasks(db):
    soon = _now() + timedelta(days=1)
    t = _task(db, title="ลบแล้ว", due_date=soon)
    _svc(db).delete_task(t.id)
    result = _svc(db).get_near_due_tasks(days_ahead=3)
    ids = [r.id for r in result]
    assert t.id not in ids


def test_get_near_due_tasks_excludes_tasks_beyond_window(db):
    far = _now() + timedelta(days=10)
    _task(db, title="ยังไกลมาก", due_date=far)
    result = _svc(db).get_near_due_tasks(days_ahead=3)
    assert result == []


# ═══════════════════════════════════════════════════════════════════
#  TaskService.get_near_due_count
# ═══════════════════════════════════════════════════════════════════

def test_get_near_due_count_zero_when_empty(db):
    assert _svc(db).get_near_due_count() == 0


def test_get_near_due_count_returns_correct_count(db):
    soon = _now() + timedelta(days=1)
    _task(db, title="A", due_date=soon)
    _task(db, title="B", due_date=soon)
    assert _svc(db).get_near_due_count(days_ahead=3) == 2


def test_get_near_due_count_excludes_done(db):
    soon = _now() + timedelta(days=1)
    t = _task(db, title="เสร็จแล้ว", due_date=soon)
    _svc(db).change_status(t.id, TaskStatus.DONE)
    assert _svc(db).get_near_due_count(days_ahead=3) == 0


# ═══════════════════════════════════════════════════════════════════
#  TaskRepository.get_deleted
# ═══════════════════════════════════════════════════════════════════

def test_repo_get_deleted_returns_only_deleted(db):
    repo = _repo(db)
    t1 = repo.create(title="ปกติ")
    t2 = repo.create(title="ลบแล้ว")
    repo.delete(t2.id)
    deleted = repo.get_deleted()
    ids = [t.id for t in deleted]
    assert t2.id in ids
    assert t1.id not in ids


def test_repo_get_deleted_empty_when_none(db):
    repo = _repo(db)
    repo.create(title="ปกติ")
    assert repo.get_deleted() == []


# ═══════════════════════════════════════════════════════════════════
#  TaskRepository.get_any_by_id
# ═══════════════════════════════════════════════════════════════════

def test_repo_get_any_by_id_returns_active_task(db):
    repo = _repo(db)
    t = repo.create(title="ปกติ")
    assert repo.get_any_by_id(t.id) is not None


def test_repo_get_any_by_id_returns_deleted_task(db):
    repo = _repo(db)
    t = repo.create(title="ลบแล้ว")
    repo.delete(t.id)
    # get_by_id would return None, but get_any_by_id should find it
    assert repo.get_by_id(t.id) is None
    assert repo.get_any_by_id(t.id) is not None


def test_repo_get_any_by_id_returns_none_for_unknown(db):
    repo = _repo(db)
    assert repo.get_any_by_id(9999) is None


# ═══════════════════════════════════════════════════════════════════
#  TaskRepository.restore
# ═══════════════════════════════════════════════════════════════════

def test_repo_restore_makes_task_active(db):
    repo = _repo(db)
    t = repo.create(title="กู้คืน")
    repo.delete(t.id)
    assert repo.get_by_id(t.id) is None
    restored = repo.restore(t.id)
    assert restored is not None
    assert restored.is_deleted is False
    assert repo.get_by_id(t.id) is not None


def test_repo_restore_returns_none_for_unknown(db):
    repo = _repo(db)
    assert repo.restore(9999) is None


# ═══════════════════════════════════════════════════════════════════
#  TaskRepository.unassign_user
# ═══════════════════════════════════════════════════════════════════

def test_repo_unassign_user_returns_count(db):
    from app.repositories.user_repo import UserRepository
    from app.models.user import UserRole
    user = UserRepository(db).create(name="ผู้ใช้", role=UserRole.TECHNICIAN)
    repo = _repo(db)
    t1 = repo.create(title="งาน 1", assignee_id=user.id)
    t2 = repo.create(title="งาน 2", assignee_id=user.id)
    count = repo.unassign_user(user.id)
    assert count == 2


def test_repo_unassign_user_clears_assignee(db):
    from app.repositories.user_repo import UserRepository
    from app.models.user import UserRole
    user = UserRepository(db).create(name="ผู้ใช้", role=UserRole.TECHNICIAN)
    repo = _repo(db)
    t = repo.create(title="งาน", assignee_id=user.id)
    repo.unassign_user(user.id)
    updated = repo.get_by_id(t.id)
    assert updated.assignee_id is None


def test_repo_unassign_user_does_not_unassign_done_tasks(db):
    from app.repositories.user_repo import UserRepository
    from app.models.user import UserRole
    user = UserRepository(db).create(name="ผู้ใช้", role=UserRole.TECHNICIAN)
    repo = _repo(db)
    t = repo.create(title="งานเสร็จ", assignee_id=user.id)
    repo.change_status(t.id, TaskStatus.DONE)
    count = repo.unassign_user(user.id)
    assert count == 0
    done_task = repo.get_by_id(t.id)
    assert done_task.assignee_id == user.id


def test_repo_unassign_user_returns_zero_when_no_tasks(db):
    repo = _repo(db)
    count = repo.unassign_user(9999)
    assert count == 0


# ═══════════════════════════════════════════════════════════════════
#  TaskRepository.count_active_by_assignee
# ═══════════════════════════════════════════════════════════════════

def test_repo_count_active_by_assignee_zero_when_none(db):
    repo = _repo(db)
    assert repo.count_active_by_assignee(9999) == 0


def test_repo_count_active_by_assignee_counts_only_active(db):
    from app.repositories.user_repo import UserRepository
    from app.models.user import UserRole
    user = UserRepository(db).create(name="ผู้ใช้", role=UserRole.TECHNICIAN)
    repo = _repo(db)
    repo.create(title="งานรอ", assignee_id=user.id)
    repo.create(title="งานทำอยู่", assignee_id=user.id)
    t_done = repo.create(title="งานเสร็จ", assignee_id=user.id)
    repo.change_status(t_done.id, TaskStatus.DONE)
    assert repo.count_active_by_assignee(user.id) == 2


def test_repo_count_active_by_assignee_excludes_cancelled(db):
    from app.repositories.user_repo import UserRepository
    from app.models.user import UserRole
    user = UserRepository(db).create(name="ผู้ใช้", role=UserRole.TECHNICIAN)
    repo = _repo(db)
    t = repo.create(title="ยกเลิก", assignee_id=user.id)
    repo.change_status(t.id, TaskStatus.CANCELLED)
    assert repo.count_active_by_assignee(user.id) == 0
