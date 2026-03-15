"""
MainLayout — Shell UI ของแอป
Sidebar navigation + Content area + Settings (dummy)
Compatible with Flet 0.80.x (function-based, no UserControl)
"""

import flet as ft
from app.database import SessionLocal
import app.utils.theme as theme


NAV_ITEMS = [
    ("dashboard", ft.Icons.DASHBOARD_OUTLINED,     "Dashboard"),
    ("team",      ft.Icons.GROUP_OUTLINED,          "ทีมงาน"),
    ("task",      ft.Icons.TASK_ALT_OUTLINED,       "งาน"),
    ("calendar",  ft.Icons.CALENDAR_MONTH_OUTLINED, "ปฏิทิน"),
    ("diary",     ft.Icons.BOOK_OUTLINED,           "บันทึกงาน"),
    ("summary",   ft.Icons.SUMMARIZE_OUTLINED,      "สรุปงาน"),
    ("history",   ft.Icons.HISTORY_OUTLINED,        "ประวัติ"),
]


def build_main_layout(page: ft.Page) -> ft.Control:
    """Build and return the complete app shell."""
    db = SessionLocal()

    # ── State ─────────────────────────────────────────────────────
    active_key = {"value": "dashboard"}
    nav_containers: dict = {}
    content_area = ft.Column(expand=True, spacing=0)

    # ── View factory ──────────────────────────────────────────────
    def get_view(key: str) -> ft.Control:
        from app.views.team_view     import build_team_view
        from app.views.task_view     import build_task_view
        from app.views.calendar_view import build_calendar_view
        from app.views.diary_view    import build_diary_view
        from app.views.summary_view  import build_summary_view
        from app.views.history_view  import build_history_view

        factories = {
            "dashboard": lambda: build_dashboard_view(db),
            "team":      lambda: build_team_view(db, page),
            "task":      lambda: build_task_view(db, page),
            "calendar":  lambda: build_calendar_view(db, page),
            "diary":     lambda: build_diary_view(db, page),
            "summary":   lambda: build_summary_view(db, page),
            "history":   lambda: build_history_view(db, page),
        }
        return factories.get(key, lambda: build_dashboard_view(db))()

    # ── Navigation ────────────────────────────────────────────────
    def navigate(key: str) -> None:
        old_key = active_key["value"]
        if old_key == key:
            return

        # Deactivate old
        old_c = nav_containers.get(old_key)
        if old_c:
            old_c.bgcolor = "transparent"
            row: ft.Row = old_c.content
            row.controls[0].color = theme.TEXT_SEC
            row.controls[1].color = theme.TEXT_SEC
            row.controls[1].weight = ft.FontWeight.NORMAL
            old_c.update()

        active_key["value"] = key

        # Activate new
        new_c = nav_containers.get(key)
        if new_c:
            new_c.bgcolor = theme.ACCENT + "22"
            row: ft.Row = new_c.content
            row.controls[0].color = theme.ACCENT
            row.controls[1].color = theme.TEXT_PRI
            row.controls[1].weight = ft.FontWeight.W_500
            new_c.update()

        # Swap content
        content_area.controls = [get_view(key)]
        content_area.update()

    # ── Nav button builder ────────────────────────────────────────
    def build_nav_btn(key: str, icon, label: str) -> ft.Container:
        is_active = key == active_key["value"]
        c = ft.Container(
            height=42,
            border_radius=8,
            bgcolor=theme.ACCENT + "22" if is_active else "transparent",
            padding=ft.padding.symmetric(horizontal=10),
            content=ft.Row(
                controls=[
                    ft.Icon(icon, color=theme.ACCENT if is_active else theme.TEXT_SEC, size=20),
                    ft.Text(
                        label,
                        color=theme.TEXT_PRI if is_active else theme.TEXT_SEC,
                        size=14,
                        weight=ft.FontWeight.W_500 if is_active else ft.FontWeight.NORMAL,
                    ),
                ],
                spacing=10,
            ),
            on_click=lambda e, k=key: navigate(k),
            ink=True,
        )
        nav_containers[key] = c
        return c

    # ── Settings button (dummy — placeholder for future features) ─
    def _open_settings(e=None):
        pass   # TODO: implement settings in the future

    settings_btn = ft.Container(
        height=42,
        border_radius=8,
        bgcolor="transparent",
        padding=ft.padding.symmetric(horizontal=10),
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.SETTINGS_OUTLINED, color=theme.TEXT_SEC, size=20),
                ft.Text("ตั้งค่า", color=theme.TEXT_SEC, size=14),
            ],
            spacing=10,
        ),
        on_click=_open_settings,
        ink=True,
    )

    # ── Sidebar ───────────────────────────────────────────────────
    logo = ft.Row(
        controls=[
            ft.Icon(ft.Icons.BOLT, color=theme.ACCENT, size=26),
            ft.Text("TaskFlow", size=18, weight=ft.FontWeight.BOLD,
                     color=theme.TEXT_PRI),
        ],
        spacing=8,
    )

    nav_col = ft.Column(
        controls=[build_nav_btn(k, ico, lbl) for k, ico, lbl in NAV_ITEMS],
        spacing=4,
    )

    sidebar = ft.Container(
        width=220,
        bgcolor=theme.BG_SIDEBAR,
        padding=ft.padding.only(left=12, right=12, top=24, bottom=16),
        border=ft.border.only(right=ft.BorderSide(1, theme.BORDER)),
        content=ft.Column(
            controls=[
                logo,
                ft.Divider(height=24, color=theme.BORDER),
                nav_col,
                ft.Container(expand=True),          # spacer — push settings to bottom
                ft.Divider(height=1, color=theme.BORDER),
                settings_btn,
            ],
            spacing=0,
            expand=True,
        ),
    )

    # ── Initial content ───────────────────────────────────────────
    content_area.controls = [get_view("dashboard")]

    return ft.Row(
        controls=[sidebar, content_area],
        spacing=0,
        expand=True,
    )


# ── Dashboard view (inline) ───────────────────────────────────────────────────
def build_dashboard_view(db) -> ft.Control:
    from app.services.task_service import TaskService
    svc   = TaskService(db)
    stats = svc.get_dashboard_stats()

    def stat_card(label: str, value: int, color: str) -> ft.Container:
        return ft.Container(
            width=160,
            height=90,
            bgcolor=theme.BG_CARD,
            border_radius=12,
            border=ft.border.all(1, theme.BORDER),
            padding=16,
            content=ft.Column(
                controls=[
                    ft.Text(str(value), size=32, weight=ft.FontWeight.BOLD,
                            color=color),
                    ft.Text(label, size=13, color=theme.TEXT_SEC),
                ],
                spacing=2,
            ),
        )

    cards = ft.Row(
        controls=[
            stat_card("งานทั้งหมด",  stats["total"],       theme.TEXT_PRI),
            stat_card("กำลังทำ",     stats["in_progress"], theme.ACCENT2),
            stat_card("เสร็จแล้ว",  stats["done"],        "#22C55E"),
            stat_card("เกินกำหนด",  stats["overdue"],     "#EF4444"),
            stat_card("ค้างอยู่",   stats["pending"],     "#F59E0B"),
        ],
        spacing=12,
        wrap=True,
    )

    return ft.Container(
        expand=True,
        bgcolor=theme.BG_DARK,
        padding=24,
        content=ft.Column(
            controls=[
                ft.Text("Dashboard", size=24,
                        weight=ft.FontWeight.BOLD, color=theme.TEXT_PRI),
                ft.Text("ภาพรวมงานทั้งหมด", size=13, color=theme.TEXT_SEC),
                ft.Divider(height=20, color=theme.BORDER),
                cards,
            ],
            spacing=8,
        ),
    )
