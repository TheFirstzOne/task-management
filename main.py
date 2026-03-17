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
from app.database import init_db
from app.views.main_layout import build_main_layout
import app.utils.theme as theme


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

    # ── Init database ─────────────────────────────────────────────
    init_db()

    # ── Mount main layout ─────────────────────────────────────────
    layout = build_main_layout(page)
    page.add(layout)
    page.update()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
