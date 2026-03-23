"""
DiaryView — บันทึกการทำงานรายวัน
Function-based view compatible with Flet 0.80+ (no UserControl)
"""

import os
from datetime import datetime
import flet as ft
import app.utils.theme as theme
from app.utils.logger import get_logger
from app.utils.ui_helpers import show_snack
logger = get_logger(__name__)


def build_diary_view(api, page: ft.Page) -> ft.Control:
    # ── State ────────────────────────────────────────────────────
    status_text = ft.Text("", size=13, color=theme.ACCENT)

    # ── Write Tab ────────────────────────────────────────────────
    diary_field = ft.TextField(
        label="บันทึกการทำงาน",
        hint_text="กรอกรายละเอียดการทำงานของคุณที่นี่...",
        multiline=True,
        min_lines=12,
        max_lines=20,
        border_color=theme.BORDER,
        focused_border_color=theme.ACCENT,
        bgcolor=theme.BG_CARD,
        color=theme.TEXT_PRI,
        label_style=ft.TextStyle(color=theme.TEXT_SEC),
        expand=True,
    )

    def save_entry(e):
        text = (diary_field.value or "").strip()
        if not text:
            status_text.value = "กรุณากรอกข้อความก่อนบันทึก!"
            status_text.color = theme.COLOR_OVERDUE
            page.update()
            return
        api.create_diary(text)
        diary_field.value = ""
        status_text.value = "บันทึกสำเร็จ!"
        status_text.color = theme.COLOR_DONE
        page.update()

    def clear_text(e):
        diary_field.value = ""
        status_text.value = ""
        page.update()

    def _do_export_api(fmt: str, filepath: str):
        """Shared export logic: call api, save to file, open with OS."""
        try:
            data = api.export_diary(fmt)
            with open(filepath, "wb") as f:
                f.write(data)
            status_text.value = f"Export สำเร็จ: {os.path.basename(filepath)}"
            status_text.color = theme.COLOR_DONE
            page.update()
            try:
                os.startfile(filepath)
            except Exception as ex:
                logger.debug("open file failed: %s", ex)
        except Exception as ex:
            logger.error("export failed: %s", ex, exc_info=True)
            show_snack(page, f"เกิดข้อผิดพลาด: {ex}", error=True)
            status_text.value = f"Export ผิดพลาด: {ex}"
            status_text.color = theme.COLOR_OVERDUE
            page.update()

    def export_word(e):
        _do_export_api("word", os.path.join("data", "job_diary.docx"))

    def export_pdf(e):
        _do_export_api("pdf", os.path.join("data", "job_diary.pdf"))

    # ── Export button style (shared concept) ──────────────────────
    def _export_btn(label: str, icon, on_click, bgcolor: str) -> ft.ElevatedButton:
        return ft.ElevatedButton(
            label, icon=icon, on_click=on_click,
            style=ft.ButtonStyle(bgcolor=bgcolor, color="#FFFFFF", padding=12),
        )

    save_btn = ft.ElevatedButton(
        "บันทึก",
        icon=ft.Icons.SAVE,
        on_click=save_entry,
        style=ft.ButtonStyle(bgcolor=theme.ACCENT, color="#FFFFFF", padding=12),
    )
    clear_btn = ft.ElevatedButton(
        "ล้างข้อความ",
        icon=ft.Icons.CLEAR,
        on_click=clear_text,
        style=ft.ButtonStyle(bgcolor=theme.COLOR_PENDING, color="#FFFFFF", padding=12),
    )
    export_word_btn = _export_btn(
        "Export Word", ft.Icons.DESCRIPTION_OUTLINED, export_word, theme.COLOR_DONE,
    )
    export_pdf_btn = _export_btn(
        "Export PDF", ft.Icons.PICTURE_AS_PDF_OUTLINED, export_pdf, "#EF4444",
    )

    write_tab = ft.Container(
        content=ft.Column(
            controls=[
                diary_field,
                ft.Row(
                    controls=[save_btn, clear_btn, export_word_btn, export_pdf_btn],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
                status_text,
            ],
            spacing=12,
            expand=True,
        ),
        padding=16,
        expand=True,
    )

    # ── History Tab ──────────────────────────────────────────────
    date_list = ft.ListView(spacing=6, padding=8, expand=True)
    history_content = ft.Column(
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    def show_date_entries(date_key, entries):
        history_content.controls.clear()
        # Header
        history_content.controls.append(
            ft.Text(
                f"📅 {date_key}",
                size=18,
                weight=ft.FontWeight.BOLD,
                color=theme.ACCENT,
            )
        )
        for entry in entries:
            created_at = (
                datetime.fromisoformat(entry["created_at"])
                if entry.get("created_at") else None
            )
            time_str = created_at.strftime("%H:%M:%S") if created_at else "—"
            card = ft.Container(
                bgcolor=theme.BG_CARD,
                border=ft.border.all(1, theme.BORDER),
                border_radius=10,
                padding=14,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.ACCESS_TIME, size=14, color=theme.ACCENT2),
                                ft.Text(time_str, size=13, weight=ft.FontWeight.BOLD, color=theme.ACCENT2),
                            ],
                            spacing=6,
                        ),
                        ft.Divider(height=1, color=theme.BORDER),
                        ft.Text(entry["content"], size=14, color=theme.TEXT_PRI, selectable=True),
                    ],
                    spacing=8,
                ),
            )
            history_content.controls.append(card)
        page.update()

    def load_history(e=None):
        date_list.controls.clear()
        history_content.controls.clear()

        grouped = api.get_diary_grouped()

        if not grouped:
            history_content.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.INFO_OUTLINE, size=48, color=theme.TEXT_DIM),
                            ft.Text("ยังไม่มีบันทึก", size=16, color=theme.TEXT_SEC,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text("กรุณาบันทึกข้อมูลใน Tab 'บันทึกใหม่' ก่อน",
                                    size=13, color=theme.TEXT_DIM),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                )
            )
            page.update()
            return

        first_date = None
        for date_key, entries in grouped.items():
            if first_date is None:
                first_date = date_key

            date_btn = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CALENDAR_TODAY, size=14, color=theme.ACCENT),
                        ft.Text(date_key, size=13, weight=ft.FontWeight.W_500, color=theme.TEXT_PRI),
                        ft.Text(f"({len(entries)})", size=12, color=theme.TEXT_DIM),
                    ],
                    spacing=6,
                ),
                padding=10,
                border_radius=8,
                bgcolor=theme.BG_CARD,
                border=ft.border.all(1, theme.BORDER),
                ink=True,
                on_click=lambda e, dk=date_key, ent=entries: show_date_entries(dk, ent),
            )
            date_list.controls.append(date_btn)

        # Show first date automatically
        if first_date:
            show_date_entries(first_date, grouped[first_date])
        page.update()

    refresh_btn = ft.IconButton(
        icon=ft.Icons.REFRESH,
        tooltip="โหลดข้อมูลใหม่",
        on_click=load_history,
        icon_color=theme.ACCENT,
    )

    left_panel = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("📅 รายการวันที่", size=15, weight=ft.FontWeight.BOLD, color=theme.ACCENT),
                        refresh_btn,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(height=1, color=theme.BORDER),
                date_list,
            ],
            spacing=6,
        ),
        width=240,
        bgcolor=theme.BG_CARD,
        border=ft.border.all(1, theme.BORDER),
        border_radius=10,
        padding=10,
    )

    right_panel = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("📝 เนื้อหาบันทึก", size=15, weight=ft.FontWeight.BOLD, color=theme.ACCENT),
                ft.Divider(height=1, color=theme.BORDER),
                history_content,
            ],
            spacing=6,
        ),
        expand=True,
        bgcolor=theme.BG_CARD,
        border=ft.border.all(1, theme.BORDER),
        border_radius=10,
        padding=10,
    )

    history_tab = ft.Container(
        content=ft.Row(
            controls=[left_panel, right_panel],
            spacing=10,
            expand=True,
        ),
        padding=10,
        expand=True,
    )

    # ── Custom Tab Bar ──────────────────────────────────────────
    tab_content = ft.Column(controls=[write_tab], expand=True, spacing=0)
    active_tab = {"value": 0}

    def make_tab_btn(label, icon, index):
        is_active = index == 0
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icon, size=16,
                            color=theme.ACCENT if is_active else theme.TEXT_SEC),
                    ft.Text(label, size=14,
                            color=theme.ACCENT if is_active else theme.TEXT_SEC,
                            weight=ft.FontWeight.W_500 if is_active else ft.FontWeight.NORMAL),
                ],
                spacing=6,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border=ft.border.only(
                bottom=ft.BorderSide(2, theme.ACCENT if is_active else "transparent")),
            on_click=lambda e, idx=index: switch_tab(idx),
            ink=True,
        )

    tab_btns = [
        make_tab_btn("บันทึกใหม่", ft.Icons.EDIT, 0),
        make_tab_btn("อ่านย้อนหลัง", ft.Icons.HISTORY, 1),
    ]

    def switch_tab(idx):
        if active_tab["value"] == idx:
            return
        active_tab["value"] = idx

        # Update button styles
        for i, btn in enumerate(tab_btns):
            is_active = i == idx
            row = btn.content
            row.controls[0].color = theme.ACCENT if is_active else theme.TEXT_SEC
            row.controls[1].color = theme.ACCENT if is_active else theme.TEXT_SEC
            row.controls[1].weight = ft.FontWeight.W_500 if is_active else ft.FontWeight.NORMAL
            btn.border = ft.border.only(
                bottom=ft.BorderSide(2, theme.ACCENT if is_active else "transparent"))

        # Swap content
        if idx == 0:
            tab_content.controls = [write_tab]
        else:
            tab_content.controls = [history_tab]
            load_history()
        page.update()

    tab_bar = ft.Row(controls=tab_btns, spacing=0)

    # ── Main container ───────────────────────────────────────────
    return ft.Container(
        expand=True,
        bgcolor=theme.BG_DARK,
        padding=24,
        content=ft.Column(
            controls=[
                ft.Text("บันทึกการทำงานรายวัน", size=24,
                         weight=ft.FontWeight.BOLD, color=theme.TEXT_PRI),
                ft.Text("บันทึกรายละเอียดการทำงานประจำวันของคุณ",
                         size=13, color=theme.TEXT_SEC),
                ft.Divider(height=16, color=theme.BORDER),
                tab_bar,
                tab_content,
            ],
            spacing=8,
            expand=True,
        ),
    )
