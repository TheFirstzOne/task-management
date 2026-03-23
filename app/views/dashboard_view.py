# -*- coding: utf-8 -*-
"""
Dashboard View — Phase 13 (B) — Professional Light Theme
Charts saved as PNG files (Flet desktop does not support data-URI in Image.src).
Layout: balanced 2-column grid inspired by Linear / Asana / Monday.com style.
"""
from __future__ import annotations

import os
import threading
import traceback
from datetime import datetime, timedelta
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import flet as ft
from sqlalchemy.orm import Session

import app.utils.theme as theme
from app.utils.theme import status_color, priority_color
from app.services.task_service import TaskService
from app.models.task import TaskStatus
from app.database import DATA_DIR


# ── Chart output directory ───────────────────────────────────────────────────
_CHART_DIR = os.path.join(DATA_DIR, "charts")
os.makedirs(_CHART_DIR, exist_ok=True)

# ── Consistent chart dimensions ──────────────────────────────────────────────
_FIG_W    = 5.2    # all charts same width
_FIG_H    = 3.0    # all charts same height
_IMG_H    = 240    # rendered Image height in Flet

# ── Chart cache — skip re-render if data unchanged ───────────────────────────
_CACHE_KEY: dict = {"value": None}   # module-level: persists across navigations
_MATPLOTLIB_LOCK = threading.Lock()  # protect global pyplot state (Agg is not 100% thread-safe)


def _make_cache_key(stats: dict, priority_counts: dict, workload_counter: dict) -> tuple:
    """Hashable signature of chart inputs + today's date (trend changes per day)."""
    return (
        stats.get("total", 0), stats.get("pending", 0),
        stats.get("in_progress", 0), stats.get("review", 0),
        stats.get("done", 0), stats.get("cancelled", 0),
        stats.get("overdue", 0),
        tuple(sorted(priority_counts.items())),
        tuple(sorted(workload_counter.items())),
        datetime.now().date(),
    )

# ── Palette — matches light UI theme ─────────────────────────────────────────
_TEXT_DARK  = "#1E293B"
_TEXT_MID   = "#64748B"
_GRID_COLOR = "#E2E8F0"

STATUS_COLORS = {s: status_color(s) for s in ["Pending", "In Progress", "Review", "Done", "Cancelled"]}
PRIO_COLORS   = {p: priority_color(p) for p in ["Urgent", "High", "Medium", "Low"]}


# ── Thai font setup ──────────────────────────────────────────────────────────
def _setup_thai_font() -> str | None:
    import matplotlib.font_manager as fm
    for family in ["Tahoma", "Leelawadee UI", "Leelawadee",
                   "Angsana New", "Cordia New", "Browallia New"]:
        try:
            found = fm.findfont(fm.FontProperties(family=family),
                                fallback_to_default=False)
            if found and "DejaVu" not in found:
                matplotlib.rcParams["font.family"]       = family
                matplotlib.rcParams["axes.unicode_minus"] = False
                return family
        except Exception:
            pass
    for fp in fm.findSystemFonts():
        fn = fp.lower()
        if any(x in fn for x in ("thsarabun", "noto", "thai", "angsana",
                                   "leelawadee", "tahoma", "garuda")):
            try:
                prop = fm.FontProperties(fname=fp)
                name = prop.get_name()
                matplotlib.rcParams["font.family"]       = name
                matplotlib.rcParams["axes.unicode_minus"] = False
                return name
            except Exception:
                pass
    return None


_THAI_FONT = _setup_thai_font()


def _tfp():
    if _THAI_FONT:
        import matplotlib.font_manager as fm
        return fm.FontProperties(family=_THAI_FONT)
    return None


# ── Render helper — save to PNG file ─────────────────────────────────────────
def _render_chart(fig, name: str) -> str:
    """Figure → PNG file path. Flet Image.src uses this path."""
    path = os.path.join(_CHART_DIR, f"{name}.png")
    with _MATPLOTLIB_LOCK:
        fig.savefig(path, format="png", bbox_inches="tight",
                    facecolor="#FFFFFF", dpi=120)
        plt.close(fig)
    return path


def _chart_path(name: str) -> str:
    return os.path.join(_CHART_DIR, f"{name}.png")


def _cached_image(name: str) -> ft.Control | None:
    """Return ft.Image if PNG already exists on disk (stale-but-instant display)."""
    path = _chart_path(name)
    if os.path.exists(path):
        return ft.Image(src=path, height=_IMG_H, fit="contain")
    return None


def _ax_light(ax):
    """Apply light-theme styling to axes."""
    ax.set_facecolor("#FFFFFF")
    ax.tick_params(colors=_TEXT_MID, labelsize=9, length=0)
    for spine in ax.spines.values():
        spine.set_color(_GRID_COLOR)
    ax.yaxis.label.set_color(_TEXT_MID)
    ax.xaxis.label.set_color(_TEXT_MID)


# ── Chart card wrapper ───────────────────────────────────────────────────────
def _chart_card(title: str, chart_ctrl: ft.Control,
                subtitle: str = "") -> ft.Container:
    header = [
        ft.Text(title, size=14, weight=ft.FontWeight.W_600,
                color=theme.TEXT_PRI),
    ]
    if subtitle:
        header.append(ft.Text(subtitle, size=11, color=theme.TEXT_SEC))

    return ft.Container(
        bgcolor=theme.BG_CARD,
        border_radius=12,
        border=ft.border.all(1, theme.BORDER),
        padding=ft.padding.all(16),
        expand=True,
        content=ft.Column(
            controls=[
                ft.Column(controls=header, spacing=2),
                ft.Divider(height=8, color=theme.BORDER),
                ft.Container(
                    content=chart_ctrl,
                    alignment=ft.alignment.Alignment(0, 0),
                ),
            ],
            spacing=4,
        ),
    )


# ── B1: Status Donut ────────────────────────────────────────────────────────
def _chart_status_donut(stats: dict) -> ft.Control:
    data = [
        ("Pending",     stats.get("pending", 0),     STATUS_COLORS["Pending"]),
        ("In Progress", stats.get("in_progress", 0), STATUS_COLORS["In Progress"]),
        ("Review",      stats.get("review", 0),      STATUS_COLORS["Review"]),
        ("Done",        stats.get("done", 0),         STATUS_COLORS["Done"]),
        ("Cancelled",   stats.get("cancelled", 0),   STATUS_COLORS["Cancelled"]),
    ]
    data = [(l, v, c) for l, v, c in data if v > 0]
    if not data:
        return ft.Text("ยังไม่มีข้อมูล", size=12, color=theme.TEXT_SEC)

    labels, values, colors = zip(*data)
    fig, ax = plt.subplots(figsize=(_FIG_W, _FIG_H), facecolor="#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    wedges, _, autotexts = ax.pie(
        values, colors=colors,
        autopct="%1.0f%%", pctdistance=0.78,
        wedgeprops=dict(width=0.52, edgecolor="#FFFFFF", linewidth=2),
        startangle=90,
    )
    for at in autotexts:
        at.set_color(_TEXT_DARK)
        at.set_fontsize(9)
        at.set_fontweight("bold")

    ax.legend(
        wedges, labels,
        loc="center left", bbox_to_anchor=(1.05, 0.5),
        fontsize=9, frameon=False, labelcolor=_TEXT_MID,
    )

    return ft.Image(src=_render_chart(fig, "status_donut"),
                    height=_IMG_H, fit="contain")


# ── B2: Priority Bar ────────────────────────────────────────────────────────
def _chart_priority_bar(priority_counts: dict) -> ft.Control:
    """Accepts pre-collected {priority_value: count} dict — no ORM access."""
    counts = priority_counts
    order  = ["Urgent", "High", "Medium", "Low"]
    vals   = [counts.get(p, 0) for p in order]
    clrs   = [PRIO_COLORS[p] for p in order]

    if not any(vals):
        return ft.Text("ยังไม่มีข้อมูล", size=12, color=theme.TEXT_SEC)

    fig, ax = plt.subplots(figsize=(_FIG_W, _FIG_H), facecolor="#FFFFFF")
    _ax_light(ax)

    bars = ax.barh(order[::-1], vals[::-1], color=clrs[::-1],
                   height=0.55, edgecolor="none")
    for bar, v in zip(bars, vals[::-1]):
        if v > 0:
            ax.text(bar.get_width() + 0.15,
                    bar.get_y() + bar.get_height() / 2,
                    str(v), va="center", color=_TEXT_DARK,
                    fontsize=10, fontweight="bold")

    ax.set_xlabel("จำนวนงาน", color=_TEXT_MID, fontsize=9,
                  fontproperties=_tfp())
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(0, max(vals or [1]) * 1.35)
    ax.grid(axis="x", color=_GRID_COLOR, linestyle="--",
            linewidth=0.5, alpha=0.8)
    ax.set_axisbelow(True)

    return ft.Image(src=_render_chart(fig, "priority_bar"),
                    height=_IMG_H, fit="contain")


# ── B3: Weekly Trend ─────────────────────────────────────────────────────────
def _chart_weekly_trend(trend_created: list, trend_done: list) -> ft.Control:
    """Accepts pre-collected tuples — no ORM access in background thread."""
    today = datetime.now().date()
    days  = [today - timedelta(days=i) for i in range(6, -1, -1)]

    created = Counter(row[0].date() for row in trend_created)
    done_d  = Counter(
        row[0].date() for row in trend_done
        if row[1] == TaskStatus.DONE)

    c_vals  = [created.get(d, 0) for d in days]
    d_vals  = [done_d.get(d, 0) for d in days]
    xlabels = [d.strftime("%d/%m") for d in days]

    fig, ax = plt.subplots(figsize=(_FIG_W, _FIG_H), facecolor="#FFFFFF")
    _ax_light(ax)

    ax.fill_between(xlabels, c_vals, alpha=0.12, color="#3B82F6")
    ax.fill_between(xlabels, d_vals, alpha=0.12, color="#22C55E")
    ax.plot(xlabels, c_vals, color="#3B82F6", marker="o",
            markersize=5, linewidth=2, label="สร้าง",
            markerfacecolor="#FFFFFF", markeredgewidth=1.5)
    ax.plot(xlabels, d_vals, color="#22C55E", marker="o",
            markersize=5, linewidth=2, label="เสร็จ",
            markerfacecolor="#FFFFFF", markeredgewidth=1.5)

    ax.set_ylim(0, max(max(c_vals or [0]), max(d_vals or [0])) + 1.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color=_GRID_COLOR, linestyle="--",
            linewidth=0.5, alpha=0.8)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    fp = _tfp()
    if fp:
        ax.legend(fontsize=9, frameon=False, labelcolor=_TEXT_MID, prop=fp)
    else:
        ax.legend(fontsize=9, frameon=False, labelcolor=_TEXT_MID)

    return ft.Image(src=_render_chart(fig, "weekly_trend"),
                    height=_IMG_H, fit="contain")


# ── B4: Team Workload ────────────────────────────────────────────────────────
def _chart_team_workload(workload_counter: dict) -> ft.Control:
    """Accepts pre-collected {name: count} dict — avoids lazy-load in background thread."""
    counter = Counter(workload_counter)

    if not counter:
        return ft.Text("ยังไม่มีข้อมูล", size=12, color=theme.TEXT_SEC)

    pairs  = counter.most_common(8)
    names  = [p[0] for p in pairs][::-1]
    counts = [p[1] for p in pairs][::-1]
    max_c  = max(counts or [1])
    clrs   = [f"#{int(59 + (v/max_c)*60):02X}{int(130 + (v/max_c)*60):02X}{int(246):02X}"
              for v in counts]

    fig, ax = plt.subplots(figsize=(_FIG_W, _FIG_H), facecolor="#FFFFFF")
    _ax_light(ax)

    bars = ax.barh(names, counts, color=clrs, height=0.55, edgecolor="none")
    for bar, v in zip(bars, counts):
        if v > 0:
            ax.text(bar.get_width() + 0.15,
                    bar.get_y() + bar.get_height() / 2,
                    str(v), va="center", color=_TEXT_DARK,
                    fontsize=10, fontweight="bold")

    ax.set_xlabel("งานที่ยังไม่เสร็จ", color=_TEXT_MID, fontsize=9,
                  fontproperties=_tfp())
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(0, max(counts or [1]) * 1.35)
    ax.grid(axis="x", color=_GRID_COLOR, linestyle="--",
            linewidth=0.5, alpha=0.8)
    ax.set_axisbelow(True)

    return ft.Image(src=_render_chart(fig, "team_workload"),
                    height=_IMG_H, fit="contain")


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY
# ═══════════════════════════════════════════════════════════════════════════════
def build_dashboard_view(db: Session, navigate_fn=None) -> ft.Control:
    try:
        return _build_dashboard_inner(db, navigate_fn)
    except Exception as err:
        tb = traceback.format_exc()
        return ft.Container(
            expand=True,
            bgcolor=theme.BG_DARK,
            padding=24,
            content=ft.Column(
                controls=[
                    ft.Text("Dashboard Error", size=18,
                            weight=ft.FontWeight.BOLD, color="#EF4444"),
                    ft.Text(str(err), size=13, color=theme.TEXT_SEC),
                    ft.Text(tb, size=10, color=theme.TEXT_SEC,
                            selectable=True),
                ],
                scroll=ft.ScrollMode.AUTO, spacing=8,
            ),
        )


def _build_dashboard_inner(db: Session, navigate_fn=None) -> ft.Control:
    svc   = TaskService(db)
    stats = svc.get_dashboard_stats()
    tasks = svc.get_all_tasks()

    # ── Stat cards ─────────────────────────────────────────────────
    def _stat_card(label: str, value: int, color: str,
                   icon, bg_color: str) -> ft.Container:
        return ft.Container(
            height=80,
            expand=True,
            bgcolor=theme.BG_CARD,
            border_radius=12,
            border=ft.border.all(1, theme.BORDER),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            ink=True,
            on_click=lambda e: navigate_fn("task") if navigate_fn else None,
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=38, height=38, border_radius=10,
                        bgcolor=bg_color,
                        alignment=ft.alignment.Alignment(0, 0),
                        content=ft.Icon(icon, color=color, size=18),
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(str(value), size=22,
                                    weight=ft.FontWeight.BOLD, color=color),
                            ft.Text(label, size=11, color=theme.TEXT_SEC),
                        ],
                        spacing=0,
                        tight=True,
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    stat_row = ft.Row(
        controls=[
            _stat_card("ทั้งหมด",    stats["total"],
                       theme.TEXT_PRI, ft.Icons.LIST_ALT_OUTLINED,    "#F1F5F9"),
            _stat_card("กำลังทำ",    stats["in_progress"],
                       "#3B82F6",     ft.Icons.PENDING_ACTIONS_OUTLINED, "#EFF6FF"),
            _stat_card("เสร็จแล้ว",  stats["done"],
                       "#22C55E",     ft.Icons.TASK_ALT,                 "#F0FDF4"),
            _stat_card("เกินกำหนด",  stats["overdue"],
                       "#EF4444",     ft.Icons.WARNING_AMBER_OUTLINED,   "#FEF2F2"),
            _stat_card("ค้างอยู่",   stats["pending"],
                       "#F59E0B",     ft.Icons.HOURGLASS_EMPTY_OUTLINED, "#FFFBEB"),
        ],
        spacing=10,
    )

    # ── Pre-collect ALL data needed by charts (must happen in main thread) ────
    # Background thread cannot safely access lazy-loaded relationships or
    # expired ORM attributes after session changes. Snapshot everything now.
    from collections import Counter as _Counter

    # For _chart_team_workload — requires lazy-loaded task.assignee.name
    _wl_counter: _Counter = _Counter()
    for _t in tasks:
        if _t.status not in (TaskStatus.DONE, TaskStatus.CANCELLED):
            _wl_counter[_t.assignee.name if _t.assignee else "ไม่ระบุ"] += 1
    workload_counter = dict(_wl_counter)

    # For _chart_priority_bar — snapshot priority counts
    priority_counts = dict(_Counter(t.priority.value for t in tasks if t.status not in (TaskStatus.DONE, TaskStatus.CANCELLED)))

    # For _chart_weekly_trend — snapshot dates and statuses
    trend_created = [(t.created_at, ) for t in tasks if t.created_at]
    trend_done    = [(t.updated_at, t.status) for t in tasks if t.updated_at]

    # ── UX#5: Chart area with loading indicator ────────────────────
    def _loading_placeholder(height: int = 260) -> ft.Container:
        return ft.Container(
            height=height, expand=True,
            bgcolor=theme.BG_CARD,
            border_radius=12,
            border=ft.border.all(1, theme.BORDER),
            alignment=ft.alignment.Alignment(0, 0),
            content=ft.Column(
                controls=[
                    ft.ProgressRing(width=28, height=28,
                                    stroke_width=3, color=theme.ACCENT),
                    ft.Text("กำลังโหลด...", size=12, color=theme.TEXT_SEC),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
        )

    # ── Cache check ───────────────────────────────────────────────────────────
    current_key = _make_cache_key(stats, priority_counts, workload_counter)
    data_unchanged = (current_key == _CACHE_KEY["value"])

    # ── Placeholder: show stale PNG instantly if it exists, else spinner ──────
    def _init_placeholder(chart_name: str) -> ft.Container:
        cached = _cached_image(chart_name)
        if cached:
            # Stale-but-instant: reuse existing PNG while new one renders
            return ft.Container(expand=True, content=ft.Container(
                content=cached, alignment=ft.alignment.Alignment(0, 0)))
        return _loading_placeholder()

    ph_donut    = _init_placeholder("status_donut")
    ph_prio     = _init_placeholder("priority_bar")
    ph_trend    = _init_placeholder("weekly_trend")
    ph_workload = _init_placeholder("team_workload")

    chart_grid = ft.Column(
        controls=[
            ft.Row(controls=[
                _chart_card("สถานะงาน", ph_donut,    "สัดส่วนงานแยกตามสถานะ"),
                _chart_card("Priority",  ph_prio,     "จำนวนงานแยกตาม Priority"),
            ], spacing=12),
            ft.Row(controls=[
                _chart_card("แนวโน้ม 7 วัน",    ph_trend,    "งานที่สร้างและเสร็จในแต่ละวัน"),
                _chart_card("ภาระงานต่อสมาชิก", ph_workload, "งานที่ยังไม่เสร็จต่อสมาชิก"),
            ], spacing=12),
        ],
        spacing=12,
    )

    def _replace_chart_placeholder(placeholder: ft.Container,
                                    new_ctrl: ft.Control) -> None:
        """Swap placeholder content with the rendered chart."""
        placeholder.content = ft.Container(
            content=new_ctrl,
            alignment=ft.alignment.Alignment(0, 0),
        )
        placeholder.height = None   # let chart determine height
        try:
            placeholder.update()
        except Exception:
            pass

    def _render_one(placeholder: ft.Container, build_fn, is_cached: bool) -> None:
        """Render one chart in its own thread. Skip if data unchanged and PNG exists.

        Thread safety: each build_fn creates its own Figure via plt.subplots() which
        is safe on the Agg backend as long as figures are independent. _MATPLOTLIB_LOCK
        guards only savefig/plt.close — the only operations touching global pyplot state.
        """
        if is_cached:
            return   # PNG on disk is already current — nothing to do
        try:
            ctrl = build_fn()
        except Exception as err:
            ctrl = ft.Text(f"Chart error: {err}", color="#EF4444", size=12)
        _replace_chart_placeholder(placeholder, ctrl)

    def _render_charts_bg() -> None:
        """Parallel rendering: 4 threads, one per chart.
        Uses only pre-collected plain dicts/lists — no ORM objects."""
        pairs = [
            (ph_donut,    lambda: _chart_status_donut(stats)),
            (ph_prio,     lambda: _chart_priority_bar(priority_counts)),
            (ph_trend,    lambda: _chart_weekly_trend(trend_created, trend_done)),
            (ph_workload, lambda: _chart_team_workload(workload_counter)),
        ]
        threads = [
            threading.Thread(
                target=_render_one,
                args=(ph, fn, data_unchanged),
                daemon=True,
            )
            for ph, fn in pairs
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # Update cache key only after all charts are successfully written
        if not data_unchanged:
            _CACHE_KEY["value"] = current_key

    threading.Thread(target=_render_charts_bg, daemon=True).start()

    return ft.Container(
        expand=True,
        bgcolor=theme.BG_DARK,
        padding=24,
        content=ft.Column(
            controls=[
                ft.Text("Dashboard", size=24,
                        weight=ft.FontWeight.BOLD, color=theme.TEXT_PRI),
                ft.Text("ภาพรวมงานทั้งหมด", size=13, color=theme.TEXT_SEC),
                ft.Divider(height=16, color=theme.BORDER),
                stat_row,
                ft.Divider(height=16, color=theme.BORDER),
                chart_grid,
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        ),
    )
