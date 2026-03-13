# -*- coding: utf-8 -*-
"""
TaskView — Phase 3: Task Creation & Assignment UI
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
from sqlalchemy.orm import Session

from app.services.task_service import TaskService
from app.services.team_service import TeamService
from app.models.task import TaskStatus, TaskPriority
from app.utils.theme import (
    BG_DARK, BG_CARD, BG_INPUT,
    ACCENT, ACCENT2, TEXT_PRI, TEXT_SEC, BORDER,
    COLOR_URGENT, COLOR_DONE,
    status_color, priority_color,
)
from app.utils.date_helpers import format_date, is_overdue, days_until

# ── Constants ─────────────────────────────────────────────────────────────────
STATUS_LIST   = [s.value for s in TaskStatus]
PRIORITY_LIST = [p.value for p in TaskPriority]
COLOR_NEAR    = "#FF9800"   # due within 2 days


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _status_chip(status: str) -> ft.Container:
    color = status_color(status)
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
        border_radius=20,
        bgcolor=color,
        content=ft.Text(status, size=11, color="#FFFFFF", weight=ft.FontWeight.W_500),
    )

def _priority_chip(priority: str) -> ft.Container:
    color = priority_color(priority)
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
        border_radius=20,
        bgcolor=color,
        content=ft.Text(priority, size=11, color="#FFFFFF", weight=ft.FontWeight.W_500),
    )

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


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY
# ══════════════════════════════════════════════════════════════════════════════
def build_task_view(db: Session, page: ft.Page) -> ft.Control:
    task_svc = TaskService(db)
    team_svc = TeamService(db)

    # ── State ──────────────────────────────────────────────────────
    selected_task_id: dict = {"value": None}
    filter_status:    dict = {"value": "ทั้งหมด"}
    filter_priority:  dict = {"value": "ทั้งหมด"}
    search_query:     dict = {"value": ""}

    # ── Layout refs ────────────────────────────────────────────────
    task_list_col  = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)
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
        value="Medium",
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
            try:
                tf_start_date.update()
            except Exception:
                pass

    def _on_due_date_picked(e):
        if due_date_picker.value:
            local = _fix_picker_date(due_date_picker.value)
            tf_due_date.value = local.strftime("%d/%m/%Y")
            try:
                tf_due_date.update()
            except Exception:
                pass

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
        options=[ft.dropdown.Option(key="none", text="— ไม่ระบุ —")],
        value="none",
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
    )

    # Assignee dropdown (populated when dialog opens)
    dd_assignee = ft.Dropdown(
        label="มอบหมายให้",
        options=[ft.dropdown.Option(key="none", text="— ไม่ระบุ —")],
        value="none",
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
    )

    # Dependency dropdown (populated when dialog opens)
    dd_depends_on = ft.Dropdown(
        label="งานที่ต้องทำก่อน",
        options=[ft.dropdown.Option(key="none", text="— ไม่มี —")],
        value="none",
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
    )

    task_dlg_title = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRI)
    task_dlg_err   = ft.Text("", color=COLOR_URGENT, size=12)
    _editing_task_id: dict = {"value": None}

    def _parse_date(s: str) -> Optional[datetime]:
        s = (s or "").strip()
        if not s:
            return None
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        raise ValueError(f"รูปแบบวันที่ไม่ถูกต้อง: {s!r}  (ใช้ dd/mm/yyyy)")

    def _populate_team_dropdown():
        teams = team_svc.get_all_teams()
        dd_team_dlg.options = [ft.dropdown.Option(key="none", text="— ไม่ระบุ —")] + [
            ft.dropdown.Option(key=str(t.id), text=t.name) for t in teams
        ]

    def _populate_assignee_dropdown(team_key: str = "none"):
        if team_key and team_key != "none":
            try:
                tid = int(team_key)
                users = team_svc.user_repo.get_by_team(tid, active_only=True)
            except (ValueError, TypeError):
                users = team_svc.user_repo.get_all(active_only=True)
        else:
            users = team_svc.user_repo.get_all(active_only=True)
        dd_assignee.options = [ft.dropdown.Option(key="none", text="— ไม่ระบุ —")] + [
            ft.dropdown.Option(key=str(u.id), text=u.name) for u in users
        ]

    def _populate_depends_on_dropdown(exclude_task_id: Optional[int] = None):
        tasks = task_svc.get_all_tasks()
        tasks = [t for t in tasks
                 if t.id != exclude_task_id
                 and t.status != TaskStatus.CANCELLED]
        dd_depends_on.options = [ft.dropdown.Option(key="none", text="— ไม่มี —")] + [
            ft.dropdown.Option(key=str(t.id), text=f"{t.title[:40]} ({t.status.value})")
            for t in tasks
        ]

    def _close_task_dialog(e=None):
        task_dlg.open = False
        tf_title.value = tf_desc.value = tf_tags.value = ""
        tf_start_date.value = tf_due_date.value = ""
        dd_priority.value = "Medium"
        dd_team_dlg.value = "none"
        dd_assignee.value = "none"
        dd_depends_on.value = "none"
        task_dlg_err.value = ""
        _editing_task_id["value"] = None
        try:
            page.update()
        except Exception:
            pass

    def _save_task(e):
        title = (tf_title.value or "").strip()
        if not title:
            task_dlg_err.value = "กรุณาใส่ชื่องาน"
            try:
                page.update()
            except Exception:
                pass
            return
        try:
            start = _parse_date(tf_start_date.value)
            due   = _parse_date(tf_due_date.value)
        except ValueError as ex:
            task_dlg_err.value = str(ex)
            try:
                page.update()
            except Exception:
                pass
            return

        team_id = None
        if dd_team_dlg.value and dd_team_dlg.value != "none":
            try:
                team_id = int(dd_team_dlg.value)
            except (ValueError, TypeError):
                pass

        assignee_id = None
        if dd_assignee.value and dd_assignee.value != "none":
            try:
                assignee_id = int(dd_assignee.value)
            except (ValueError, TypeError):
                pass

        depends_on_id = None
        if dd_depends_on.value and dd_depends_on.value != "none":
            try:
                depends_on_id = int(dd_depends_on.value)
            except (ValueError, TypeError):
                pass

        try:
            if _editing_task_id["value"]:
                task_svc.update_task(
                    _editing_task_id["value"],
                    title=title,
                    description=tf_desc.value or "",
                    priority=TaskPriority(dd_priority.value),
                    tags=tf_tags.value or "",
                    start_date=start,
                    due_date=due,
                    team_id=team_id,
                    assignee_id=assignee_id,
                    depends_on_id=depends_on_id,
                )
            else:
                task_svc.create_task(
                    title=title,
                    description=tf_desc.value or "",
                    priority=TaskPriority(dd_priority.value),
                    tags=tf_tags.value or "",
                    start_date=start,
                    due_date=due,
                    team_id=team_id,
                    assignee_id=assignee_id,
                    depends_on_id=depends_on_id,
                )
            _close_task_dialog()
            _refresh_tasks()
        except Exception as ex:
            task_dlg_err.value = str(ex)
            try:
                page.update()
            except Exception:
                pass

    task_dlg = ft.AlertDialog(
        modal=True,
        bgcolor=BG_CARD,
        shape=ft.RoundedRectangleBorder(radius=12),
        title=task_dlg_title,
        content=ft.Container(
            width=440,
            content=ft.Column(
                controls=[
                    tf_title,
                    tf_desc,
                    ft.Row([dd_priority, dd_team_dlg], spacing=10),
                    dd_assignee,
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
        try:
            page.update()
        except Exception:
            pass

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
        team_key = e.control.value or "none"
        _populate_assignee_dropdown(team_key)
        dd_assignee.value = "none"
        try:
            dd_assignee.update()
        except Exception:
            pass

    dd_team_dlg.on_select = _on_team_dlg_change

    def _open_create(e=None):
        task_dlg_title.value = "สร้างงานใหม่"
        _editing_task_id["value"] = None
        tf_title.value = tf_desc.value = tf_tags.value = ""
        tf_start_date.value = tf_due_date.value = ""
        dd_priority.value = "Medium"
        task_dlg_err.value = ""
        _populate_team_dropdown()
        dd_team_dlg.value = "none"
        _populate_assignee_dropdown("none")
        dd_assignee.value = "none"
        _populate_depends_on_dropdown(exclude_task_id=None)
        dd_depends_on.value = "none"
        task_dlg.open = True
        try:
            page.update()
        except Exception:
            pass

    def _open_edit(task):
        task_dlg_title.value = "แก้ไขงาน"
        _editing_task_id["value"] = task.id
        tf_title.value       = task.title
        tf_desc.value        = task.description or ""
        tf_tags.value        = task.tags or ""
        dd_priority.value    = task.priority.value
        tf_start_date.value  = format_date(task.start_date) if task.start_date else ""
        tf_due_date.value    = format_date(task.due_date)   if task.due_date   else ""
        task_dlg_err.value   = ""
        _populate_team_dropdown()
        dd_team_dlg.value    = str(task.team_id) if task.team_id else "none"
        _populate_assignee_dropdown(dd_team_dlg.value)
        dd_assignee.value    = str(task.assignee_id) if task.assignee_id else "none"
        _populate_depends_on_dropdown(exclude_task_id=task.id)
        dd_depends_on.value  = str(task.depends_on_id) if task.depends_on_id else "none"
        task_dlg.open        = True
        try:
            page.update()
        except Exception:
            pass

    def _open_delete(task):
        confirm_msg.value = f'ต้องการลบงาน "{task.title}" ใช่ไหม?'
        def _do():
            if selected_task_id["value"] == task.id:
                selected_task_id["value"] = None
                detail_panel.visible = False
            task_svc.delete_task(task.id)
            _refresh_tasks()
        _confirm_fn["value"] = _do
        confirm_dlg.open = True
        try:
            page.update()
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════
    #  DEPENDENCY HELPERS (for detail panel)
    # ══════════════════════════════════════════════════════════════
    def _build_dependency_section(task) -> list:
        """Return list of controls showing dependency info (or empty list)."""
        controls = []
        # ── Show prerequisite task ──────────────────────────────
        if task.depends_on_id:
            dep = task_svc.task_repo.get_by_id(task.depends_on_id)
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
                                        ft.Text(dep.title, size=13, color=TEXT_PRI,
                                                expand=True, no_wrap=True,
                                                overflow=ft.TextOverflow.ELLIPSIS),
                                        _status_chip(dep.status.value),
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
                if dep.status != TaskStatus.DONE:
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
        dependents = task_svc.get_dependent_tasks(task.id)
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
                                        ft.Text(dt.title[:35], size=12,
                                                color=TEXT_PRI, expand=True,
                                                no_wrap=True,
                                                overflow=ft.TextOverflow.ELLIPSIS),
                                        _status_chip(dt.status.value),
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
    #  DETAIL PANEL
    # ══════════════════════════════════════════════════════════════
    def _build_detail_panel(task) -> ft.Container:
        # ── Subtask section ───────────────────────────────────────
        subtask_col = ft.Column(spacing=6)
        new_sub_tf  = ft.TextField(
            hint_text="เพิ่ม sub-task...",
            border_color=BORDER, focused_border_color=ACCENT,
            color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
            height=40, content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
            text_size=13,
        )

        def _refresh_subtasks():
            db.refresh(task)
            subtask_col.controls = [
                _subtask_row(st) for st in (task.subtasks or [])
            ]
            try:
                subtask_col.update()
            except Exception:
                pass

        def _subtask_row(st) -> ft.Row:
            return ft.Row(
                controls=[
                    ft.Checkbox(
                        value=st.is_done,
                        fill_color=ACCENT,
                        on_change=lambda e, sid=st.id: (
                            task_svc.toggle_subtask(sid),
                            _refresh_subtasks(),
                        ),
                    ),
                    ft.Text(
                        st.title, size=13,
                        color=TEXT_SEC if st.is_done else TEXT_PRI,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE, icon_size=14,
                        icon_color=TEXT_SEC,
                        on_click=lambda e, sid=st.id: (
                            task_svc.delete_subtask(sid),
                            _refresh_subtasks(),
                        ),
                    ),
                ],
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

        def _add_subtask(e):
            text = (new_sub_tf.value or "").strip()
            if text:
                task_svc.add_subtask(task.id, text)
                new_sub_tf.value = ""
                _refresh_subtasks()
                try:
                    page.update()
                except Exception:
                    pass

        _refresh_subtasks()

        # ── Comment section ───────────────────────────────────────
        comment_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
        new_comment_tf = ft.TextField(
            hint_text="เพิ่ม comment...",
            multiline=True, min_lines=2, max_lines=4,
            border_color=BORDER, focused_border_color=ACCENT,
            color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
            text_size=13,
        )

        def _refresh_comments():
            comments = task_svc.task_repo.get_comments(task.id)
            comment_col.controls = [_comment_bubble(c) for c in comments]
            try:
                comment_col.update()
            except Exception:
                pass

        def _comment_bubble(c) -> ft.Container:
            author_name = c.author.name if c.author else "ระบบ"
            return ft.Container(
                bgcolor=BG_INPUT,
                border_radius=8,
                padding=10,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=24, height=24, border_radius=12,
                                    bgcolor=ACCENT + "44",
                                    content=ft.Text(
                                        author_name[0].upper(),
                                        size=11, color=ACCENT,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    alignment=ft.alignment.Alignment.CENTER,
                                ),
                                ft.Text(author_name, size=12,
                                        color=ACCENT, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    c.created_at.strftime("%d/%m %H:%M"),
                                    size=11, color=TEXT_SEC,
                                ),
                            ],
                            spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Text(c.body, size=13, color=TEXT_PRI),
                    ],
                    spacing=4,
                ),
            )

        def _add_comment(e):
            body = (new_comment_tf.value or "").strip()
            if body:
                task_svc.add_comment(task.id, body)
                new_comment_tf.value = ""
                _refresh_comments()
                try:
                    page.update()
                except Exception:
                    pass

        _refresh_comments()

        # ── Status change buttons ─────────────────────────────────
        def _status_btn(s: str) -> ft.ElevatedButton:
            is_cur = task.status.value == s
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

        status_row = ft.Row(
            controls=[_status_btn(s) for s in STATUS_LIST],
            spacing=4, wrap=True,
        )

        # ── Header ────────────────────────────────────────────────
        assignee_name = task.assignee.name if task.assignee else "ไม่ระบุ"

        return ft.Container(
            expand=True,
            padding=ft.padding.all(16),
            bgcolor=BG_CARD,
            content=ft.Column(
                controls=[
                    # Title + close
                    ft.Row(
                        controls=[
                            ft.Text("รายละเอียดงาน", size=15,
                                    weight=ft.FontWeight.BOLD, color=TEXT_PRI),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_color=TEXT_SEC, icon_size=18,
                                on_click=lambda e: _close_detail(),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=1, color=BORDER),

                    # Task info
                    ft.Text(task.title, size=16,
                            weight=ft.FontWeight.BOLD, color=TEXT_PRI),
                    ft.Text(task.description or "ไม่มีคำอธิบาย",
                            size=13, color=TEXT_SEC),
                    ft.Row(
                        controls=[
                            _status_chip(task.status.value),
                            _priority_chip(task.priority.value),
                        ],
                        spacing=6,
                    ),
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.PERSON_OUTLINE, color=TEXT_SEC, size=14),
                            ft.Text(assignee_name, size=12, color=TEXT_SEC),
                            ft.Icon(ft.Icons.CALENDAR_TODAY_OUTLINED,
                                    color=TEXT_SEC, size=14),
                            _due_label(task.due_date),
                        ],
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),

                    # ── Dependency info ─────────────────────────────
                    *_build_dependency_section(task),

                    # Status change
                    ft.Text("เปลี่ยนสถานะ", size=12, color=TEXT_SEC),
                    status_row,

                    ft.Divider(height=1, color=BORDER),

                    # Sub-tasks
                    ft.Text("Sub-tasks", size=13,
                            weight=ft.FontWeight.W_500, color=TEXT_PRI),
                    subtask_col,
                    ft.Row(
                        controls=[
                            ft.Container(expand=True, content=new_sub_tf),
                            ft.IconButton(
                                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                                icon_color=ACCENT, icon_size=22,
                                tooltip="เพิ่ม sub-task",
                                on_click=_add_subtask,
                            ),
                        ],
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),

                    ft.Divider(height=1, color=BORDER),

                    # Comments
                    ft.Text("Comments", size=13,
                            weight=ft.FontWeight.W_500, color=TEXT_PRI),
                    ft.Container(
                        height=160,
                        content=comment_col,
                    ),
                    new_comment_tf,
                    ft.Button(
                        "ส่ง comment",
                        bgcolor=ACCENT, color="#FFFFFF",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                        on_click=_add_comment,
                    ),
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
        )

    # ══════════════════════════════════════════════════════════════
    #  TASK ROW
    # ══════════════════════════════════════════════════════════════
    def _build_task_row(task) -> ft.Container:
        is_selected = selected_task_id["value"] == task.id
        overdue     = is_overdue(task.due_date) and task.status not in (
            TaskStatus.DONE, TaskStatus.CANCELLED)

        left_accent_color = priority_color(task.priority.value)
        assignee_name = task.assignee.name if task.assignee else "—"

        tags_row = ft.Row(
            controls=[
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=6, vertical=1),
                    border_radius=10,
                    bgcolor=ACCENT2 + "22",
                    content=ft.Text(t.strip(), size=10, color=ACCENT2),
                )
                for t in (task.tags or "").split(",") if t.strip()
            ],
            spacing=4, wrap=True,
        )

        return ft.Container(
            bgcolor=BG_CARD if not is_selected else ACCENT + "11",
            border_radius=8,
            border=ft.border.only(
                left=ft.BorderSide(3, left_accent_color),
                top=ft.BorderSide(1, ACCENT + "44" if is_selected else BORDER),
                right=ft.BorderSide(1, ACCENT + "44" if is_selected else BORDER),
                bottom=ft.BorderSide(1, ACCENT + "44" if is_selected else BORDER),
            ),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            ink=True,
            on_click=lambda e, t=task: _select_task(t),
            content=ft.Row(
                controls=[
                    # Main info
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(task.title, size=14,
                                            weight=ft.FontWeight.W_500,
                                            color=TEXT_PRI, expand=True,
                                            no_wrap=True,
                                            overflow=ft.TextOverflow.ELLIPSIS),
                                    _status_chip(task.status.value),
                                    _priority_chip(task.priority.value),
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
                                    _due_label(task.due_date),
                                    tags_row,
                                ],
                                spacing=4,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=4, expand=True,
                    ),
                    # Action buttons
                    ft.Row(
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
                    ),
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
        if new_status_str in (TaskStatus.IN_PROGRESS.value,
                               TaskStatus.REVIEW.value,
                               TaskStatus.DONE.value):
            warning = task_svc.check_dependency_warning(task.id)
            if warning:
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
                except Exception:
                    pass

        task_svc.change_status(task.id, TaskStatus(new_status_str))
        _refresh_tasks()
        # Reopen detail with fresh data
        fresh = task_svc.get_task(task.id)
        _select_task(fresh, force=True)

    def _select_task(task, force: bool = False):
        if not force and selected_task_id["value"] == task.id:
            _close_detail()
            return
        selected_task_id["value"] = task.id
        detail_panel.content = _build_detail_panel(task)
        detail_panel.visible = True
        try:
            detail_panel.update()
        except Exception:
            pass
        _refresh_task_list_only()

    def _close_detail():
        selected_task_id["value"] = None
        detail_panel.visible = False
        try:
            detail_panel.update()
        except Exception:
            pass
        _refresh_task_list_only()

    def _refresh_task_list_only():
        tasks = _filtered_tasks()
        task_list_col.controls = [_build_task_row(t) for t in tasks] or [_empty_state()]
        try:
            task_list_col.update()
        except Exception:
            pass

    def _refresh_tasks():
        _refresh_task_list_only()
        # If detail open, refresh it too
        if selected_task_id["value"]:
            try:
                fresh = task_svc.get_task(selected_task_id["value"])
                detail_panel.content = _build_detail_panel(fresh)
                detail_panel.update()
            except Exception:
                _close_detail()

    def _filtered_tasks():
        tasks = task_svc.get_all_tasks()
        fs = filter_status["value"]
        fp = filter_priority["value"]
        sq = search_query["value"].lower()
        if fs != "ทั้งหมด":
            tasks = [t for t in tasks if t.status.value == fs]
        if fp != "ทั้งหมด":
            tasks = [t for t in tasks if t.priority.value == fp]
        if sq:
            tasks = [t for t in tasks if sq in t.title.lower()
                     or sq in (t.description or "").lower()
                     or sq in (t.tags or "").lower()]
        return tasks

    def _empty_state() -> ft.Container:
        return ft.Container(
            alignment=ft.alignment.Alignment.CENTER, padding=40,
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.TASK_ALT_OUTLINED, color=TEXT_SEC, size=48),
                    ft.Text("ไม่มีงาน", size=16, color=TEXT_SEC),
                    ft.Text("กดปุ่ม '+ สร้างงาน' เพื่อเริ่มต้น",
                            size=13, color=TEXT_SEC),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
        )

    # Initial load
    _refresh_task_list_only()

    # ══════════════════════════════════════════════════════════════
    #  FILTER BAR
    # ══════════════════════════════════════════════════════════════
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

    # Status filter row
    status_filters = ft.Row(
        controls=[
            _filter_chip("ทั้งหมด", "status", filter_status,
                         lambda: (_refresh_task_list_only(), _rebuild_filters())),
            *[_filter_chip(s, "status", filter_status,
                           lambda: (_refresh_task_list_only(), _rebuild_filters()))
              for s in STATUS_LIST],
        ],
        spacing=6, wrap=True,
    )

    priority_filters = ft.Row(
        controls=[
            _filter_chip("ทั้งหมด", "priority", filter_priority,
                         lambda: (_refresh_task_list_only(), _rebuild_filters())),
            *[_filter_chip(p, "priority", filter_priority,
                           lambda: (_refresh_task_list_only(), _rebuild_filters()))
              for p in PRIORITY_LIST],
        ],
        spacing=6, wrap=True,
    )

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
            ft.Row(
                controls=[
                    ft.Text("Status:", size=12, color=TEXT_SEC, width=60),
                    status_filters,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Row(
                controls=[
                    ft.Text("Priority:", size=12, color=TEXT_SEC, width=60),
                    priority_filters,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        spacing=6,
    )

    filter_container = ft.Ref[ft.Column]()

    def _rebuild_filters():
        """Rebuild filter chips so active state re-renders."""
        new_status_chips = [
            _filter_chip("ทั้งหมด", "s", filter_status,
                         lambda: (_refresh_task_list_only(), _rebuild_filters())),
            *[_filter_chip(s, "s", filter_status,
                           lambda: (_refresh_task_list_only(), _rebuild_filters()))
              for s in STATUS_LIST],
        ]
        new_priority_chips = [
            _filter_chip("ทั้งหมด", "p", filter_priority,
                         lambda: (_refresh_task_list_only(), _rebuild_filters())),
            *[_filter_chip(p, "p", filter_priority,
                           lambda: (_refresh_task_list_only(), _rebuild_filters()))
              for p in PRIORITY_LIST],
        ]
        status_filters.controls  = new_status_chips
        priority_filters.controls = new_priority_chips
        try:
            status_filters.update()
        except Exception:
            pass
        try:
            priority_filters.update()
        except Exception:
            pass

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
                        "+ สร้างงาน",
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
    #  ROOT LAYOUT
    # ══════════════════════════════════════════════════════════════
    left_pane = ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                top_bar,
                ft.Divider(height=16, color=BORDER),
                filter_col,
                ft.Divider(height=12, color=BORDER),
                task_list_col,
            ],
            spacing=0,
            expand=True,
        ),
        padding=ft.padding.all(24),
    )

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