"""
Task Manager Desktop App
Entry point — Flet 0.80.x application bootstrap
"""

import sys
import asyncio

# ── Suppress Windows asyncio pipe cleanup error ──────────────────
# ConnectionResetError [WinError 10054] is a known harmless bug
# in Python's ProactorEventLoop on Windows.
if sys.platform == "win32":
    _orig_handler = None

    def _suppress_connection_reset(loop, context):
        exc = context.get("exception")
        if isinstance(exc, ConnectionResetError):
            return                          # silently ignore
        if _orig_handler:
            _orig_handler(context)          # forward everything else
        else:
            loop.default_exception_handler(context)

    _loop = asyncio.new_event_loop()
    _orig_handler = _loop.get_exception_handler()
    _loop.set_exception_handler(_suppress_connection_reset)
    asyncio.set_event_loop(_loop)

import flet as ft
from app.database import init_db
from app.views.main_layout import build_main_layout
import app.utils.theme as theme


def main(page: ft.Page) -> None:
    # ── Window settings ──────────────────────────────────────────
    page.title = "Task Manager"
    page.window.width      = 1280
    page.window.height     = 800
    page.window.min_width  = 960
    page.window.min_height = 600

    # ── Theme (Blue-White) ─────────────────────────────────────────
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor    = theme.BG_DARK
    page.padding    = 0

    # ── Init database ─────────────────────────────────────────────
    init_db()

    # ── Mount main layout ─────────────────────────────────────────
    layout = build_main_layout(page)
    page.add(layout)
    page.update()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
