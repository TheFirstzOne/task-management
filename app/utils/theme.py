"""
Centralised colour palette & typography constants.
Import this wherever UI colours are needed.
Blue-White theme — clean, professional look.
"""

# ══════════════════════════════════════════════════════════════════════════════
#  BACKGROUNDS
# ══════════════════════════════════════════════════════════════════════════════
BG_DARK    = "#F0F4F8"   # Page background (light grey-blue)
BG_SIDEBAR = "#FFFFFF"   # Sidebar background (white)
BG_CARD    = "#FFFFFF"   # Card background (white)
BG_INPUT   = "#E8EDF2"   # Input field background

# ══════════════════════════════════════════════════════════════════════════════
#  ACCENT COLOURS
# ══════════════════════════════════════════════════════════════════════════════
ACCENT     = "#2563EB"   # Blue — primary action
ACCENT2    = "#0EA5E9"   # Sky blue — secondary highlight

# ══════════════════════════════════════════════════════════════════════════════
#  TEXT
# ══════════════════════════════════════════════════════════════════════════════
TEXT_PRI = "#1E293B"   # Primary text (dark slate)
TEXT_SEC = "#64748B"   # Secondary text (slate)
TEXT_DIM = "#94A3B8"   # Dimmed text (light slate)

# ══════════════════════════════════════════════════════════════════════════════
#  BORDER
# ══════════════════════════════════════════════════════════════════════════════
BORDER = "#CBD5E1"     # Border (slate-200)

# ══════════════════════════════════════════════════════════════════════════════
#  STATUS COLOURS
# ══════════════════════════════════════════════════════════════════════════════
COLOR_PENDING     = "#F59E0B"   # Amber
COLOR_IN_PROGRESS = "#0EA5E9"   # Sky blue
COLOR_REVIEW      = "#8B5CF6"   # Violet
COLOR_DONE        = "#22C55E"   # Green
COLOR_CANCELLED   = "#9CA3AF"   # Grey
COLOR_OVERDUE     = "#EF4444"   # Red

# ══════════════════════════════════════════════════════════════════════════════
#  PRIORITY COLOURS
# ══════════════════════════════════════════════════════════════════════════════
COLOR_LOW    = "#22C55E"
COLOR_MEDIUM = "#F59E0B"
COLOR_HIGH   = "#F97316"
COLOR_URGENT = "#EF4444"


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

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
