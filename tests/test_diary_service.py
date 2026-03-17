"""
Tests for DiaryService — daily work diary logic.
"""

import pytest
from app.services.diary_service import DiaryService


def _svc(db) -> DiaryService:
    return DiaryService(db)


def test_create_entry(db):
    entry = _svc(db).create_entry("ทำงาน A เสร็จแล้ว")
    assert entry.id is not None
    assert entry.content == "ทำงาน A เสร็จแล้ว"
    assert entry.created_at is not None


def test_get_all_entries_empty(db):
    assert _svc(db).get_all_entries() == []


def test_get_all_entries_ordered_newest_first(db):
    svc = _svc(db)
    svc.create_entry("รายการแรก")
    svc.create_entry("รายการสอง")
    entries = svc.get_all_entries()
    assert len(entries) == 2
    # newest first
    assert entries[0].content == "รายการสอง"


def test_delete_entry(db):
    svc = _svc(db)
    entry = svc.create_entry("จะลบ")
    result = svc.delete_entry(entry.id)
    assert result is True
    assert svc.get_all_entries() == []


def test_delete_nonexistent_returns_false(db):
    assert _svc(db).delete_entry(9999) is False


def test_update_entry(db):
    svc = _svc(db)
    entry = svc.create_entry("ข้อความเก่า")
    updated = svc.update_entry(entry.id, "ข้อความใหม่")
    assert updated.content == "ข้อความใหม่"


def test_get_entries_grouped(db):
    svc = _svc(db)
    svc.create_entry("บันทึก 1")
    svc.create_entry("บันทึก 2")
    grouped = svc.get_entries_grouped()
    assert len(grouped) >= 1
    # All entries under same date key (today)
    total = sum(len(v) for v in grouped.values())
    assert total == 2
