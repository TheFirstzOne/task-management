# -*- coding: utf-8 -*-
"""
TeamView — Phase 21: Team Management UI (API-backed)
Features:
  - Team cards list (create / edit / delete)
  - Member list per team (add / edit / remove / toggle active)
  - Workload bar per member
Flet 0.80.x  —  function-based, no UserControl
"""

import flet as ft

from app.utils.theme import (
    BG_DARK, BG_CARD, BG_INPUT,
    ACCENT, ACCENT2, TEXT_PRI, TEXT_SEC, BORDER,
    COLOR_DONE, COLOR_URGENT,
)
from app.utils.logger import get_logger
from app.utils.ui_helpers import show_snack, safe_update
logger = get_logger(__name__)

# ── Role options ──────────────────────────────────────────────────────────────
ROLE_OPTIONS = ["Engineer", "Technician", "Operator", "Manager", "Other"]

# ── Workload colour thresholds ────────────────────────────────────────────────
def _workload_color(count: int) -> str:
    if count <= 2:  return "#00D4FF"       # cyan  — low load
    if count <= 4:  return "#FFC107"       # amber — medium load
    return COLOR_URGENT                    # red   — overloaded


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY
# ═════════════════════════════════════════════════════════════════════════════
def build_team_view(api, page: ft.Page) -> ft.Control:

    # ── Shared mutable refs ───────────────────────────────────────
    selected_team_id: dict = {"value": None}   # which team is expanded

    team_cards_col   = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO)
    member_panel_ref = ft.Ref[ft.Container]()

    # ═══════════════════════════════════════════════════════════════
    #  DIALOGS
    # ═══════════════════════════════════════════════════════════════

    # ── Team dialog ───────────────────────────────────────────────
    tf_team_name = ft.TextField(
        label="ชื่อทีม", hint_text="เช่น ทีม Maintenance",
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
    )
    tf_team_desc = ft.TextField(
        label="คำอธิบาย (optional)",
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
    )
    team_dialog_title = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRI)
    team_dialog_err   = ft.Text("", color=COLOR_URGENT, size=12)
    _editing_team_id: dict = {"value": None}

    def _close_team_dialog(e=None):
        team_dlg.open = False
        tf_team_name.value = ""
        tf_team_desc.value = ""
        team_dialog_err.value = ""
        _editing_team_id["value"] = None
        try:
            page.update()
        except Exception as e:
            logger.warning("load failed: %s", e, exc_info=True)

    def _save_team(e):
        name = (tf_team_name.value or "").strip()
        desc = (tf_team_desc.value or "").strip()
        if not name:
            team_dialog_err.value = "กรุณาใส่ชื่อทีม"
            try:
                page.update()
            except Exception as e:
                logger.warning("load failed: %s", e, exc_info=True)
            return
        try:
            if _editing_team_id["value"]:
                api.update_team(_editing_team_id["value"], name=name, description=desc)
            else:
                api.create_team(name, desc)
            _close_team_dialog()
            _refresh_teams()
        except ValueError as ex:
            team_dialog_err.value = str(ex)
            try:
                page.update()
            except Exception as e:
                logger.warning("load failed: %s", e, exc_info=True)

    team_dlg = ft.AlertDialog(
        modal=True,
        bgcolor=BG_CARD,
        shape=ft.RoundedRectangleBorder(radius=12),
        title=team_dialog_title,
        content=ft.Container(
            width=380,
            content=ft.Column(
                controls=[tf_team_name, tf_team_desc, team_dialog_err],
                spacing=12, tight=True,
            ),
        ),
        actions=[
            ft.TextButton("ยกเลิก", on_click=_close_team_dialog,
                          style=ft.ButtonStyle(color=TEXT_SEC)),
            ft.Button("บันทึก", bgcolor=ACCENT, color="#FFFFFF",
                              on_click=_save_team),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # ── Member dialog ─────────────────────────────────────────────
    tf_mem_name  = ft.TextField(
        label="ชื่อสมาชิก",
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
    )
    dd_mem_role = ft.Dropdown(
        label="ตำแหน่ง / Role",
        options=[ft.dropdown.Option(r) for r in ROLE_OPTIONS],
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
        value=ROLE_OPTIONS[0],
    )
    tf_mem_skills = ft.TextField(
        label="ทักษะ (คั่นด้วย ,)",
        hint_text="เช่น Python, CNC, PLC",
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
    )
    mem_dialog_title = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRI)
    mem_dialog_err   = ft.Text("", color=COLOR_URGENT, size=12)
    _editing_member_id: dict = {"value": None}
    _mem_team_id: dict       = {"value": None}

    def _close_mem_dialog(e=None):
        mem_dlg.open = False
        tf_mem_name.value   = ""
        tf_mem_skills.value = ""
        mem_dialog_err.value = ""
        dd_mem_role.value   = ROLE_OPTIONS[0]
        _editing_member_id["value"] = None
        try:
            page.update()
        except Exception as e:
            logger.warning("load failed: %s", e, exc_info=True)

    def _save_member(e):
        name   = (tf_mem_name.value or "").strip()
        skills = (tf_mem_skills.value or "").strip()
        role   = dd_mem_role.value or ROLE_OPTIONS[0]
        if not name:
            mem_dialog_err.value = "กรุณาใส่ชื่อสมาชิก"
            try:
                page.update()
            except Exception as e:
                logger.warning("load failed: %s", e, exc_info=True)
            return
        try:
            if _editing_member_id["value"]:
                api.update_member(
                    _editing_member_id["value"],
                    name=name, role=role, skills=skills,
                )
            else:
                api.add_member(_mem_team_id["value"], name, role, skills)
            _close_mem_dialog()
            _refresh_teams()
        except Exception as ex:
            logger.error("save failed: %s", ex, exc_info=True)
            show_snack(page, f"เกิดข้อผิดพลาด: {ex}", error=True)
            mem_dialog_err.value = str(ex)
            try:
                page.update()
            except Exception as e:
                logger.warning("load failed: %s", e, exc_info=True)

    mem_dlg = ft.AlertDialog(
        modal=True,
        bgcolor=BG_CARD,
        shape=ft.RoundedRectangleBorder(radius=12),
        title=mem_dialog_title,
        content=ft.Container(
            width=380,
            content=ft.Column(
                controls=[tf_mem_name, dd_mem_role, tf_mem_skills, mem_dialog_err],
                spacing=12, tight=True,
            ),
        ),
        actions=[
            ft.TextButton("ยกเลิก", on_click=_close_mem_dialog,
                          style=ft.ButtonStyle(color=TEXT_SEC)),
            ft.Button("บันทึก", bgcolor=ACCENT, color="#FFFFFF",
                              on_click=_save_member),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # ── Confirm delete dialog ─────────────────────────────────────
    confirm_msg      = ft.Text("", color=TEXT_SEC, size=14)
    _confirm_action: dict = {"fn": None}

    def _close_confirm(e=None):
        confirm_dlg.open = False
        try:
            page.update()
        except Exception as e:
            logger.warning("load failed: %s", e, exc_info=True)

    def _do_confirm(e):
        _close_confirm()
        if _confirm_action["fn"]:
            _confirm_action["fn"]()

    confirm_dlg = ft.AlertDialog(
        modal=True,
        bgcolor=BG_CARD,
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

    # Register dialogs
    page.overlay.extend([team_dlg, mem_dlg, confirm_dlg])

    # ═══════════════════════════════════════════════════════════════
    #  HELPERS — open dialogs
    # ═══════════════════════════════════════════════════════════════
    def _open_add_team(e=None):
        team_dialog_title.value = "เพิ่มทีมใหม่"
        _editing_team_id["value"] = None
        tf_team_name.value = ""
        tf_team_desc.value = ""
        team_dialog_err.value = ""
        team_dlg.open = True
        try:
            page.update()
        except Exception as e:
            logger.warning("load failed: %s", e, exc_info=True)

    def _open_edit_team(team):
        team_dialog_title.value = "แก้ไขทีม"
        _editing_team_id["value"] = team["id"]
        tf_team_name.value = team["name"]
        tf_team_desc.value = team.get("description") or ""
        team_dialog_err.value = ""
        team_dlg.open = True
        try:
            page.update()
        except Exception as e:
            logger.warning("load failed: %s", e, exc_info=True)

    def _open_delete_team(team):
        confirm_msg.value = (
            f'ต้องการลบทีม "{team["name"]}" ใช่ไหม?\n'
            f'สมาชิกทุกคนจะถูก unassign ออกจากทีม (ยังคงอยู่ในระบบ)'
        )
        def _do():
            try:
                api.delete_team(team["id"])
                if selected_team_id["value"] == team["id"]:
                    selected_team_id["value"] = None
                show_snack(page, f'ลบทีม "{team["name"]}" เรียบร้อย')
            except Exception as ex:
                logger.error("delete team failed: %s", ex, exc_info=True)
                show_snack(page, f"เกิดข้อผิดพลาด: {ex}", error=True)
            _refresh_teams()
        _confirm_action["fn"] = _do
        confirm_dlg.open = True
        try:
            page.update()
        except Exception as e:
            logger.warning("load failed: %s", e, exc_info=True)

    def _open_add_member(team_id: int):
        mem_dialog_title.value = "เพิ่มสมาชิก"
        _editing_member_id["value"] = None
        _mem_team_id["value"] = team_id
        tf_mem_name.value   = ""
        tf_mem_skills.value = ""
        dd_mem_role.value   = ROLE_OPTIONS[0]
        mem_dialog_err.value = ""
        mem_dlg.open = True
        try:
            page.update()
        except Exception as e:
            logger.warning("load failed: %s", e, exc_info=True)

    def _open_edit_member(member):
        mem_dialog_title.value = "แก้ไขสมาชิก"
        _editing_member_id["value"] = member["id"]
        _mem_team_id["value"] = member.get("team_id")
        tf_mem_name.value   = member["name"]
        tf_mem_skills.value = member.get("skills") or ""
        dd_mem_role.value   = member.get("role") or ROLE_OPTIONS[0]
        mem_dialog_err.value = ""
        mem_dlg.open = True
        try:
            page.update()
        except Exception as e:
            logger.warning("load failed: %s", e, exc_info=True)

    def _open_delete_member(member):
        confirm_msg.value = (
            f'ต้องการลบ "{member["name"]}" ออกจากระบบใช่ไหม?\n'
            f'งานที่ยังดำเนินอยู่จะถูก unassign โดยอัตโนมัติ'
        )
        def _do():
            try:
                api.delete_member(member["id"])
                show_snack(page, f'ลบสมาชิก "{member["name"]}" เรียบร้อย')
            except Exception as ex:
                logger.error("delete member failed: %s", ex, exc_info=True)
                show_snack(page, f"เกิดข้อผิดพลาด: {ex}", error=True)
            _refresh_teams()
        _confirm_action["fn"] = _do
        confirm_dlg.open = True
        try:
            page.update()
        except Exception as e:
            logger.warning("load failed: %s", e, exc_info=True)

    # ═══════════════════════════════════════════════════════════════
    #  BUILD: member row
    # ═══════════════════════════════════════════════════════════════
    def _build_member_row(member, workload: int) -> ft.Container:
        bar_pct  = min(workload / 8, 1.0)
        bar_color = _workload_color(workload)
        member_role = member.get("role") or "Other"
        member_name = member["name"]
        is_active = member.get("is_active", True)

        role_chip = ft.Container(
            padding=ft.padding.symmetric(horizontal=8, vertical=2),
            border_radius=20,
            bgcolor=ACCENT + "22",
            content=ft.Text(member_role, size=11, color=ACCENT),
        )

        active_icon = ft.IconButton(
            icon=ft.Icons.TOGGLE_ON if is_active else ft.Icons.TOGGLE_OFF,
            icon_color=ACCENT2 if is_active else TEXT_SEC,
            icon_size=22,
            tooltip="เปิด/ปิด Active",
            on_click=lambda e, mid=member["id"]: _toggle_active(mid),
        )

        skills_text = ft.Text(
            member.get("skills") or "—",
            size=11, color=TEXT_SEC,
            no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS,
        )

        workload_row = ft.Row(
            controls=[
                ft.Text(f"งาน {workload}", size=11, color=bar_color),
                ft.Container(
                    width=80, height=4, border_radius=4,
                    bgcolor=BORDER,
                    content=ft.Container(
                        width=80 * bar_pct,
                        height=4,
                        border_radius=4,
                        bgcolor=bar_color,
                    ),
                ),
            ],
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Container(
            bgcolor=BG_INPUT,
            border_radius=8,
            border=ft.border.all(1, BORDER),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            content=ft.Row(
                controls=[
                    # Avatar
                    ft.Container(
                        width=36, height=36, border_radius=18,
                        bgcolor=ACCENT,
                        content=ft.Text(
                            member_name[0].upper(),
                            size=14, weight=ft.FontWeight.BOLD,
                            color="#FFFFFF",
                            text_align=ft.TextAlign.CENTER,
                        ),
                        alignment=ft.alignment.Alignment.CENTER,
                    ),
                    # Info
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(member_name, size=14,
                                            weight=ft.FontWeight.W_500, color=TEXT_PRI),
                                    role_chip,
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Row(
                                controls=[skills_text, workload_row],
                                spacing=12,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=4, expand=True,
                    ),
                    # Actions
                    ft.Row(
                        controls=[
                            active_icon,
                            ft.IconButton(
                                icon=ft.Icons.EDIT_OUTLINED,
                                icon_color=TEXT_SEC, icon_size=18,
                                tooltip="แก้ไข",
                                on_click=lambda e, m=member: _open_edit_member(m),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color=COLOR_URGENT, icon_size=18,
                                tooltip="ลบ",
                                on_click=lambda e, m=member: _open_delete_member(m),
                            ),
                        ],
                        spacing=0,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    # ═══════════════════════════════════════════════════════════════
    #  BUILD: team card
    # ═══════════════════════════════════════════════════════════════
    def _build_team_card(team) -> ft.Container:
        members  = team.get("members", [])
        workload = api.get_workload(team["id"])
        active_c = sum(1 for m in members if m.get("is_active", True))
        is_open  = selected_team_id["value"] == team["id"]

        # ── Member rows (collapsible) ─────────────────────────────
        member_rows = ft.Column(
            controls=[
                _build_member_row(m, workload.get(str(m["id"]), workload.get(m["id"], 0)))
                for m in members
            ],
            spacing=6,
            visible=is_open,
        )

        add_member_btn = ft.TextButton(
            "+ เพิ่มสมาชิก",
            icon=ft.Icons.PERSON_ADD_ALT_1_OUTLINED,
            style=ft.ButtonStyle(color=ACCENT),
            on_click=lambda e, tid=team["id"]: _open_add_member(tid),
            visible=is_open,
        )

        # ── Header ───────────────────────────────────────────────
        def _toggle_expand(e, tid=team["id"]):
            if selected_team_id["value"] == tid:
                selected_team_id["value"] = None
            else:
                selected_team_id["value"] = tid
            _refresh_teams()

        expand_icon = ft.Icon(
            ft.Icons.KEYBOARD_ARROW_DOWN if is_open else ft.Icons.KEYBOARD_ARROW_RIGHT,
            color=TEXT_SEC, size=20,
        )

        member_count_badge = ft.Container(
            padding=ft.padding.symmetric(horizontal=8, vertical=2),
            border_radius=12,
            bgcolor=BG_INPUT,
            content=ft.Text(
                f"{active_c} / {len(members)} คน",
                size=12, color=TEXT_SEC,
            ),
        )

        header = ft.Container(
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            ink=True,
            border_radius=ft.border_radius.only(
                top_left=10, top_right=10,
                bottom_left=0 if is_open else 10,
                bottom_right=0 if is_open else 10,
            ),
            on_click=_toggle_expand,
            content=ft.Row(
                controls=[
                    expand_icon,
                    ft.Icon(ft.Icons.GROUPS_2_OUTLINED, color=ACCENT, size=22),
                    ft.Column(
                        controls=[
                            ft.Text(team["name"], size=16,
                                    weight=ft.FontWeight.BOLD, color=TEXT_PRI),
                            ft.Text(team.get("description") or "ไม่มีคำอธิบาย",
                                    size=12, color=TEXT_SEC,
                                    no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                        ],
                        spacing=2, expand=True,
                    ),
                    member_count_badge,
                    ft.IconButton(
                        icon=ft.Icons.EDIT_OUTLINED,
                        icon_color=TEXT_SEC, icon_size=18,
                        tooltip="แก้ไขทีม",
                        on_click=lambda e, t=team: _open_edit_team(t),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=COLOR_URGENT, icon_size=18,
                        tooltip="ลบทีม",
                        on_click=lambda e, t=team: _open_delete_team(t),
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # ── Body (members) ─────────────────────────────────────────
        body = ft.Container(
            visible=is_open,
            padding=ft.padding.only(left=16, right=16, bottom=14),
            border=ft.border.only(
                left=ft.BorderSide(1, BORDER),
                right=ft.BorderSide(1, BORDER),
                bottom=ft.BorderSide(1, BORDER),
            ),
            border_radius=ft.border_radius.only(bottom_left=10, bottom_right=10),
            bgcolor=BG_CARD,
            content=ft.Column(
                controls=[
                    ft.Divider(height=1, color=BORDER),
                    member_rows,
                    add_member_btn,
                ],
                spacing=8,
            ),
        )

        return ft.Column(
            controls=[
                ft.Container(
                    bgcolor=BG_CARD,
                    border_radius=ft.border_radius.only(
                        top_left=10, top_right=10,
                        bottom_left=0 if is_open else 10,
                        bottom_right=0 if is_open else 10,
                    ),
                    border=ft.border.only(
                        top=ft.BorderSide(1, BORDER),
                        left=ft.BorderSide(1, BORDER),
                        right=ft.BorderSide(1, BORDER),
                        bottom=ft.BorderSide(0 if is_open else 1, BORDER),
                    ),
                    content=header,
                ),
                body,
            ],
            spacing=0,
        )

    # ═══════════════════════════════════════════════════════════════
    #  ACTIONS
    # ═══════════════════════════════════════════════════════════════
    def _toggle_active(member_id: int):
        api.toggle_member_active(member_id)
        _refresh_teams()

    def _refresh_teams():
        teams = api.get_teams()
        team_cards_col.controls = [_build_team_card(t) for t in teams]

        # Empty state
        if not teams:
            team_cards_col.controls = [
                ft.Container(
                    alignment=ft.alignment.Alignment.CENTER,
                    padding=40,
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.GROUPS_OUTLINED, color=TEXT_SEC, size=48),
                            ft.Text("ยังไม่มีทีม", size=16, color=TEXT_SEC),
                            ft.Text("กดปุ่ม '+ สร้างทีม' เพื่อเริ่มต้น",
                                    size=13, color=TEXT_SEC),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                )
            ]
        safe_update(team_cards_col)

    # Initial load
    _refresh_teams()

    # ═══════════════════════════════════════════════════════════════
    #  TOP BAR
    # ═══════════════════════════════════════════════════════════════
    top_bar = ft.Row(
        controls=[
            ft.Column(
                controls=[
                    ft.Text("ทีมงาน", size=24,
                            weight=ft.FontWeight.BOLD, color=TEXT_PRI),
                    ft.Text("จัดการทีมและสมาชิก", size=13, color=TEXT_SEC),
                ],
                spacing=2,
            ),
            ft.Button(
                "+ สร้างทีม",
                icon=ft.Icons.ADD,
                bgcolor=ACCENT, color="#FFFFFF",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                on_click=_open_add_team,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    # ═══════════════════════════════════════════════════════════════
    #  ROOT LAYOUT
    # ═══════════════════════════════════════════════════════════════
    return ft.Container(
        expand=True,
        bgcolor=BG_DARK,
        padding=ft.padding.all(24),
        content=ft.Column(
            controls=[
                top_bar,
                ft.Divider(height=20, color=BORDER),
                ft.Container(
                    expand=True,
                    content=team_cards_col,
                ),
            ],
            spacing=0,
            expand=True,
        ),
    )
