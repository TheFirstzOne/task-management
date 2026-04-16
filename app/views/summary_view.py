# -*- coding: utf-8 -*-
"""
SummaryView — Phase 5: Summary & Export UI
Features:
  - Overview stat cards  (total / done / in-progress / overdue / cancelled)
  - Status breakdown bar  (visual proportion per status)
  - Priority breakdown bar
  - Per-team table  (team | total | done | in-progress | overdue)
  - Per-member table  (name | team | assigned | done | overdue)
  - Filter: date range  (ช่วงวันที่)  +  team dropdown
  - Export to Excel  (via API)
Flet 0.80.x — function-based
"""

from __future__ import annotations

import os
from datetime import date, datetime
from typing import List, Optional

import flet as ft

from app.utils.theme import (
    BG_DARK, BG_CARD, BG_INPUT,
    ACCENT, ACCENT2,
    TEXT_PRI, TEXT_SEC, BORDER,
    COLOR_PENDING, COLOR_IN_PROGRESS, COLOR_REVIEW,
    COLOR_DONE, COLOR_CANCELLED, COLOR_OVERDUE,
    COLOR_LOW, COLOR_MEDIUM, COLOR_HIGH, COLOR_URGENT,
    status_color, priority_color,
)

from app.utils.date_helpers import parse_date_field

ALL_OPT = "ทั้งหมด"

# ── Status / Priority display order (string-based for API dicts) ────────────
_STATUS_ORDER = ["Pending", "In Progress", "Review", "Done", "Cancelled"]
_STATUS_COLORS = {
    "Pending":     COLOR_PENDING,
    "In Progress": COLOR_IN_PROGRESS,
    "Review":      COLOR_REVIEW,
    "Done":        COLOR_DONE,
    "Cancelled":   COLOR_CANCELLED,
}
_PRIO_ORDER  = ["Low", "Medium", "High", "Urgent"]
_PRIO_COLORS = {
    "Low":    COLOR_LOW,
    "Medium": COLOR_MEDIUM,
    "High":   COLOR_HIGH,
    "Urgent": COLOR_URGENT,
}


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY
# ══════════════════════════════════════════════════════════════════════════════
def build_summary_view(api, page: ft.Page) -> ft.Control:
    today = date.today()

    # ── State ──────────────────────────────────────────────────────
    state = {
        "filter_team":   ALL_OPT,
        "date_from":     None,   # date | None
        "date_to":       None,   # date | None
    }

    # ── Mutable content container ───────────────────────────────────
    content_col = ft.Column(spacing=20, expand=True, scroll=ft.ScrollMode.AUTO)

    # ── Export status snackbar helper ───────────────────────────────
    def _snack(msg: str, color: str = COLOR_DONE):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(msg, color=TEXT_PRI),
            bgcolor=color,
        )
        page.snack_bar.open = True
        try:
            page.update()
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════
    #  DATA HELPERS
    # ══════════════════════════════════════════════════════════════
    def _parse_due(t: dict) -> Optional[datetime]:
        raw = t.get("due_date")
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw)
        except (ValueError, TypeError):
            return None

    def _parse_created(t: dict) -> Optional[datetime]:
        raw = t.get("created_at")
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw)
        except (ValueError, TypeError):
            return None

    def _get_filtered_tasks() -> List[dict]:
        tasks = api.get_tasks()

        # Team filter
        if state["filter_team"] != ALL_OPT:
            try:
                tid = int(state["filter_team"])
                tasks = [t for t in tasks if t.get("team_id") == tid]
            except (ValueError, TypeError):
                pass

        # Date range filter (based on due_date)
        if state["date_from"]:
            dt_from = datetime.combine(state["date_from"], datetime.min.time())
            tasks = [t for t in tasks
                     if _parse_due(t) and _parse_due(t) >= dt_from]
        if state["date_to"]:
            dt_to = datetime.combine(state["date_to"], datetime.max.time())
            tasks = [t for t in tasks
                     if _parse_due(t) and _parse_due(t) <= dt_to]

        return tasks

    def _is_overdue(t: dict) -> bool:
        due = _parse_due(t)
        status = t.get("status", "Pending")
        return (
            due is not None
            and due.date() < today
            and status not in ("Done", "Cancelled")
        )

    def _compute_stats(tasks: List[dict]) -> dict:
        total     = len(tasks)
        by_status = {s: sum(1 for t in tasks if t.get("status", "Pending") == s)
                     for s in _STATUS_ORDER}
        by_prio   = {p: sum(1 for t in tasks if t.get("priority", "Medium") == p)
                     for p in _PRIO_ORDER}
        overdue   = sum(1 for t in tasks if _is_overdue(t))
        return {
            "total":     total,
            "by_status": by_status,
            "by_prio":   by_prio,
            "overdue":   overdue,
        }

    def _get_all_members_dedup() -> List[dict]:
        """Flatten members from all teams, deduplicated by id."""
        teams = api.get_teams()
        seen = {}
        for team in teams:
            for m in team.get("members", []):
                mid = m.get("id")
                if mid is not None and mid not in seen:
                    seen[mid] = m
        return list(seen.values())

    def _per_team_rows(tasks: List[dict]):
        """Return list of (team_name, total, done, in_prog, overdue)."""
        teams = api.get_teams()
        rows = []
        for team in teams:
            tid = team["id"]
            tt = [t for t in tasks if t.get("team_id") == tid]
            if not tt:
                continue
            done    = sum(1 for t in tt if t.get("status") == "Done")
            in_prog = sum(1 for t in tt if t.get("status") == "In Progress")
            ov      = sum(1 for t in tt if _is_overdue(t))
            rows.append((team["name"], len(tt), done, in_prog, ov))
        # Unassigned team
        no_team = [t for t in tasks if t.get("team_id") is None]
        if no_team:
            done    = sum(1 for t in no_team if t.get("status") == "Done")
            in_prog = sum(1 for t in no_team if t.get("status") == "In Progress")
            ov      = sum(1 for t in no_team if _is_overdue(t))
            rows.append(("(ไม่มีทีม)", len(no_team), done, in_prog, ov))
        return rows

    def _per_member_rows(tasks: List[dict]):
        """Return list of (name, team_name, total, done, overdue, subtasks)."""
        users = _get_all_members_dedup()
        rows = []
        for u in users:
            uid = u["id"]
            ut = [t for t in tasks if t.get("assignee_id") == uid]
            # Count subtasks assigned to this member
            st_count = sum(
                1 for t in tasks
                for st in t.get("subtasks", [])
                if st.get("assignee_id") == uid and not st.get("is_deleted")
            )
            if not ut and not st_count:
                continue
            done = sum(1 for t in ut if t.get("status") == "Done")
            ov   = sum(1 for t in ut if _is_overdue(t))
            team_name = u.get("team_name") or "—"
            rows.append((u["name"], team_name, len(ut), done, ov, st_count))
        return rows

    # ══════════════════════════════════════════════════════════════
    #  UI BUILDERS
    # ══════════════════════════════════════════════════════════════

    # ── Stat card ────────────────────────────────────────────────
    def _stat_card(label: str, value: int, color: str,
                   icon: str) -> ft.Container:
        return ft.Container(
            width=170,
            bgcolor=BG_CARD,
            border_radius=12,
            border=ft.border.all(1, BORDER),
            padding=ft.padding.all(18),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(icon, color=color, size=22),
                            ft.Text(label, size=12, color=TEXT_SEC),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(str(value), size=32,
                            weight=ft.FontWeight.BOLD, color=color),
                ],
                spacing=8,
            ),
        )

    # ── Horizontal proportion bar ─────────────────────────────────
    def _prop_bar(items: list, total: int) -> ft.Column:
        """
        items = [(label, count, color), ...]
        Builds a stacked bar + legend row.
        """
        bar_segments = []
        for label, count, col in items:
            if total > 0 and count > 0:
                bar_segments.append(
                    ft.Container(
                        expand=count,
                        height=14,
                        bgcolor=col,
                        tooltip=f"{label}: {count}",
                    )
                )

        bar = ft.Row(
            controls=bar_segments or [
                ft.Container(expand=1, height=14, bgcolor=BORDER)
            ],
            spacing=0,
            expand=True,
        )

        legend_items = []
        for label, count, col in items:
            legend_items.append(
                ft.Row(
                    controls=[
                        ft.Container(
                            width=10, height=10, border_radius=5, bgcolor=col,
                        ),
                        ft.Text(f"{label} ({count})", size=11, color=TEXT_SEC),
                    ],
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        legend = ft.Row(controls=legend_items, spacing=16, wrap=True)

        return ft.Column(
            controls=[
                ft.Container(
                    content=bar,
                    border_radius=7,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                ),
                legend,
            ],
            spacing=8,
        )

    # ── Section header ────────────────────────────────────────────
    def _section(title: str, content: ft.Control) -> ft.Container:
        return ft.Container(
            bgcolor=BG_CARD,
            border_radius=12,
            border=ft.border.all(1, BORDER),
            padding=ft.padding.all(20),
            content=ft.Column(
                controls=[
                    ft.Text(title, size=15,
                            weight=ft.FontWeight.W_600, color=TEXT_PRI),
                    ft.Divider(height=1, color=BORDER),
                    content,
                ],
                spacing=12,
            ),
        )

    # ── Table helper ─────────────────────────────────────────────
    def _table_header(*cols: str) -> ft.Row:
        return ft.Row(
            controls=[
                ft.Container(
                    expand=True,
                    content=ft.Text(c, size=11, color=TEXT_SEC,
                                    weight=ft.FontWeight.W_600),
                )
                for c in cols
            ],
            spacing=4,
        )

    def _table_row(*vals, highlight_last_red: bool = False,
                   highlight_col_red: int = None) -> ft.Container:
        cells = []
        for i, v in enumerate(vals):
            color = TEXT_PRI
            if highlight_last_red and i == len(vals) - 1 and int(v) > 0:
                color = COLOR_OVERDUE
            elif highlight_col_red is not None and i == highlight_col_red and int(v) > 0:
                color = COLOR_OVERDUE
            cells.append(
                ft.Container(
                    expand=True,
                    content=ft.Text(str(v), size=12, color=color),
                )
            )
        return ft.Container(
            content=ft.Row(controls=cells, spacing=4),
            padding=ft.padding.symmetric(vertical=6),
            border=ft.border.only(bottom=ft.BorderSide(1, BORDER + "66")),
        )

    # ══════════════════════════════════════════════════════════════
    #  EXPORT HELPERS
    # ══════════════════════════════════════════════════════════════
    def _export_excel(e):
        try:
            data = api.export_summary_excel()
            filepath = os.path.join("data", "summary_export.xlsx")
            with open(filepath, "wb") as f:
                f.write(data)
            _snack(f"บันทึก Excel แล้ว: {os.path.basename(filepath)}")
            try:
                os.startfile(filepath)
            except Exception:
                pass
        except Exception as ex:
            _snack(f"Export ผิดพลาด: {ex}", COLOR_OVERDUE)

    # ══════════════════════════════════════════════════════════════
    #  REBUILD CONTENT
    # ══════════════════════════════════════════════════════════════
    def _rebuild():
        tasks = _get_filtered_tasks()
        stats = _compute_stats(tasks)
        total = stats["total"]

        # ── Stat cards row ──────────────────────────────────────
        cards = ft.Row(
            controls=[
                _stat_card("งานทั้งหมด", total,
                           ACCENT, ft.Icons.ASSIGNMENT_OUTLINED),
                _stat_card("เสร็จแล้ว",
                           stats["by_status"]["Done"],
                           COLOR_DONE, ft.Icons.CHECK_CIRCLE_OUTLINE),
                _stat_card("กำลังทำ",
                           stats["by_status"]["In Progress"],
                           COLOR_IN_PROGRESS, ft.Icons.TIMELAPSE),
                _stat_card("รอดำเนินการ",
                           stats["by_status"]["Pending"],
                           COLOR_PENDING, ft.Icons.PENDING_OUTLINED),
                _stat_card("เกินกำหนด", stats["overdue"],
                           COLOR_OVERDUE, ft.Icons.WARNING_AMBER_OUTLINED),
            ],
            spacing=12,
            wrap=True,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # ── Status bar ──────────────────────────────────────────
        status_items = [
            (s, stats["by_status"][s], _STATUS_COLORS[s])
            for s in _STATUS_ORDER
            if stats["by_status"][s] > 0
        ]
        status_section = _section(
            "สัดส่วนตามสถานะ",
            _prop_bar(status_items, total),
        )

        # ── Priority bar ────────────────────────────────────────
        prio_items = [
            (p, stats["by_prio"][p], _PRIO_COLORS[p])
            for p in _PRIO_ORDER
            if stats["by_prio"][p] > 0
        ]
        prio_section = _section(
            "สัดส่วนตาม Priority",
            _prop_bar(prio_items, total),
        )

        # ── Per-team table ──────────────────────────────────────
        team_rows = _per_team_rows(tasks)
        team_rows_ctrl = [
            _table_header("ทีม", "งานทั้งหมด", "เสร็จแล้ว", "กำลังทำ", "เกินกำหนด"),
        ]
        if team_rows:
            for r in team_rows:
                team_rows_ctrl.append(
                    _table_row(*r, highlight_last_red=True)
                )
        else:
            team_rows_ctrl.append(
                ft.Text("ไม่มีข้อมูล", size=12, color=TEXT_SEC)
            )
        team_section = _section(
            "สรุปตามทีม",
            ft.Column(controls=team_rows_ctrl, spacing=0),
        )

        # ── Per-member table ────────────────────────────────────
        member_rows = _per_member_rows(tasks)
        member_rows_ctrl = [
            _table_header("ชื่อ", "ทีม", "งานทั้งหมด", "เสร็จแล้ว", "เกินกำหนด", "Sub-tasks"),
        ]
        if member_rows:
            for r in member_rows:
                # highlight col index 4 (overdue) red; col 5 (sub-tasks) is default
                member_rows_ctrl.append(
                    _table_row(*r, highlight_col_red=4)
                )
        else:
            member_rows_ctrl.append(
                ft.Text("ไม่มีข้อมูล", size=12, color=TEXT_SEC)
            )
        member_section = _section(
            "สรุปตามสมาชิก",
            ft.Column(controls=member_rows_ctrl, spacing=0),
        )

        # ── C4: Time Tracking report ────────────────────────────
        by_task   = api.get_time_summary_by_task()
        by_member = api.get_time_summary_by_member()

        def _fmt_min(m: int) -> str:
            if m < 60:
                return f"{m} นาที"
            h, r = divmod(m, 60)
            return f"{h} ชม. {r} นาที" if r else f"{h} ชม."

        # Time table header
        def _time_header(*cols) -> ft.Row:
            return ft.Row(
                controls=[ft.Text(c, size=11, color=TEXT_SEC,
                                  weight=ft.FontWeight.W_600,
                                  expand=1 if i == 0 else 0,
                                  width=None if i == 0 else 90)
                           for i, c in enumerate(cols)],
                spacing=0,
            )

        def _time_row(label, minutes) -> ft.Row:
            return ft.Row(
                controls=[
                    ft.Text(label, size=12, color=TEXT_PRI, expand=True,
                            no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(_fmt_min(minutes), size=12, color=ACCENT, width=90),
                ],
                spacing=0,
            )

        task_time_rows  = [_time_header("งาน", "เวลารวม")] + (
            [_time_row(r["title"][:40], r["total_minutes"]) for r in by_task[:10]]
            or [ft.Text("ยังไม่มีข้อมูล", size=12, color=TEXT_SEC)]
        )
        member_time_rows = [_time_header("สมาชิก", "เวลารวม")] + (
            [_time_row(r["name"], r["total_minutes"]) for r in by_member[:10]]
            or [ft.Text("ยังไม่มีข้อมูล", size=12, color=TEXT_SEC)]
        )

        time_section = _section(
            "สรุปเวลาทำงาน",
            ft.Row(
                controls=[
                    ft.Container(
                        expand=True,
                        content=ft.Column(controls=task_time_rows, spacing=6),
                    ),
                    ft.Container(width=1, bgcolor=BORDER),
                    ft.Container(
                        expand=True,
                        content=ft.Column(controls=member_time_rows, spacing=6),
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )

        content_col.controls = [
            cards,
            ft.Row(controls=[status_section, prio_section],
                   spacing=16, expand=True),
            team_section,
            member_section,
            time_section,
        ]
        try:
            content_col.update()
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════
    #  FILTER BAR
    # ══════════════════════════════════════════════════════════════
    def _team_options():
        teams = api.get_teams()
        return [ft.dropdown.Option(ALL_OPT)] + [
            ft.dropdown.Option(key=str(t["id"]), text=t["name"]) for t in teams
        ]

    dd_team = ft.Dropdown(
        label="ทีม", width=150,
        options=_team_options(), value=ALL_OPT,
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
        text_size=12,
        on_select=lambda e: _on_filter("filter_team", e.control.value),
    )

    # Date from / to as simple text fields (dd/mm/yyyy)
    tf_date_from = ft.TextField(
        label="วันที่เริ่ม (dd/mm/yyyy)", width=170,
        hint_text="01/01/2568",
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC, size=11),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
        text_size=12,
        on_submit=lambda e: _apply_dates(),
        on_blur=lambda e: _apply_dates(),
    )
    tf_date_to = ft.TextField(
        label="วันที่สิ้นสุด (dd/mm/yyyy)", width=170,
        hint_text="31/12/2568",
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_SEC, size=11),
        color=TEXT_PRI, bgcolor=BG_INPUT, border_radius=8,
        text_size=12,
        on_submit=lambda e: _apply_dates(),
        on_blur=lambda e: _apply_dates(),
    )

    def _apply_dates():
        state["date_from"] = parse_date_field(tf_date_from.value or "")
        state["date_to"]   = parse_date_field(tf_date_to.value or "")
        _rebuild()

    def _on_filter(key: str, val):
        state[key] = val
        _rebuild()

    def _clear_filters(e):
        state["filter_team"] = ALL_OPT
        state["date_from"]   = None
        state["date_to"]     = None
        dd_team.value        = ALL_OPT
        tf_date_from.value   = ""
        tf_date_to.value     = ""
        try:
            dd_team.update()
        except Exception:
            pass
        try:
            tf_date_from.update()
        except Exception:
            pass
        try:
            tf_date_to.update()
        except Exception:
            pass
        _rebuild()

    # ── Refresh button ────────────────────────────────────────────
    def _on_refresh(e):
        _rebuild()

    # ══════════════════════════════════════════════════════════════
    #  TOP BAR
    # ══════════════════════════════════════════════════════════════
    top_bar = ft.Row(
        controls=[
            ft.Column(
                controls=[
                    ft.Text("สรุปงาน", size=24,
                            weight=ft.FontWeight.BOLD, color=TEXT_PRI),
                    ft.Text("ภาพรวมและสถิติของงานทั้งหมด",
                            size=13, color=TEXT_SEC),
                ],
                spacing=2,
            ),
            ft.Row(
                controls=[
                    ft.Button(
                        content=ft.Text("Export Excel"),
                        icon=ft.Icons.TABLE_CHART_OUTLINED,
                        bgcolor=BG_CARD,
                        color=COLOR_DONE,
                        style=ft.ButtonStyle(
                            side=ft.BorderSide(1, COLOR_DONE + "66"),
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        on_click=_export_excel,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        icon_color=TEXT_SEC, icon_size=20,
                        tooltip="รีเฟรช",
                        on_click=_on_refresh,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    filter_bar = ft.Row(
        controls=[
            ft.Icon(ft.Icons.FILTER_LIST, color=TEXT_SEC, size=18),
            ft.Text("กรองข้อมูล:", size=12, color=TEXT_SEC),
            dd_team,
            tf_date_from,
            tf_date_to,
            ft.TextButton(
                "ล้าง",
                style=ft.ButtonStyle(color=TEXT_SEC),
                on_click=_clear_filters,
            ),
        ],
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        wrap=True,
    )

    # ── Initial render ────────────────────────────────────────────
    _rebuild()

    return ft.Container(
        expand=True,
        bgcolor=BG_DARK,
        padding=ft.padding.all(24),
        content=ft.Column(
            controls=[
                top_bar,
                ft.Divider(height=12, color=BORDER),
                filter_bar,
                ft.Divider(height=12, color=BORDER),
                content_col,
            ],
            spacing=0,
            expand=True,
        ),
    )
