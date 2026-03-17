"""
Shared UI helper functions for TaskFlow views.
Provides consistent feedback patterns across all views.
"""

from __future__ import annotations
import logging
import flet as ft
import app.utils.theme as theme

_log = logging.getLogger("taskflow.ui_helpers")


def safe_update(control: ft.Control) -> None:
    """
    Safely call control.update() — silently ignores RuntimeError that occurs
    when a control has not yet been added to the page (e.g. during initial
    view build before content_area.update() is called).

    Usage:
        from app.utils.ui_helpers import safe_update
        safe_update(my_column)   # instead of my_column.update()
    """
    try:
        control.update()
    except RuntimeError:
        pass  # Control not yet on page — will render when parent updates
    except Exception as e:
        _log.warning("safe_update failed: %s", e)


def show_snack(
    page: ft.Page,
    message: str,
    error: bool = False,
    duration: int = 3000,
) -> None:
    """
    Show a SnackBar notification at the bottom of the page.

    Args:
        page:     The Flet Page instance.
        message:  Text to display.
        error:    If True, uses red/error color. Defaults to green/success.
        duration: Auto-dismiss time in milliseconds (default 3000).

    Usage:
        from app.utils.ui_helpers import show_snack
        show_snack(page, "บันทึกสำเร็จ!")
        show_snack(page, "เกิดข้อผิดพลาด", error=True)
    """
    bgcolor = theme.COLOR_OVERDUE if error else theme.COLOR_DONE
    try:
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="#FFFFFF", size=13),
            bgcolor=bgcolor,
            duration=duration,
        )
        page.snack_bar.open = True
        page.update()
    except Exception:
        pass  # Never crash the app because of a notification


def show_loading(container: ft.Column | ft.Stack, visible: bool, page: ft.Page) -> None:
    """
    Toggle a ProgressRing overlay inside a container.
    Expects the first control in container.controls to be a ProgressRing.

    Usage:
        show_loading(content_col, visible=True, page=page)
        # ... do work ...
        show_loading(content_col, visible=False, page=page)
    """
    try:
        if container.controls and isinstance(container.controls[0], ft.ProgressRing):
            container.controls[0].visible = visible
            page.update()
    except Exception:
        pass


def confirm_dialog(
    page: ft.Page,
    title: str,
    message: str,
    on_confirm,
    confirm_label: str = "ยืนยัน",
    confirm_color: str = theme.COLOR_OVERDUE,
) -> None:
    """
    Show a modal confirmation dialog.

    Args:
        page:          The Flet Page instance.
        title:         Dialog title text.
        message:       Body message text.
        on_confirm:    Callback function when user confirms.
        confirm_label: Label for the confirm button (default: "ยืนยัน").
        confirm_color: Background color of confirm button (default: red).

    Usage:
        confirm_dialog(
            page,
            title="ลบงาน",
            message=f"ต้องการลบ '{task.title}' ใช่หรือไม่?",
            on_confirm=lambda e: delete_task(task.id),
        )
    """
    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=theme.TEXT_PRI),
        content=ft.Text(message, size=13, color=theme.TEXT_SEC),
        actions=[
            ft.TextButton(
                "ยกเลิก",
                on_click=lambda e: _close_dlg(page, dlg),
                style=ft.ButtonStyle(color=theme.TEXT_SEC),
            ),
            ft.ElevatedButton(
                confirm_label,
                on_click=lambda e: (_close_dlg(page, dlg), on_confirm(e)),
                style=ft.ButtonStyle(bgcolor=confirm_color, color="#FFFFFF"),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    if dlg not in page.overlay:
        page.overlay.append(dlg)
    dlg.open = True
    page.update()


def _close_dlg(page: ft.Page, dlg: ft.AlertDialog) -> None:
    dlg.open = False
    page.update()
