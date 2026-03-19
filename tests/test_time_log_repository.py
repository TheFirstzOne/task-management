# -*- coding: utf-8 -*-
"""
Tests for TimeLogRepository (app/repositories/time_log_repo.py).
"""
from datetime import datetime, timezone, timedelta

import pytest

from app.repositories.time_log_repo import TimeLogRepository


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _make_task(db, title="Test Task"):
    from app.models.task import Task, TaskPriority, TaskStatus
    t = Task(title=title, priority=TaskPriority.MEDIUM, status=TaskStatus.PENDING)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def _make_log(repo, task_id, started_at=None, is_running=True, ended_at=None,
              duration_minutes=None, note=""):
    return repo.create(
        task_id=task_id,
        started_at=started_at or _now(),
        is_running=is_running,
        ended_at=ended_at,
        duration_minutes=duration_minutes,
        note=note,
    )


# ── create() ──────────────────────────────────────────────────────────────────

def test_create_persists_timelog(db):
    task = _make_task(db)
    repo = TimeLogRepository(db)
    started = _now()
    log = _make_log(repo, task.id, started_at=started)

    assert log.id is not None
    assert log.task_id == task.id
    assert log.is_running is True
    assert log.started_at == started


def test_create_stores_note_and_user_id(db):
    task = _make_task(db)
    repo = TimeLogRepository(db)
    log = repo.create(
        task_id=task.id,
        started_at=_now(),
        is_running=True,
        note="working hard",
        user_id=None,
    )
    assert log.note == "working hard"
    assert log.user_id is None


# ── get_running() ─────────────────────────────────────────────────────────────

def test_get_running_returns_running_log(db):
    task = _make_task(db)
    repo = TimeLogRepository(db)
    log = _make_log(repo, task.id, is_running=True)

    result = repo.get_running(task.id)
    assert result is not None
    assert result.id == log.id


def test_get_running_returns_none_when_no_running_log(db):
    task = _make_task(db)
    repo = TimeLogRepository(db)

    result = repo.get_running(task.id)
    assert result is None


def test_get_running_returns_none_after_log_is_stopped(db):
    task = _make_task(db)
    repo = TimeLogRepository(db)
    log = _make_log(repo, task.id, is_running=True)

    repo.stop(log, ended_at=_now(), duration_minutes=30)
    result = repo.get_running(task.id)
    assert result is None


# ── get_by_task() ─────────────────────────────────────────────────────────────

def test_get_by_task_returns_completed_logs(db):
    task = _make_task(db)
    repo = TimeLogRepository(db)
    started = _now() - timedelta(hours=1)
    log = _make_log(repo, task.id, started_at=started, is_running=False,
                    ended_at=_now(), duration_minutes=60)

    results = repo.get_by_task(task.id)
    assert len(results) == 1
    assert results[0].id == log.id


def test_get_by_task_excludes_running_logs(db):
    task = _make_task(db)
    repo = TimeLogRepository(db)
    # One completed, one running
    _make_log(repo, task.id, is_running=False, ended_at=_now(), duration_minutes=10)
    _make_log(repo, task.id, is_running=True)

    results = repo.get_by_task(task.id)
    assert len(results) == 1
    assert results[0].is_running is False


def test_get_by_task_ordered_by_started_at_desc(db):
    task = _make_task(db)
    repo = TimeLogRepository(db)
    base = _now() - timedelta(hours=3)
    _make_log(repo, task.id, started_at=base,                   is_running=False, duration_minutes=10)
    _make_log(repo, task.id, started_at=base + timedelta(hours=1), is_running=False, duration_minutes=20)
    _make_log(repo, task.id, started_at=base + timedelta(hours=2), is_running=False, duration_minutes=30)

    results = repo.get_by_task(task.id)
    assert len(results) == 3
    assert results[0].started_at > results[1].started_at
    assert results[1].started_at > results[2].started_at


# ── get_all_completed() ───────────────────────────────────────────────────────

def test_get_all_completed_returns_only_non_running(db):
    task = _make_task(db)
    repo = TimeLogRepository(db)
    _make_log(repo, task.id, is_running=False, duration_minutes=15)
    _make_log(repo, task.id, is_running=True)

    results = repo.get_all_completed()
    assert len(results) == 1
    assert results[0].is_running is False


def test_get_all_completed_empty_when_all_running(db):
    task = _make_task(db)
    repo = TimeLogRepository(db)
    _make_log(repo, task.id, is_running=True)

    results = repo.get_all_completed()
    assert results == []


# ── get_all_completed_with_task() ────────────────────────────────────────────

def test_get_all_completed_with_task_loads_task_relationship(db):
    task = _make_task(db, title="My Task")
    repo = TimeLogRepository(db)
    _make_log(repo, task.id, is_running=False, duration_minutes=5)

    results = repo.get_all_completed_with_task()
    assert len(results) == 1
    # Relationship should be accessible without triggering lazy-load error
    assert results[0].task is not None
    assert results[0].task.title == "My Task"


def test_get_all_completed_with_task_excludes_running(db):
    task = _make_task(db)
    repo = TimeLogRepository(db)
    _make_log(repo, task.id, is_running=True)

    results = repo.get_all_completed_with_task()
    assert results == []


# ── stop() ────────────────────────────────────────────────────────────────────

def test_stop_sets_fields_correctly(db):
    task = _make_task(db)
    repo = TimeLogRepository(db)
    log = _make_log(repo, task.id, is_running=True)

    ended = _now()
    updated = repo.stop(log, ended_at=ended, duration_minutes=45)

    assert updated.is_running is False
    assert updated.ended_at == ended
    assert updated.duration_minutes == 45


def test_stop_persists_to_db(db):
    task = _make_task(db)
    repo = TimeLogRepository(db)
    log = _make_log(repo, task.id, is_running=True)
    ended = _now()
    repo.stop(log, ended_at=ended, duration_minutes=20)

    from app.models.time_log import TimeLog
    refreshed = db.get(TimeLog, log.id)
    assert refreshed.is_running is False
    assert refreshed.duration_minutes == 20


# ── delete() ──────────────────────────────────────────────────────────────────

def test_delete_removes_log_from_db(db):
    task = _make_task(db)
    repo = TimeLogRepository(db)
    log = _make_log(repo, task.id, is_running=False)
    log_id = log.id

    result = repo.delete(log_id)
    assert result is True

    from app.models.time_log import TimeLog
    assert db.get(TimeLog, log_id) is None


def test_delete_nonexistent_returns_false(db):
    repo = TimeLogRepository(db)
    result = repo.delete(99999)
    assert result is False
