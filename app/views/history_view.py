# -*- coding: utf-8 -*-
"""
HistoryView — Phase 6: Work History & Search UI
Features:
  - Timeline of all WorkHistory entries (latest first)
  - Search by task title or detail keyword
  - Filter by action type  (created / status_changed / assigned / commented / etc.)
  - Filter by actor (member)
  - Filter by date range
  - Color-coded action badges
  - Pagination (50 entries per page)
Flet 0.80.x — function-based
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

import flet as ft

from app.utils.theme import (
    BG_DARK, BG_CARD, BG_INPUT, BG_SIDEBAR,
    ACCENT, ACCENT2,
    TEXT_PRI, TEXT_SEC, BORDER,
    COLOR_DONE, COLOR_OVERDUE, COLOR_PENDING,
    COLOR_IN_PROGRESS, COLOR_REVIEW, COLOR_CANCELLED,
)

from app.utils.date_helpers import parse_date_field
from app.utils.logger import get_logger
from app.utils.ui_helpers import show_snack, safe_update
logger = get_logger(__name__)

ALL_OPT = "ทั้งหมด"
PAGE_SIZE = 50

# ── Action badge colours ───────────────────────────────────────────────────────
_ACTION_META: dict[str, tuple[str, str]] = {
    # (display_label, colour)
    "created":          ("สร้างงาน",        ACCENT),
    "status_changed":   ("เปลี่ยนสถานะ",    COLOR_IN_PROGRESS),
    "assigned":         ("มอบหมาย",         "#AB47BC"),
    "commented":        ("ความคิดเห็น",     COLOR_PENDING),
    "updated_title":    ("แก้ไขชื่อ",       ACCENT2),
    "updated_description": ("แก้ไขรายละเอียด", ACCENT2),
    "updated_priority": ("เปลี่ยน Priority", COLOR_REVIEW),
    "updated_due_date": ("เปลี่ยนวันกำหนด", COLOR_OVERDUE),
    "deleted":          ("ลบงาน",           COLOR_OVERDUE),
}

def _action_label(action: str) -> str:
    return _ACTION_META.get(action, (action, TEXT_SEC))[0]

def _action_color(action: str) -> str:
    return _ACTION_META.get(action, (action, TEXT_SEC))[1]

def _fmt_dt(dt: datetime) -> str:
    return dt.strftime("%d/%m/%Y %H:%M") if dt else "—"

def _relative_time(dt: datetime) -> str:
    """Return human-readable relative time string."""
    if not dt:
        return ""
    delta = datetime.now(timezone.utc).replace(tzinfo=None) - dt
    secs  = int(delta.total_seconds())
    if secs < 60:
        return "เมื่อกี้"
    if secs < 3600:
        return f"{secs // 60} นาทีที่แล้ว"
    if secs < 86400:
        return f"{secs // 3600} ชั่วโมงที่แล้ว"
    if secs < 86400 * 7:
        return f"{secs // 86400} วันที่แล้ว"
    return _fmt_dt(dt)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY
# ══════════════════════════════════════════════════════════════════════════════
def build_history_view(api, page: ft.Page) -> ft.Control:

    # ── State ──────────────────────────────────────────────────────
    state = {
        "search":        "",
        "filter_action": ALL_OPT,
        "filter_actor":  ALL_OPT,
        "date_from":     None,
        "date_to":       None,
        "page_num":      0,     # 0-indexed
    }

    # ── Mutable containers ─────────────────────────────────────────
    list_col    = ft.Column(spacing=6, expand=True, scroll=ft.ScrollMode.AUTO)
    pager_row   = ft.Row(spacing=8,
                         vertical_alignment=ft.CrossAxisAlignment.CENTER)
    count_text  = ft.Text("", size=12, color=TEXT_SEC)

    # ══════════════════════════════════════════════════════════════
    #  DATA HELPERS
    # ══════════════════════════════════════════════════════════════
    def _fetch_entries() -> List[dict]:
        actor_val = state["filter_actor"]
        actor_id  = None
        if actor_val != ALL_OPT:
            try:
                actor_id = int(actor_val)
            except (ValueError, TypeError):
                pass

        date_from_str = None
        date_to_str   = None
        if state["date_from"]:
            date_from_str = state["date_from"].strftime("%Y-%m-%d")
        if state["date_to"]:
            date_to_str = state["date_to"].strftime("%Y-%m-%d")

        return api.get_history(
            search=state["search"],
            action=state["filter_action"] if state["filter_action"] != ALL_OPT else "",
            actor_id=actor_id,
            date_from=date_from_str,
            date_to=date_to_str,
            page=state["page_num"],
        )

    # ══════════════════════════════════════════════════════════════
    #  ROW BUILDER
    # ══════════════════════════════════════════════════════════════
    def _entry_row(e: dict) -> ft.Container:
        action     = e.get("action", "")
        action_col = _action_color(action)
        action_lbl = _action_label(action)

        # Avatar / actor
        actor_name = e.get("actor_name", "ระบบ") or "ระบบ"
        actor_init = actor_name[0].upper() if actor_name else "S"

        # Parse created_at
        created_at_raw = e.get("created_at")
        if created_at_raw:
            try:
                created_at = datetime.fromisoformat(created_at_raw)
            except (ValueError, TypeError):
                created_at = None
        else:
            created_at = None

        avatar = ft.Container(
            width=34, height=34, border_radius=17,
            bgcolor=ACCENT + "33",
            content=ft.Text(actor_init, size=13,
                            weight=ft.FontWeight.BOLD,
                            color=ACCENT,
                            text_align=ft.TextAlign.CENTER),
            alignment=ft.Alignment(0, 0),
        )

        # Action badge
        badge = ft.Container(
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            border_radius=10,
            bgcolor=action_col + "22",
            border=ft.border.all(1, action_col + "55"),
            content=ft.Text(action_lbl, size=10, color=action_col,
                            weight=ft.FontWeight.W_500),
        )

        # Task title chip
        task_id    = e.get("task_id")
        old_value  = e.get("old_value")
        new_value  = e.get("new_value")
        detail_val = e.get("detail", "")

        task_chip = ft.Container(
            visible=task_id is not None,
            padding=ft.padding.symmetric(horizontal=7, vertical=2),
            border_radius=6,
            bgcolor=BG_INPUT,
            content=ft.Text(
                f"Task #{task_id}" if task_id else "",
                size=11, color=TEXT_SEC,
                no_wrap=True,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        )

        # Detail text
        detail_txt = ft.Text(
            detail_val or "",
            size=12, color=TEXT_PRI,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        # Old→New value
        change_row_controls = []
        if old_value and new_value:
            change_row_controls = [
                ft.Text(str(old_value)[:30], size=10,
                        color=TEXT_SEC,
                        style=ft.TextStyle(
                            decoration=ft.TextDecoration.LINE_THROUGH,
                        )),
                ft.Icon(ft.Icons.ARROW_FORWARD, size=12, color=TEXT_SEC),
                ft.Text(str(new_value)[:30], size=10, color=ACCENT2),
            ]
        change_row = ft.Row(
            controls=change_row_controls,
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            visible=len(change_row_controls) > 0,
        )

        # Time
        time_txt = ft.Text(
            _relative_time(created_at),
            size=10, color=TEXT_SEC,
            tooltip=_fmt_dt(created_at),
        )

        right_col = ft.Column(
            controls=[
                ft.Row(
                    controls=[badge, task_chip],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    wrap=True,
                ),
                detail_txt,
                change_row,
                ft.Row(
                    controls=[
                        ft.Text(actor_name, size=11, color=TEXT_SEC),
                        ft.Text("·", size=11, color=TEXT_SEC),
                        time_txt,
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=4,
            expand=True,
        )

        return ft.Container(
            bgcolor=BG_CARD,
            border_radius=8,
            border=ft.border.only(left=ft.BorderSide(3, action_col)),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            content=ft.Row(
                controls=[avatar, right_col],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )

    # ══════════════════════════════════════════════════════════════
    #  REBUILD
    # ══════════════════════════════════════════════════════════════
    def _rebuild():
        try:
            page_entries = _fetch_entries()
        except Exception as ex:
            logger.error(f"history fetch error: {ex}")
            page_entries = []

        cur_page = state["page_num"]
        total    = len(page_entries)

        count_text.value = (
            f"หน้า {cur_page + 1} — {total} รายการ"
        ) if total > 0 else "ไม่พบรายการ"

        list_col.controls = (
            [_entry_row(e) for e in page_entries]
            if page_entries
            else [ft.Text("ไม่พบประวัติที่ตรงกัน", size=13, color=TEXT_SEC)]
        )

        # Pager
        btn_prev = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            icon_color=TEXT_SEC if cur_page == 0 else ACCENT,
            icon_size=20,
            disabled=cur_page == 0,
            on_click=lambda e: _go_page(cur_page - 1),
        )
        has_next = total >= PAGE_SIZE
        btn_next = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            icon_color=TEXT_SEC if not has_next else ACCENT,
            icon_size=20,
            disabled=not has_next,
            on_click=lambda e: _go_page(cur_page + 1),
        )
        pager_row.controls = [
            btn_prev,
            ft.Text(f"หน้า {cur_page + 1}", size=12, color=TEXT_SEC),
            btn_next,
        ]

        safe_update(count_text)
        safe_update(list_col)
        safe_update(pager_row)

    def _go_page(n: int):
        state["page_num"] = max(0, n)
        _rebuild()

    def _on_search(e):
        state["search"]   = e.control.value or ""
        state["page_num"] = 0
        _rebuild()

    def _on_filter_action(val):
        state["filter_action"] = val
        state["page_num"]      = 0
        _rebuild()

    def _on_filter_actor(val):
        state["filter_actor"] = val
        state["page_num"]     = 0
        _rebuild()

    def _apply_dates():
        state["date_from"]  = parse_date_field(tf_from.value or "")
        state["date_to"]    = parse_date_field(tf_to.value or "")
        state["page_num"]   = 0
        _rebuild()

    def _clear_filters(e):
        state.update({
            "search": "", "filter_action": ALL_OPT,
            "filter_actor": ALL_OPT, "date_from": None,
            "date_to": None, "page_num": 0,
        })
        tf_search.value   = ""
        dd_action.value   = ALL_OPT
        dd_actor.value    = ALL_OPT
        tf_from.value     = ""
        tf_to.value       = ""
        for ctrl in [tf_search, dd_action, dd_actor, tf_from, tf_to]:
            safe_update(ctrl)
        _rebuild()

    # ══════════════════════════════════════════════════════════════
    #  FILTER CONTROLS
    # ══════════════════════════════════════════════════════════════
    # Collect distinct actions from API
    def _action_options():
        try:
            actions = sorted(api.get_history_actions())
        except Exception:
            actions = []
        return [ft.dropdown.Option(ALL_OPT)] + [
            ft.dropdown.Option(key=a, text=_action_label(a)) for a in actions
        ]

    def _actor_options():
        try:
            users = api.get_users()
        except Exception:
            users = []
        return [ft.dropdown.Option(ALL_OPT)] + [
            ft.dropdown.Option(key=str(u["id"]), text=u["name"]) for u in users
        ]

    tf_search = ft.TextField(
        hint_text="ค้นหา... (ชื่องาน / รายละเอียด)",
        width=220,
        height=40,
        border_color=BORDER, focused_border_color=ACCENT,
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
        text_size=12,
        prefix_icon=ft.Icons.SEARCH,
        on_change=_on_search,
    )

    dd_action = ft.Dropdown(
        label="ประเภท", width=160,
        options=_action_options(), value=ALL_OPT,
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
        text_size=12,
        on_select=lambda e: _on_filter_action(e.control.value),
    )

    dd_actor = ft.Dropdown(
        label="ผู้ดำเนินการ", width=150,
        options=_actor_options(), value=ALL_OPT,
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
        text_size=12,
        on_select=lambda e: _on_filter_actor(e.control.value),
    )

    tf_from = ft.TextField(
        label="ตั้งแต่ (dd/mm/yyyy)", width=160,
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC, size=10),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
        text_size=12,
        on_submit=lambda e: _apply_dates(),
        on_blur=lambda e: _apply_dates(),
    )

    tf_to = ft.TextField(
        label="ถึง (dd/mm/yyyy)", width=160,
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC, size=10),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
        text_size=12,
        on_submit=lambda e: _apply_dates(),
        on_blur=lambda e: _apply_dates(),
    )

    # ── Initial render ────────────────────────────────────────────
    _rebuild()

    # ══════════════════════════════════════════════════════════════
    #  TOP BAR
    # ══════════════════════════════════════════════════════════════
    top_bar = ft.Row(
        controls=[
            ft.Column(
                controls=[
                    ft.Text("ประวัติการทำงาน", size=24,
                            weight=ft.FontWeight.BOLD, color=TEXT_PRI),
                    ft.Text("บันทึกการเปลี่ยนแปลงทั้งหมดในระบบ",
                            size=13, color=TEXT_SEC),
                ],
                spacing=2,
            ),
            ft.IconButton(
                icon=ft.Icons.REFRESH,
                icon_color=TEXT_SEC, icon_size=20,
                tooltip="รีเฟรช",
                on_click=lambda e: _rebuild(),
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    filter_bar = ft.Row(
        controls=[
            ft.Icon(ft.Icons.FILTER_LIST, color=TEXT_SEC, size=18),
            tf_search,
            dd_action,
            dd_actor,
            tf_from,
            tf_to,
            ft.TextButton(
                "ล้าง",
                style=ft.ButtonStyle(color=TEXT_SEC),
                on_click=_clear_filters,
            ),
        ],
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        wrap=True,
    )

    footer = ft.Row(
        controls=[count_text, ft.Container(expand=True), pager_row],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    return ft.Container(
        expand=True,
        bgcolor=BG_DARK,
        padding=ft.padding.all(24),
        content=ft.Column(
            controls=[
                top_bar,
                ft.Divider(height=12, color=BORDER),
                filter_bar,
                ft.Divider(height=8, color=BORDER),
                list_col,
                ft.Divider(height=8, color=BORDER),
                footer,
            ],
            spacing=0,
            expand=True,
        ),
    )
