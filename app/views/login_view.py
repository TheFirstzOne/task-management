# -*- coding: utf-8 -*-
"""
LoginView — Phase 19: Login Screen
Split-panel layout: Blue branding left + White form right.
ใช้พื้นที่ window เต็ม.
"""
from __future__ import annotations
from typing import Callable

import flet as ft

from app.utils.exceptions import InvalidCredentialsError, TaskFlowError
import app.utils.theme as theme


def build_login_view(
    api,
    page: ft.Page,
    on_success: Callable[[dict], None],
) -> ft.Control:
    """Full-window split-panel login: branding left, form right."""

    loading  = {"value": False}

    # ── Form controls ──────────────────────────────────────────────
    tf_username = ft.TextField(
        label="ชื่อผู้ใช้",
        hint_text="username",
        autofocus=True,
        border_radius=8,
        border_color=theme.BORDER,
        focused_border_color=theme.ACCENT,
        text_size=14,
        bgcolor=theme.BG_INPUT,
    )

    tf_password = ft.TextField(
        label="รหัสผ่าน",
        hint_text="password",
        password=True,
        can_reveal_password=True,
        border_radius=8,
        border_color=theme.BORDER,
        focused_border_color=theme.ACCENT,
        text_size=14,
        bgcolor=theme.BG_INPUT,
    )

    error_text = ft.Text(
        "",
        color="#EF4444",
        size=13,
        visible=False,
        text_align=ft.TextAlign.CENTER,
    )

    login_btn = ft.ElevatedButton(
        "เข้าสู่ระบบ",
        style=ft.ButtonStyle(
            bgcolor=theme.ACCENT,
            color="#FFFFFF",
            padding=ft.padding.symmetric(vertical=14),
        ),
    )

    progress = ft.ProgressBar(
        visible=False, color="#FFFFFF", bgcolor=theme.ACCENT + "66",
    )

    # ── Logic ──────────────────────────────────────────────────────
    def _set_error(msg: str) -> None:
        error_text.value   = msg
        error_text.visible = bool(msg)
        page.update()

    def _set_loading(val: bool) -> None:
        loading["value"]       = val
        login_btn.disabled     = val
        tf_username.disabled   = val
        tf_password.disabled   = val
        progress.visible       = val
        page.update()

    def _attempt_login(e=None) -> None:
        if loading["value"]:
            return
        _set_error("")
        username = tf_username.value or ""
        password = tf_password.value or ""
        if not username.strip():
            _set_error("กรุณากรอกชื่อผู้ใช้")
            return
        if not password:
            _set_error("กรุณากรอกรหัสผ่าน")
            return
        _set_loading(True)
        try:
            result = api.login(username, password)
            api.token = result["access_token"]
            page.session.store.set("api_client_token", result["access_token"])
            on_success(result["user"])
        except InvalidCredentialsError:
            _set_error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
            tf_password.value = ""
            page.update()
        except TaskFlowError as ex:
            _set_error(str(ex))
        except Exception as ex:
            import traceback; traceback.print_exc()
            _set_error(f"เกิดข้อผิดพลาด: {ex}")
        finally:
            _set_loading(False)

    login_btn.on_click = _attempt_login

    def _on_field_submit(e):
        if e.control is tf_username:
            tf_password.focus()
        else:
            _attempt_login()

    tf_username.on_submit = _on_field_submit
    tf_password.on_submit = _on_field_submit

    # ── Left panel — branding ──────────────────────────────────────
    left_panel = ft.Container(
        expand=2,   # 40% of width (ratio 2:3)
        bgcolor=theme.ACCENT,
        padding=ft.padding.all(48),
        content=ft.Column(
            controls=[
                # Logo
                ft.Row(
                    controls=[
                        ft.Container(
                            width=48, height=48, border_radius=12,
                            bgcolor="#FFFFFF",
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(ft.Icons.BOLT, color=theme.ACCENT, size=28),
                        ),
                        ft.Text(
                            "VindFlow",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color="#FFFFFF",
                        ),
                    ],
                    spacing=12,
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Container(expand=True),   # push content to center
                # Tagline
                ft.Text(
                    "Task Management",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color="#FFFFFF",
                ),
                ft.Container(height=12),
                ft.Text(
                    "จัดการงาน ทีมงาน และเวลา\nในที่เดียว",
                    size=15,
                    color="#FFFFFFCC",
                ),
                ft.Container(height=32),
                # Feature bullets
                *[
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=28, height=28, border_radius=14,
                                bgcolor="#FFFFFF",
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(ico, color=theme.ACCENT, size=15),
                            ),
                            ft.Text(lbl, color="#FFFFFF", size=13),
                        ],
                        spacing=10,
                    )
                    for ico, lbl in [
                        (ft.Icons.TASK_ALT_OUTLINED,     "ติดตามงานและ subtask"),
                        (ft.Icons.GROUP_OUTLINED,        "จัดการทีมงาน"),
                        (ft.Icons.TIMER_OUTLINED,        "บันทึกเวลาทำงาน"),
                        (ft.Icons.DASHBOARD_OUTLINED,    "Dashboard & รายงาน"),
                    ]
                ],
                ft.Container(expand=True),   # push to vertical center
            ],
            spacing=8,
            expand=True,
        ),
    )

    # ── Right panel — form ─────────────────────────────────────────
    right_panel = ft.Container(
        expand=3,   # 60% of width (ratio 2:3)
        bgcolor=theme.BG_CARD,
        padding=ft.padding.symmetric(horizontal=64, vertical=48),
        content=ft.Column(
            controls=[
                ft.Container(expand=True),   # push form to vertical center
                ft.Text(
                    "เข้าสู่ระบบ",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=theme.TEXT_PRI,
                ),
                ft.Container(height=6),
                ft.Text(
                    "ยินดีต้อนรับกลับ กรอกข้อมูลเพื่อเข้าใช้งาน",
                    size=13,
                    color=theme.TEXT_SEC,
                ),
                ft.Container(height=32),
                tf_username,
                ft.Container(height=14),
                tf_password,
                ft.Container(height=8),
                error_text,
                ft.Container(height=4),
                progress,
                ft.Container(height=20),
                login_btn,
                ft.Container(expand=True),   # push form to vertical center
            ],
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            spacing=0,
            expand=True,
        ),
    )

    # ── Full-window layout ─────────────────────────────────────────
    return ft.Row(
        controls=[left_panel, right_panel],
        spacing=0,
        expand=True,
    )
