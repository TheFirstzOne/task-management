# -*- coding: utf-8 -*-
"""JWT helpers for VindFlow API — Phase 21"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from jose import JWTError, jwt

SECRET_KEY = "vindflow-lans-2025"
ALGORITHM = "HS256"
EXPIRE_HOURS = 24


def create_token(user_id: int, name: str, is_admin: bool) -> str:
    """Create a signed JWT token for the given user."""
    expire = datetime.now(timezone.utc) + timedelta(hours=EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "name": name,
        "is_admin": is_admin,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token. Raises HTTP 401 if invalid or expired."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("sub") is None:
            raise HTTPException(status_code=401, detail="Token ไม่ถูกต้อง")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token ไม่ถูกต้องหรือหมดอายุ")
