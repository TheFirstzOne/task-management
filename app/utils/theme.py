"""
Centralised colour palette & typography constants.
Import this wherever UI colours are needed.
"""

# ── Backgrounds ───────────────────────────────────────────────────
BG_DARK    = "#0F1117"
BG_SIDEBAR = "#16181F"
BG_CARD    = "#1E2028"
BG_INPUT   = "#252834"

# ── Accent colours ────────────────────────────────────────────────
ACCENT     = "#6C63FF"   # Purple — primary action
ACCENT2    = "#00D4FF"   # Cyan  — secondary highlight

# ── Status colours ────────────────────────────────────────────────
COLOR_PENDING     = "#FFC107"   # Amber
COLOR_IN_PROGRESS = "#00D4FF"   # Cyan
COLOR_REVIEW      = "#AB47BC"   # Purple
COLOR_DONE        = "#4CAF50"   # Green
COLOR_CANCELLED   = "#757575"   # Grey
COLOR_OVERDUE     = "#FF5252"   # Red

# ── Priority colours ──────────────────────────────────────────────
COLOR_LOW    = "#4CAF50"
COLOR_MEDIUM = "#FFC107"
COLOR_HIGH   = "#FF9800"
COLOR_URGENT = "#FF5252"

# ── Text ──────────────────────────────────────────────────────────
TEXT_PRI = "#F0F2F5"
TEXT_SEC = "#8B8FA8"
TEXT_DIM = "#4A4D5E"

# ── Border ────────────────────────────────────────────────────────
BORDER = "#2A2D3A"


def status_color(status: str) -> str:
    return {
        "Pending":     COLOR_PENDING,
        "In Progress": COLOR_IN_PROGRESS,
        "Review":      COLOR_REVIEW,
        "Done":        COLOR_DONE,
        "Cancelled":   COLOR_CANCELLED,
    }.get(status, TEXT_SEC)


def priority_color(priority: str) -> str:
    return {
        "Low":    COLOR_LOW,
        "Medium": COLOR_MEDIUM,
        "High":   COLOR_HIGH,
        "Urgent": COLOR_URGENT,
    }.get(priority, TEXT_SEC)
