# -*- coding: utf-8 -*-
"""Teams and Members router — Phase 21"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository
from app.services.team_service import TeamService
from app.utils.exceptions import NotFoundError, TaskFlowError, ValidationError
from server.deps import get_current_user, get_db
from server.serializers import team_to_dict, user_to_dict

# Two routers: one for /teams, one for /members
teams_router = APIRouter()
members_router = APIRouter()


# ── Request body schemas ──────────────────────────────────────────────────────

class CreateTeamIn(BaseModel):
    name: str
    description: str = ""


class UpdateTeamIn(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class AddMemberIn(BaseModel):
    name: str
    role: str
    skills: str = ""


class UpdateMemberIn(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    skills: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _handle_exc(exc: Exception):
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, TaskFlowError):
        raise HTTPException(status_code=400, detail=str(exc))
    raise exc


# ── Team endpoints (/api/teams/...) ──────────────────────────────────────────

@teams_router.get("")
def list_teams(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return all teams with members."""
    svc = TeamService(db)
    return [team_to_dict(t) for t in svc.get_all_teams()]


@teams_router.post("")
def create_team(
    body: CreateTeamIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Create a new team."""
    svc = TeamService(db)
    try:
        team = svc.create_team(name=body.name, description=body.description)
        return team_to_dict(team)
    except Exception as exc:
        _handle_exc(exc)


@teams_router.patch("/{team_id}")
def update_team(
    team_id: int,
    body: UpdateTeamIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Update team name or description."""
    svc = TeamService(db)
    kwargs = body.model_dump(exclude_none=True)
    try:
        team = svc.update_team(team_id, **kwargs)
        return team_to_dict(team)
    except Exception as exc:
        _handle_exc(exc)


@teams_router.delete("/{team_id}")
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Delete a team."""
    svc = TeamService(db)
    try:
        svc.delete_team(team_id)
        return {}
    except Exception as exc:
        _handle_exc(exc)


@teams_router.get("/{team_id}/workload")
def team_workload(
    team_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return active task counts per member for a team."""
    svc = TeamService(db)
    try:
        workload = svc.get_workload(team_id)
        return {"workload": workload}
    except Exception as exc:
        _handle_exc(exc)


@teams_router.post("/{team_id}/members")
def add_member(
    team_id: int,
    body: AddMemberIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Add a new member to a team."""
    svc = TeamService(db)
    try:
        user = svc.add_member(
            team_id=team_id,
            name=body.name,
            role=UserRole(body.role),
            skills=body.skills,
        )
        return user_to_dict(user)
    except Exception as exc:
        _handle_exc(exc)


# ── Member endpoints (/api/members/...) ──────────────────────────────────────

@members_router.get("/dropdown")
def members_dropdown(
    team_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return active users for assignee dropdown, optionally filtered by team."""
    svc = TeamService(db)
    return [user_to_dict(u) for u in svc.get_members_for_dropdown(team_id)]


@members_router.patch("/{member_id}")
def update_member(
    member_id: int,
    body: UpdateMemberIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Update a member's name, role, or skills."""
    repo = UserRepository(db)
    kwargs = body.model_dump(exclude_none=True)
    if "role" in kwargs:
        kwargs["role"] = UserRole(kwargs["role"])
    try:
        user = repo.update(member_id, **kwargs)
        if not user:
            raise HTTPException(status_code=404, detail=f"ไม่พบสมาชิก (id={member_id})")
        return user_to_dict(user)
    except HTTPException:
        raise
    except Exception as exc:
        _handle_exc(exc)


@members_router.delete("/{member_id}")
def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Soft-delete a member."""
    svc = TeamService(db)
    try:
        svc.delete_member(member_id)
        return {}
    except Exception as exc:
        _handle_exc(exc)


@members_router.post("/{member_id}/toggle-active")
def toggle_member_active(
    member_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Toggle a member's active status."""
    svc = TeamService(db)
    try:
        user = svc.toggle_member_active(member_id)
        return user_to_dict(user)
    except Exception as exc:
        _handle_exc(exc)
