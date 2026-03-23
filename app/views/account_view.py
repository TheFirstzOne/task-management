# -*- coding: utf-8 -*-
"""
AccountView — Phase 19: User Profile & Account Settings
ทุก user เข้าได้ — แก้ชื่อ + เปลี่ยนรหัสผ่านของตัวเอง
"""
from __future__ import annotations

import flet as ft

from app.utils.exceptions import ValidationError
from app.utils.ui_helpers import show_snack
import app.utils.theme as theme


def build_account_view(api, page: ft.Page) -> ft.Control:
    """Profile + password change page for the currently logged-in user."""

    # ── Current user from session ─────────────────────────────────
    current = page.session.store.get("current_user") or {}
    user_id = current.get("id")

    # Load user via API
    if user_id:
        try:
            all_users = api.get_users()
            user = next((u for u in all_users if u["id"] == user_id), None)
        except Exception:
            user = None
    else:
        user = None

    if not user:
        return ft.Container(
            expand=True, bgcolor=theme.BG_DARK,
            content=ft.Column(
                controls=[ft.Text("ไม่พบข้อมูลผู้ใช้", color=theme.TEXT_SEC, size=16)],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            ),
        )

    # ── Profile display controls ──────────────────────────────────
    name_text = ft.Text(
        user["name"], size=18, weight=ft.FontWeight.BOLD, color=theme.TEXT_PRI,
    )
    username_text = ft.Text(
        f"@{user.get('username')}" if user.get("username") else "— ยังไม่มี username",
        size=13, color=theme.ACCENT if user.get("username") else theme.TEXT_DIM,
    )
    role_text = ft.Text(
        user.get("role", ""), size=13, color=theme.TEXT_SEC,
    )
    admin_badge = ft.Container(
        visible=bool(user.get("is_admin", False)),
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
        border_radius=12, bgcolor=theme.ACCENT + "22",
        content=ft.Text("Admin", size=11, color=theme.ACCENT,
                        weight=ft.FontWeight.W_600),
    )

    # ── Dialog state ─────────────────────────────────────────────
    _dlg = {"value": None}

    def _close_dlg():
        if _dlg["value"]:
            _dlg["value"].open = False
            page.update()

    def _open_dlg(dlg):
        _dlg["value"] = dlg
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # ── Edit name dialog ──────────────────────────────────────────
    def _show_edit_name(e=None):
        tf = ft.TextField(
            label="ชื่อ-นามสกุล",
            value=user["name"],
            border_radius=8,
            border_color=theme.BORDER,
            focused_border_color=theme.ACCENT,
            text_size=14,
            bgcolor=theme.BG_INPUT,
        )
        err = ft.Text("", color="#EF4444", size=12, visible=False)

        def _save(e=None):
            new_name = tf.value.strip()
            if not new_name:
                err.value = "ชื่อต้องไม่ว่าง"
                err.visible = True
                page.update()
                return
            try:
                api.update_user(user_id, name=new_name)
                name_text.value = new_name
                name_text.update()
                # sync session store
                cur = page.session.store.get("current_user") or {}
                cur["name"] = new_name
                page.session.store.set("current_user", cur)
            except Exception as ex:
                err.value = f"เกิดข้อผิดพลาด: {ex}"
                err.visible = True
                page.update()
                return
            _close_dlg()
            show_snack(page, "อัปเดตชื่อสำเร็จ ✓")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("แก้ไขชื่อ", size=16, weight=ft.FontWeight.W_600),
            content=ft.Column(
                controls=[tf, ft.Container(height=4), err],
                tight=True, spacing=0, width=320,
            ),
            actions=[
                ft.TextButton("ยกเลิก", on_click=lambda e: _close_dlg(),
                              style=ft.ButtonStyle(color=theme.TEXT_SEC)),
                ft.ElevatedButton(
                    "บันทึก",
                    style=ft.ButtonStyle(bgcolor=theme.ACCENT, color="#FFFFFF"),
                    on_click=_save,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        _open_dlg(dlg)

    # ── Password change controls ──────────────────────────────────
    tf_old  = ft.TextField(
        label="รหัสผ่านเดิม",
        password=True, can_reveal_password=True,
        border_radius=8, border_color=theme.BORDER,
        focused_border_color=theme.ACCENT,
        text_size=14, bgcolor=theme.BG_INPUT,
    )
    tf_new  = ft.TextField(
        label="รหัสผ่านใหม่",
        password=True, can_reveal_password=True,
        border_radius=8, border_color=theme.BORDER,
        focused_border_color=theme.ACCENT,
        text_size=14, bgcolor=theme.BG_INPUT,
    )
    tf_conf = ft.TextField(
        label="ยืนยันรหัสผ่านใหม่",
        password=True, can_reveal_password=True,
        border_radius=8, border_color=theme.BORDER,
        focused_border_color=theme.ACCENT,
        text_size=14, bgcolor=theme.BG_INPUT,
    )
    pwd_err = ft.Text("", color="#EF4444", size=12, visible=False)
    pwd_ok  = ft.Text("", color="#22C55E", size=12, visible=False)

    def _save_password(e=None):
        old  = tf_old.value or ""
        new  = tf_new.value or ""
        conf = tf_conf.value or ""
        pwd_err.visible = False
        pwd_ok.visible  = False

        if not old:
            pwd_err.value = "กรุณากรอกรหัสผ่านเดิม"
            pwd_err.visible = True
            page.update()
            return
        if not new:
            pwd_err.value = "กรุณากรอกรหัสผ่านใหม่"
            pwd_err.visible = True
            page.update()
            return
        if new != conf:
            pwd_err.value = "รหัสผ่านใหม่ไม่ตรงกัน"
            pwd_err.visible = True
            page.update()
            return
        try:
            api.change_password(user_id, old, new)
            tf_old.value = tf_new.value = tf_conf.value = ""
            pwd_ok.value   = "เปลี่ยนรหัสผ่านสำเร็จ ✓"
            pwd_ok.visible = True
        except ValidationError as ex:
            pwd_err.value   = str(ex)
            pwd_err.visible = True
        except Exception as ex:
            pwd_err.value   = f"เกิดข้อผิดพลาด: {ex}"
            pwd_err.visible = True
        page.update()

    # ── Profile card ──────────────────────────────────────────────
    profile_card = ft.Container(
        bgcolor=theme.BG_CARD,
        border=ft.border.all(1, theme.BORDER),
        border_radius=12,
        padding=ft.padding.all(24),
        content=ft.Column(
            controls=[
                ft.Text("ข้อมูลส่วนตัว", size=15, weight=ft.FontWeight.W_600,
                        color=theme.TEXT_PRI),
                ft.Divider(height=12, color=theme.BORDER),
                ft.Row(
                    controls=[
                        # Avatar
                        ft.Container(
                            width=64, height=64, border_radius=32,
                            bgcolor=theme.ACCENT + "22",
                            alignment=ft.Alignment(0, 0),
                            content=ft.Text(
                                (user.get("name") or "?")[0].upper(),
                                size=26, weight=ft.FontWeight.BOLD,
                                color=theme.ACCENT,
                            ),
                        ),
                        # Info
                        ft.Column(
                            controls=[
                                ft.Row(controls=[name_text, admin_badge], spacing=8),
                                username_text,
                                role_text,
                            ],
                            spacing=4,
                            expand=True,
                        ),
                        # Edit button
                        ft.ElevatedButton(
                            "แก้ชื่อ",
                            style=ft.ButtonStyle(
                                bgcolor=theme.BG_INPUT, color=theme.TEXT_PRI,
                                padding=ft.padding.symmetric(horizontal=14, vertical=8),
                            ),
                            on_click=_show_edit_name,
                        ),
                    ],
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=0,
        ),
    )

    # ── Password card (only if user has login credentials) ────────
    has_login = bool(user.get("username"))

    password_card = ft.Container(
        bgcolor=theme.BG_CARD,
        border=ft.border.all(1, theme.BORDER),
        border_radius=12,
        padding=ft.padding.all(24),
        visible=has_login,
        content=ft.Column(
            controls=[
                ft.Text("เปลี่ยนรหัสผ่าน", size=15, weight=ft.FontWeight.W_600,
                        color=theme.TEXT_PRI),
                ft.Divider(height=12, color=theme.BORDER),
                tf_old,
                ft.Container(height=10),
                tf_new,
                ft.Container(height=10),
                tf_conf,
                ft.Container(height=8),
                pwd_err,
                pwd_ok,
                ft.Container(height=4),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            "บันทึกรหัสผ่าน",
                            style=ft.ButtonStyle(
                                bgcolor=theme.ACCENT, color="#FFFFFF",
                                padding=ft.padding.symmetric(horizontal=20, vertical=10),
                            ),
                            on_click=_save_password,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=0,
        ),
    )

    # ── Page layout ───────────────────────────────────────────────
    return ft.Container(
        expand=True,
        bgcolor=theme.BG_DARK,
        padding=ft.padding.all(28),
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.PERSON_OUTLINED, color=theme.ACCENT, size=24),
                        ft.Text("บัญชีของฉัน", size=20,
                                weight=ft.FontWeight.BOLD, color=theme.TEXT_PRI),
                    ],
                    spacing=12,
                ),
                ft.Container(height=16),
                profile_card,
                ft.Container(height=12),
                password_card,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )
