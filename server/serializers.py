# -*- coding: utf-8 -*-
"""ORM → plain dict serializers for VindFlow API — Phase 21"""

from __future__ import annotations


def task_to_dict(t) -> dict:
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description or "",
        "status": t.status.value if t.status else "Pending",
        "priority": t.priority.value if t.priority else "Medium",
        "tags": t.tags or "",
        "is_deleted": t.is_deleted,
        "start_date": t.start_date.isoformat() if t.start_date else None,
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        "team_id": t.team_id,
        "team_name": t.team.name if t.team else None,
        "assignee_id": t.assignee_id,
        "assignee_name": t.assignee.name if t.assignee else None,
        "created_by_id": t.created_by_id,
        "depends_on_id": t.depends_on_id,
        "milestone_id": t.milestone_id,
        "milestone_name": t.milestone.name if t.milestone else None,
        "subtasks": [subtask_to_dict(s) for s in (t.subtasks or []) if not s.is_deleted],
    }


def milestone_to_dict(m) -> dict:
    tasks = [t for t in (m.tasks or []) if not t.is_deleted]
    done  = sum(1 for t in tasks if t.status and t.status.value == "Done")
    return {
        "id":          m.id,
        "name":        m.name,
        "description": m.description or "",
        "due_date":    m.due_date.isoformat() if m.due_date else None,
        "created_at":  m.created_at.isoformat() if m.created_at else None,
        "updated_at":  m.updated_at.isoformat() if m.updated_at else None,
        "task_count":  len(tasks),
        "done_count":  done,
        "progress":    round(done / len(tasks), 2) if tasks else 0.0,
    }


def subtask_to_dict(s) -> dict:
    return {
        "id": s.id,
        "task_id": s.task_id,
        "title": s.title,
        "is_done": s.is_done,
        "is_deleted": s.is_deleted,
        "due_date": s.due_date.isoformat() if s.due_date else None,
        "assignee_id": s.assignee_id,
        "assignee_name": s.assignee.name if s.assignee else None,
    }


def user_to_dict(u) -> dict:
    return {
        "id": u.id,
        "name": u.name,
        "username": u.username,
        "role": u.role.value if u.role else "Other",
        "skills": u.skills or "",
        "is_active": u.is_active,
        "is_deleted": u.is_deleted,
        "team_id": u.team_id,
        "is_admin": u.is_admin,
    }


def team_to_dict(t, include_members: bool = True) -> dict:
    d = {
        "id": t.id,
        "name": t.name,
        "description": t.description or "",
        "is_deleted": t.is_deleted,
    }
    if include_members:
        d["members"] = [user_to_dict(m) for m in (t.members or []) if not m.is_deleted]
    return d


def diary_to_dict(e) -> dict:
    return {
        "id": e.id,
        "content": e.content,
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "updated_at": e.updated_at.isoformat() if e.updated_at else None,
    }


def comment_to_dict(c) -> dict:
    return {
        "id": c.id,
        "task_id": c.task_id,
        "body": c.body,
        "author_id": c.author_id,
        "author_name": c.author.name if c.author else "ไม่ระบุ",
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def timelog_to_dict(tl) -> dict:
    return {
        "id": tl.id,
        "task_id": tl.task_id,
        "user_id": tl.user_id,
        "started_at": tl.started_at.isoformat() if tl.started_at else None,
        "ended_at": tl.ended_at.isoformat() if tl.ended_at else None,
        "duration_minutes": tl.duration_minutes,
        "note": tl.note or "",
        "is_running": tl.is_running,
    }


def history_to_dict(h) -> dict:
    return {
        "id": h.id,
        "task_id": h.task_id,
        "action": h.action,
        "detail": h.detail or "",
        "actor_id": h.actor_id,
        "actor_name": h.actor.name if h.actor else "ระบบ",
        "old_value": h.old_value,
        "new_value": h.new_value,
        "created_at": h.created_at.isoformat() if h.created_at else None,
    }
