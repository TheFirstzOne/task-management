"""
Keyboard shortcut registry — views register handlers; shell dispatches.

Usage in shell (main_layout.py):
    from app.utils import shortcut_registry
    page.on_keyboard_event = lambda e: shortcut_registry.dispatch(e.key, e.ctrl, e.shift, e.alt)

Usage in views:
    from app.utils import shortcut_registry
    shortcut_registry.register("ctrl_n", lambda: open_dialog())
    shortcut_registry.register("esc",    lambda: close_dialog())
"""
from __future__ import annotations
from typing import Callable, Dict

_handlers: Dict[str, Callable] = {}


def register(shortcut: str, fn: Callable) -> None:
    """Register a handler. shortcut key e.g. 'ctrl_n', 'esc', 'enter', 'ctrl_f'."""
    _handlers[shortcut] = fn


def clear() -> None:
    """Clear all handlers — call before navigating away from a view."""
    _handlers.clear()


def dispatch(key: str, ctrl: bool, shift: bool, alt: bool) -> bool:
    """Try to call a registered handler. Returns True if handled."""
    if ctrl and not shift and not alt:
        combo = f"ctrl_{key.lower()}"
    elif not ctrl and not shift and not alt:
        combo = key.lower()
    else:
        return False
    fn = _handlers.get(combo)
    if fn:
        try:
            fn()
        except Exception:
            pass
        return True
    return False
