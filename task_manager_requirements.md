# VindFlow — Requirements & Tech Stack

> **Project:** Team Task Management Desktop Application
> **Platform:** Windows Desktop (Python Flet) + FastAPI Server (LAN)
> **Version:** 2.1.0
> **Last Updated:** April 2026

---

## 1. Project Overview

Desktop application สำหรับจัดการงานและมอบหมายงานในทีม รองรับการทำงานแบบ **Online Multi-user** ผ่าน LAN
ทุกเครื่องในทีมเชื่อมต่อมายัง FastAPI server กลาง ข้อมูลซิงค์กันแบบ real-time

**สถาปัตยกรรมปัจจุบัน:**
```
เครื่อง A:  [Flet UI] → [HTTP Client] ──┐
เครื่อง B:  [Flet UI] → [HTTP Client] ──┼──→ [FastAPI Server :8000] → [SQLite]
เครื่อง C:  [Flet UI] → [HTTP Client] ──┘
```

---

## 2. Functional Requirements

### 2.1 ระบบสร้างทีมงาน
- สร้าง แก้ไข ลบทีม
- เพิ่ม/ลบสมาชิกในทีม
- กำหนด Role และ Skill เช่น Technician, Engineer, CNC, PLC, Hydraulic
- แสดง Workload ของแต่ละคน เพื่อป้องกันงานกองเกิน
- เปิด/ปิดสถานะ Active ของสมาชิก

### 2.2 ระบบแจกจ่ายงาน
#### 2.2.1 สร้างงาน
- กำหนด Title, Description, Priority (Low / Medium / High / Urgent)
- กำหนด Start Date และ Due Date
- แนบ Checklist ย่อย (Sub-tasks) ภายในงาน
- ระบุ Tag หรือหมวดหมู่งาน
- Visual indicator เมื่องานใกล้หรือเกิน Deadline
- Recycle Bin — กู้คืนงานที่ลบแล้วได้ (Soft Delete)

#### 2.2.2 มอบหมายงาน
- มอบหมายงานให้สมาชิกในทีม
- Task Status Flow: `Pending → In Progress → Review → Done / Cancelled`
- รองรับ Task Dependencies (ระบุว่างานไหนต้องทำก่อน)
- บันทึก Comment / Note ต่องานแบบ Timeline

### 2.3 ปฏิทินแผนงาน
- แสดงงานและการมอบหมายในรูปแบบ Calendar View
- Filter ตาม ทีม, สมาชิก, สถานะ, Priority
- แสดง Deadline และช่วงเวลาของงานแต่ละชิ้น

### 2.4 สรุปงาน
- สรุปงานทั้งหมดในรูปแบบ Text
- กรองสรุปตามทีม, สมาชิก, ช่วงวันที่, สถานะ
- Export รายงานเป็น PDF และ Excel
- Dashboard ตัวเลขภาพรวม: งานเสร็จ / ค้าง / เกินกำหนด
- สรุปเวลาทำงานแยกตามงาน และแยกตามสมาชิก

### 2.5 ประวัติการทำงาน
- บันทึก Action Log ทุกการเปลี่ยนแปลงของงาน เช่น สร้าง, มอบหมาย, เปลี่ยน Status, Comment
- ดูประวัติย้อนหลังรายงานแต่ละชิ้น
- ค้นหาและ Filter ประวัติด้วยวันที่ หรือสมาชิก

### 2.6 ระบบ Login & Auth (Phase 19)
- Login ด้วย username / password
- PBKDF2-SHA256 hashing (260,000 iterations)
- Admin สร้าง/จัดการบัญชีผู้ใช้ทั้งหมด
- แต่ละ user จัดการโปรไฟล์และเปลี่ยนรหัสผ่านตัวเองได้
- Default admin: username=`admin`, password=`admin` (สร้างอัตโนมัติเมื่อ DB ว่าง)

### 2.7 Online Multi-user (Phase 21)
- ทุกเครื่องเชื่อมต่อ FastAPI server กลางผ่าน LAN
- JWT token authentication (24 ชั่วโมง)
- Swagger UI ที่ `/docs` สำหรับ developer
- 52+ API endpoints ครอบคลุมทุก feature

---

## 3. Non-Functional Requirements

| หัวข้อ | รายละเอียด |
|--------|-----------|
| **Platform** | Windows Desktop (.exe) + FastAPI Server |
| **UI Theme** | Blue-White ถาวร |
| **Database** | SQLite บน server กลาง (LAN) |
| **Network** | Online-only ผ่าน LAN (ต้องเชื่อมต่อ server) |
| **Performance** | เปิดแอปได้ภายใน 3 วินาที |
| **Security** | JWT Bearer token, PBKDF2 password hashing |
| **Packaging** | Build เป็น .exe ด้วย PyInstaller แจกจ่ายในทีม |
| **Server** | รัน `python server.py` บนเครื่องที่เปิดทิ้งไว้ |

---

## 4. Tech Stack

### 4.1 Core

| Layer | Technology | หมายเหตุ |
|-------|-----------|---------|
| **UI Framework** | `Flet 0.27.6` | Python-based, function-based views |
| **Language** | `Python 3.10+` | |
| **Database** | `SQLite` | บน server กลาง |
| **ORM** | `SQLAlchemy 2.x` | จัดการ database query แบบ Pythonic |
| **API Server** | `FastAPI 0.110+` | REST API สำหรับ multi-user |
| **ASGI Server** | `uvicorn` | รัน FastAPI |
| **HTTP Client** | `httpx` | Sync HTTP client บน desktop |
| **Auth** | `python-jose[cryptography]` | JWT token |

### 4.2 Utilities

| Package | การใช้งาน |
|---------|---------|
| `openpyxl` | Export รายงานเป็น Excel (.xlsx) |
| `reportlab` | Export รายงานเป็น PDF |
| `python-docx` | Export บันทึกการทำงานเป็น Word (.docx) |
| `matplotlib` | Dashboard charts (Donut, Bar, Line) |
| `python-dateutil` | จัดการวันที่และ timezone |

### 4.3 Development Tools

| Tool | การใช้งาน |
|------|---------|
| `venv` | Virtual Environment |
| `PyInstaller` | Build เป็น .exe |
| `pytest` | Unit test runner (199 tests) |
| `pytest-cov` | Code coverage report |

---

## 5. Architecture

```
D:\Task Management\
├── main.py                          # Desktop client entry point
├── server.py                        # FastAPI server entry point (port 8000)
│
├── server/                          # FastAPI server package
│   ├── main.py                      # FastAPI app + CORS + routers
│   ├── auth.py                      # JWT: create_token, verify_token
│   ├── deps.py                      # get_db(), get_current_user()
│   ├── serializers.py               # ORM → dict converters
│   └── routers/
│       ├── auth.py                  # POST /auth/login
│       ├── tasks.py                 # /api/tasks (CRUD + subtasks + comments)
│       ├── subtasks.py              # /api/subtasks
│       ├── teams.py                 # /api/teams + /api/members
│       ├── users.py                 # /api/users (admin ops)
│       ├── diary.py                 # /api/diary + export
│       ├── history.py               # /api/history
│       ├── dashboard.py             # /api/dashboard/stats
│       └── summary.py               # /api/summary + export excel
│
├── app/
│   ├── database.py                  # engine, SessionLocal, init_db()
│   ├── client/                      # HTTP client layer (desktop-side)
│   │   ├── __init__.py
│   │   ├── config.py                # SERVER_URL = "http://192.168.x.x:8000"
│   │   └── api_client.py            # APIClient — 50+ methods ครอบคลุมทุก endpoint
│   ├── models/
│   │   ├── task.py                  # Task, SubTask, TaskComment
│   │   ├── user.py                  # User (+ username, password_hash, is_admin)
│   │   ├── team.py                  # Team
│   │   ├── history.py               # HistoryLog
│   │   ├── diary.py                 # DiaryEntry
│   │   └── time_log.py              # TimeLog
│   ├── repositories/
│   │   ├── base.py
│   │   ├── task_repo.py
│   │   ├── user_repo.py
│   │   ├── team_repo.py
│   │   ├── diary_repo.py
│   │   └── time_log_repo.py
│   ├── services/
│   │   ├── task_service.py
│   │   ├── team_service.py
│   │   ├── diary_service.py
│   │   ├── time_tracking_service.py
│   │   └── auth_service.py          # PBKDF2 hash, login, JWT-ready
│   ├── views/
│   │   ├── main_layout.py           # Sidebar nav + APIClient per navigation
│   │   ├── login_view.py            # Split-panel login (Phase 19)
│   │   ├── dashboard_view.py        # 4 matplotlib charts
│   │   ├── task_view.py             # Task list + recycle bin
│   │   ├── team_view.py             # Team CRUD
│   │   ├── calendar_view.py         # Calendar
│   │   ├── summary_view.py          # Export Excel/PDF + time report
│   │   ├── diary_view.py            # Job diary + export Word/PDF
│   │   ├── history_view.py          # Activity log
│   │   ├── settings_view.py         # User management — admin only (Phase 19)
│   │   └── account_view.py          # Profile + เปลี่ยนรหัสผ่าน (Phase 19)
│   └── utils/
│       ├── theme.py                 # Color constants (Blue-White)
│       ├── exceptions.py            # Custom exception hierarchy
│       ├── logger.py                # Rotating file logger
│       ├── ui_helpers.py            # show_snack, confirm_dialog
│       ├── date_helpers.py          # Thai date utilities
│       └── shortcut_registry.py    # Keyboard shortcut registry
│
├── tests/                           # 199 tests — ทุกตัวผ่าน
│   ├── conftest.py
│   ├── test_task_service.py
│   ├── test_task_service_phase16.py
│   ├── test_team_service.py
│   ├── test_time_tracking_service.py
│   ├── test_task_repository.py
│   ├── test_time_log_repository.py
│   ├── test_dashboard_stats.py
│   ├── test_diary_service.py
│   ├── test_auth_service.py
│   ├── test_shortcut_registry.py
│   └── test_exceptions.py
│
└── data/
    ├── task_manager.db              # SQLite database (บน server)
    ├── charts/                      # PNG จาก matplotlib
    └── taskflow.log                 # Application log (rotating)
```

**Pattern:** Repository → Service → FastAPI Router → HTTP Client → Flet UI
**Data Flow:** `Views → APIClient → FastAPI → Services → Repositories → SQLite`

---

## 6. Database Schema

| ตาราง | คำอธิบาย |
|-------|---------|
| `users` | สมาชิกทีม, role, skills, username, password_hash, is_admin |
| `teams` | ข้อมูลทีม |
| `tasks` | งานหลัก พร้อม status, priority, deadline, soft-delete |
| `subtasks` | งานย่อย FK → tasks |
| `task_comments` | Comment/Note แบบ timeline |
| `work_history` | Action log ทุกการเปลี่ยนแปลง |
| `diary_entries` | บันทึกการทำงานรายวัน |
| `time_logs` | บันทึกเวลาทำงานต่องาน (started_at, ended_at, duration_minutes) |

---

## 7. Installation & Running

### Server (รันบนเครื่องที่เปิดทิ้งไว้)
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python server.py          # FastAPI on 0.0.0.0:8000
```

### Client (รันทุกเครื่องในทีม)
```bash
# 1. แก้ IP ใน app/client/config.py
SERVER_URL = "http://192.168.x.x:8000"   # ← ipconfig บนเครื่อง server

# 2. รันแอป
python main.py
```

### ตรวจสอบการเชื่อมต่อ
เปิด browser → `http://192.168.x.x:8000/docs` → เห็น Swagger UI = ✅

### รัน Tests
```bash
pytest tests/ -v                    # ทั้งหมด (199 tests)
pytest tests/ --cov=app             # พร้อม coverage
```

---

## 8. Development Roadmap

| Phase | สิ่งที่ทำ | สถานะ |
|-------|---------|-------|
| **Phase 1** | Core setup: DB, Models, Repositories | ✅ Done |
| **Phase 2** | Team Management UI | ✅ Done |
| **Phase 3** | Task Creation & Assignment UI | ✅ Done |
| **Phase 4** | Calendar View | ✅ Done |
| **Phase 5** | Summary & Export | ✅ Done |
| **Phase 6** | History & Search | ✅ Done |
| **Phase 7** | Bug Fix & QA + Task Dependencies | ✅ Done |
| **Phase 8** | Build & Package (.exe) | ✅ Done |
| **Phase 9** | Environment Recovery & UI Color Fix | ✅ Done |
| **Phase 10** | Blue-White Theme | ✅ Done |
| **Phase 11** | JobDiary Integration + Export PDF/Word | ✅ Done |
| **Phase 12** | Code Quality & Architecture Hardening | ✅ Done |
| **Phase 13** | Dashboard Charts + Time Tracking | ✅ Done |
| **Phase 14** | Architecture Review (Session, UTC, SQL COUNT, 103 tests) | ✅ Done |
| **Phase 15** | Dashboard Cache + Parallel Chart Rendering | ✅ Done |
| **Phase 16** | Repository & Service Hardening (199 tests) | ✅ Done |
| **Phase 17** | Global Search + Keyboard Shortcuts | ✅ Done |
| **Phase 19** | Login System (PBKDF2, Admin UI, Account Page) | ✅ Done |
| **Phase 21** | Online Desktop App (FastAPI + HTTP Client, LAN multi-user) | ✅ Done |
