"""
Tests for TimeTrackingService — timer control + manual log + summary queries.
Covers: start/stop timer, concurrent timer guard, manual log, delete log,
        get_total_minutes, get_summary_by_member, get_summary_by_task.
"""

import time
import pytest
from app.services.time_tracking_service import TimeTrackingService
from app.services.task_service import TaskService
from app.services.team_service import TeamService
from app.models.user import UserRole


# ── Helpers ────────────────────────────────────────────────────────────────

def _svc(db) -> TimeTrackingService:
    return TimeTrackingService(db)


def _task(db, title="งานทดสอบ"):
    return TaskService(db).create_task(title=title)


def _member(db, name="ช่าง"):
    team = TeamService(db).create_team(name=f"ทีม-{name}")
    return TeamService(db).add_member(team.id, name=name, role=UserRole.TECHNICIAN)


# ══════════════════════════════════════════════════════════════════════════════
#  TIMER CONTROL
# ══════════════════════════════════════════════════════════════════════════════

def test_start_timer_creates_running_log(db):
    task = _task(db)
    log = _svc(db).start_timer(task.id)
    assert log.id is not None
    assert log.task_id == task.id
    assert log.is_running is True
    assert log.ended_at is None


def test_is_running_true_after_start(db):
    task = _task(db)
    _svc(db).start_timer(task.id)
    assert _svc(db).is_running(task.id) is True


def test_is_running_false_before_start(db):
    task = _task(db)
    assert _svc(db).is_running(task.id) is False


def test_stop_timer_sets_ended_at(db):
    task = _task(db)
    svc = _svc(db)
    svc.start_timer(task.id)
    stopped = svc.stop_timer(task.id)
    assert stopped is not None
    assert stopped.ended_at is not None
    assert stopped.is_running is False


def test_stop_timer_computes_duration(db):
    task = _task(db)
    svc = _svc(db)
    svc.start_timer(task.id)
    # duration_minutes is max(1, actual_seconds // 60) so it's at least 1
    stopped = svc.stop_timer(task.id)
    assert stopped.duration_minutes >= 1


def test_stop_timer_no_running_returns_none(db):
    task = _task(db)
    result = _svc(db).stop_timer(task.id)
    assert result is None


def test_is_running_false_after_stop(db):
    task = _task(db)
    svc = _svc(db)
    svc.start_timer(task.id)
    svc.stop_timer(task.id)
    assert svc.is_running(task.id) is False


def test_start_timer_stops_existing_running(db):
    """Starting a new timer should stop any already-running timer for the same task."""
    task = _task(db)
    svc = _svc(db)
    first = svc.start_timer(task.id)
    second = svc.start_timer(task.id)   # should auto-stop first

    # first timer should now be stopped
    db.refresh(first)
    assert first.is_running is False
    # second timer is running
    assert svc.is_running(task.id) is True
    assert second.is_running is True


def test_get_running_log(db):
    task = _task(db)
    svc = _svc(db)
    started = svc.start_timer(task.id)
    running = svc.get_running_log(task.id)
    assert running is not None
    assert running.id == started.id


def test_timers_are_independent_per_task(db):
    t1 = _task(db, title="งาน 1")
    t2 = _task(db, title="งาน 2")
    svc = _svc(db)
    svc.start_timer(t1.id)
    svc.start_timer(t2.id)
    assert svc.is_running(t1.id) is True
    assert svc.is_running(t2.id) is True
    svc.stop_timer(t1.id)
    assert svc.is_running(t1.id) is False
    assert svc.is_running(t2.id) is True


# ══════════════════════════════════════════════════════════════════════════════
#  MANUAL LOG
# ══════════════════════════════════════════════════════════════════════════════

def test_add_manual_log_basic(db):
    task = _task(db)
    log = _svc(db).add_manual_log(task.id, duration_minutes=30, note="ทำงาน")
    assert log.id is not None
    assert log.duration_minutes == 30
    assert log.note == "ทำงาน"
    assert log.is_running is False


def test_add_manual_log_minimum_one_minute(db):
    task = _task(db)
    log = _svc(db).add_manual_log(task.id, duration_minutes=0)
    assert log.duration_minutes == 1   # max(1, 0)


def test_add_manual_log_with_user(db):
    task = _task(db)
    member = _member(db, name="ช่าง1")
    log = _svc(db).add_manual_log(task.id, duration_minutes=60, user_id=member.id)
    assert log.user_id == member.id


def test_delete_log_removes_entry(db):
    task = _task(db)
    svc = _svc(db)
    log = svc.add_manual_log(task.id, duration_minutes=15)
    svc.delete_log(log.id)
    assert svc.get_logs_by_task(task.id) == []


def test_delete_nonexistent_log_no_error(db):
    # Should not raise
    _svc(db).delete_log(9999)


# ══════════════════════════════════════════════════════════════════════════════
#  QUERY
# ══════════════════════════════════════════════════════════════════════════════

def test_get_logs_by_task_empty(db):
    task = _task(db)
    assert _svc(db).get_logs_by_task(task.id) == []


def test_get_logs_by_task_excludes_running(db):
    task = _task(db)
    svc = _svc(db)
    svc.start_timer(task.id)   # running — should NOT appear
    svc.add_manual_log(task.id, duration_minutes=10)   # stopped — should appear
    logs = svc.get_logs_by_task(task.id)
    assert len(logs) == 1
    assert logs[0].duration_minutes == 10


def test_get_total_minutes_zero_when_no_logs(db):
    task = _task(db)
    assert _svc(db).get_total_minutes(task.id) == 0


def test_get_total_minutes_sums_logs(db):
    task = _task(db)
    svc = _svc(db)
    svc.add_manual_log(task.id, duration_minutes=20)
    svc.add_manual_log(task.id, duration_minutes=40)
    assert svc.get_total_minutes(task.id) == 60


def test_get_total_minutes_excludes_running_log(db):
    task = _task(db)
    svc = _svc(db)
    svc.add_manual_log(task.id, duration_minutes=30)
    svc.start_timer(task.id)   # running — not counted
    assert svc.get_total_minutes(task.id) == 30


# ══════════════════════════════════════════════════════════════════════════════
#  SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

def test_summary_by_member_empty(db):
    assert _svc(db).get_summary_by_member() == []


def test_summary_by_member_aggregates(db):
    task = _task(db)
    member = _member(db, name="ช่าง")
    svc = _svc(db)
    svc.add_manual_log(task.id, duration_minutes=30, user_id=member.id)
    svc.add_manual_log(task.id, duration_minutes=45, user_id=member.id)

    summary = svc.get_summary_by_member()
    assert len(summary) == 1
    row = summary[0]
    assert row["total_minutes"] == 75
    assert row["task_count"] == 1
    assert row["name"] == "ช่าง"


def test_summary_by_member_multiple_members(db):
    t1 = _task(db, title="งาน 1")
    t2 = _task(db, title="งาน 2")
    m1 = _member(db, name="ช่าง A")
    m2 = _member(db, name="ช่าง B")
    svc = _svc(db)
    svc.add_manual_log(t1.id, duration_minutes=60, user_id=m1.id)
    svc.add_manual_log(t2.id, duration_minutes=30, user_id=m2.id)

    summary = svc.get_summary_by_member()
    names = [r["name"] for r in summary]
    assert "ช่าง A" in names
    assert "ช่าง B" in names
    # sorted by total_minutes desc
    assert summary[0]["total_minutes"] >= summary[1]["total_minutes"]


def test_summary_by_task_empty(db):
    assert _svc(db).get_summary_by_task() == []


def test_summary_by_task_aggregates(db):
    task = _task(db, title="งานใหญ่")
    svc = _svc(db)
    svc.add_manual_log(task.id, duration_minutes=20)
    svc.add_manual_log(task.id, duration_minutes=40)

    summary = svc.get_summary_by_task()
    assert len(summary) == 1
    assert summary[0]["total_minutes"] == 60
    assert "งานใหญ่" in summary[0]["title"]
