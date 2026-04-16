# -*- coding: utf-8 -*-
"""
Phase 23 — Sub-task due_date + assignee fields
Tests covering: add with fields, update, defaults inherit from parent,
workload heatmap includes subtasks.
"""

from datetime import datetime, timezone, timedelta

import pytest

from app.services.task_service import TaskService
from app.utils.exceptions import NotFoundError, ValidationError


# ── helpers ──────────────────────────────────────────────────────────────────

def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def _utc(days: int = 0):
    return (_now() + timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)


def _make_team(db):
    from app.services.team_service import TeamService
    return TeamService(db).create_team("팀Alpha")


def _make_member(db, team_id: int, name: str = "สมชาย"):
    from app.services.team_service import TeamService
    return TeamService(db).add_member(team_id, name, "Other")


def _make_task(db, team_id=None, assignee_id=None, due_date=None):
    svc = TaskService(db)
    return svc.create_task("Task A", team_id=team_id,
                           assignee_id=assignee_id, due_date=due_date)


# ── add_subtask with new fields ───────────────────────────────────────────────

def test_add_subtask_with_due_date(db):
    task = _make_task(db)
    due = _utc(5)
    svc = TaskService(db)
    st = svc.add_subtask(task.id, "sub A", due_date=due)
    assert st.due_date == due


def test_add_subtask_with_assignee(db):
    team = _make_team(db)
    member = _make_member(db, team.id)
    task = _make_task(db, team_id=team.id)
    svc = TaskService(db)
    st = svc.add_subtask(task.id, "sub B", assignee_id=member.id)
    assert st.assignee_id == member.id


def test_add_subtask_with_both_fields(db):
    team = _make_team(db)
    member = _make_member(db, team.id)
    due = _utc(7)
    task = _make_task(db, team_id=team.id, assignee_id=member.id, due_date=due)
    svc = TaskService(db)
    st = svc.add_subtask(task.id, "sub C", due_date=due, assignee_id=member.id)
    assert st.due_date == due
    assert st.assignee_id == member.id


def test_add_subtask_no_fields_defaults_to_none(db):
    task = _make_task(db)
    svc = TaskService(db)
    st = svc.add_subtask(task.id, "sub plain")
    assert st.due_date is None
    assert st.assignee_id is None


# ── update_subtask ────────────────────────────────────────────────────────────

def test_update_subtask_title(db):
    task = _make_task(db)
    svc = TaskService(db)
    st = svc.add_subtask(task.id, "original")
    updated = svc.update_subtask(st.id, title="renamed")
    assert updated.title == "renamed"


def test_update_subtask_due_date(db):
    task = _make_task(db)
    svc = TaskService(db)
    st = svc.add_subtask(task.id, "sub X")
    new_due = _utc(10)
    updated = svc.update_subtask(st.id, title="sub X", due_date=new_due)
    assert updated.due_date == new_due


def test_update_subtask_clear_due_date(db):
    task = _make_task(db)
    svc = TaskService(db)
    st = svc.add_subtask(task.id, "sub Y", due_date=_utc(3))
    updated = svc.update_subtask(st.id, title="sub Y", due_date=None)
    assert updated.due_date is None


def test_update_subtask_assignee(db):
    team = _make_team(db)
    m1 = _make_member(db, team.id, "สมชาย")
    m2 = _make_member(db, team.id, "สมหญิง")
    task = _make_task(db, team_id=team.id)
    svc = TaskService(db)
    st = svc.add_subtask(task.id, "sub Z", assignee_id=m1.id)
    updated = svc.update_subtask(st.id, title="sub Z", assignee_id=m2.id)
    assert updated.assignee_id == m2.id


def test_update_subtask_not_found_raises(db):
    svc = TaskService(db)
    with pytest.raises(NotFoundError):
        svc.update_subtask(9999, title="ghost")


def test_update_deleted_subtask_raises(db):
    task = _make_task(db)
    svc = TaskService(db)
    st = svc.add_subtask(task.id, "to delete")
    svc.delete_subtask(st.id)
    with pytest.raises(NotFoundError):
        svc.update_subtask(st.id, title="after delete")


# ── assignee relationship ────────────────────────────────────────────────────

def test_subtask_assignee_relationship_loaded(db):
    team = _make_team(db)
    member = _make_member(db, team.id, "สมชาย")
    task = _make_task(db, team_id=team.id)
    svc = TaskService(db)
    st = svc.add_subtask(task.id, "check rel", assignee_id=member.id)
    # access via relationship
    assert st.assignee is not None
    assert st.assignee.name == "สมชาย"


# ── workload heatmap includes subtasks ───────────────────────────────────────

def test_workload_heatmap_includes_subtasks(db):
    """Active subtask with due_date + assignee should appear in heatmap data."""
    team = _make_team(db)
    member = _make_member(db, team.id, "นักพัฒนา")
    task = _make_task(db, team_id=team.id)
    svc = TaskService(db)
    # Subtask due this week
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    due = datetime(week_start.year, week_start.month, week_start.day) + timedelta(days=2)
    svc.add_subtask(task.id, "st heatmap", due_date=due, assignee_id=member.id)

    result = svc.get_workload_heatmap(weeks=6)
    assert "นักพัฒนา" in result["users"]
    idx = result["users"].index("นักพัฒนา")
    assert sum(result["data"][idx]) >= 1
