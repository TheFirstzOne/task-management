# -*- coding: utf-8 -*-
"""
SettingsView — Phase 19: User Management (Admin Panel)
Admin เท่านั้นที่เข้าถึงได้
- ดูรายชื่อ user ทั้งหมด
- สร้าง login account ใหม่
- กำหนด/reset username + password ให้ existing user
- toggle admin status
"""
from __future__ import annotations

import flet as ft

from app.utils.exceptions import ValidationError, TaskFlowError
from app.utils.ui_helpers import show_snack, confirm_dialog
import app.utils.theme as theme

# UserRole values — kept as plain strings to avoid ORM import
_USER_ROLES = ["Technician", "Engineer", "CNC", "PLC", "Hydraulic", "Other"]
_DEFAULT_ROLE = "Other"


def build_settings_view(api, page: ft.Page) -> ft.Control:
    """Admin panel — user account management."""

    # ── Current logged-in user from session ───────────────────────
    current  = page.session.store.get("current_user") or {}
    is_admin = current.get("is_admin", False)

    # ── State ─────────────────────────────────────────────────────
    user_list_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    _dialog_ref   = {"value": None}

    # ── Helpers ───────────────────────────────────────────────────
    def _close_dialog():
        if _dialog_ref["value"]:
            _dialog_ref["value"].open = False
            page.update()

    def _open_dialog(dlg: ft.AlertDialog):
        _dialog_ref["value"] = dlg
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def _refresh_list():
        try:
            users = api.get_users()
        except Exception:
            users = []
        user_list_col.controls.clear()
        for u in users:
            user_list_col.controls.append(_build_user_row(u))
        page.update()

    # ── User row card ─────────────────────────────────────────────
    def _build_user_row(u: dict) -> ft.Container:
        has_login = bool(u.get("username"))

        admin_badge = ft.Container(
            visible=bool(u.get("is_admin", False)),
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            border_radius=10,
            bgcolor=theme.ACCENT + "22",
            content=ft.Text("Admin", size=10, color=theme.ACCENT,
                            weight=ft.FontWeight.W_600),
        )
        inactive_badge = ft.Container(
            visible=not u.get("is_active", True),
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            border_radius=10,
            bgcolor="#F1F5F9",
            content=ft.Text("ไม่ใช้งาน", size=10, color=theme.TEXT_SEC),
        )

        login_status = ft.Text(
            f"@{u.get('username')}" if has_login else "— ยังไม่มี username",
            size=12,
            color=theme.ACCENT if has_login else theme.TEXT_DIM,
        )

        # Action buttons
        btn_set_cred = ft.TextButton(
            "กำหนด Login" if not has_login else "เปลี่ยนรหัส",
            style=ft.ButtonStyle(color=theme.ACCENT),
            on_click=lambda e, uid=u["id"], uname=u.get("username"): _show_set_credential_dialog(uid, uname),
            visible=is_admin,
        )

        btn_toggle_admin = ft.TextButton(
            "ถอด Admin" if u.get("is_admin", False) else "ตั้งเป็น Admin",
            style=ft.ButtonStyle(color=theme.TEXT_SEC),
            on_click=lambda e, uid=u["id"], cur_admin=u.get("is_admin", False): _toggle_admin(uid, cur_admin),
            visible=is_admin and u["id"] != current.get("id"),
        )

        return ft.Container(
            bgcolor=theme.BG_CARD,
            border=ft.border.all(1, theme.BORDER),
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=36, height=36, border_radius=18,
                        bgcolor=theme.ACCENT + "22",
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text(
                            (u.get("name") or "?")[0].upper(),
                            size=15, weight=ft.FontWeight.BOLD,
                            color=theme.ACCENT,
                        ),
                    ),
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(u.get("name", ""), size=14,
                                            weight=ft.FontWeight.W_500,
                                            color=theme.TEXT_PRI),
                                    admin_badge,
                                    inactive_badge,
                                ],
                                spacing=6,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text(u.get("role", ""),
                                            size=12, color=theme.TEXT_SEC),
                                    ft.Text("·", color=theme.TEXT_DIM, size=12),
                                    login_status,
                                ],
                                spacing=4,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Row(
                        controls=[btn_set_cred, btn_toggle_admin],
                        spacing=4,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    # ── Set credential dialog ─────────────────────────────────────
    def _show_set_credential_dialog(user_id: int, current_username: str | None):
        is_new = not current_username

        tf_username = ft.TextField(
            label="Username",
            value=current_username or "",
            border_radius=8,
            border_color=theme.BORDER,
            focused_border_color=theme.ACCENT,
            text_size=14,
            disabled=not is_new,   # username ไม่เปลี่ยนถ้ามีแล้ว
            bgcolor=theme.BG_INPUT,
        )
        tf_password = ft.TextField(
            label="รหัสผ่าน (ใหม่)" if not is_new else "รหัสผ่าน",
            password=True,
            can_reveal_password=True,
            border_radius=8,
            border_color=theme.BORDER,
            focused_border_color=theme.ACCENT,
            text_size=14,
            bgcolor=theme.BG_INPUT,
        )
        tf_confirm = ft.TextField(
            label="ยืนยันรหัสผ่าน",
            password=True,
            can_reveal_password=True,
            border_radius=8,
            border_color=theme.BORDER,
            focused_border_color=theme.ACCENT,
            text_size=14,
            bgcolor=theme.BG_INPUT,
        )
        err_text = ft.Text("", color="#EF4444", size=12, visible=False)

        def _save(e):
            uname = tf_username.value.strip()
            pwd   = tf_password.value
            cpwd  = tf_confirm.value
            if is_new and not uname:
                err_text.value = "กรุณากรอก username"
                err_text.visible = True
                page.update()
                return
            if not pwd:
                err_text.value = "กรุณากรอกรหัสผ่าน"
                err_text.visible = True
                page.update()
                return
            if pwd != cpwd:
                err_text.value = "รหัสผ่านไม่ตรงกัน"
                err_text.visible = True
                page.update()
                return
            try:
                if is_new:
                    api.set_user_credential(user_id, uname, pwd)
                else:
                    api.set_user_password(user_id, pwd)
                _close_dialog()
                show_snack(page, "บันทึกสำเร็จ ✓")
                _refresh_list()
            except ValidationError as ex:
                err_text.value   = str(ex)
                err_text.visible = True
                page.update()
            except Exception as ex:
                err_text.value   = f"เกิดข้อผิดพลาด: {ex}"
                err_text.visible = True
                page.update()

        title = "กำหนด Login Account" if is_new else "เปลี่ยนรหัสผ่าน"
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(title, size=16, weight=ft.FontWeight.W_600),
            content=ft.Column(
                controls=[
                    tf_username,
                    ft.Container(height=8),
                    tf_password,
                    ft.Container(height=8),
                    tf_confirm,
                    ft.Container(height=4),
                    err_text,
                ],
                tight=True,
                spacing=0,
                width=360,
            ),
            actions=[
                ft.TextButton("ยกเลิก", on_click=lambda e: _close_dialog(),
                              style=ft.ButtonStyle(color=theme.TEXT_SEC)),
                ft.ElevatedButton(
                    "บันทึก",
                    style=ft.ButtonStyle(bgcolor=theme.ACCENT, color="#FFFFFF"),
                    on_click=_save,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        _open_dialog(dlg)

    # ── Create new standalone login user ─────────────────────────
    def _show_create_user_dialog(e=None):
        tf_name     = ft.TextField(label="ชื่อ-นามสกุล", border_radius=8,
                                   border_color=theme.BORDER,
                                   focused_border_color=theme.ACCENT,
                                   text_size=14, bgcolor=theme.BG_INPUT)
        tf_username = ft.TextField(label="Username", border_radius=8,
                                   border_color=theme.BORDER,
                                   focused_border_color=theme.ACCENT,
                                   text_size=14, bgcolor=theme.BG_INPUT)
        tf_password = ft.TextField(label="รหัสผ่าน", password=True,
                                   can_reveal_password=True,
                                   border_radius=8, border_color=theme.BORDER,
                                   focused_border_color=theme.ACCENT,
                                   text_size=14, bgcolor=theme.BG_INPUT)
        dd_role = ft.Dropdown(
            label="ตำแหน่ง",
            options=[ft.dropdown.Option(r) for r in _USER_ROLES],
            value=_DEFAULT_ROLE,
            border_radius=8,
            text_size=14,
        )
        chk_admin = ft.Checkbox(label="เป็น Admin", value=False)
        err_text  = ft.Text("", color="#EF4444", size=12, visible=False)

        def _create(e):
            name     = tf_name.value.strip()
            username = tf_username.value.strip()
            password = tf_password.value
            role_val = dd_role.value or _DEFAULT_ROLE

            if not name:
                err_text.value = "กรุณากรอกชื่อ"
                err_text.visible = True
                page.update()
                return
            if not username:
                err_text.value = "กรุณากรอก username"
                err_text.visible = True
                page.update()
                return
            try:
                api.create_user(
                    name=name,
                    username=username,
                    password=password if password else "changeme",
                    role=role_val,
                    is_admin=chk_admin.value or False,
                )
                _close_dialog()
                show_snack(page, f"สร้าง '{name}' สำเร็จ" +
                           ("" if password else " (รหัสเริ่มต้น: changeme)"))
                _refresh_list()
            except ValidationError as ex:
                err_text.value   = str(ex)
                err_text.visible = True
                page.update()
            except Exception as ex:
                err_text.value   = f"เกิดข้อผิดพลาด: {ex}"
                err_text.visible = True
                page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("สร้าง User ใหม่", size=16, weight=ft.FontWeight.W_600),
            content=ft.Column(
                controls=[
                    tf_name,
                    ft.Container(height=8),
                    tf_username,
                    ft.Container(height=8),
                    tf_password,
                    ft.Container(height=8),
                    dd_role,
                    ft.Container(height=4),
                    chk_admin,
                    ft.Container(height=4),
                    err_text,
                ],
                tight=True,
                spacing=0,
                width=360,
            ),
            actions=[
                ft.TextButton("ยกเลิก", on_click=lambda e: _close_dialog(),
                              style=ft.ButtonStyle(color=theme.TEXT_SEC)),
                ft.ElevatedButton(
                    "สร้าง",
                    style=ft.ButtonStyle(bgcolor=theme.ACCENT, color="#FFFFFF"),
                    on_click=_create,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        _open_dialog(dlg)

    # ── Toggle admin ──────────────────────────────────────────────
    def _toggle_admin(user_id: int, cur_admin: bool):
        action = "ถอดสิทธิ์ Admin" if cur_admin else "ตั้งเป็น Admin"

        def _do(e=None):
            try:
                api.toggle_user_admin(user_id)
                show_snack(page, f"{action} สำเร็จ")
                _refresh_list()
            except Exception as ex:
                show_snack(page, f"เกิดข้อผิดพลาด: {ex}", error=True)

        confirm_dialog(page,
                       title=f"ยืนยัน{action}",
                       message=f"ต้องการ{action}ให้ผู้ใช้นี้?",
                       on_confirm=_do)

    # ── Header ────────────────────────────────────────────────────
    header = ft.Row(
        controls=[
            ft.Icon(ft.Icons.MANAGE_ACCOUNTS_OUTLINED, color=theme.ACCENT, size=24),
            ft.Text("จัดการ User Accounts", size=20,
                    weight=ft.FontWeight.BOLD, color=theme.TEXT_PRI, expand=True),
            ft.ElevatedButton(
                "＋ สร้าง User ใหม่",
                style=ft.ButtonStyle(bgcolor=theme.ACCENT, color="#FFFFFF",
                                     padding=ft.padding.symmetric(horizontal=16, vertical=10)),
                on_click=_show_create_user_dialog,
                visible=is_admin,
            ),
        ],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    info_banner = ft.Container(
        visible=not is_admin,
        bgcolor="#FEF9C3",
        border=ft.border.all(1, "#FDE68A"),
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=14, vertical=10),
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.INFO_OUTLINE, color="#D97706", size=18),
                ft.Text("เฉพาะ Admin เท่านั้นที่สามารถจัดการ account ได้",
                        size=13, color="#92400E"),
            ],
            spacing=8,
        ),
    )

    # ── Init list ─────────────────────────────────────────────────
    _refresh_list()

    return ft.Container(
        expand=True,
        bgcolor=theme.BG_DARK,
        padding=ft.padding.all(28),
        content=ft.Column(
            controls=[
                header,
                ft.Container(height=8),
                info_banner,
                ft.Container(height=8),
                user_list_col,
            ],
            spacing=0,
            expand=True,
        ),
    )
