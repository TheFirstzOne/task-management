# -*- coding: utf-8 -*-
"""
TaskView — Phase 21: Task Management UI (API-backed)
Features:
  - Task list with filter bar (status / priority / assignee / search)
  - Create / Edit Task dialog (all fields)
  - Task detail side-panel (subtasks + comment timeline)
  - Status change chip, assign, delete
  - Deadline visual indicator (overdue / near-due)
Flet 0.80.x  —  function-based
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional

import flet as ft

from app.utils.theme import (
    BG_DARK, BG_CARD, BG_INPUT,
    ACCENT, ACCENT2, TEXT_PRI, TEXT_SEC, BORDER,
    COLOR_URGENT, COLOR_DONE,
    status_color, priority_color,
)
from app.utils.date_helpers import format_date, is_overdue, days_until, parse_date_input
from app.utils.exceptions import (
    ValidationError, NotFoundError,
    CircularDependencyError, SelfDependencyError,
)
from app.utils.logger import get_logger
from app.utils.ui_helpers import show_snack, safe_update, safe_page_update
from app.utils import shortcut_registry
logger = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
STATUS_LIST      = ["Pending", "In Progress", "Review", "Done", "Cancelled"]
PRIORITY_LIST    = ["Urgent", "High", "Medium", "Low"]
COLOR_NEAR       = "#FF9800"   # due within 2 days
ALL_FILTER       = "ทั้งหมด"  # filter chip "show all" value
NO_SELECTION     = "none"      # dropdown "not selected" key
DEFAULT_PRIORITY = "Medium"    # default task priority on new dialog


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _chip(label: str, color: str) -> ft.Container:
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
        border_radius=20,
        bgcolor=color,
        content=ft.Text(label, size=11, color="#FFFFFF", weight=ft.FontWeight.W_500),
    )

def _status_chip(status: str)     -> ft.Container: return _chip(status,   status_color(status))
def _priority_chip(priority: str) -> ft.Container: return _chip(priority, priority_color(priority))

def _due_label(due: Optional[datetime]) -> ft.Text:
    if not due:
        return ft.Text("", size=11)
    d = days_until(due)
    if d is None:
        return ft.Text("", size=11)
    if d < 0:
        return ft.Text(f"เกิน {-d} วัน", size=11, color=COLOR_URGENT,
                       weight=ft.FontWeight.W_500)
    if d == 0:
        return ft.Text("ครบกำหนดวันนี้", size=11, color=COLOR_NEAR,
                       weight=ft.FontWeight.W_500)
    if d <= 2:
        return ft.Text(f"อีก {d} วัน", size=11, color=COLOR_NEAR)
    return ft.Text(f"{format_date(due)}", size=11, color=TEXT_SEC)


def _parse_dt(val) -> Optional[datetime]:
    """Parse ISO datetime string or return None."""
    if not val:
        return None
    try:
        return datetime.fromisoformat(val)
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY
# ══════════════════════════════════════════════════════════════════════════════
def build_task_view(api, page: ft.Page,
                    highlight_task_id: Optional[int] = None) -> ft.Control:

    # ── State ──────────────────────────────────────────────────────
    selected_task_id: dict = {"value": None}
    filter_status:    dict = {"value": ALL_FILTER}
    filter_priority:  dict = {"value": ALL_FILTER}
    search_query:     dict = {"value": ""}
    sort_order:       dict = {"value": "สร้างล่าสุด"}

    SORT_OPTIONS = ["สร้างล่าสุด", "เก่าสุด", "ครบกำหนด", "Priority", "ชื่อ"]
    PRIO_ORDER   = {"Urgent": 0, "High": 1, "Medium": 2, "Low": 3}

    # ── Layout refs ────────────────────────────────────────────────
    task_list_col  = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)
    _filter_loading = ft.Row(
        controls=[
            ft.ProgressRing(width=16, height=16, stroke_width=2, color=ACCENT),
            ft.Text("กำลังกรอง...", size=12, color=TEXT_SEC),
        ],
        spacing=6, visible=False,
    )
    detail_panel   = ft.Container(
        visible=False,
        width=340,
        bgcolor=BG_CARD,
        border=ft.border.only(left=ft.BorderSide(1, BORDER)),
        expand=False,
    )

    # ══════════════════════════════════════════════════════════════
    #  CREATE / EDIT DIALOG
    # ══════════════════════════════════════════════════════════════
    tf_title = ft.TextField(
        label="ชื่องาน *", hint_text="เช่น ซ่อมเครื่อง CNC #3",
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
    )
    tf_desc = ft.TextField(
        label="รายละเอียด", multiline=True, min_lines=2, max_lines=4,
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
    )
    dd_priority = ft.Dropdown(
        label="Priority",
        options=[ft.dropdown.Option(p) for p in PRIORITY_LIST],
        value=DEFAULT_PRIORITY,
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
    )
    tf_tags = ft.TextField(
        label="Tags (คั่นด้วย ,)", hint_text="เช่น CNC, PM, Urgent",
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
    )
    tf_start_date = ft.TextField(
        label="Start Date (dd/mm/yyyy)",
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8, expand=True,
    )
    tf_due_date = ft.TextField(
        label="Due Date (dd/mm/yyyy)",
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8, expand=True,
    )

    # ── Date Pickers ─────────────────────────────────────────────────
    import time as _time
    _utc_offset_sec = -_time.timezone                  # e.g. +25200 for UTC+7

    def _fix_picker_date(picker_value):
        """DatePicker returns local-midnight as UTC — shift back to local."""
        return picker_value + timedelta(seconds=_utc_offset_sec)

    def _on_start_date_picked(e):
        if start_date_picker.value:
            local = _fix_picker_date(start_date_picker.value)
            tf_start_date.value = local.strftime("%d/%m/%Y")
            safe_update(tf_start_date)

    def _on_due_date_picked(e):
        if due_date_picker.value:
            local = _fix_picker_date(due_date_picker.value)
            tf_due_date.value = local.strftime("%d/%m/%Y")
            safe_update(tf_due_date)

    def _open_date_picker(picker):
        """Open DatePicker using page.show_dialog (recommended for Flet 0.82)."""
        try:
            page.show_dialog(picker)
        except RuntimeError:
            pass  # already open

    start_date_picker = ft.DatePicker(on_change=_on_start_date_picked)
    due_date_picker   = ft.DatePicker(on_change=_on_due_date_picked)

    btn_start_date = ft.IconButton(
        icon=ft.Icons.CALENDAR_TODAY, icon_color=TEXT_SEC, icon_size=20,
        tooltip="เลือกวันที่เริ่ม",
        on_click=lambda e: _open_date_picker(start_date_picker),
    )
    btn_due_date = ft.IconButton(
        icon=ft.Icons.CALENDAR_TODAY, icon_color=TEXT_SEC, icon_size=20,
        tooltip="เลือกวันที่ครบกำหนด",
        on_click=lambda e: _open_date_picker(due_date_picker),
    )

    # Team dropdown (populated when dialog opens)
    dd_team_dlg = ft.Dropdown(
        label="ทีม",
        options=[ft.dropdown.Option(key=NO_SELECTION, text="— ไม่ระบุ —")],
        value=NO_SELECTION,
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
    )

    # Assignee dropdown (populated when dialog opens)
    dd_assignee = ft.Dropdown(
        label="มอบหมายให้",
        options=[ft.dropdown.Option(key=NO_SELECTION, text="— ไม่ระบุ —")],
        value=NO_SELECTION,
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
    )

    # Dependency dropdown (populated when dialog opens)
    dd_depends_on = ft.Dropdown(
        label="งานที่ต้องทำก่อน",
        options=[ft.dropdown.Option(key=NO_SELECTION, text="— ไม่มี —")],
        value=NO_SELECTION,
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
    )

    task_dlg_title = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRI)
    task_dlg_err   = ft.Text("", color=COLOR_URGENT, size=12)
    _editing_task_id: dict = {"value": None}

    def _populate_team_dropdown():
        teams = api.get_teams()
        dd_team_dlg.options = [ft.dropdown.Option(key=NO_SELECTION, text="— ไม่ระบุ —")] + [
            ft.dropdown.Option(key=str(t["id"]), text=t["name"]) for t in teams
        ]

    def _populate_assignee_dropdown(team_key: str = NO_SELECTION):
        team_id = None
        if team_key and team_key != NO_SELECTION:
            try:
                team_id = int(team_key)
            except (ValueError, TypeError):
                pass
        users = api.get_members_for_dropdown(team_id)
        dd_assignee.options = [ft.dropdown.Option(key=NO_SELECTION, text="— ไม่ระบุ —")] + [
            ft.dropdown.Option(key=str(u["id"]), text=u["name"]) for u in users
        ]

    def _populate_depends_on_dropdown(exclude_task_id: Optional[int] = None):
        tasks = api.get_tasks_for_dropdown(exclude_id=exclude_task_id)
        dd_depends_on.options = [ft.dropdown.Option(key=NO_SELECTION, text="— ไม่มี —")] + [
            ft.dropdown.Option(key=str(t["id"]),
                               text=f"{t['title'][:40]} ({t.get('status', 'Pending')})")
            for t in tasks
        ]

    def _close_task_dialog(e=None):
        task_dlg.open = False
        tf_title.value = tf_desc.value = tf_tags.value = ""
        tf_start_date.value = tf_due_date.value = ""
        dd_priority.value = DEFAULT_PRIORITY
        dd_team_dlg.value = NO_SELECTION
        dd_assignee.value = NO_SELECTION
        dd_depends_on.value = NO_SELECTION
        task_dlg_err.value = ""
        _editing_task_id["value"] = None
        safe_page_update(page)

    def _save_task(e):
        title = (tf_title.value or "").strip()
        if not title:
            task_dlg_err.value = "กรุณาใส่ชื่องาน"
            safe_page_update(page)
            return
        try:
            start = parse_date_input(tf_start_date.value)
            due   = parse_date_input(tf_due_date.value)
        except ValueError as ex:
            task_dlg_err.value = str(ex)
            safe_page_update(page)
            return

        def _dd_int(dropdown: ft.Dropdown) -> Optional[int]:
            v = dropdown.value
            if v and v != NO_SELECTION:
                try:
                    return int(v)
                except (ValueError, TypeError):
                    pass
            return None

        team_id       = _dd_int(dd_team_dlg)
        assignee_id   = _dd_int(dd_assignee)
        depends_on_id = _dd_int(dd_depends_on)

        try:
            if _editing_task_id["value"]:
                api.update_task(
                    _editing_task_id["value"],
                    title=title,
                    description=tf_desc.value or "",
                    priority=dd_priority.value,
                    tags=tf_tags.value or "",
                    start_date=start,
                    due_date=due,
                    team_id=team_id,
                    assignee_id=assignee_id,
                    depends_on_id=depends_on_id,
                )
            else:
                api.create_task(
                    title=title,
                    description=tf_desc.value or "",
                    priority=dd_priority.value,
                    tags=tf_tags.value or "",
                    start_date=start,
                    due_date=due,
                    team_id=team_id,
                    assignee_id=assignee_id,
                    depends_on_id=depends_on_id,
                )
            _close_task_dialog()
            _refresh_tasks()
        except (ValidationError, CircularDependencyError, SelfDependencyError) as ex:
            task_dlg_err.value = str(ex)
            safe_page_update(page)
        except NotFoundError as ex:
            show_snack(page, str(ex), error=True)
            _close_task_dialog()
        except Exception as ex:
            logger.error("save failed (unexpected): %s", ex, exc_info=True)
            show_snack(page, "เกิดข้อผิดพลาดที่ไม่คาดคิด", error=True)
            task_dlg_err.value = str(ex)
            safe_page_update(page)

    def _section_header(icon, label: str) -> ft.Row:
        """A6: Section divider header for the task dialog."""
        return ft.Row(
            controls=[
                ft.Icon(icon, color=ACCENT, size=14),
                ft.Text(label, size=12, color=TEXT_SEC,
                        weight=ft.FontWeight.W_600),
            ],
            spacing=6,
        )

    task_dlg = ft.AlertDialog(
        modal=True,
        bgcolor=BG_CARD,
        shape=ft.RoundedRectangleBorder(radius=12),
        title=task_dlg_title,
        content=ft.Container(
            width=460,
            content=ft.Column(
                controls=[
                    # ── Section 1: ข้อมูลหลัก ─────────────────────
                    _section_header(ft.Icons.ASSIGNMENT_OUTLINED, "ข้อมูลหลัก"),
                    ft.Divider(height=1, color=BORDER),
                    tf_title,
                    tf_desc,
                    ft.Row([dd_priority, dd_team_dlg], spacing=10),
                    dd_assignee,
                    # ── Section 2: รายละเอียดเพิ่มเติม ────────────
                    ft.Container(height=4),
                    _section_header(ft.Icons.TUNE, "รายละเอียดเพิ่มเติม"),
                    ft.Divider(height=1, color=BORDER),
                    tf_tags,
                    dd_depends_on,
                    ft.Row([
                        tf_start_date, btn_start_date,
                        tf_due_date, btn_due_date,
                    ], spacing=4),
                    task_dlg_err,
                ],
                spacing=12, tight=True,
                scroll=ft.ScrollMode.AUTO,
            ),
        ),
        actions=[
            ft.TextButton("ยกเลิก", on_click=_close_task_dialog,
                          style=ft.ButtonStyle(color=TEXT_SEC)),
            ft.Button("บันทึก", bgcolor=ACCENT, color="#FFFFFF",
                              on_click=_save_task),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # ── Confirm delete dialog ──────────────────────────────────────
    confirm_msg       = ft.Text("", color=TEXT_SEC, size=14)
    _confirm_fn: dict = {"value": None}

    def _close_confirm(e=None):
        confirm_dlg.open = False
        safe_page_update(page)

    def _do_confirm(e):
        _close_confirm()
        if _confirm_fn["value"]:
            _confirm_fn["value"]()

    confirm_dlg = ft.AlertDialog(
        modal=True, bgcolor=BG_CARD,
        shape=ft.RoundedRectangleBorder(radius=12),
        title=ft.Text("ยืนยันการลบ", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRI),
        content=confirm_msg,
        actions=[
            ft.TextButton("ยกเลิก", on_click=_close_confirm,
                          style=ft.ButtonStyle(color=TEXT_SEC)),
            ft.Button("ลบ", bgcolor=COLOR_URGENT, color=TEXT_PRI,
                              on_click=_do_confirm),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.overlay.extend([task_dlg, confirm_dlg])
    # DatePickers are opened via page.show_dialog() — no overlay needed

    # ══════════════════════════════════════════════════════════════
    #  OPEN DIALOG HELPERS
    # ══════════════════════════════════════════════════════════════
    def _on_team_dlg_change(e):
        """When team dropdown changes, refresh assignee list for that team."""
        team_key = e.control.value or NO_SELECTION
        _populate_assignee_dropdown(team_key)
        dd_assignee.value = NO_SELECTION
        try:
            dd_assignee.update()
        except Exception as e:
            logger.warning("load failed: %s", e, exc_info=True)

    dd_team_dlg.on_select = _on_team_dlg_change

    def _open_create(e=None):
        task_dlg_title.value = "สร้างงานใหม่"
        _editing_task_id["value"] = None
        tf_title.value = tf_desc.value = tf_tags.value = ""
        tf_start_date.value = tf_due_date.value = ""
        dd_priority.value = DEFAULT_PRIORITY
        task_dlg_err.value = ""
        _populate_team_dropdown()
        dd_team_dlg.value = NO_SELECTION
        _populate_assignee_dropdown(NO_SELECTION)
        dd_assignee.value = NO_SELECTION
        _populate_depends_on_dropdown(exclude_task_id=None)
        dd_depends_on.value = NO_SELECTION
        task_dlg.open = True
        safe_page_update(page)

    def _open_edit(task):
        task_dlg_title.value = "แก้ไขงาน"
        _editing_task_id["value"] = task["id"]
        tf_title.value       = task["title"]
        tf_desc.value        = task.get("description") or ""
        tf_tags.value        = task.get("tags") or ""
        dd_priority.value    = task.get("priority", "Medium")
        start_dt = _parse_dt(task.get("start_date"))
        due_dt   = _parse_dt(task.get("due_date"))
        tf_start_date.value  = format_date(start_dt) if start_dt else ""
        tf_due_date.value    = format_date(due_dt)   if due_dt   else ""
        task_dlg_err.value   = ""
        _populate_team_dropdown()
        dd_team_dlg.value    = str(task["team_id"]) if task.get("team_id") else NO_SELECTION
        _populate_assignee_dropdown(dd_team_dlg.value)
        dd_assignee.value    = str(task["assignee_id"]) if task.get("assignee_id") else NO_SELECTION
        _populate_depends_on_dropdown(exclude_task_id=task["id"])
        dd_depends_on.value  = str(task["depends_on_id"]) if task.get("depends_on_id") else NO_SELECTION
        task_dlg.open        = True
        safe_page_update(page)

    def _open_delete(task):
        confirm_msg.value = f'ต้องการลบงาน "{task["title"]}" ใช่ไหม?'
        def _do():
            if selected_task_id["value"] == task["id"]:
                selected_task_id["value"] = None
                detail_panel.visible = False
            api.delete_task(task["id"])
            _refresh_tasks()
        _confirm_fn["value"] = _do
        confirm_dlg.open = True
        safe_page_update(page)

    # ══════════════════════════════════════════════════════════════
    #  DEPENDENCY HELPERS (for detail panel)
    # ══════════════════════════════════════════════════════════════
    def _build_dependency_section(task) -> list:
        """Return list of controls showing dependency info (or empty list)."""
        controls = []
        # ── Show prerequisite task ──────────────────────────────
        if task.get("depends_on_id"):
            dep = None
            try:
                dep = api.get_task(task["depends_on_id"])
            except NotFoundError:
                pass
            if dep:
                controls.append(ft.Divider(height=1, color=BORDER))
                controls.append(
                    ft.Container(
                        bgcolor=BG_INPUT,
                        border_radius=8,
                        padding=10,
                        content=ft.Column(
                            controls=[
                                ft.Text("ต้องทำก่อน", size=12, color=TEXT_SEC,
                                        weight=ft.FontWeight.W_500),
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.LINK, color=ACCENT, size=14),
                                        ft.Text(dep["title"], size=13, color=TEXT_PRI,
                                                expand=True, no_wrap=True,
                                                overflow=ft.TextOverflow.ELLIPSIS),
                                        _status_chip(dep.get("status", "Pending")),
                                    ],
                                    spacing=6,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ],
                            spacing=4,
                        ),
                    )
                )
                # Warning if dependency not done
                if dep.get("status") != "Done":
                    controls.append(
                        ft.Container(
                            bgcolor=COLOR_NEAR + "22",
                            border_radius=6,
                            padding=ft.padding.symmetric(horizontal=10, vertical=6),
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED,
                                            color=COLOR_NEAR, size=16),
                                    ft.Text(
                                        f"งานที่ต้องทำก่อนยังไม่เสร็จ",
                                        size=12, color=COLOR_NEAR,
                                    ),
                                ],
                                spacing=6,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        )
                    )
        # ── Show dependent tasks (reverse lookup) ───────────────
        dependents = api.get_dependent_tasks(task["id"])
        if dependents:
            if not controls:
                controls.append(ft.Divider(height=1, color=BORDER))
            controls.append(
                ft.Container(
                    bgcolor=BG_INPUT,
                    border_radius=8,
                    padding=10,
                    content=ft.Column(
                        controls=[
                            ft.Text(f"งานที่รอ task นี้: {len(dependents)} งาน",
                                    size=12, color=TEXT_SEC,
                                    weight=ft.FontWeight.W_500),
                            *[
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.SUBDIRECTORY_ARROW_RIGHT,
                                                color=TEXT_SEC, size=14),
                                        ft.Text(dt["title"][:35], size=12,
                                                color=TEXT_PRI, expand=True,
                                                no_wrap=True,
                                                overflow=ft.TextOverflow.ELLIPSIS),
                                        _status_chip(dt.get("status", "Pending")),
                                    ],
                                    spacing=6,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                )
                                for dt in dependents[:5]   # show max 5
                            ],
                        ],
                        spacing=4,
                    ),
                )
            )
        return controls

    # ══════════════════════════════════════════════════════════════
    #  DETAIL PANEL — assembled from 4 focused sub-builders
    # ══════════════════════════════════════════════════════════════
    def _build_subtask_section(task) -> tuple:
        """Returns (subtask_col, add_row) — captures outer closure."""
        subtask_col = ft.Column(spacing=6)
        new_sub_tf  = ft.TextField(
            hint_text="เพิ่ม sub-task...",
            border_color=BORDER, focused_border_color=ACCENT,
            color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
            height=40, content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
            text_size=13,
        )

        # ── Edit popup state ─────────────────────────────────────
        _edit_st = {"id": None, "due_date": None}

        st_title_tf = ft.TextField(
            hint_text="ชื่อ sub-task",
            border_color=BORDER, focused_border_color=ACCENT,
            color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
            text_size=13,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
        )
        st_due_label = ft.Text("ไม่ได้กำหนด", size=12, color=TEXT_SEC)

        def _on_st_date_picked(e):
            if st_due_picker.value:
                local = _fix_picker_date(st_due_picker.value)
                _edit_st["due_date"] = local
                st_due_label.value = local.strftime("%d/%m/%Y")
                safe_page_update(page)

        st_due_picker = ft.DatePicker(on_change=_on_st_date_picked)

        def _clear_st_due(e):
            _edit_st["due_date"] = None
            st_due_label.value = "ไม่ได้กำหนด"
            safe_page_update(page)

        st_assignee_dd = ft.Dropdown(
            hint_text="เลือกผู้รับผิดชอบ",
            border_color=BORDER, focused_border_color=ACCENT,
            text_size=13, bgcolor=BG_INPUT, width=280,
            options=[ft.dropdown.Option("", "— ไม่ระบุ —")],
        )

        def _open_st_edit(st):
            _edit_st["id"] = st["id"]
            st_title_tf.value = st.get("title", "")
            due_str = st.get("due_date")
            if due_str:
                try:
                    dt = datetime.fromisoformat(due_str)
                    _edit_st["due_date"] = dt
                    st_due_label.value = dt.strftime("%d/%m/%Y")
                except Exception:
                    _edit_st["due_date"] = None
                    st_due_label.value = "ไม่ได้กำหนด"
            else:
                _edit_st["due_date"] = None
                st_due_label.value = "ไม่ได้กำหนด"
            try:
                team_id = task.get("team_id")
                members = (api.get_members_for_dropdown(team_id=team_id)
                           if team_id else api.get_members_for_dropdown())
            except Exception:
                members = []
            st_assignee_dd.options = [
                ft.dropdown.Option("", "— ไม่ระบุ —"),
                *[ft.dropdown.Option(str(m["id"]), m["name"]) for m in members],
            ]
            cur_aid = st.get("assignee_id")
            st_assignee_dd.value = str(cur_aid) if cur_aid else ""
            st_edit_dlg.open = True
            safe_page_update(page)

        def _save_st_edit(e):
            sid = _edit_st.get("id")
            if not sid:
                return
            title = (st_title_tf.value or "").strip()
            if not title:
                show_snack(page, "ชื่อ sub-task ต้องไม่ว่าง", error=True)
                return
            aid_str = st_assignee_dd.value or ""
            assignee_id = int(aid_str) if aid_str else None
            try:
                api.update_subtask(sid, title=title,
                                   due_date=_edit_st["due_date"],
                                   assignee_id=assignee_id)
                st_edit_dlg.open = False
                _refresh_subtasks()
                safe_page_update(page)
            except Exception as ex:
                show_snack(page, str(ex), error=True)

        def _close_st_edit(e):
            st_edit_dlg.open = False
            safe_page_update(page)

        st_edit_dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("แก้ไข Sub-task", size=15,
                          weight=ft.FontWeight.W_600, color=TEXT_PRI),
            content=ft.Column(
                tight=True,
                width=340,
                spacing=10,
                controls=[
                    ft.Text("ชื่องาน", size=12, color=TEXT_SEC,
                            weight=ft.FontWeight.W_500),
                    st_title_tf,
                    ft.Text("วันครบกำหนด", size=12, color=TEXT_SEC,
                            weight=ft.FontWeight.W_500),
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.CALENDAR_TODAY,
                                icon_color=ACCENT, icon_size=18,
                                tooltip="เลือกวันที่",
                                on_click=lambda e: page.show_dialog(st_due_picker),
                            ),
                            st_due_label,
                            ft.IconButton(
                                icon=ft.Icons.CLOSE, icon_size=14,
                                icon_color=TEXT_SEC, tooltip="ล้างวันที่",
                                on_click=_clear_st_due,
                            ),
                        ],
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text("ผู้รับผิดชอบ", size=12, color=TEXT_SEC,
                            weight=ft.FontWeight.W_500),
                    st_assignee_dd,
                ],
            ),
            actions=[
                ft.TextButton("ยกเลิก", on_click=_close_st_edit),
                ft.ElevatedButton(
                    "บันทึก",
                    style=ft.ButtonStyle(bgcolor=ACCENT, color="#FFFFFF"),
                    on_click=_save_st_edit,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(st_edit_dlg)

        # ── Delete confirmation ──────────────────────────────────
        def _confirm_delete_subtask(sid: int, title: str):
            confirm_msg.value = f'ต้องการลบ sub-task "{title}" ใช่ไหม?'
            def _do():
                api.delete_subtask(sid)
                _refresh_subtasks()
            _confirm_fn["value"] = _do
            confirm_dlg.open = True
            safe_page_update(page)

        # ── Helper: format ISO date string for inline display ────
        def _fmt_st_date(iso: str) -> str:
            try:
                return datetime.fromisoformat(iso).strftime("%d/%m/%y")
            except Exception:
                return iso[:10] if iso else ""

        # ── Sub-task row ─────────────────────────────────────────
        def _subtask_row(st) -> ft.Row:
            controls: list = [
                ft.Checkbox(
                    value=st.get("is_done", False), fill_color=ACCENT,
                    on_change=lambda e, sid=st["id"]: (
                        api.toggle_subtask(sid), _refresh_subtasks()),
                ),
                ft.Text(
                    st["title"], size=13,
                    color=TEXT_SEC if st.get("is_done", False) else TEXT_PRI,
                    expand=True,
                ),
            ]
            if st.get("assignee_name"):
                controls.append(
                    ft.Text(f"👤 {st['assignee_name']}", size=11, color=TEXT_SEC)
                )
            if st.get("due_date"):
                controls.append(
                    ft.Text(f"📅 {_fmt_st_date(st['due_date'])}", size=11, color=TEXT_SEC)
                )
            controls.extend([
                ft.IconButton(
                    icon=ft.Icons.EDIT_OUTLINED, icon_size=14, icon_color=ACCENT2,
                    tooltip="แก้ไข sub-task",
                    on_click=lambda e, s=st: _open_st_edit(s),
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE, icon_size=14, icon_color=TEXT_SEC,
                    tooltip="ลบ sub-task",
                    on_click=lambda e, sid=st["id"], t=st["title"]: (
                        _confirm_delete_subtask(sid, t)),
                ),
            ])
            return ft.Row(
                controls=controls,
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

        def _refresh_subtasks():
            try:
                fresh = api.get_task(task["id"])
                subtasks = fresh.get("subtasks", [])
            except Exception:
                subtasks = task.get("subtasks", [])
            subtask_col.controls = [
                _subtask_row(st) for st in subtasks
                if not st.get("is_deleted", False)
            ]
            try:
                if subtask_col.page:
                    subtask_col.update()
            except Exception:
                pass

        def _add_subtask(e):
            text = (new_sub_tf.value or "").strip()
            if not text:
                return
            parent_due = task.get("due_date")
            parent_aid = task.get("assignee_id")
            due_dt: Optional[datetime] = None
            if parent_due:
                try:
                    due_dt = datetime.fromisoformat(parent_due)
                except Exception:
                    pass
            api.add_subtask(task["id"], text,
                            due_date=due_dt, assignee_id=parent_aid)
            new_sub_tf.value = ""
            _refresh_subtasks()
            safe_page_update(page)

        _refresh_subtasks()
        add_row = ft.Row(
            controls=[
                ft.Container(expand=True, content=new_sub_tf),
                ft.IconButton(
                    icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                    icon_color=ACCENT, icon_size=22,
                    tooltip="เพิ่ม sub-task",
                    on_click=_add_subtask,
                ),
            ],
            spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        return subtask_col, add_row

    def _build_comment_section(task) -> tuple:
        """Returns (comment_col, comment_tf, send_btn)."""
        comment_col    = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
        new_comment_tf = ft.TextField(
            hint_text="เพิ่ม comment...",
            multiline=True, min_lines=2, max_lines=4,
            border_color=BORDER, focused_border_color=ACCENT,
            color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8, text_size=13,
        )

        def _comment_bubble(c) -> ft.Container:
            author_name = c.get("author_name") or "ระบบ"
            created_dt = _parse_dt(c.get("created_at"))
            time_str = created_dt.strftime("%d/%m %H:%M") if created_dt else ""
            return ft.Container(
                bgcolor=BG_INPUT, border_radius=8, padding=10,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=24, height=24, border_radius=12,
                                    bgcolor=ACCENT + "44",
                                    content=ft.Text(author_name[0].upper(), size=11,
                                                    color=ACCENT,
                                                    text_align=ft.TextAlign.CENTER),
                                    alignment=ft.alignment.Alignment.CENTER,
                                ),
                                ft.Text(author_name, size=12, color=ACCENT,
                                        weight=ft.FontWeight.W_500),
                                ft.Text(time_str, size=11, color=TEXT_SEC),
                            ],
                            spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Text(c["body"], size=13, color=TEXT_PRI),
                    ],
                    spacing=4,
                ),
            )

        def _refresh_comments():
            comment_col.controls = [_comment_bubble(c)
                                    for c in api.get_comments(task["id"])]
            try:
                if comment_col.page:
                    comment_col.update()
            except Exception:
                pass

        def _add_comment(e):
            body = (new_comment_tf.value or "").strip()
            if body:
                current_user = page.session.store.get("current_user") or {}
                author_id = current_user.get("id")
                api.add_comment(task["id"], body, author_id=author_id)
                new_comment_tf.value = ""
                _refresh_comments()
                safe_page_update(page)

        _refresh_comments()
        send_btn = ft.Button(
            "ส่ง comment", bgcolor=ACCENT, color="#FFFFFF",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=_add_comment,
        )
        return comment_col, new_comment_tf, send_btn

    def _build_status_row(task) -> ft.Row:
        """Status-change button row."""
        def _status_btn(s: str) -> ft.Button:
            is_cur = task.get("status", "Pending") == s
            col    = status_color(s)
            return ft.Button(
                s,
                bgcolor=col if is_cur else col + "22",
                color=TEXT_PRI if is_cur else col,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=6),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                ),
                on_click=lambda e, st=s: _change_status(task, st),
            )
        return ft.Row(controls=[_status_btn(s) for s in STATUS_LIST],
                      spacing=4, wrap=True)

    def _build_time_section(task) -> ft.Column:
        """Time tracking section — timer toggle + log list."""
        task_id = task["id"]

        timer_status_text = ft.Text("", size=12, color=TEXT_SEC)
        timer_total_text  = ft.Text("", size=12, color=TEXT_PRI,
                                    weight=ft.FontWeight.W_500)
        time_log_col      = ft.Column(spacing=4)

        def _fmt_minutes(m: int) -> str:
            if m < 60: return f"{m} นาที"
            h, rem = divmod(m, 60)
            return f"{h} ชม. {rem} นาที" if rem else f"{h} ชม."

        def _update_time_ui():
            for ctrl in [timer_status_text, timer_total_text, time_log_col]:
                try: ctrl.update()
                except Exception: pass

        def _refresh_time_section():
            running = api.get_running_log(task_id)
            total   = api.get_total_minutes(task_id)
            timer_total_text.value = (f"รวม: {_fmt_minutes(total)}"
                                      if total else "ยังไม่มีบันทึก")
            if running:
                started_dt = _parse_dt(running.get("started_at"))
                time_str = started_dt.strftime("%H:%M") if started_dt else ""
                timer_status_text.value = f"⏱ กำลังบันทึก... (เริ่ม {time_str})"
                timer_status_text.color = "#22C55E"
            else:
                timer_status_text.value = ""
            logs = api.get_time_logs(task_id)[:5]
            time_log_col.controls = []
            for lg in logs:
                started_dt = _parse_dt(lg.get("started_at"))
                started_str = started_dt.strftime("%d/%m %H:%M") if started_dt else ""
                time_log_col.controls.append(ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ACCESS_TIME, color=TEXT_SEC, size=12),
                        ft.Text(
                            f"{_fmt_minutes(lg.get('duration_minutes') or 0)}  {started_str}",
                            size=11, color=TEXT_SEC, expand=True,
                        ),
                        ft.Text(lg.get("note") or "", size=11, color=TEXT_SEC),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE, icon_size=13,
                            icon_color=COLOR_URGENT, tooltip="ลบ",
                            on_click=lambda e, lid=lg["id"]: (
                                api.delete_time_log(lid),
                                _refresh_time_section(),
                                _update_time_ui(),
                            ),
                        ),
                    ],
                    spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ))
            _update_time_ui()

        def _toggle_timer(e):
            running = api.get_running_log(task_id)
            if running:
                api.stop_timer(task_id)
                timer_toggle_btn.icon       = ft.Icons.PLAY_ARROW
                timer_toggle_btn.icon_color = ACCENT
                timer_toggle_btn.tooltip    = "เริ่มบันทึก"
            else:
                api.start_timer(task_id)
                timer_toggle_btn.icon       = ft.Icons.STOP
                timer_toggle_btn.icon_color = "#EF4444"
                timer_toggle_btn.tooltip    = "หยุดบันทึก"
            try: timer_toggle_btn.update()
            except Exception: pass
            _refresh_time_section()

        _is_running_now = api.get_running_log(task_id) is not None
        timer_toggle_btn = ft.IconButton(
            icon=ft.Icons.STOP if _is_running_now else ft.Icons.PLAY_ARROW,
            icon_color="#EF4444" if _is_running_now else ACCENT,
            icon_size=22,
            tooltip="หยุดบันทึก" if _is_running_now else "เริ่มบันทึก",
            on_click=_toggle_timer,
        )
        _refresh_time_section()

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.TIMER_OUTLINED, color=ACCENT, size=15),
                        ft.Text("บันทึกเวลา", size=13,
                                weight=ft.FontWeight.W_500, color=TEXT_PRI),
                        ft.Container(expand=True),
                        timer_toggle_btn,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                timer_status_text, timer_total_text, time_log_col,
            ],
            spacing=4,
        )

    def _build_detail_panel(task) -> ft.Container:
        """Thin assembler — composes 4 focused sub-builders."""
        subtask_col, subtask_add_row = _build_subtask_section(task)
        comment_col, comment_tf, send_btn = _build_comment_section(task)
        status_row   = _build_status_row(task)
        time_section = _build_time_section(task)
        assignee_name = task.get("assignee_name") or "ไม่ระบุ"
        due_dt = _parse_dt(task.get("due_date"))

        return ft.Container(
            expand=True, padding=ft.padding.all(16), bgcolor=BG_CARD,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("รายละเอียดงาน", size=15,
                                    weight=ft.FontWeight.BOLD, color=TEXT_PRI),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE, icon_color=TEXT_SEC, icon_size=18,
                                on_click=lambda e: _close_detail(),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=1, color=BORDER),
                    ft.Text(task["title"], size=16,
                            weight=ft.FontWeight.BOLD, color=TEXT_PRI),
                    ft.Text(task.get("description") or "ไม่มีคำอธิบาย",
                            size=13, color=TEXT_SEC),
                    ft.Row(controls=[
                        _status_chip(task.get("status", "Pending")),
                        _priority_chip(task.get("priority", "Medium")),
                    ], spacing=6),
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.PERSON_OUTLINE, color=TEXT_SEC, size=14),
                            ft.Text(assignee_name, size=12, color=TEXT_SEC),
                            ft.Icon(ft.Icons.CALENDAR_TODAY_OUTLINED,
                                    color=TEXT_SEC, size=14),
                            _due_label(due_dt),
                        ],
                        spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    *_build_dependency_section(task),
                    ft.Text("เปลี่ยนสถานะ", size=12, color=TEXT_SEC),
                    status_row,
                    ft.Divider(height=1, color=BORDER),
                    time_section,
                    ft.Divider(height=1, color=BORDER),
                    ft.Text("Sub-tasks", size=13,
                            weight=ft.FontWeight.W_500, color=TEXT_PRI),
                    subtask_col,
                    subtask_add_row,
                    ft.Divider(height=1, color=BORDER),
                    ft.Text("Comments", size=13,
                            weight=ft.FontWeight.W_500, color=TEXT_PRI),
                    ft.Container(height=160, content=comment_col),
                    comment_tf,
                    send_btn,
                ],
                spacing=10, scroll=ft.ScrollMode.AUTO, expand=True,
            ),
        )

    # ══════════════════════════════════════════════════════════════
    #  TASK ROW
    # ══════════════════════════════════════════════════════════════
    def _build_task_row(task) -> ft.Container:
        task_status = task.get("status", "Pending")
        task_priority = task.get("priority", "Medium")
        due_dt = _parse_dt(task.get("due_date"))

        is_selected          = selected_task_id["value"] == task["id"]
        overdue              = is_overdue(due_dt) and task_status not in ("Done", "Cancelled")
        is_done_or_cancelled = task_status in ("Done", "Cancelled")

        left_accent_color = priority_color(task_priority)
        assignee_name     = task.get("assignee_name") or "—"

        # Subtask progress
        _all_st   = [st for st in task.get("subtasks", [])
                     if not st.get("is_deleted", False)]
        _done_st  = sum(1 for st in _all_st if st.get("is_done", False))
        _total_st = len(_all_st)
        _st_color = COLOR_DONE if (_total_st > 0 and _done_st == _total_st) else TEXT_SEC

        tags_row = ft.Row(
            controls=[
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=6, vertical=1),
                    border_radius=10,
                    bgcolor=ACCENT2 + "22",
                    content=ft.Text(t.strip(), size=10, color=ACCENT2),
                )
                for t in (task.get("tags") or "").split(",") if t.strip()
            ],
            spacing=4, wrap=True,
        )

        # ── A2: Action buttons — hidden by default, revealed on hover ──
        action_row = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.EDIT_OUTLINED,
                    icon_color=TEXT_SEC, icon_size=16,
                    tooltip="แก้ไข",
                    on_click=lambda e, t=task: _open_edit(t),
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=COLOR_URGENT, icon_size=16,
                    tooltip="ลบ",
                    on_click=lambda e, t=task: _open_delete(t),
                ),
            ],
            spacing=0,
            visible=is_selected,   # stay visible when card is selected
        )

        def _on_hover(e, ar=action_row, sel=is_selected):
            ar.visible = (e.data == "true") or sel
            try:
                ar.update()
            except Exception:
                pass

        return ft.Container(
            bgcolor=BG_CARD if not is_selected else ACCENT + "11",
            border_radius=8,
            # ── A3: Fade completed/cancelled tasks ──────────────────
            opacity=0.55 if is_done_or_cancelled else 1.0,
            border=ft.border.only(
                left=ft.BorderSide(3, left_accent_color),
                top=ft.BorderSide(1, ACCENT + "44" if is_selected else BORDER),
                right=ft.BorderSide(1, ACCENT + "44" if is_selected else BORDER),
                bottom=ft.BorderSide(1, ACCENT + "44" if is_selected else BORDER),
            ),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            ink=True,
            on_click=lambda e, t=task: _select_task(t),
            on_hover=_on_hover,
            content=ft.Row(
                controls=[
                    # Main info
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        task["title"], size=14,
                                        weight=ft.FontWeight.W_500,
                                        color=TEXT_SEC if is_done_or_cancelled else TEXT_PRI,
                                        expand=True,
                                        no_wrap=True,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    _status_chip(task_status),
                                    _priority_chip(task_priority),
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.PERSON_OUTLINE,
                                            color=TEXT_SEC, size=13),
                                    ft.Text(assignee_name, size=12, color=TEXT_SEC),
                                    ft.Icon(ft.Icons.CALENDAR_TODAY_OUTLINED,
                                            color=COLOR_URGENT if overdue else TEXT_SEC,
                                            size=13),
                                    _due_label(due_dt),
                                    *([
                                        ft.Container(width=1, height=12, bgcolor=BORDER),
                                        ft.Icon(ft.Icons.CHECKLIST,
                                                color=_st_color, size=13),
                                        ft.Text(f"{_done_st}/{_total_st}",
                                                size=11, color=_st_color),
                                    ] if _total_st > 0 else []),
                                    tags_row,
                                ],
                                spacing=4,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=4, expand=True,
                    ),
                    action_row,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    # ══════════════════════════════════════════════════════════════
    #  ACTIONS
    # ══════════════════════════════════════════════════════════════
    def _change_status(task, new_status_str: str):
        # Soft warning if dependency not done (for In Progress / Review / Done)
        if new_status_str in ("In Progress", "Review", "Done"):
            dep_id = task.get("depends_on_id")
            if dep_id:
                try:
                    dep = api.get_task(dep_id)
                    if dep.get("status") != "Done":
                        warning = f"งานที่ต้องทำก่อน \"{dep['title']}\" ยังไม่เสร็จ"
                        snack = ft.SnackBar(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED,
                                            color="#FFFFFF", size=18),
                                    ft.Text(
                                        f"⚠ {warning}",
                                        color="#FFFFFF", size=13,
                                    ),
                                ],
                                spacing=8,
                            ),
                            bgcolor=COLOR_NEAR,
                            duration=4000,
                        )
                        try:
                            page.show_dialog(snack)
                        except Exception as e:
                            logger.warning("load failed: %s", e, exc_info=True)
                except Exception:
                    pass

        api.update_task(task["id"], status=new_status_str)
        _refresh_tasks()
        # Reopen detail with fresh data
        try:
            fresh = api.get_task(task["id"])
            _select_task(fresh, force=True)
        except Exception:
            pass

    def _select_task(task, force: bool = False):
        if not force and selected_task_id["value"] == task["id"]:
            _close_detail()
            return
        selected_task_id["value"] = task["id"]
        detail_panel.content = _build_detail_panel(task)
        detail_panel.visible = True
        try:
            detail_panel.update()
        except Exception as e:
            logger.warning("load failed: %s", e, exc_info=True)
        _refresh_task_list_only()

    def _close_detail():
        selected_task_id["value"] = None
        detail_panel.visible = False
        try:
            detail_panel.update()
        except Exception as e:
            logger.warning("load failed: %s", e, exc_info=True)
        _refresh_task_list_only()

    def _refresh_task_list_only():
        _filter_loading.visible = True
        safe_update(_filter_loading)
        tasks = _filtered_tasks()
        if tasks:
            task_list_col.controls = [_build_task_row(t) for t in tasks]
        else:
            # A5: show filtered-empty vs truly-empty state
            all_count = len(api.get_tasks())
            task_list_col.controls = [_empty_state(is_filtered=all_count > 0)]
        _filter_loading.visible = False
        safe_update(task_list_col)

    def _refresh_tasks():
        _refresh_task_list_only()
        # If detail open, refresh it too
        if selected_task_id["value"]:
            try:
                fresh = api.get_task(selected_task_id["value"])
                detail_panel.content = _build_detail_panel(fresh)
                detail_panel.update()
            except Exception as e:
                logger.warning("load failed: %s", e, exc_info=True)
                _close_detail()

    def _filtered_tasks():
        tasks = api.get_tasks()
        fs = filter_status["value"]
        fp = filter_priority["value"]
        sq = search_query["value"].lower()
        if fs != ALL_FILTER:
            tasks = [t for t in tasks if t.get("status", "Pending") == fs]
        if fp != ALL_FILTER:
            tasks = [t for t in tasks if t.get("priority", "Medium") == fp]
        if sq:
            tasks = [t for t in tasks if sq in t["title"].lower()
                     or sq in (t.get("description") or "").lower()
                     or sq in (t.get("tags") or "").lower()]
        # ── Sort ────────────────────────────────────────────────
        so = sort_order["value"]
        if so == "สร้างล่าสุด":
            tasks.sort(key=lambda t: t.get("created_at") or "", reverse=True)
        elif so == "เก่าสุด":
            tasks.sort(key=lambda t: t.get("created_at") or "")
        elif so == "ครบกำหนด":
            tasks.sort(key=lambda t: (
                t.get("due_date") is None,
                t.get("due_date") or "9999",
            ))
        elif so == "Priority":
            tasks.sort(key=lambda t: PRIO_ORDER.get(t.get("priority", "Medium"), 99))
        elif so == "ชื่อ":
            tasks.sort(key=lambda t: t["title"].lower())
        return tasks

    def _empty_state(is_filtered: bool = False) -> ft.Container:
        """A5: Differentiate between 'no tasks' and 'filter returned nothing'."""
        if is_filtered:
            icon     = ft.Icons.SEARCH_OFF
            title    = "ไม่พบงานที่ตรงกับเงื่อนไข"
            subtitle = "ลองปรับ filter หรือล้างตัวกรองเพื่อดูงานทั้งหมด"
            extra    = [ft.TextButton(
                "ล้างตัวกรอง",
                icon=ft.Icons.FILTER_ALT_OFF,
                style=ft.ButtonStyle(color=ACCENT),
                on_click=lambda e: _clear_filters(),
            )]
        else:
            icon     = ft.Icons.TASK_ALT_OUTLINED
            title    = "ไม่มีงาน"
            subtitle = "กดปุ่ม '+ สร้างงาน' เพื่อเริ่มต้น"
            extra    = []

        return ft.Container(
            alignment=ft.alignment.Alignment(0, 0), padding=40,
            content=ft.Column(
                controls=[
                    ft.Icon(icon, color=TEXT_SEC, size=48),
                    ft.Text(title, size=16, color=TEXT_SEC),
                    ft.Text(subtitle, size=13, color=TEXT_SEC),
                    *extra,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
        )

    # Initial load
    _refresh_task_list_only()

    # ══════════════════════════════════════════════════════════════
    #  UX#4: RECYCLE BIN (soft-deleted tasks)
    # ══════════════════════════════════════════════════════════════
    deleted_col         = ft.Column(spacing=6)
    trash_section_open  = {"value": False}

    def _refresh_deleted():
        deleted = api.get_deleted_tasks()
        if not deleted:
            deleted_col.controls = [
                ft.Text("ไม่มีงานที่ถูกลบ", size=13, color=TEXT_SEC)
            ]
        else:
            deleted_col.controls = [_deleted_task_row(t) for t in deleted]
        safe_update(deleted_col)

    def _deleted_task_row(task) -> ft.Container:
        return ft.Container(
            bgcolor=BG_CARD,
            border_radius=8,
            border=ft.border.all(1, BORDER),
            padding=ft.padding.symmetric(horizontal=14, vertical=8),
            opacity=0.6,
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.DELETE_OUTLINE, color=TEXT_SEC, size=16),
                    ft.Column(
                        controls=[
                            ft.Text(task["title"], size=13, color=TEXT_SEC,
                                    weight=ft.FontWeight.W_500,
                                    no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(_priority_chip(task.get("priority", "Medium")).content.value,
                                    size=11, color=TEXT_SEC),
                        ],
                        spacing=2, expand=True,
                    ),
                    ft.TextButton(
                        "กู้คืน",
                        icon=ft.Icons.RESTORE,
                        style=ft.ButtonStyle(color=ACCENT),
                        on_click=lambda e, tid=task["id"]: _restore_task(tid),
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _restore_task(task_id: int):
        try:
            api.restore_task(task_id)
            show_snack(page, "กู้คืนงานสำเร็จ")
            _refresh_deleted()
            _refresh_tasks()
        except Exception as ex:
            show_snack(page, f"เกิดข้อผิดพลาด: {ex}", error=True)

    trash_body = ft.Column(
        controls=[deleted_col],
        spacing=0,
        visible=False,
    )

    trash_toggle_btn = ft.TextButton(
        "แสดงงานที่ถูกลบ",
        icon=ft.Icons.DELETE_OUTLINE,
        style=ft.ButtonStyle(color=TEXT_SEC),
    )

    def _toggle_trash(e):
        open_ = not trash_section_open["value"]
        trash_section_open["value"] = open_
        trash_body.visible = open_
        trash_toggle_btn.text  = "ซ่อนงานที่ถูกลบ" if open_ else "แสดงงานที่ถูกลบ"
        trash_toggle_btn.icon  = ft.Icons.EXPAND_LESS if open_ else ft.Icons.DELETE_OUTLINE
        if open_:
            _refresh_deleted()
        try:
            trash_body.update()
            trash_toggle_btn.update()
        except Exception:
            pass

    trash_toggle_btn.on_click = _toggle_trash

    # ══════════════════════════════════════════════════════════════
    #  FILTER BAR
    # ══════════════════════════════════════════════════════════════
    # ── A4: Clear filter helpers ──────────────────────────────────
    def _is_filtered() -> bool:
        return (filter_status["value"]   != ALL_FILTER
                or filter_priority["value"] != ALL_FILTER
                or sort_order["value"]      != "สร้างล่าสุด"
                or bool(search_query["value"]))

    def _clear_filters():
        filter_status["value"]   = ALL_FILTER
        filter_priority["value"] = ALL_FILTER
        sort_order["value"]      = "สร้างล่าสุด"
        search_query["value"]    = ""
        search_tf.value          = ""
        try:
            search_tf.update()
        except Exception:
            pass
        _refresh_task_list_only()
        _rebuild_filters()

    clear_filter_btn = ft.TextButton(
        "ล้างตัวกรอง",
        icon=ft.Icons.FILTER_ALT_OFF,
        style=ft.ButtonStyle(color=COLOR_URGENT),
        visible=False,
        on_click=lambda e: _clear_filters(),
    )

    def _filter_chip(label: str, key: str, state_dict: dict,
                     refresh_fn) -> ft.Container:
        is_active = state_dict["value"] == label

        def _on_click(e, lbl=label):
            state_dict["value"] = lbl
            refresh_fn()

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=20,
            bgcolor=ACCENT + "33" if is_active else BG_CARD,
            border=ft.border.all(1, ACCENT if is_active else BORDER),
            ink=True,
            on_click=_on_click,
            content=ft.Text(label, size=12,
                            color=TEXT_PRI if is_active else TEXT_SEC),
        )

    # ── Filter chip builders — single source of truth ───────────────
    def _on_filter(): _refresh_task_list_only(); _rebuild_filters()

    def _build_status_chips():
        return [
            _filter_chip(ALL_FILTER, "status", filter_status, _on_filter),
            *[_filter_chip(s, "status", filter_status, _on_filter) for s in STATUS_LIST],
        ]

    def _build_priority_chips():
        return [
            _filter_chip(ALL_FILTER, "priority", filter_priority, _on_filter),
            *[_filter_chip(p, "priority", filter_priority, _on_filter) for p in PRIORITY_LIST],
        ]

    def _build_sort_chips():
        return [_filter_chip(o, "sort", sort_order, _on_filter) for o in SORT_OPTIONS]

    status_filters   = ft.Row(controls=_build_status_chips(),   spacing=6, wrap=False)
    priority_filters = ft.Row(controls=_build_priority_chips(), spacing=6, wrap=False)
    sort_filters     = ft.Row(controls=_build_sort_chips(),     spacing=6, wrap=False)

    search_tf = ft.TextField(
        hint_text="ค้นหางาน...",
        prefix_icon=ft.Icons.SEARCH,
        border_color=BORDER, focused_border_color=ACCENT,
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
        height=42, text_size=13,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
        on_change=lambda e: (
            search_query.update({"value": e.control.value or ""}),
            _refresh_task_list_only(),
        ),
    )

    filter_col = ft.Column(
        controls=[
            # แถว 1: Status filter
            ft.Row(
                controls=[
                    ft.Text("Status:", size=12, color=TEXT_SEC),
                    status_filters,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            # แถว 2: Priority + Sort + A4 Clear button
            ft.Row(
                controls=[
                    ft.Text("Priority:", size=12, color=TEXT_SEC),
                    priority_filters,
                    ft.Container(width=1, height=24, bgcolor=BORDER),
                    ft.Text("เรียง:", size=12, color=TEXT_SEC),
                    sort_filters,
                    ft.Container(width=1, height=24, bgcolor=BORDER),
                    clear_filter_btn,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
        ],
        spacing=8,
    )

    def _rebuild_filters():
        """Rebuild filter chips so active state re-renders."""
        status_filters.controls   = _build_status_chips()
        priority_filters.controls = _build_priority_chips()
        sort_filters.controls     = _build_sort_chips()
        clear_filter_btn.visible  = _is_filtered()
        for ctrl in [status_filters, priority_filters, sort_filters, clear_filter_btn]:
            safe_update(ctrl)

    # ══════════════════════════════════════════════════════════════
    #  UX#1: QUICK-ADD INLINE BAR
    # ══════════════════════════════════════════════════════════════
    quick_add_tf = ft.TextField(
        hint_text="+ เพิ่มงานด่วน... (พิมพ์ชื่อแล้วกด Enter)",
        border_color=BORDER, focused_border_color=ACCENT,
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
        height=40, text_size=13, expand=True,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
    )

    def _quick_add_task(e=None):
        title = (quick_add_tf.value or "").strip()
        if not title:
            return
        try:
            api.create_task(title=title)
            quick_add_tf.value = ""
            try:
                quick_add_tf.update()
            except Exception:
                pass
            _refresh_tasks()
            show_snack(page, f"สร้างงาน \"{title}\" แล้ว")
        except Exception as ex:
            show_snack(page, f"เกิดข้อผิดพลาด: {ex}", error=True)

    quick_add_tf.on_submit = _quick_add_task

    quick_add_bar = ft.Container(
        content=ft.Row(
            controls=[
                quick_add_tf,
                ft.IconButton(
                    icon=ft.Icons.ADD_CIRCLE,
                    icon_color=ACCENT, icon_size=24,
                    tooltip="สร้างงานด่วน",
                    on_click=_quick_add_task,
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.only(bottom=4),
    )

    # ══════════════════════════════════════════════════════════════
    #  TOP BAR
    # ══════════════════════════════════════════════════════════════
    top_bar = ft.Row(
        controls=[
            ft.Column(
                controls=[
                    ft.Text("งาน", size=24,
                            weight=ft.FontWeight.BOLD, color=TEXT_PRI),
                    ft.Text("จัดการและติดตามงานทั้งหมด",
                            size=13, color=TEXT_SEC),
                ],
                spacing=2,
            ),
            ft.Row(
                controls=[
                    ft.Container(width=240, content=search_tf),
                    ft.Button(
                        "สร้างงาน",
                        icon=ft.Icons.ADD,
                        bgcolor=ACCENT, color="#FFFFFF",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8)),
                        on_click=_open_create,
                    ),
                ],
                spacing=12,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    # ══════════════════════════════════════════════════════════════
    #  NOTIFICATION PANEL (near-due tasks)
    # ══════════════════════════════════════════════════════════════
    _dismissed_near_due: dict = {"ids": set()}

    def _build_notif_panel() -> ft.Container:
        near_tasks = api.get_near_due_tasks(days=3)
        rows_data = [
            (t["id"], t["title"], _parse_dt(t.get("due_date")))
            for t in near_tasks
            if t["id"] not in _dismissed_near_due["ids"]
        ]
        if not rows_data:
            return ft.Container(visible=False, height=0)

        def _dismiss_all(e):
            for tid, _, _ in rows_data:
                _dismissed_near_due["ids"].add(tid)
            notif_panel.visible = False
            safe_page_update(page)

        items = []
        for _tid, title, due in rows_data:
            d = days_until(due)
            if d is None or d < 0:
                continue
            if d == 0:
                label, lcolor = "ครบกำหนดวันนี้", COLOR_URGENT
            elif d == 1:
                label, lcolor = "พรุ่งนี้", COLOR_NEAR
            else:
                label, lcolor = f"อีก {d} วัน", COLOR_NEAR
            items.append(
                ft.Row(controls=[
                    ft.Icon(ft.Icons.ALARM, size=13, color=lcolor),
                    ft.Text(f"{title[:38]}{'…' if len(title) > 38 else ''} — {label}",
                            size=12, color=TEXT_PRI),
                ], spacing=5)
            )

        if not items:
            return ft.Container(visible=False, height=0)

        return ft.Container(
            bgcolor="#FFF7ED",
            border=ft.border.all(1, "#FED7AA"),
            border_radius=8,
            padding=ft.padding.all(10),
            margin=ft.margin.only(bottom=8),
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Row(controls=[
                                ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE,
                                        color=COLOR_NEAR, size=15),
                                ft.Text("งานใกล้ครบกำหนด", size=13,
                                        weight=ft.FontWeight.W_500, color=TEXT_PRI),
                            ], spacing=6),
                            *items,
                        ],
                        spacing=4, expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE, icon_size=15, icon_color=TEXT_SEC,
                        tooltip="ปิด",
                        on_click=_dismiss_all,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )

    notif_panel = _build_notif_panel()

    # ══════════════════════════════════════════════════════════════
    #  ROOT LAYOUT
    # ══════════════════════════════════════════════════════════════
    left_pane = ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                top_bar,
                ft.Divider(height=16, color=BORDER),
                notif_panel,           # near-due notification banner
                filter_col,
                ft.Divider(height=12, color=BORDER),
                quick_add_bar,         # UX#1: quick-add inline bar
                _filter_loading,       # B4-T1: loading indicator while filtering
                task_list_col,
                ft.Divider(height=8, color=BORDER),
                trash_toggle_btn,      # UX#4: recycle bin toggle
                trash_body,            # UX#4: deleted tasks list
            ],
            spacing=0,
            expand=True,
        ),
        padding=ft.padding.all(24),
    )

    # ── Keyboard shortcuts ──────────────────────────────────────────
    def _shortcut_esc():
        if task_dlg.open:
            _close_task_dialog()
        elif selected_task_id["value"] is not None:
            selected_task_id["value"] = None
            detail_panel.visible = False
            safe_page_update(page)

    def _shortcut_enter():
        if task_dlg.open:
            _save_task(None)

    def _shortcut_search():
        try:
            search_tf.focus()
        except Exception:
            pass

    shortcut_registry.register("ctrl_n", _open_create)
    shortcut_registry.register("esc",    _shortcut_esc)
    shortcut_registry.register("enter",  _shortcut_enter)
    shortcut_registry.register("ctrl_f", _shortcut_search)

    # Auto-open detail panel for highlighted task (from global search)
    if highlight_task_id is not None:
        try:
            task_to_highlight = api.get_task(highlight_task_id)
            if task_to_highlight:
                selected_task_id["value"] = task_to_highlight["id"]
                detail_panel.content = _build_detail_panel(task_to_highlight)
                detail_panel.visible = True
                _refresh_task_list_only()
        except NotFoundError:
            pass

    return ft.Container(
        expand=True,
        bgcolor=BG_DARK,
        content=ft.Row(
            controls=[left_pane, detail_panel],
            spacing=0,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
    )
