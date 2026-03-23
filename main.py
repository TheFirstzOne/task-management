"""
Task Manager Desktop App
Entry point — Flet 0.80.x application bootstrap
"""

import sys
import asyncio

# ── Suppress Windows asyncio pipe cleanup error ──────────────────
# ConnectionResetError [WinError 10054] is a known harmless Windows bug:
# ProactorEventLoop tries to call shutdown() on an already-closed socket
# during app exit.  ft.run() creates its own event loop internally, so
# setting a custom loop/handler before calling ft.run() has no effect.
# The reliable fix is to monkey-patch the method at class level so the
# suppression applies regardless of which loop Flet uses.
if sys.platform == "win32":
    from asyncio import proactor_events as _pe

    _orig_ccl = _pe._ProactorBasePipeTransport._call_connection_lost

    def _patched_ccl(self, exc):
        try:
            _orig_ccl(self, exc)
        except ConnectionResetError:
            pass   # harmless — socket already closed by the remote host

    _pe._ProactorBasePipeTransport._call_connection_lost = _patched_ccl

import flet as ft
from app.database import init_db, SessionLocal
from app.views.main_layout import build_main_layout
from app.views.login_view import build_login_view
from app.services.auth_service import AuthService
import app.utils.theme as theme


def _ensure_default_admin(db) -> None:
    """Create default admin account on first run if no login user exists."""
    auth_svc = AuthService(db)
    if not auth_svc.has_any_login_user():
        try:
            auth_svc.create_admin(
                username="admin",
                name="Administrator",
                password="admin",
            )
        except Exception:
            pass  # Already exists — race condition safety


def main(page: ft.Page) -> None:
    # ── Window settings ──────────────────────────────────────────
    page.title = "VindFlow"
    page.window.width      = 1280
    page.window.height     = 800
    page.window.min_width  = 960
    page.window.min_height = 600

    # ── Theme (Blue-White) ─────────────────────────────────────────
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor    = theme.BG_DARK
    page.padding    = 0

    # ── Init database + first-run admin ───────────────────────────
    init_db()
    setup_db = SessionLocal()
    try:
        _ensure_default_admin(setup_db)
    finally:
        setup_db.close()

    # ── Login gate ────────────────────────────────────────────────
    def _show_login() -> None:
        login_db = SessionLocal()
        login_view = build_login_view(
            db=login_db,
            page=page,
            on_success=_on_login_success,
        )
        page.controls.clear()
        page.add(login_view)
        page.update()

    def _on_login_success(user) -> None:
        # Store current user in session
        page.session.store.set("current_user", {
            "id":       user.id,
            "name":     user.name,
            "is_admin": user.is_admin,
            "username": user.username,
        })
        _show_main()

    def _on_logout() -> None:
        page.session.store.remove("current_user")
        _show_login()

    def _show_main() -> None:
        layout = build_main_layout(page, on_logout=_on_logout)
        page.controls.clear()
        page.add(layout)
        page.update()

    _show_login()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
