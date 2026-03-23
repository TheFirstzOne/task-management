"""
AuthService — Authentication logic for Phase 19 Login System.

Password hashing uses hashlib.pbkdf2_hmac (Python built-in, no extra deps).
Salt is generated per-password via secrets.token_hex so identical passwords
produce different hashes.
"""

import hashlib
import secrets
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.utils.exceptions import InvalidCredentialsError, ValidationError


_HASH_ALGO       = "sha256"
_ITERATIONS      = 260_000   # OWASP 2023 recommendation for PBKDF2-SHA256
_SALT_HEX_LENGTH = 32        # 16 bytes → 32 hex chars


class AuthService:

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Password helpers ──────────────────────────────────────────────────────

    def hash_password(self, password: str) -> str:
        """Return '<salt_hex>:<hash_hex>' ready to store in password_hash column."""
        salt = secrets.token_hex(_SALT_HEX_LENGTH // 2)
        hashed = hashlib.pbkdf2_hmac(
            _HASH_ALGO, password.encode(), salt.encode(), _ITERATIONS
        )
        return f"{salt}:{hashed.hex()}"

    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Return True if *password* matches *stored_hash*."""
        try:
            salt, expected_hex = stored_hash.split(":", 1)
        except ValueError:
            return False
        check = hashlib.pbkdf2_hmac(
            _HASH_ALGO, password.encode(), salt.encode(), _ITERATIONS
        )
        return secrets.compare_digest(check.hex(), expected_hex)

    # ── Login ─────────────────────────────────────────────────────────────────

    def login(self, username: str, password: str) -> User:
        """Return User if credentials valid; raise InvalidCredentialsError otherwise."""
        if not username or not password:
            raise InvalidCredentialsError()
        user = (
            self.db.query(User)
            .filter(
                User.username == username.strip(),
                User.is_deleted == False,
                User.is_active  == True,
            )
            .first()
        )
        if not user or not user.password_hash:
            raise InvalidCredentialsError()
        if not self.verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        return user

    # ── Account management ────────────────────────────────────────────────────

    def create_admin(self, username: str, name: str, password: str) -> User:
        """Create (or reuse) an admin account. Raises ValidationError on bad input."""
        username = username.strip()
        if not username:
            raise ValidationError("ชื่อผู้ใช้ต้องไม่ว่าง")
        if len(password) < 4:
            raise ValidationError("รหัสผ่านต้องมีอย่างน้อย 4 ตัวอักษร")
        existing = self.db.query(User).filter(User.username == username).first()
        if existing:
            raise ValidationError(f"ชื่อผู้ใช้ '{username}' มีอยู่แล้ว")
        user = User(
            name=name or username,
            username=username,
            password_hash=self.hash_password(password),
            is_admin=True,
            role=UserRole.OTHER,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_password(self, user_id: int, new_password: str) -> None:
        """Update password for an existing user."""
        if len(new_password) < 4:
            raise ValidationError("รหัสผ่านต้องมีอย่างน้อย 4 ตัวอักษร")
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            from app.utils.exceptions import NotFoundError
            raise NotFoundError("User", user_id)
        user.password_hash = self.hash_password(new_password)
        self.db.commit()

    def change_password(self, user_id: int, old_password: str, new_password: str) -> None:
        """Verify old password then replace with new one."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.password_hash:
            raise ValidationError("ไม่พบบัญชีผู้ใช้")
        if not self.verify_password(old_password, user.password_hash):
            raise ValidationError("รหัสผ่านเดิมไม่ถูกต้อง")
        self.set_password(user_id, new_password)

    def has_any_login_user(self) -> bool:
        """Return True if at least one user with a username exists."""
        return (
            self.db.query(User)
            .filter(User.username.isnot(None), User.is_deleted == False)
            .count()
        ) > 0
