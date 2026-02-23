"""
Task Manager Desktop App
Entry point — Flet 0.80.x application bootstrap
"""

import flet as ft
from app.database import init_db
from app.views.main_layout import build_main_layout


def main(page: ft.Page) -> None:
    # ── Window settings ──────────────────────────────────────────
    page.title = "Task Manager"
    page.window.width      = 1280
    page.window.height     = 800
    page.window.min_width  = 960
    page.window.min_height = 600

    # ── Theme: Dark mode ─────────────────────────────────────────
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor    = "#0F1117"
    page.padding    = 0

    # ── Init database ─────────────────────────────────────────────
    init_db()

    # ── Mount main layout ─────────────────────────────────────────
    layout = build_main_layout(page)
    page.add(layout)
    page.update()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
