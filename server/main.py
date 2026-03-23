# -*- coding: utf-8 -*-
"""FastAPI application factory — Phase 21"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.routers import auth as auth_router
from server.routers import dashboard, diary, history, summary, tasks, users
from server.routers.subtasks import router as subtasks_router
from server.routers.teams import members_router, teams_router

app = FastAPI(
    title="VindFlow API",
    version="21.0",
    description="REST API layer for VindFlow desktop task management app",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
# Auth — prefix /auth (login is POST /auth/login)
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])

# Task and related endpoints
app.include_router(tasks.router,     prefix="/api/tasks",     tags=["tasks"])
# Subtask and standalone time-log endpoints (PATCH /api/subtasks/{id}/toggle, etc.)
app.include_router(subtasks_router,  prefix="/api",           tags=["subtasks"])

# Team and member endpoints
app.include_router(teams_router,   prefix="/api/teams",   tags=["teams"])
app.include_router(members_router, prefix="/api/members", tags=["members"])

# Other resources
app.include_router(users.router,     prefix="/api/users",     tags=["users"])
app.include_router(diary.router,     prefix="/api/diary",     tags=["diary"])
app.include_router(history.router,   prefix="/api/history",   tags=["history"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(summary.router,   prefix="/api/summary",   tags=["summary"])


@app.get("/")
def root():
    return {"message": "VindFlow API v21.0", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}
