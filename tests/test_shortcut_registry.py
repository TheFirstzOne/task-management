# -*- coding: utf-8 -*-
"""
Tests for app/utils/shortcut_registry.py.
Each test clears the registry before running to ensure isolation.
"""
import pytest

from app.utils import shortcut_registry


@pytest.fixture(autouse=True)
def _clean_registry():
    """Ensure the global registry is empty before and after every test."""
    shortcut_registry.clear()
    yield
    shortcut_registry.clear()


# ── register + dispatch ───────────────────────────────────────────────────────

def test_register_and_dispatch():
    called = []
    shortcut_registry.register("ctrl_n", lambda: called.append(True))

    shortcut_registry.dispatch("n", ctrl=True, shift=False, alt=False)
    assert called == [True]


def test_clear_removes_handlers():
    called = []
    shortcut_registry.register("ctrl_n", lambda: called.append(True))
    shortcut_registry.clear()

    shortcut_registry.dispatch("n", ctrl=True, shift=False, alt=False)
    assert called == []


def test_dispatch_ctrl_combo():
    called = []
    shortcut_registry.register("ctrl_n", lambda: called.append("ctrl_n"))

    shortcut_registry.dispatch(key="n", ctrl=True, shift=False, alt=False)
    assert "ctrl_n" in called


def test_dispatch_plain_key():
    called = []
    shortcut_registry.register("escape", lambda: called.append("esc"))

    shortcut_registry.dispatch(key="Escape", ctrl=False, shift=False, alt=False)
    assert "esc" in called


def test_dispatch_unknown_shortcut_returns_false():
    result = shortcut_registry.dispatch("z", ctrl=True, shift=False, alt=False)
    assert result is False


def test_dispatch_shift_combo_not_handled():
    """ctrl+shift combo should NOT match a ctrl-only handler."""
    called = []
    shortcut_registry.register("ctrl_n", lambda: called.append(True))

    result = shortcut_registry.dispatch("n", ctrl=True, shift=True, alt=False)
    assert called == []
    assert result is False


def test_dispatch_known_shortcut_returns_true():
    shortcut_registry.register("ctrl_s", lambda: None)

    result = shortcut_registry.dispatch("s", ctrl=True, shift=False, alt=False)
    assert result is True


def test_dispatch_alt_combo_not_handled():
    """alt combos are not dispatched to any registered handler."""
    called = []
    shortcut_registry.register("ctrl_f", lambda: called.append(True))

    result = shortcut_registry.dispatch("f", ctrl=False, shift=False, alt=True)
    assert result is False
    assert called == []


def test_register_overwrites_previous_handler():
    results = []
    shortcut_registry.register("ctrl_q", lambda: results.append("first"))
    shortcut_registry.register("ctrl_q", lambda: results.append("second"))

    shortcut_registry.dispatch("q", ctrl=True, shift=False, alt=False)
    assert results == ["second"]


def test_multiple_shortcuts_independent(db=None):
    results = []
    shortcut_registry.register("ctrl_a", lambda: results.append("a"))
    shortcut_registry.register("ctrl_b", lambda: results.append("b"))

    shortcut_registry.dispatch("a", ctrl=True, shift=False, alt=False)
    shortcut_registry.dispatch("b", ctrl=True, shift=False, alt=False)
    assert results == ["a", "b"]
