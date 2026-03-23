# -*- coding: utf-8 -*-
"""Auth router — POST /auth/login"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.services.auth_service import AuthService
from app.utils.exceptions import InvalidCredentialsError
from server.auth import create_token
from server.deps import get_db
from server.serializers import user_to_dict

router = APIRouter()


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    """Authenticate user and return JWT access token."""
    try:
        user = AuthService(db).login(body.username, body.password)
        token = create_token(user.id, user.name, user.is_admin)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user_to_dict(user),
        }
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
