# -*- coding: utf-8 -*-
"""Users router — Phase 21"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService
from app.utils.exceptions import NotFoundError, TaskFlowError, ValidationError
from server.deps import get_current_user, get_db
from server.serializers import user_to_dict

router = APIRouter()


# ── Request body schemas ──────────────────────────────────────────────────────

class CreateUserIn(BaseModel):
    name: str
    username: str
    password: str
    role: str = "Other"
    is_admin: bool = False


class UpdateUserIn(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    skills: Optional[str] = None
    is_active: Optional[bool] = None


class SetPasswordIn(BaseModel):
    password: str


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str


class SetCredentialIn(BaseModel):
    username: str
    password: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _handle_exc(exc: Exception):
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, TaskFlowError):
        raise HTTPException(status_code=400, detail=str(exc))
    raise exc


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return all non-deleted users."""
    repo = UserRepository(db)
    return [user_to_dict(u) for u in repo.get_all()]


@router.post("")
def create_user(
    body: CreateUserIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Create a new user with login credentials."""
    repo = UserRepository(db)
    auth_svc = AuthService(db)
    try:
        user = repo.create(name=body.name, role=UserRole(body.role))
        user.username = body.username
        user.password_hash = auth_svc.hash_password(body.password)
        user.is_admin = body.is_admin
        db.commit()
        db.refresh(user)
        return user_to_dict(user)
    except Exception as exc:
        _handle_exc(exc)


@router.patch("/{user_id}")
def update_user(
    user_id: int,
    body: UpdateUserIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Update user fields."""
    repo = UserRepository(db)
    kwargs = body.model_dump(exclude_none=True)
    if "role" in kwargs:
        kwargs["role"] = UserRole(kwargs["role"])
    try:
        user = repo.update(user_id, **kwargs)
        if not user:
            raise HTTPException(status_code=404, detail=f"ไม่พบผู้ใช้ (id={user_id})")
        return user_to_dict(user)
    except HTTPException:
        raise
    except Exception as exc:
        _handle_exc(exc)


@router.post("/{user_id}/set-password")
def set_password(
    user_id: int,
    body: SetPasswordIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Set a new password for a user (admin action)."""
    auth_svc = AuthService(db)
    try:
        auth_svc.set_password(user_id, body.password)
        return {}
    except Exception as exc:
        _handle_exc(exc)


@router.post("/{user_id}/toggle-admin")
def toggle_admin(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Toggle admin status for a user."""
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"ไม่พบผู้ใช้ (id={user_id})")
    user.is_admin = not user.is_admin
    db.commit()
    db.refresh(user)
    return user_to_dict(user)


@router.post("/{user_id}/change-password")
def change_password(
    user_id: int,
    body: ChangePasswordIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Change password by verifying old password first."""
    auth_svc = AuthService(db)
    try:
        auth_svc.change_password(user_id, body.old_password, body.new_password)
        return {}
    except Exception as exc:
        _handle_exc(exc)


@router.post("/{user_id}/set-credential")
def set_credential(
    user_id: int,
    body: SetCredentialIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Set username and password for a user (admin action)."""
    repo = UserRepository(db)
    auth_svc = AuthService(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"ไม่พบผู้ใช้ (id={user_id})")
    user.username = body.username
    user.password_hash = auth_svc.hash_password(body.password)
    db.commit()
    return {}
