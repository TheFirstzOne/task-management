# -*- coding: utf-8 -*-
"""
Milestone View — Phase 22
แสดงรายการ Milestone + สร้าง/แก้ไข/ลบ + assign task + progress bar
"""

from __future__ import annotations

import flet as ft
from typing import Callable, Optional

from app.utils.theme import (
    ACCENT, BG_CARD, BG_DARK, BG_INPUT, BORDER,
    TEXT_DIM, TEXT_PRI, TEXT_SEC,
    status_color, priority_color,
)
from app.utils.ui_helpers import show_snack, confirm_dialog, safe_page_update
from app.utils.exceptions import TaskFlowError
from app.utils.logger import get_logger

logger = get_logger(__name__)


def build_milestone_view(api, page: ft.Page, navigate_fn: Optional[Callable] = None) -> ft.Control:
    """Milestone management view — สร้าง/แก้ไข/ลบ milestone และ assign tasks"""

    # ── State ──────────────────────────────────────────────────────────────────
    milestones: list[dict] = []
    selected_milestone: dict = {}   # {"value": milestone_dict | None}
    selected_milestone["value"] = None

    # ── Refs ───────────────────────────────────────────────────────────────────
    milestone_list_col = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

    # ── Dialog fields ──────────────────────────────────────────────────────────
    tf_name = ft.TextField(
        label="ชื่อ Milestone *",
        hint_text="เช่น Release v2.2",
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
    )
    tf_description = ft.TextField(
        label="รายละเอียด",
        multiline=True, min_lines=2, max_lines=3,
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
    )
    dp_due_date = ft.TextField(
        label="Due Date (YYYY-MM-DD)",
        hint_text="เช่น 2026-05-30 (ไม่บังคับ)",
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
    )

    # Assign task dropdown
    dd_assign_task = ft.Dropdown(
        label="เลือกงานที่จะเพิ่ม",
        options=[],
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
    )

    # ── Dialog ─────────────────────────────────────────────────────────────────
    edit_id: dict = {"value": None}  # None = create mode, int = edit mode

    dialog_title = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRI)

    milestone_dlg = ft.AlertDialog(
        modal=True,
        title=dialog_title,
        content=ft.Container(
            width=400,
            content=ft.Column(
                [tf_name, tf_description, dp_due_date],
                spacing=12, tight=True,
            ),
        ),
        actions=[
            ft.TextButton("ยกเลิก", on_click=lambda _: _close_dialog()),
            ft.ElevatedButton(
                "บันทึก",
                on_click=lambda _: _save_milestone(),
                bgcolor=ACCENT, color="#FFFFFF",
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(milestone_dlg)

    # Assign task dialog
    assign_dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("เพิ่มงานเข้า Milestone", color=TEXT_PRI),
        content=ft.Container(width=380, content=dd_assign_task),
        actions=[
            ft.TextButton("ยกเลิก", on_click=lambda _: _close_assign_dialog()),
            ft.ElevatedButton(
                "เพิ่ม",
                on_click=lambda _: _do_assign_task(),
                bgcolor=ACCENT, color="#FFFFFF",
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(assign_dlg)

    # ── Data loading ───────────────────────────────────────────────────────────

    def _load_milestones():
        nonlocal milestones
        try:
            milestones = api.get_milestones()
        except TaskFlowError as e:
            show_snack(page, str(e), error=True)
            milestones = []
        _rebuild_list()

    def _rebuild_list():
        if not milestones:
            milestone_list_col.controls = [
                ft.Container(
                    padding=ft.padding.symmetric(vertical=60),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.FLAG_OUTLINED, size=48, color=TEXT_DIM),
                            ft.Text("ยังไม่มี Milestone", size=16, color=TEXT_DIM),
                            ft.Text("กด '+ สร้าง' เพื่อเพิ่มเป้าหมายใหม่", size=13, color=TEXT_DIM),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                )
            ]
        else:
            milestone_list_col.controls = [_build_milestone_card(m) for m in milestones]
        try:
            milestone_list_col.update()
        except Exception:
            safe_page_update(page)

    # ── Card builder ───────────────────────────────────────────────────────────

    def _build_milestone_card(m: dict) -> ft.Container:
        progress = m.get("progress", 0.0)
        task_count = m.get("task_count", 0)
        done_count = m.get("done_count", 0)
        due = m.get("due_date")
        due_label = due[:10] if due else "ไม่ระบุวัน"

        # Progress color
        if progress >= 1.0:
            prog_color = "#22C55E"      # green — done
        elif progress >= 0.5:
            prog_color = ACCENT         # blue — halfway
        else:
            prog_color = "#F59E0B"      # amber — early stage

        # Task chips (max 5 shown) — each chip มีปุ่ม ✕ ลบออกจาก milestone
        task_chips: list[ft.Control] = []
        if task_count > 0:
            try:
                detail = api.get_milestone(m["id"])
                all_tasks_in = detail.get("tasks", [])
                tasks_in = all_tasks_in[:5]
                for t in tasks_in:
                    task_chips.append(
                        ft.Container(
                            bgcolor=f"{status_color(t.get('status', 'Pending'))}22",
                            border_radius=4,
                            padding=ft.padding.only(left=8, right=4, top=3, bottom=3),
                            content=ft.Row(
                                [
                                    ft.Text(
                                        t.get("title", "")[:20],
                                        size=11, color=TEXT_PRI,
                                    ),
                                    ft.GestureDetector(
                                        content=ft.Icon(
                                            ft.Icons.CLOSE, size=12, color=TEXT_SEC
                                        ),
                                        on_tap=lambda _, tid=t["id"], mid=m["id"]: _remove_task_from_milestone(mid, tid),
                                    ),
                                ],
                                spacing=4,
                                tight=True,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        )
                    )
                if len(all_tasks_in) > 5:
                    task_chips.append(
                        ft.Text(f"+{len(all_tasks_in) - 5} งาน", size=11, color=TEXT_SEC)
                    )
            except Exception:
                pass

        return ft.Container(
            bgcolor=BG_CARD,
            border_radius=12,
            border=ft.border.all(1, BORDER),
            padding=ft.padding.all(16),
            content=ft.Column(
                [
                    # Header row
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.FLAG, size=18, color=ACCENT),
                                    ft.Text(m["name"], size=15, weight=ft.FontWeight.W_600, color=TEXT_PRI),
                                ],
                                spacing=6,
                                expand=True,
                            ),
                            # Actions
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.ADD_TASK_OUTLINED,
                                        icon_size=18, icon_color=ACCENT, tooltip="เพิ่มงาน",
                                        on_click=lambda _, mid=m["id"]: _open_assign_dialog(mid),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT_OUTLINED,
                                        icon_size=18, icon_color=TEXT_SEC, tooltip="แก้ไข",
                                        on_click=lambda _, ms=m: _open_edit_dialog(ms),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_OUTLINE,
                                        icon_size=18, icon_color="#EF4444", tooltip="ลบ",
                                        on_click=lambda _, mid=m["id"], mname=m["name"]: _confirm_delete(mid, mname),
                                    ),
                                ],
                                spacing=0,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    # Due date + task count
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.CALENDAR_TODAY_OUTLINED, size=13, color=TEXT_SEC),
                                    ft.Text(due_label, size=12, color=TEXT_SEC),
                                ],
                                spacing=4,
                            ),
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.TASK_ALT_OUTLINED, size=13, color=TEXT_SEC),
                                    ft.Text(f"{done_count}/{task_count} งาน", size=12, color=TEXT_SEC),
                                ],
                                spacing=4,
                            ),
                        ],
                        spacing=16,
                    ),
                    # Progress bar
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.ProgressBar(
                                        value=progress,
                                        color=prog_color,
                                        bgcolor=BORDER,
                                        expand=True,
                                        height=8,
                                        border_radius=4,
                                    ),
                                    ft.Text(f"{int(progress * 100)}%", size=12, color=TEXT_SEC, width=36),
                                ],
                                spacing=8,
                            ),
                        ],
                        spacing=4,
                    ),
                    # Task chips (if any)
                    *(
                        [ft.Row(task_chips, wrap=True, spacing=6, run_spacing=4)]
                        if task_chips else
                        [ft.Text("ยังไม่มีงาน — กด + เพื่อเพิ่มงาน", size=12, color=TEXT_DIM)]
                    ),
                    # Description
                    *(
                        [ft.Text(m["description"], size=12, color=TEXT_SEC)]
                        if m.get("description") else []
                    ),
                ],
                spacing=10,
            ),
        )

    # ── Dialog open/close ──────────────────────────────────────────────────────

    def _open_create_dialog():
        edit_id["value"] = None
        dialog_title.value = "สร้าง Milestone ใหม่"
        tf_name.value = ""
        tf_description.value = ""
        dp_due_date.value = ""
        milestone_dlg.open = True
        safe_page_update(page)

    def _open_edit_dialog(m: dict):
        edit_id["value"] = m["id"]
        dialog_title.value = "แก้ไข Milestone"
        tf_name.value = m.get("name", "")
        tf_description.value = m.get("description", "")
        due = m.get("due_date")
        dp_due_date.value = due[:10] if due else ""
        milestone_dlg.open = True
        safe_page_update(page)

    def _close_dialog():
        milestone_dlg.open = False
        safe_page_update(page)

    def _open_assign_dialog(milestone_id: int):
        selected_milestone["value"] = milestone_id
        # Populate task dropdown
        try:
            all_tasks = api.get_tasks()
            # Exclude tasks already in any milestone
            unassigned = [t for t in all_tasks if not t.get("milestone_id")]
            dd_assign_task.options = [
                ft.dropdown.Option(key=str(t["id"]), text=t["title"][:50])
                for t in unassigned
            ]
            dd_assign_task.value = None
        except TaskFlowError as e:
            show_snack(page, str(e), error=True)
            return
        assign_dlg.open = True
        safe_page_update(page)

    def _close_assign_dialog():
        assign_dlg.open = False
        safe_page_update(page)

    # ── CRUD handlers ──────────────────────────────────────────────────────────

    def _save_milestone():
        name = (tf_name.value or "").strip()
        if not name:
            show_snack(page, "กรุณาระบุชื่อ Milestone", error=True)
            return
        due_str = (dp_due_date.value or "").strip() or None

        _close_dialog()
        try:
            if edit_id["value"] is None:
                api.create_milestone(
                    name=name,
                    description=tf_description.value or "",
                    due_date=due_str,
                )
                show_snack(page, f"สร้าง Milestone '{name}' สำเร็จ")
            else:
                kwargs: dict = {"name": name, "description": tf_description.value or ""}
                if due_str is not None:
                    kwargs["due_date"] = due_str
                api.update_milestone(edit_id["value"], **kwargs)
                show_snack(page, f"อัปเดต Milestone '{name}' สำเร็จ")
            _load_milestones()
        except TaskFlowError as e:
            show_snack(page, str(e), error=True)

    def _confirm_delete(milestone_id: int, name: str):
        confirm_dialog(
            page,
            title="ยืนยันการลบ",
            message=f"ต้องการลบ Milestone '{name}' ?\nงานที่อยู่ใน Milestone จะถูกยกเลิกการจัดกลุ่ม",
            on_confirm=lambda _: _do_delete(milestone_id, name),
        )

    def _do_delete(milestone_id: int, name: str):
        try:
            api.delete_milestone(milestone_id)
            show_snack(page, f"ลบ Milestone '{name}' แล้ว")
            _load_milestones()
        except TaskFlowError as e:
            show_snack(page, str(e), error=True)

    def _do_assign_task():
        task_id_str = dd_assign_task.value
        mid = selected_milestone["value"]
        if not task_id_str or not mid:
            show_snack(page, "กรุณาเลือกงาน", error=True)
            return
        _close_assign_dialog()
        try:
            api.assign_task_to_milestone(int(mid), int(task_id_str))
            show_snack(page, "เพิ่มงานเข้า Milestone สำเร็จ")
            _load_milestones()
        except TaskFlowError as e:
            show_snack(page, str(e), error=True)

    def _remove_task_from_milestone(milestone_id: int, task_id: int):
        try:
            api.remove_task_from_milestone(milestone_id, task_id)
            show_snack(page, "นำงานออกจาก Milestone แล้ว")
            _load_milestones()
        except TaskFlowError as e:
            show_snack(page, str(e), error=True)

    # ── Initial load ───────────────────────────────────────────────────────────
    _load_milestones()

    # ── Layout ─────────────────────────────────────────────────────────────────
    header = ft.Row(
        [
            ft.Column(
                [
                    ft.Text("Milestone", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRI),
                    ft.Text("จัดการเป้าหมายของทีม", size=13, color=TEXT_SEC),
                ],
                spacing=2,
                expand=True,
            ),
            ft.ElevatedButton(
                "+ สร้าง",
                on_click=lambda _: _open_create_dialog(),
                bgcolor=ACCENT, color="#FFFFFF",
                style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=20, vertical=12)),
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    return ft.Container(
        expand=True,
        bgcolor=BG_DARK,
        content=ft.Container(
            expand=True,
            padding=ft.padding.all(24),
            content=ft.Column(
                [
                    header,
                    ft.Divider(height=16, color=BORDER),
                    milestone_list_col,
                ],
                spacing=0,
                expand=True,
            ),
        ),
    )
