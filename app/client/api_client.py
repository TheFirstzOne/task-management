# -*- coding: utf-8 -*-
"""
APIClient — Phase 21 HTTP client
Wraps all FastAPI server endpoints with type hints and error mapping.
"""
from __future__ import annotations
import httpx
from typing import Optional, Any
from .config import SERVER_URL
from app.utils.exceptions import (
    TaskFlowError, InvalidCredentialsError, ValidationError, NotFoundError
)

_TIMEOUT = 30.0   # seconds


class APIClient:
    def __init__(self, token: str = "") -> None:
        self.token   = token
        self._base   = SERVER_URL.rstrip("/")

    @property
    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    # ── HTTP helpers ───────────────────────────────────────────────────────
    def _get(self, path: str, params: dict = None) -> Any:
        r = httpx.get(f"{self._base}{path}", params=params or {},
                      headers=self._headers, timeout=_TIMEOUT)
        self._raise(r)
        return r.json()

    def _post(self, path: str, body: dict = None) -> Any:
        r = httpx.post(f"{self._base}{path}", json=body or {},
                       headers=self._headers, timeout=_TIMEOUT)
        self._raise(r)
        return r.json()

    def _patch(self, path: str, body: dict = None) -> Any:
        r = httpx.patch(f"{self._base}{path}", json=body or {},
                        headers=self._headers, timeout=_TIMEOUT)
        self._raise(r)
        return r.json()

    def _delete(self, path: str) -> None:
        r = httpx.delete(f"{self._base}{path}",
                         headers=self._headers, timeout=_TIMEOUT)
        self._raise(r)

    def _download(self, path: str) -> bytes:
        r = httpx.get(f"{self._base}{path}",
                      headers=self._headers, timeout=60.0)
        self._raise(r)
        return r.content

    def _raise(self, r: httpx.Response) -> None:
        if r.status_code < 400:
            return
        try:
            detail = r.json().get("detail", str(r.status_code))
        except Exception:
            detail = str(r.status_code)
        if r.status_code == 401:
            raise InvalidCredentialsError()
        if r.status_code == 404:
            raise NotFoundError("Resource", 0)
        if r.status_code == 422:
            raise ValidationError(str(detail))
        raise TaskFlowError(str(detail))

    # ── Auth ───────────────────────────────────────────────────────────────
    def login(self, username: str, password: str) -> dict:
        """POST /auth/login → {access_token, user:{id,name,username,is_admin}}"""
        return self._post("/auth/login", {"username": username, "password": password})

    # ── Tasks ──────────────────────────────────────────────────────────────
    def get_tasks(self) -> list[dict]:
        return self._get("/api/tasks")

    def get_task(self, task_id: int) -> dict:
        return self._get(f"/api/tasks/{task_id}")

    def get_deleted_tasks(self) -> list[dict]:
        return self._get("/api/tasks/deleted")

    def search_tasks(self, query: str, limit: int = 20) -> list[dict]:
        return self._get("/api/tasks/search", {"q": query, "limit": limit})

    def get_near_due_tasks(self, days: int = 3) -> list[dict]:
        return self._get("/api/tasks/near-due", {"days": days})

    def get_near_due_count(self, days: int = 3) -> int:
        return self._get("/api/tasks/near-due/count", {"days": days}).get("count", 0)

    def get_tasks_for_dropdown(self, exclude_id: int = None) -> list[dict]:
        params = {}
        if exclude_id is not None:
            params["exclude_id"] = exclude_id
        return self._get("/api/tasks/for-dropdown", params)

    def get_dependent_tasks(self, task_id: int) -> list[dict]:
        return self._get(f"/api/tasks/{task_id}/dependents")

    def create_task(self, title: str, description: str = "", priority: str = "Medium",
                    tags: str = "", start_date=None, due_date=None,
                    team_id: int = None, assignee_id: int = None,
                    depends_on_id: int = None) -> dict:
        body = {"title": title, "description": description, "priority": priority,
                "tags": tags, "start_date": start_date, "due_date": due_date,
                "team_id": team_id, "assignee_id": assignee_id,
                "depends_on_id": depends_on_id}
        return self._post("/api/tasks", {k: v for k, v in body.items()
                                         if v is not None or k in ("title", "description", "tags", "priority")})

    def update_task(self, task_id: int, **kwargs) -> dict:
        # Convert datetime objects to isoformat strings for JSON serialization
        body = {}
        for k, v in kwargs.items():
            if v is not None and hasattr(v, "isoformat"):
                body[k] = v.isoformat()
            elif v is not None:
                body[k] = v
            else:
                body[k] = None
        return self._patch(f"/api/tasks/{task_id}", body)

    def delete_task(self, task_id: int) -> None:
        self._delete(f"/api/tasks/{task_id}")

    def restore_task(self, task_id: int) -> dict:
        return self._post(f"/api/tasks/{task_id}/restore")

    # Subtasks
    def add_subtask(self, task_id: int, title: str,
                    due_date=None, assignee_id: int = None) -> dict:
        body: dict = {"title": title}
        if due_date is not None:
            body["due_date"] = (due_date.isoformat()
                                if hasattr(due_date, "isoformat") else str(due_date))
        if assignee_id is not None:
            body["assignee_id"] = assignee_id
        return self._post(f"/api/tasks/{task_id}/subtasks", body)

    def update_subtask(self, subtask_id: int, title: str,
                       due_date=None, assignee_id: int = None) -> dict:
        body: dict = {
            "title": title,
            "due_date": (due_date.isoformat()
                         if due_date and hasattr(due_date, "isoformat") else None),
            "assignee_id": assignee_id,
        }
        return self._patch(f"/api/subtasks/{subtask_id}", body)

    def toggle_subtask(self, subtask_id: int) -> dict:
        return self._patch(f"/api/subtasks/{subtask_id}/toggle")

    def delete_subtask(self, subtask_id: int) -> None:
        self._delete(f"/api/subtasks/{subtask_id}")

    # Comments
    def get_comments(self, task_id: int) -> list[dict]:
        return self._get(f"/api/tasks/{task_id}/comments")

    def add_comment(self, task_id: int, body: str, author_id: int = None) -> dict:
        return self._post(f"/api/tasks/{task_id}/comments", {"body": body, "author_id": author_id})

    # Time tracking
    def get_time_logs(self, task_id: int) -> list[dict]:
        return self._get(f"/api/tasks/{task_id}/time-logs")

    def get_total_minutes(self, task_id: int) -> int:
        return self._get(f"/api/tasks/{task_id}/time-logs/total").get("total_minutes", 0)

    def start_timer(self, task_id: int) -> dict:
        return self._post(f"/api/tasks/{task_id}/time-logs/start")

    def stop_timer(self, task_id: int) -> dict:
        return self._post(f"/api/tasks/{task_id}/time-logs/stop")

    def get_running_log(self, task_id: int) -> dict | None:
        """Returns running time log or None"""
        logs = self.get_time_logs(task_id)
        for log in logs:
            if log.get("is_running"):
                return log
        return None

    def delete_time_log(self, log_id: int) -> None:
        self._delete(f"/api/time-logs/{log_id}")

    # Dashboard
    def get_dashboard_stats(self) -> dict:
        return self._get("/api/dashboard/stats")

    # ── Teams ──────────────────────────────────────────────────────────────
    def get_teams(self) -> list[dict]:
        return self._get("/api/teams")

    def create_team(self, name: str, description: str = "") -> dict:
        return self._post("/api/teams", {"name": name, "description": description})

    def update_team(self, team_id: int, **kwargs) -> dict:
        return self._patch(f"/api/teams/{team_id}", kwargs)

    def delete_team(self, team_id: int) -> None:
        self._delete(f"/api/teams/{team_id}")

    def get_workload(self, team_id: int) -> dict:
        return self._get(f"/api/teams/{team_id}/workload").get("workload", {})

    def get_members_for_dropdown(self, team_id: int = None) -> list[dict]:
        params = {"team_id": team_id} if team_id else {}
        return self._get("/api/members/dropdown", params)

    def add_member(self, team_id: int, name: str, role: str, skills: str = "") -> dict:
        return self._post(f"/api/teams/{team_id}/members",
                          {"name": name, "role": role, "skills": skills})

    def update_member(self, user_id: int, **kwargs) -> dict:
        return self._patch(f"/api/members/{user_id}", kwargs)

    def delete_member(self, user_id: int) -> None:
        self._delete(f"/api/members/{user_id}")

    def toggle_member_active(self, user_id: int) -> dict:
        return self._post(f"/api/members/{user_id}/toggle-active")

    # ── Users (admin) ──────────────────────────────────────────────────────
    def get_users(self) -> list[dict]:
        return self._get("/api/users")

    def create_user(self, name: str, username: str, password: str,
                    role: str = "Other", is_admin: bool = False) -> dict:
        return self._post("/api/users", {"name": name, "username": username,
                                         "password": password, "role": role,
                                         "is_admin": is_admin})

    def update_user(self, user_id: int, **kwargs) -> dict:
        return self._patch(f"/api/users/{user_id}", kwargs)

    def set_user_password(self, user_id: int, password: str) -> None:
        self._post(f"/api/users/{user_id}/set-password", {"password": password})

    def toggle_user_admin(self, user_id: int) -> dict:
        return self._post(f"/api/users/{user_id}/toggle-admin")

    def change_password(self, user_id: int, old_password: str, new_password: str) -> None:
        self._post(f"/api/users/{user_id}/change-password",
                   {"old_password": old_password, "new_password": new_password})

    def set_user_credential(self, user_id: int, username: str, password: str) -> None:
        self._post(f"/api/users/{user_id}/set-credential",
                   {"username": username, "password": password})

    # ── Diary ──────────────────────────────────────────────────────────────
    def create_diary(self, content: str) -> dict:
        return self._post("/api/diary", {"content": content})

    def get_diary_grouped(self) -> dict:
        return self._get("/api/diary/grouped")

    def export_diary(self, fmt: str) -> bytes:
        """fmt = 'word' | 'pdf' — returns file bytes"""
        return self._download(f"/api/diary/export/{fmt}")

    # ── History ────────────────────────────────────────────────────────────
    def get_history(self, search: str = "", action: str = "",
                    actor_id: int = None, date_from: str = None,
                    date_to: str = None, page: int = 0) -> list[dict]:
        params = {"search": search, "action": action, "page": page}
        if actor_id:
            params["actor_id"] = actor_id
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        return self._get("/api/history", params)

    def get_history_actions(self) -> list[str]:
        return self._get("/api/history/actions")

    # ── Summary ────────────────────────────────────────────────────────────
    def get_time_summary_by_task(self) -> list[dict]:
        return self._get("/api/summary/time-by-task")

    def get_time_summary_by_member(self) -> list[dict]:
        return self._get("/api/summary/time-by-member")

    def export_summary_excel(self) -> bytes:
        return self._download("/api/summary/export/excel")

    # ── Milestones ─────────────────────────────────────────────────────────
    def get_milestones(self) -> list[dict]:
        return self._get("/api/milestones")

    def get_milestone(self, milestone_id: int) -> dict:
        return self._get(f"/api/milestones/{milestone_id}")

    def create_milestone(self, name: str, description: str = "", due_date=None) -> dict:
        body: dict = {"name": name, "description": description}
        if due_date is not None:
            body["due_date"] = due_date.isoformat() if hasattr(due_date, "isoformat") else str(due_date)
        return self._post("/api/milestones", body)

    def update_milestone(self, milestone_id: int, **kwargs) -> dict:
        body = {}
        for k, v in kwargs.items():
            if v is not None and hasattr(v, "isoformat"):
                body[k] = v.isoformat()
            else:
                body[k] = v
        return self._patch(f"/api/milestones/{milestone_id}", body)

    def delete_milestone(self, milestone_id: int) -> None:
        self._delete(f"/api/milestones/{milestone_id}")

    def assign_task_to_milestone(self, milestone_id: int, task_id: int) -> dict:
        return self._post(f"/api/milestones/{milestone_id}/tasks/{task_id}", {})

    def remove_task_from_milestone(self, milestone_id: int, task_id: int) -> None:
        self._delete(f"/api/milestones/{milestone_id}/tasks/{task_id}")

    # ── Dashboard Heatmap ──────────────────────────────────────────────────
    def get_workload_heatmap(self) -> dict:
        return self._get("/api/dashboard/workload-heatmap")
