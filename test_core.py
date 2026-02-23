# -*- coding: utf-8 -*-
"""
Core test script — Phase 1 validation
Run: venv\Scripts\python.exe test_core.py
"""

import sys
import os

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def check(label, fn):
    try:
        result = fn()
        print(f"{PASS} {label}" + (f" -> {result}" if result is not None else ""))
        results.append((True, label))
        return result
    except Exception as e:
        print(f"{FAIL} {label}\n       ERROR: {e}")
        results.append((False, label))
        return None


# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("  Task Manager — Phase 1 Core Tests")
print("=" * 60)

# 1. DB init + wipe test data (delete SQLite file for clean slate)
import glob as _glob
_db_files = _glob.glob(os.path.join(os.path.dirname(__file__), "data", "*.db"))
for _f in _db_files:
    os.remove(_f)

from app.database import init_db, SessionLocal
init_db()
check("DB init + create tables", lambda: "OK")

db = SessionLocal()

# 2. Team
from app.services.team_service import TeamService
tsvc = TeamService(db)
team = check("Create team", lambda: tsvc.create_team("TeamA", "Test team"))

# 3. Member
from app.models.user import UserRole
user = check("Add member to team",
             lambda: tsvc.add_member(team.id, "Alice", UserRole.ENGINEER, "Python"))

# 4. Workload
check("Get workload", lambda: tsvc.get_workload(team.id))

# 5. Task
from app.services.task_service import TaskService
from app.models.task import TaskPriority, TaskStatus
from datetime import datetime, timedelta

task_svc = TaskService(db)
task = check("Create task",
             lambda: task_svc.create_task(
                 title="Fix bug #42",
                 description="Reproduce and fix",
                 priority=TaskPriority.HIGH,
                 due_date=datetime.utcnow() + timedelta(days=3),
                 team_id=team.id,
                 assignee_id=user.id,
                 created_by_id=user.id,
             ))

# 6. Change status
check("Change status -> IN_PROGRESS",
      lambda: task_svc.change_status(task.id, TaskStatus.IN_PROGRESS, actor_id=user.id).status.value)

# 7. Dashboard stats
check("Dashboard stats", lambda: task_svc.get_dashboard_stats())

# 8. Comment
check("Add comment",
      lambda: task_svc.add_comment(task.id, "Started working", author_id=user.id).id)

# 9. Subtask
sub = check("Add subtask",
            lambda: task_svc.add_subtask(task.id, "Write unit test"))
if sub:
    check("Toggle subtask done",
          lambda: task_svc.toggle_subtask(sub.id).is_done)

# 10. History log
from app.models.history import WorkHistory
check("History entries recorded",
      lambda: db.query(WorkHistory).filter(WorkHistory.task_id == task.id).count())

# 11. Overdue (due = past)
past_task = task_svc.create_task(
    title="Overdue task",
    due_date=datetime.utcnow() - timedelta(days=1),
    team_id=team.id,
)
check("Detect overdue tasks",
      lambda: len(task_svc.get_overdue_tasks()))

# 12. View imports
print()
print("-- View imports --")


def import_views():
    from app.views.main_layout   import build_main_layout    # noqa
    from app.views.team_view     import build_team_view      # noqa
    from app.views.task_view     import build_task_view      # noqa
    from app.views.calendar_view import build_calendar_view  # noqa
    from app.views.summary_view  import build_summary_view   # noqa
    from app.views.history_view  import build_history_view   # noqa
    return "all views importable"


check("Import all views", import_views)

db.close()

# ─────────────────────────────────────────────────────────────────────────────
print()
print("=" * 60)
passed = sum(1 for ok, _ in results if ok)
failed = sum(1 for ok, _ in results if not ok)
print(f"  Results: {passed} passed, {failed} failed out of {len(results)} tests")
print("=" * 60)

if failed:
    for ok, label in results:
        if not ok:
            print(f"  {FAIL} {label}")
    sys.exit(1)
else:
    print("  All tests passed!")
