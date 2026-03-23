# -*- coding: utf-8 -*-
"""FastAPI dependency injection helpers — Phase 21"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from server.auth import verify_token

security = HTTPBearer()


def get_db():
    """Yield a fresh SQLAlchemy session, closing it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the current user from the Bearer token. Raises 401 if invalid."""
    payload = verify_token(credentials.credentials)
    user_id = int(payload["sub"])
    user = (
        db.query(User)
        .filter(User.id == user_id, User.is_deleted == False)  # noqa: E712
        .first()
    )
    if not user:
        raise HTTPException(status_code=401, detail="ไม่พบผู้ใช้งาน")
    return user
