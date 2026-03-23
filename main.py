"""
Task Manager Desktop App — Phase 21
Entry point — Flet desktop client (connects to FastAPI server)
"""

import sys

# ── Suppress Windows asyncio pipe cleanup error ──────────────────
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
from app.client import APIClient
from app.views.main_layout import build_main_layout
from app.views.login_view import build_login_view
import app.utils.theme as theme


def main(page: ft.Page) -> None:
    # ── Window settings ──────────────────────────────────────────
    page.title = "VindFlow"
    page.window.width      = 1280
    page.window.height     = 800
    page.window.min_width  = 960
    page.window.min_height = 600

    # ── Theme (Blue-White) ────────────────────────────────────────
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor    = theme.BG_DARK
    page.padding    = 0

    # ── Shared API client (token set after login) ─────────────────
    api = APIClient()

    # ── Login gate ────────────────────────────────────────────────
    def _show_login() -> None:
        login_view = build_login_view(
            api=api,
            page=page,
            on_success=_on_login_success,
        )
        page.controls.clear()
        page.add(login_view)
        page.update()

    def _on_login_success(user: dict) -> None:
        """Called by login_view after successful login.
        api.token is already set. user is a plain dict.
        """
        page.session.store.set("current_user", {
            "id":       user["id"],
            "name":     user["name"],
            "is_admin": user.get("is_admin", False),
            "username": user.get("username"),
        })
        _show_main()

    def _on_logout() -> None:
        page.session.store.remove("current_user")
        page.session.store.remove("api_client_token")
        api.token = ""
        _show_login()

    def _show_main() -> None:
        layout = build_main_layout(page, on_logout=_on_logout, api=api)
        page.controls.clear()
        page.add(layout)
        page.update()

    _show_login()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
