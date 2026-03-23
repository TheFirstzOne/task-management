"""
MainLayout — Shell UI ของแอป
Sidebar navigation + Content area + Settings (dummy)
Compatible with Flet 0.80.x (function-based, no UserControl)
"""

import threading
import flet as ft
import app.utils.theme as theme
from app.utils.ui_helpers import safe_update
from app.utils import shortcut_registry


NAV_ITEMS = [
    ("dashboard", ft.Icons.DASHBOARD_OUTLINED,       "Dashboard"),
    ("team",      ft.Icons.GROUP_OUTLINED,            "ทีมงาน"),
    ("task",      ft.Icons.TASK_ALT_OUTLINED,         "งาน"),
    ("calendar",  ft.Icons.CALENDAR_MONTH_OUTLINED,   "ปฏิทิน"),
    ("diary",     ft.Icons.BOOK_OUTLINED,             "บันทึกงาน"),
    ("summary",   ft.Icons.SUMMARIZE_OUTLINED,        "สรุปงาน"),
    ("history",   ft.Icons.HISTORY_OUTLINED,          "ประวัติ"),
    ("user_mgmt", ft.Icons.MANAGE_ACCOUNTS_OUTLINED,  "จัดการ Users"),  # admin only
]


def build_main_layout(page: ft.Page, on_logout: callable = None, api=None) -> ft.Control:
    """Build and return the complete app shell.

    on_logout: optional callback called when the user clicks Logout.
               If None, logout is hidden.
    """

    # ── Session — current user ────────────────────────────────────
    _current_user = page.session.store.get("current_user") or {}
    _is_admin     = _current_user.get("is_admin", False)

    # ── State ─────────────────────────────────────────────────────
    active_key        = {"value": "dashboard"}
    nav_containers:  dict = {}
    nav_label_refs:  dict = {}   # key → ft.Text label control
    task_badge_info: dict = {"ctrl": None}
    near_badge_info: dict = {"ctrl": None}
    sidebar_collapsed = {"value": False}
    _search_target:  dict = {"value": None}   # task_id to highlight after navigate
    content_area = ft.Column(expand=True, spacing=0)

    # ── Keyboard shortcut dispatcher ──────────────────────────────
    def _on_keyboard(e: ft.KeyboardEvent):
        shortcut_registry.dispatch(e.key, e.ctrl, e.shift, e.alt)

    page.on_keyboard_event = _on_keyboard

    def _focus_search():
        tf_search.focus()

    # ── View factory ──────────────────────────────────────────────
    def get_view(key: str) -> ft.Control:
        from app.views.dashboard_view import build_dashboard_view as _build_dash
        from app.views.team_view      import build_team_view
        from app.views.task_view      import build_task_view
        from app.views.calendar_view  import build_calendar_view
        from app.views.diary_view     import build_diary_view
        from app.views.summary_view   import build_summary_view
        from app.views.history_view   import build_history_view
        from app.views.settings_view  import build_settings_view
        from app.views.account_view   import build_account_view

        # Clear per-view shortcuts before building new view
        shortcut_registry.clear()
        # Re-register global shortcuts after clear
        shortcut_registry.register("ctrl_f", _focus_search)

        # Consume highlight target (set by search) before building view
        highlight_id = _search_target["value"]
        _search_target["value"] = None

        factories = {
            "dashboard": lambda: _build_dash(api, navigate_fn=navigate),
            "team":      lambda: build_team_view(api, page),
            "task":      lambda: build_task_view(api, page, highlight_task_id=highlight_id),
            "calendar":  lambda: build_calendar_view(api, page),
            "diary":     lambda: build_diary_view(api, page),
            "summary":   lambda: build_summary_view(api, page),
            "history":   lambda: build_history_view(api, page),
            "account":   lambda: build_account_view(api, page),
            "user_mgmt": lambda: build_settings_view(api, page),
        }
        return factories.get(key, lambda: _build_dash(api, navigate_fn=navigate))()

    # ── Overdue + near-due badge refresh ─────────────────────────
    def _refresh_task_badge() -> None:
        ctrl      = task_badge_info.get("ctrl")
        near_ctrl = near_badge_info.get("ctrl")
        if not ctrl and not near_ctrl:
            return
        try:
            stats = api.get_dashboard_stats()
            count = stats.get("overdue", 0)
            near  = api.get_near_due_count(days=3)
            expanded = not sidebar_collapsed["value"]
            if ctrl:
                if count > 0 and expanded:
                    ctrl.content.value = str(count) if count < 100 else "99+"
                    ctrl.visible = True
                else:
                    ctrl.visible = False
                safe_update(ctrl)
            if near_ctrl:
                if near > 0 and expanded:
                    near_ctrl.content.value = str(near) if near < 100 else "99+"
                    near_ctrl.visible = True
                else:
                    near_ctrl.visible = False
                safe_update(near_ctrl)
        except Exception:
            pass

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

        # Swap content + refresh overdue badge
        content_area.controls = [get_view(key)]
        content_area.update()
        _refresh_task_badge()

    # ── Nav button builder ────────────────────────────────────────
    def build_nav_btn(key: str, icon, label: str) -> ft.Container:
        is_active = key == active_key["value"]
        label_ctrl = ft.Text(
            label,
            color=theme.TEXT_PRI if is_active else theme.TEXT_SEC,
            size=14,
            weight=ft.FontWeight.W_500 if is_active else ft.FontWeight.NORMAL,
            expand=True,
        )
        nav_label_refs[key] = label_ctrl

        row_controls = [
            ft.Icon(icon, color=theme.ACCENT if is_active else theme.TEXT_SEC, size=20),
            label_ctrl,
        ]

        # Overdue + near-due badges — visible only on the "task" nav item
        if key == "task":
            badge = ft.Container(
                width=20, height=20, border_radius=10,
                bgcolor="#EF4444",
                alignment=ft.alignment.Alignment(0, 0),
                visible=False,
                content=ft.Text("0", size=9, color="#FFFFFF",
                                weight=ft.FontWeight.BOLD),
            )
            task_badge_info["ctrl"] = badge
            row_controls.append(badge)
            near_badge = ft.Container(
                width=20, height=20, border_radius=10,
                bgcolor="#FF9800",
                alignment=ft.alignment.Alignment(0, 0),
                visible=False,
                content=ft.Text("0", size=9, color="#FFFFFF",
                                weight=ft.FontWeight.BOLD),
            )
            near_badge_info["ctrl"] = near_badge
            row_controls.append(near_badge)

        c = ft.Container(
            height=42,
            border_radius=8,
            bgcolor=theme.ACCENT + "22" if is_active else "transparent",
            padding=ft.padding.symmetric(horizontal=10),
            content=ft.Row(controls=row_controls, spacing=10),
            on_click=lambda e, k=key: navigate(k),
            ink=True,
            visible=True if key != "user_mgmt" else _is_admin,
        )
        nav_containers[key] = c
        return c

    # ── Sidebar toggle ────────────────────────────────────────────
    bolt_icon_ctrl = ft.Icon(ft.Icons.BOLT, color=theme.ACCENT, size=26)
    logo_text_ctrl = ft.Text("VindFlow", size=18, weight=ft.FontWeight.BOLD,
                              color=theme.TEXT_PRI)

    # Store toggle button as a Container so we can swap its content (Icon.name
    # does not reliably trigger re-render in Flet 0.82 after mount).
    toggle_btn_ctrl = ft.Container(
        content=ft.Icon(ft.Icons.CHEVRON_LEFT, color=theme.TEXT_SEC, size=18),
        on_click=lambda e: _toggle_sidebar(e),
        ink=True,
        border_radius=6,
        padding=4,
        tooltip="ย่อ/ขยาย sidebar",
    )

    def _toggle_sidebar(e=None):
        collapsed = not sidebar_collapsed["value"]
        sidebar_collapsed["value"] = collapsed

        # Sidebar geometry — use wider collapsed width + tighter padding so toggle is reachable
        sidebar.width   = 60 if collapsed else 220
        sidebar.padding = (ft.padding.only(left=4, right=4, top=24, bottom=16)
                           if collapsed else
                           ft.padding.only(left=12, right=12, top=24, bottom=16))

        logo_text_ctrl.visible  = not collapsed

        # Hide search bar when collapsed (too narrow to be useful)
        search_container.visible = not collapsed
        if collapsed:
            tf_search.value = ""
            search_results_col.controls = []
            search_results_col.visible = False

        # Replace icon content — reliable way to change icon in Flet 0.82
        toggle_btn_ctrl.content = ft.Icon(
            ft.Icons.CHEVRON_RIGHT if collapsed else ft.Icons.CHEVRON_LEFT,
            color=theme.TEXT_SEC, size=18,
        )
        toggle_btn_ctrl.update()

        # Nav buttons — centre icon + tighten padding when collapsed
        for key, lbl in nav_label_refs.items():
            lbl.visible = not collapsed
            c = nav_containers.get(key)
            if c:
                c.padding = ft.padding.symmetric(horizontal=2 if collapsed else 10)
                row: ft.Row = c.content
                row.alignment = (ft.MainAxisAlignment.CENTER if collapsed
                                 else ft.MainAxisAlignment.START)

        # Settings button — same treatment
        settings_btn.padding = ft.padding.symmetric(horizontal=2 if collapsed else 10)
        sb_row: ft.Row = settings_btn.content
        sb_row.alignment = (ft.MainAxisAlignment.CENTER if collapsed
                             else ft.MainAxisAlignment.START)

        settings_label_ctrl.visible = not collapsed
        account_label_ctrl.visible  = not collapsed
        logout_label_ctrl.visible   = not collapsed

        account_btn.padding = ft.padding.symmetric(horizontal=2 if collapsed else 10)
        ab_row: ft.Row = account_btn.content
        ab_row.alignment = (ft.MainAxisAlignment.CENTER if collapsed
                            else ft.MainAxisAlignment.START)

        if on_logout is not None:
            logout_btn.padding = ft.padding.symmetric(horizontal=2 if collapsed else 10)
            lo_row: ft.Row = logout_btn.content
            lo_row.alignment = (ft.MainAxisAlignment.CENTER if collapsed
                                else ft.MainAxisAlignment.START)

        # Badge is only meaningful when sidebar is expanded
        if task_badge_info.get("ctrl"):
            if collapsed:
                task_badge_info["ctrl"].visible = False
            else:
                _refresh_task_badge()   # updates badge count; sidebar.update() below applies layout

        sidebar.update()

    # ── Settings button ───────────────────────────────────────────
    def _open_settings(e=None):
        pass  # dummy — feature coming soon

    settings_label_ctrl = ft.Text("ตั้งค่า", color=theme.TEXT_SEC, size=14, expand=True)

    settings_btn = ft.Container(
        height=42,
        border_radius=8,
        bgcolor="transparent",
        padding=ft.padding.symmetric(horizontal=10),
        visible=True,
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.SETTINGS_OUTLINED, color=theme.TEXT_SEC, size=20),
                settings_label_ctrl,
            ],
            spacing=10,
        ),
        on_click=_open_settings,
        ink=True,
    )

    # ── Account button (บัญชี — ทุก user เห็น) ───────────────────────────────
    account_label_ctrl = ft.Text("บัญชี", color=theme.TEXT_SEC, size=14, expand=True)

    def _open_account(e=None):
        navigate("account")

    account_btn = ft.Container(
        height=42,
        border_radius=8,
        bgcolor="transparent",
        padding=ft.padding.symmetric(horizontal=10),
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.PERSON_OUTLINED, color=theme.TEXT_SEC, size=20),
                account_label_ctrl,
            ],
            spacing=10,
        ),
        on_click=_open_account,
        ink=True,
    )

    # ── Logout button (shown only when on_logout callback is provided) ─────────
    logout_label_ctrl = ft.Text("ออกจากระบบ", color="#EF4444", size=14, expand=True)

    def _do_logout(e=None):
        if on_logout:
            on_logout()

    logout_btn = ft.Container(
        height=42,
        border_radius=8,
        bgcolor="transparent",
        padding=ft.padding.symmetric(horizontal=10),
        visible=on_logout is not None,
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.LOGOUT, color="#EF4444", size=20),
                logout_label_ctrl,
            ],
            spacing=10,
        ),
        on_click=_do_logout,
        ink=True,
    )

    # ── Search bar ────────────────────────────────────────────────
    search_results_col = ft.Column(controls=[], spacing=2, visible=False)

    def _do_search(query: str) -> None:
        if not query.strip():
            search_results_col.controls = []
            search_results_col.visible = False
            safe_update(search_results_col)
            return
        try:
            results = api.search_tasks(query)
        except Exception:
            results = []

        def _make_result_btn(t):
            from app.utils.theme import status_color
            dot_color = status_color(t.get("status", "Pending"))
            return ft.Container(
                border_radius=6,
                padding=ft.padding.symmetric(horizontal=8, vertical=6),
                bgcolor="transparent",
                ink=True,
                on_click=lambda e, tid=t["id"]: _on_search_select(tid),
                content=ft.Row(
                    controls=[
                        ft.Container(
                            width=6, height=6, border_radius=3,
                            bgcolor=dot_color,
                        ),
                        ft.Text(
                            t["title"], size=12, color=theme.TEXT_PRI,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                            expand=True,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        if results:
            search_results_col.controls = [_make_result_btn(t) for t in results]
        else:
            search_results_col.controls = [
                ft.Text("ไม่พบผลลัพธ์", size=12, color=theme.TEXT_SEC,
                        italic=True,
                        text_align=ft.TextAlign.CENTER)
            ]
        search_results_col.visible = True
        safe_update(search_results_col)

    def _on_search_select(task_id: int) -> None:
        tf_search.value = ""
        search_results_col.controls = []
        search_results_col.visible = False
        safe_update(search_results_col)
        _search_target["value"] = task_id
        if active_key["value"] == "task":
            # Already on task view — reload it with the highlight
            content_area.controls = [get_view("task")]
            active_key["value"] = "task"   # keep active
            content_area.update()
        else:
            navigate("task")

    _search_debounce: dict = {"timer": None}

    def _on_search_change(e):
        query = e.control.value or ""
        if _search_debounce["timer"]:
            _search_debounce["timer"].cancel()
        t = threading.Timer(0.3, _do_search, args=[query])
        _search_debounce["timer"] = t
        t.start()

    tf_search = ft.TextField(
        hint_text="ค้นหางาน... (Ctrl+F)",
        hint_style=ft.TextStyle(size=12, color=theme.TEXT_SEC),
        text_size=12,
        height=36,
        border_radius=8,
        border_color=theme.BORDER,
        focused_border_color=theme.ACCENT,
        bgcolor=theme.BG_INPUT if hasattr(theme, "BG_INPUT") else "#F8FAFC",
        content_padding=ft.padding.symmetric(horizontal=10, vertical=4),
        prefix_icon=ft.Icons.SEARCH,
        on_change=_on_search_change,
    )

    search_container = ft.Column(
        controls=[
            tf_search,
            ft.Container(
                content=search_results_col,
                bgcolor=theme.BG_CARD,
                border=ft.border.all(1, theme.BORDER),
                border_radius=8,
                padding=ft.padding.symmetric(vertical=4),
                visible=True,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            ),
        ],
        spacing=4,
        visible=True,
    )

    # ── Sidebar ───────────────────────────────────────────────────
    logo = ft.Row(
        controls=[
            bolt_icon_ctrl,
            logo_text_ctrl,
            ft.Container(expand=True),   # spacer — pushes toggle to the right
            toggle_btn_ctrl,
        ],
        spacing=4,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
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
                ft.Divider(height=16, color=theme.BORDER),
                search_container,
                ft.Divider(height=8, color=theme.BORDER),
                nav_col,
                ft.Container(expand=True),          # spacer — push settings to bottom
                ft.Divider(height=1, color=theme.BORDER),
                settings_btn,
                account_btn,
                logout_btn,
            ],
            spacing=0,
            expand=True,
        ),
    )

    # ── Initial content + badge ───────────────────────────────────
    content_area.controls = [get_view("dashboard")]
    _refresh_task_badge()

    return ft.Row(
        controls=[sidebar, content_area],
        spacing=0,
        expand=True,
    )

