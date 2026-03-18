"""
Tests for TeamService — team & member management.
Covers: create/update/delete team, add/remove/delete member,
        workload calculation, toggle active, duplicate name guard.
"""

import pytest
from app.services.team_service import TeamService
from app.services.task_service import TaskService
from app.models.user import UserRole
from app.models.task import TaskStatus
from app.utils.exceptions import NotFoundError, DuplicateNameError


# ── Helpers ────────────────────────────────────────────────────────────────

def _svc(db) -> TeamService:
    return TeamService(db)


def _team(db, name="ทีม A", description=""):
    return _svc(db).create_team(name=name, description=description)


def _member(db, team_id, name="สมาชิก", role=UserRole.TECHNICIAN, skills=""):
    return _svc(db).add_member(team_id, name=name, role=role, skills=skills)


# ══════════════════════════════════════════════════════════════════════════════
#  TEAM CRUD
# ══════════════════════════════════════════════════════════════════════════════

def test_create_team_basic(db):
    team = _team(db, name="Dev Team")
    assert team.id is not None
    assert team.name == "Dev Team"
    assert team.is_deleted is False


def test_create_team_duplicate_name_raises(db):
    _team(db, name="ทีม X")
    with pytest.raises(DuplicateNameError):
        _team(db, name="ทีม X")


def test_get_team_found(db):
    created = _team(db, name="ค้นหาได้")
    fetched = _svc(db).get_team(created.id)
    assert fetched.name == "ค้นหาได้"


def test_get_team_not_found_raises(db):
    with pytest.raises(NotFoundError):
        _svc(db).get_team(9999)


def test_get_all_teams_empty(db):
    assert _svc(db).get_all_teams() == []


def test_get_all_teams_returns_all(db):
    _team(db, name="A")
    _team(db, name="B")
    assert len(_svc(db).get_all_teams()) == 2


def test_update_team_name(db):
    team = _team(db, name="เก่า")
    updated = _svc(db).update_team(team.id, name="ใหม่")
    assert updated.name == "ใหม่"


def test_update_team_not_found_raises(db):
    with pytest.raises(NotFoundError):
        _svc(db).update_team(9999, name="X")


def test_delete_team_soft_deletes(db):
    team = _team(db)
    _svc(db).delete_team(team.id)
    assert _svc(db).get_all_teams() == []


def test_delete_team_not_found_raises(db):
    with pytest.raises(NotFoundError):
        _svc(db).delete_team(9999)


def test_delete_team_unassigns_members(db):
    """Members remain in system but team_id becomes None after team deletion."""
    svc = _svc(db)
    team = _team(db)
    member = _member(db, team.id, name="ช่างA")
    svc.delete_team(team.id)
    # User still exists (soft-delete on team, not user)
    user = svc.user_repo.get_by_id(member.id)
    assert user is not None
    assert user.team_id is None


# ══════════════════════════════════════════════════════════════════════════════
#  MEMBER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def test_add_member_to_team(db):
    team = _team(db)
    member = _member(db, team.id, name="ช่าง A", role=UserRole.ENGINEER)
    assert member.id is not None
    assert member.name == "ช่าง A"
    assert member.role == UserRole.ENGINEER
    assert member.team_id == team.id


def test_add_member_to_nonexistent_team_raises(db):
    with pytest.raises(NotFoundError):
        _member(db, team_id=9999, name="X")


def test_remove_member_unassigns_team(db):
    team = _team(db)
    member = _member(db, team.id)
    _svc(db).remove_member(member.id)
    user = _svc(db).user_repo.get_by_id(member.id)
    assert user.team_id is None


def test_remove_member_not_found_raises(db):
    with pytest.raises(NotFoundError):
        _svc(db).remove_member(9999)


def test_delete_member_soft_deletes(db):
    team = _team(db)
    member = _member(db, team.id)
    _svc(db).delete_member(member.id)
    deleted = _svc(db).user_repo.get_by_id(member.id)
    # get_by_id may return None for deleted users depending on repo
    # either None or is_deleted == True
    assert deleted is None or deleted.is_deleted is True


def test_delete_member_unassigns_active_tasks(db):
    """Active tasks should lose assignee when member is deleted."""
    team = _team(db)
    member = _member(db, team.id, name="ช่าง")
    task_svc = TaskService(db)
    task = task_svc.create_task("งาน", assignee_id=member.id)

    _svc(db).delete_member(member.id)

    # task should no longer have an assignee
    db.refresh(task)
    assert task.assignee_id is None


def test_delete_member_not_found_raises(db):
    with pytest.raises(NotFoundError):
        _svc(db).delete_member(9999)


def test_delete_member_keeps_done_tasks_assigned(db):
    """Completed tasks retain their assignee reference even after member deletion."""
    team = _team(db)
    member = _member(db, team.id, name="ช่าง")
    task_svc = TaskService(db)
    task = task_svc.create_task("งานเสร็จ", assignee_id=member.id)
    task_svc.change_status(task.id, TaskStatus.DONE)

    _svc(db).delete_member(member.id)

    db.refresh(task)
    # Done tasks are not unassigned
    assert task.assignee_id == member.id


def test_toggle_member_active(db):
    team = _team(db)
    member = _member(db, team.id)
    assert member.is_active is True

    toggled = _svc(db).toggle_member_active(member.id)
    assert toggled.is_active is False

    toggled_back = _svc(db).toggle_member_active(member.id)
    assert toggled_back.is_active is True


def test_toggle_member_not_found_raises(db):
    with pytest.raises(NotFoundError):
        _svc(db).toggle_member_active(9999)


# ══════════════════════════════════════════════════════════════════════════════
#  WORKLOAD
# ══════════════════════════════════════════════════════════════════════════════

def test_workload_empty_team(db):
    team = _team(db)
    workload = _svc(db).get_workload(team.id)
    assert workload == {}


def test_workload_counts_active_tasks(db):
    team = _team(db)
    member = _member(db, team.id, name="ช่าง")
    task_svc = TaskService(db)
    task_svc.create_task("งาน 1", assignee_id=member.id)
    task_svc.create_task("งาน 2", assignee_id=member.id)

    workload = _svc(db).get_workload(team.id)
    assert workload[member.id] == 2


def test_workload_excludes_done_tasks(db):
    team = _team(db)
    member = _member(db, team.id, name="ช่าง")
    task_svc = TaskService(db)
    t1 = task_svc.create_task("งาน 1", assignee_id=member.id)
    task_svc.create_task("งาน 2", assignee_id=member.id)
    task_svc.change_status(t1.id, TaskStatus.DONE)

    workload = _svc(db).get_workload(team.id)
    assert workload[member.id] == 1


def test_workload_multiple_members(db):
    team = _team(db)
    m1 = _member(db, team.id, name="ช่าง 1")
    m2 = _member(db, team.id, name="ช่าง 2")
    task_svc = TaskService(db)
    task_svc.create_task("งาน A", assignee_id=m1.id)
    task_svc.create_task("งาน B", assignee_id=m1.id)
    task_svc.create_task("งาน C", assignee_id=m2.id)

    workload = _svc(db).get_workload(team.id)
    assert workload[m1.id] == 2
    assert workload[m2.id] == 1
