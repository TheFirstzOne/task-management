# -*- coding: utf-8 -*-
"""
Tests for AuthService (app/services/auth_service.py).
"""
import pytest
from app.services.auth_service import AuthService
from app.utils.exceptions import InvalidCredentialsError, ValidationError


def _svc(db) -> AuthService:
    return AuthService(db)


def _make_admin(svc: AuthService, username="admin", name="Admin", password="secret"):
    return svc.create_admin(username=username, name=name, password=password)


# ── Password hashing ──────────────────────────────────────────────────────────

def test_hash_password_produces_salt_hash_pair(db):
    svc = _svc(db)
    stored = svc.hash_password("mypassword")
    assert ":" in stored
    salt, hashed = stored.split(":", 1)
    assert len(salt) == 32   # 16 bytes → 32 hex chars
    assert len(hashed) > 0


def test_hash_password_unique_salt_per_call(db):
    svc = _svc(db)
    h1 = svc.hash_password("same")
    h2 = svc.hash_password("same")
    assert h1 != h2   # different salts → different hashes


def test_verify_password_correct(db):
    svc = _svc(db)
    stored = svc.hash_password("correct_pass")
    assert svc.verify_password("correct_pass", stored) is True


def test_verify_password_wrong(db):
    svc = _svc(db)
    stored = svc.hash_password("correct_pass")
    assert svc.verify_password("wrong_pass", stored) is False


# ── create_admin ──────────────────────────────────────────────────────────────

def test_create_admin_returns_user(db):
    svc = _svc(db)
    user = _make_admin(svc)
    assert user.id is not None
    assert user.username == "admin"
    assert user.is_admin is True


def test_create_admin_stores_hashed_password(db):
    svc = _svc(db)
    user = _make_admin(svc, password="secret123")
    assert user.password_hash is not None
    assert "secret123" not in user.password_hash   # never stored plaintext


def test_create_admin_rejects_short_password(db):
    svc = _svc(db)
    with pytest.raises(ValidationError):
        svc.create_admin(username="bob", name="Bob", password="ab")


def test_create_admin_rejects_empty_username(db):
    svc = _svc(db)
    with pytest.raises(ValidationError):
        svc.create_admin(username="  ", name="Bob", password="password")


def test_create_admin_rejects_duplicate_username(db):
    svc = _svc(db)
    _make_admin(svc, username="alice")
    with pytest.raises(ValidationError):
        _make_admin(svc, username="alice")


# ── login ─────────────────────────────────────────────────────────────────────

def test_login_success(db):
    svc = _svc(db)
    _make_admin(svc, username="alice", password="pass1234")
    user = svc.login("alice", "pass1234")
    assert user.username == "alice"


def test_login_wrong_password(db):
    svc = _svc(db)
    _make_admin(svc, username="bob", password="correct")
    with pytest.raises(InvalidCredentialsError):
        svc.login("bob", "wrong")


def test_login_unknown_user(db):
    svc = _svc(db)
    with pytest.raises(InvalidCredentialsError):
        svc.login("nobody", "pass")


def test_login_empty_credentials(db):
    svc = _svc(db)
    with pytest.raises(InvalidCredentialsError):
        svc.login("", "")


def test_login_inactive_user_rejected(db):
    svc = _svc(db)
    user = _make_admin(svc, username="inactive_user", password="pass1234")
    user.is_active = False
    db.commit()
    with pytest.raises(InvalidCredentialsError):
        svc.login("inactive_user", "pass1234")


# ── has_any_login_user ────────────────────────────────────────────────────────

def test_has_any_login_user_false_when_empty(db):
    svc = _svc(db)
    assert svc.has_any_login_user() is False


def test_has_any_login_user_true_after_create(db):
    svc = _svc(db)
    _make_admin(svc)
    assert svc.has_any_login_user() is True


# ── set_password ──────────────────────────────────────────────────────────────

def test_set_password_allows_new_login(db):
    svc = _svc(db)
    user = _make_admin(svc, username="charlie", password="oldpass")
    svc.set_password(user.id, "newpass")
    logged_in = svc.login("charlie", "newpass")
    assert logged_in.id == user.id


def test_set_password_rejects_short_password(db):
    svc = _svc(db)
    user = _make_admin(svc)
    with pytest.raises(ValidationError):
        svc.set_password(user.id, "ab")
