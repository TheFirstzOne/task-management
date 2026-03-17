# -*- coding: utf-8 -*-
"""
CalendarView — Phase 4: Calendar Planning UI
Features:
  - Monthly calendar grid  (navigate prev / next month)
  - Task dots per day  coloured by priority
  - Click a day → side panel lists tasks due that day
  - Filter bar: team / member / status / priority
  - Today highlight  |  overdue cells tinted red
Flet 0.80.x — function-based
"""

from __future__ import annotations
import calendar
from datetime import date, datetime, timedelta
from typing import Optional

import flet as ft
from sqlalchemy.orm import Session

from app.services.task_service import TaskService
from app.services.team_service import TeamService
from app.models.task import Task, TaskStatus, TaskPriority
from app.utils.theme import (
    BG_DARK, BG_CARD, BG_INPUT,
    ACCENT, ACCENT2, TEXT_PRI, TEXT_SEC, BORDER,
    COLOR_URGENT, COLOR_DONE,
    status_color, priority_color,
)
from app.utils.date_helpers import format_date
from app.utils.logger import get_logger
from app.utils.ui_helpers import show_snack, safe_update
logger = get_logger(__name__)

# ── Thai month names ──────────────────────────────────────────────────────────
THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน",
    "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม",
    "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]
THAI_DAYS_SHORT = ["จ", "อ", "พ", "พฤ", "ศ", "ส", "อา"]   # Mon-Sun

# ── Priority colour map (compact) ────────────────────────────────────────────
_PRIO_DOT = {
    "Low":    "#4CAF50",
    "Medium": "#FFC107",
    "High":   "#FF9800",
    "Urgent": "#FF5252",
}
ALL_OPT = "ทั้งหมด"


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY
# ══════════════════════════════════════════════════════════════════════════════
def build_calendar_view(db: Session, page: ft.Page) -> ft.Control:
    task_svc = TaskService(db)
    team_svc = TeamService(db)

    today = date.today()

    # ── State ──────────────────────────────────────────────────────
    state = {
        "year":         today.year,
        "month":        today.month,
        "selected_day": None,          # date | None
        "filter_team":   ALL_OPT,
        "filter_member": ALL_OPT,
        "filter_status": ALL_OPT,
        "filter_prio":   ALL_OPT,
    }

    # ── Layout containers (mutable) ────────────────────────────────
    cal_grid      = ft.Column(spacing=4)
    header_title  = ft.Text("", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRI)
    day_panel     = ft.Container(
        visible=False,
        width=300,
        bgcolor=BG_CARD,
        border=ft.border.only(left=ft.BorderSide(1, BORDER)),
        padding=ft.padding.all(16),
    )

    # ── Filter dropdowns ───────────────────────────────────────────
    def _team_options():
        teams = team_svc.get_all_teams()
        return [ft.dropdown.Option(ALL_OPT)] + [
            ft.dropdown.Option(key=str(t.id), text=t.name) for t in teams]

    def _member_options(team_key: str):
        opts = [ft.dropdown.Option(ALL_OPT)]
        if team_key and team_key != ALL_OPT:
            try:
                tid = int(team_key)
                members = team_svc.user_repo.get_by_team(tid, active_only=True)
                opts += [ft.dropdown.Option(key=str(m.id), text=m.name) for m in members]
            except (ValueError, TypeError):
                pass
        else:
            for u in team_svc.user_repo.get_all(active_only=True):
                opts.append(ft.dropdown.Option(key=str(u.id), text=u.name))
        return opts

    dd_team = ft.Dropdown(
        label="ทีม", width=150,
        options=_team_options(), value=ALL_OPT,
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
        text_size=12,
        on_select=lambda e: _on_filter_team(e.control.value),
    )
    dd_member = ft.Dropdown(
        label="สมาชิก", width=150,
        options=_member_options(ALL_OPT), value=ALL_OPT,
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
        text_size=12,
        on_select=lambda e: _on_filter("filter_member", e.control.value),
    )
    dd_status = ft.Dropdown(
        label="สถานะ", width=140,
        options=[ft.dropdown.Option(ALL_OPT)] + [
            ft.dropdown.Option(s.value) for s in TaskStatus],
        value=ALL_OPT,
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
        text_size=12,
        on_select=lambda e: _on_filter("filter_status", e.control.value),
    )
    dd_prio = ft.Dropdown(
        label="Priority", width=130,
        options=[ft.dropdown.Option(ALL_OPT)] + [
            ft.dropdown.Option(p.value) for p in TaskPriority],
        value=ALL_OPT,
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
        text_size=12,
        on_select=lambda e: _on_filter("filter_prio", e.control.value),
    )

    def _on_filter_team(val):
        state["filter_team"]   = val
        state["filter_member"] = ALL_OPT
        dd_member.options = _member_options(val)
        dd_member.value   = ALL_OPT
        try:
            dd_member.update()
        except Exception as e:
            logger.warning("load failed: %s", e, exc_info=True)
        _rebuild_calendar()

    def _on_filter(key: str, val):
        state[key] = val
        _rebuild_calendar()

    # ══════════════════════════════════════════════════════════════
    #  DATA HELPERS
    # ══════════════════════════════════════════════════════════════
    def _get_filtered_tasks() -> list[Task]:
        tasks = task_svc.get_all_tasks()
        ft_team   = state["filter_team"]
        ft_member = state["filter_member"]
        ft_status = state["filter_status"]
        ft_prio   = state["filter_prio"]

        if ft_team != ALL_OPT:
            try:
                tid = int(ft_team)
                tasks = [t for t in tasks
                         if t.team_id == tid
                         or (t.assignee and t.assignee.team_id == tid)]
            except (ValueError, TypeError):
                pass

        if ft_member != ALL_OPT:
            try:
                mid = int(ft_member)
                tasks = [t for t in tasks if t.assignee_id == mid]
            except (ValueError, TypeError):
                pass

        if ft_status != ALL_OPT:
            tasks = [t for t in tasks if t.status.value == ft_status]
        if ft_prio != ALL_OPT:
            tasks = [t for t in tasks if t.priority.value == ft_prio]
        return tasks

    def _tasks_by_day(tasks: list[Task]) -> dict[date, list[Task]]:
        """Group tasks by their due_date day."""
        by_day: dict[date, list[Task]] = {}
        for t in tasks:
            if t.due_date:
                d = t.due_date.date()
                by_day.setdefault(d, []).append(t)
        return by_day

    # ══════════════════════════════════════════════════════════════
    #  DAY DETAIL PANEL
    # ══════════════════════════════════════════════════════════════
    def _build_day_panel(d: date, tasks: list[Task]) -> ft.Column:
        title = ft.Text(
            f"{d.day} {THAI_MONTHS[d.month]} {d.year + 543}",
            size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRI,
        )

        def _task_card(t: Task) -> ft.Container:
            sc = status_color(t.status.value)
            pc = priority_color(t.priority.value)
            return ft.Container(
                bgcolor=BG_INPUT,
                border_radius=8,
                border=ft.border.only(left=ft.BorderSide(3, pc)),
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                content=ft.Column(
                    controls=[
                        ft.Text(t.title, size=13,
                                weight=ft.FontWeight.W_500, color=TEXT_PRI,
                                no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Row(
                            controls=[
                                ft.Container(
                                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                    border_radius=10,
                                    bgcolor=sc + "22",
                                    content=ft.Text(t.status.value, size=10, color=sc),
                                ),
                                ft.Text(
                                    t.assignee.name if t.assignee else "—",
                                    size=11, color=TEXT_SEC,
                                ),
                            ],
                            spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=4,
                ),
            )

        rows = [_task_card(t) for t in tasks] if tasks else [
            ft.Text("ไม่มีงานวันนี้", size=13, color=TEXT_SEC),
        ]

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        title,
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_color=TEXT_SEC, icon_size=18,
                            on_click=lambda e: _close_day_panel(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(height=1, color=BORDER),
                ft.Text(f"{len(tasks)} งาน", size=12, color=TEXT_SEC),
                ft.Column(controls=rows, spacing=8,
                          scroll=ft.ScrollMode.AUTO, expand=True),
            ],
            spacing=10,
            expand=True,
        )

    def _close_day_panel():
        state["selected_day"] = None
        day_panel.visible = False
        try:
            day_panel.update()
        except Exception as e:
            logger.warning("load failed: %s", e, exc_info=True)
        _rebuild_calendar()

    # ══════════════════════════════════════════════════════════════
    #  CALENDAR GRID
    # ══════════════════════════════════════════════════════════════
    def _build_day_cell(d: Optional[date], day_tasks: list[Task],
                        is_today: bool, is_selected: bool,
                        is_other_month: bool) -> ft.Container:
        if d is None:
            return ft.Container(expand=True)

        has_overdue = any(
            t.due_date and t.due_date.date() < today
            and t.status not in (TaskStatus.DONE, TaskStatus.CANCELLED)
            for t in day_tasks
        )

        # Background colour
        if is_selected:
            bg = ACCENT + "33"
            border_col = ACCENT
        elif is_today:
            bg = ACCENT + "18"
            border_col = ACCENT + "66"
        elif has_overdue:
            bg = COLOR_URGENT + "11"
            border_col = COLOR_URGENT + "44"
        else:
            bg = BG_CARD
            border_col = BORDER

        # Day number text
        day_txt_color = (
            ACCENT       if is_today     else
            TEXT_SEC     if is_other_month else
            TEXT_PRI
        )

        # Priority dots (max 4)
        dots = ft.Row(
            controls=[
                ft.Container(
                    width=6, height=6, border_radius=3,
                    bgcolor=_PRIO_DOT.get(t.priority.value, TEXT_SEC),
                )
                for t in day_tasks[:4]
            ],
            spacing=2, wrap=True,
        )

        # Task count badge
        badge = ft.Container(
            visible=len(day_tasks) > 0,
            width=16, height=16, border_radius=8,
            bgcolor=ACCENT + "44",
            content=ft.Text(
                str(len(day_tasks)), size=9,
                color=ACCENT, text_align=ft.TextAlign.CENTER,
            ),
            alignment=ft.alignment.Alignment.CENTER,
        )

        return ft.Container(
            expand=True,
            bgcolor=bg,
            border_radius=6,
            border=ft.border.all(1, border_col),
            padding=ft.padding.only(left=6, top=4, right=4, bottom=4),
            ink=True,
            on_click=lambda e, _d=d: _on_day_click(_d),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(str(d.day), size=13,
                                    weight=ft.FontWeight.BOLD if is_today else ft.FontWeight.NORMAL,
                                    color=day_txt_color),
                            badge,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    dots,
                ],
                spacing=4,
            ),
        )

    def _build_grid():
        year  = state["year"]
        month = state["month"]

        # Update header
        header_title.value = f"{THAI_MONTHS[month]}  {year + 543}"
        safe_update(header_title)

        tasks    = _get_filtered_tasks()
        by_day   = _tasks_by_day(tasks)
        sel_day  = state["selected_day"]

        # Weekday header row
        day_headers = ft.Row(
            controls=[
                ft.Container(
                    expand=True,
                    content=ft.Text(
                        d, size=12, color=TEXT_SEC,
                        text_align=ft.TextAlign.CENTER,
                        weight=ft.FontWeight.W_500,
                    ),
                )
                for d in THAI_DAYS_SHORT
            ],
            spacing=4,
        )

        # Calendar days
        cal = calendar.Calendar(firstweekday=0)   # Monday first
        month_weeks = cal.monthdatescalendar(year, month)

        week_rows = []
        for week in month_weeks:
            cells = []
            for d in week:
                is_cur_month = (d.month == month)
                day_tasks = by_day.get(d, [])
                cell = _build_day_cell(
                    d=d,
                    day_tasks=day_tasks,
                    is_today=(d == today),
                    is_selected=(d == sel_day),
                    is_other_month=not is_cur_month,
                )
                cells.append(cell)
            week_rows.append(ft.Row(controls=cells, spacing=4, expand=True))

        cal_grid.controls = [day_headers] + week_rows
        safe_update(cal_grid)

    def _rebuild_calendar():
        _build_grid()
        # If day panel open, refresh it
        if state["selected_day"]:
            tasks   = _get_filtered_tasks()
            by_day  = _tasks_by_day(tasks)
            d_tasks = by_day.get(state["selected_day"], [])
            day_panel.content = _build_day_panel(state["selected_day"], d_tasks)
            try:
                day_panel.update()
            except Exception as e:
                logger.warning("load failed: %s", e, exc_info=True)

    def _on_day_click(d: date):
        if state["selected_day"] == d:
            _close_day_panel()
            return
        state["selected_day"] = d
        tasks   = _get_filtered_tasks()
        by_day  = _tasks_by_day(tasks)
        d_tasks = by_day.get(d, [])
        day_panel.content = _build_day_panel(d, d_tasks)
        day_panel.visible = True
        try:
            day_panel.update()
        except Exception as e:
            logger.warning("load failed: %s", e, exc_info=True)
        _build_grid()   # re-render grid to highlight selected

    # Navigation
    def _prev_month(e):
        m, y = state["month"] - 1, state["year"]
        if m < 1:
            m, y = 12, y - 1
        state["month"], state["year"] = m, y
        _rebuild_calendar()

    def _next_month(e):
        m, y = state["month"] + 1, state["year"]
        if m > 12:
            m, y = 1, y + 1
        state["month"], state["year"] = m, y
        _rebuild_calendar()

    def _go_today(e):
        state["year"], state["month"] = today.year, today.month
        _rebuild_calendar()

    # ── Initial render ────────────────────────────────────────────
    _build_grid()

    # ══════════════════════════════════════════════════════════════
    #  LEGEND
    # ══════════════════════════════════════════════════════════════
    legend = ft.Row(
        controls=[
            ft.Text("Priority:", size=11, color=TEXT_SEC),
            *[
                ft.Row(
                    controls=[
                        ft.Container(width=8, height=8, border_radius=4,
                                     bgcolor=col),
                        ft.Text(lbl, size=11, color=TEXT_SEC),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
                for lbl, col in _PRIO_DOT.items()
            ],
            ft.Container(width=16),
            ft.Container(width=10, height=10, border_radius=3,
                         bgcolor=COLOR_URGENT + "22",
                         border=ft.border.all(1, COLOR_URGENT + "44")),
            ft.Text("มีงานเกินกำหนด", size=11, color=TEXT_SEC),
            ft.Container(width=10, height=10, border_radius=3,
                         bgcolor=ACCENT + "18",
                         border=ft.border.all(1, ACCENT + "66")),
            ft.Text("วันนี้", size=11, color=TEXT_SEC),
        ],
        spacing=8,
        wrap=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # ══════════════════════════════════════════════════════════════
    #  TOP BAR
    # ══════════════════════════════════════════════════════════════
    top_bar = ft.Row(
        controls=[
            ft.Column(
                controls=[
                    ft.Text("ปฏิทินแผนงาน", size=24,
                            weight=ft.FontWeight.BOLD, color=TEXT_PRI),
                    ft.Text("ดูงานตามวันที่ครบกำหนด", size=13, color=TEXT_SEC),
                ],
                spacing=2,
            ),
            ft.Row(
                controls=[
                    ft.TextButton(
                        "วันนี้",
                        style=ft.ButtonStyle(color=ACCENT),
                        on_click=_go_today,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CHEVRON_LEFT,
                        icon_color=TEXT_SEC, icon_size=22,
                        tooltip="เดือนก่อน",
                        on_click=_prev_month,
                    ),
                    header_title,
                    ft.IconButton(
                        icon=ft.Icons.CHEVRON_RIGHT,
                        icon_color=TEXT_SEC, icon_size=22,
                        tooltip="เดือนถัดไป",
                        on_click=_next_month,
                    ),
                ],
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    filter_bar = ft.Row(
        controls=[dd_team, dd_member, dd_status, dd_prio],
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        wrap=True,
    )

    left_pane = ft.Container(
        expand=True,
        bgcolor=BG_DARK,
        padding=ft.padding.all(24),
        content=ft.Column(
            controls=[
                top_bar,
                ft.Divider(height=12, color=BORDER),
                filter_bar,
                ft.Divider(height=12, color=BORDER),
                ft.Container(expand=True, content=cal_grid),
                ft.Divider(height=8, color=BORDER),
                legend,
            ],
            spacing=0,
            expand=True,
        ),
    )

    # ══════════════════════════════════════════════════════════════
    #  ROOT LAYOUT
    # ══════════════════════════════════════════════════════════════
    return ft.Container(
        expand=True,
        bgcolor=BG_DARK,
        content=ft.Row(
            controls=[left_pane, day_panel],
            spacing=0,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
    )