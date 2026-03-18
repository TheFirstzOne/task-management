# Task Manager Desktop App — Requirements & Tech Stack

> **Project:** Team Task Management Desktop Application  
> **Platform:** Windows Desktop (Python Flet)  
> **Version:** 1.0.0  
> **Last Updated:** March 2026

---

## 1. Project Overview

Desktop application สำหรับจัดการงานและมอบหมายงานในทีม เน้นความเรียบง่าย ใช้งานได้ offline และรองรับทีมขนาดเล็กถึงกลาง

---

## 2. Functional Requirements

### 2.1 ระบบสร้างทีมงาน
- สร้าง แก้ไข ลบทีม
- เพิ่ม/ลบสมาชิกในทีม
- กำหนด Role และ Skill ของแต่ละคน เช่น Technician, Engineer, CNC, PLC, Hydraulic
- แสดง Workload ของแต่ละคนในทีม เพื่อป้องกันงานกองเกิน
- เปิด/ปิดสถานะ Active ของสมาชิก

### 2.2 ระบบแจกจ่ายงาน
#### 2.2.1 สร้างงาน
- กำหนด Title, Description, Priority (Low / Medium / High / Urgent)
- กำหนด Start Date และ Due Date
- แนบ Checklist ย่อย (Sub-tasks) ภายในงาน
- ระบุ Tag หรือหมวดหมู่งาน
- Visual indicator เมื่องานใกล้หรือเกิน Deadline

#### 2.2.2 มอบหมายงาน
- มอบหมายงานให้สมาชิกในทีม
- Task Status Flow: `Pending → In Progress → Review → Done / Cancelled`
- รองรับ Task Dependencies (ระบุว่างานไหนต้องทำก่อน)
- บันทึก Comment / Note ต่องานแบบ Timeline

### 2.3 ปฏิทินแผนงาน
- แสดงงานและการมอบหมายในรูปแบบ Calendar View
- Filter ตาม ทีม, สมาชิก, สถานะ, Priority
- แสดง Deadline และช่วงเวลาของงานแต่ละชิ้น

### 2.4 สรุปงาน (Text-based)
- สรุปงานทั้งหมดในรูปแบบ Text
- กรองสรุปตามทีม, สมาชิก, ช่วงวันที่, สถานะ
- Export รายงานเป็น PDF และ Excel
- Dashboard ตัวเลขภาพรวม: งานเสร็จ / ค้าง / เกินกำหนด

### 2.5 ประวัติการทำงาน
- บันทึก Action Log ทุกการเปลี่ยนแปลงของงาน เช่น สร้าง, มอบหมาย, เปลี่ยน Status, Comment
- ดูประวัติย้อนหลังรายงานแต่ละชิ้น
- ค้นหาและ Filter ประวัติด้วยวันที่ หรือสมาชิก

---

## 3. Non-Functional Requirements

| หัวข้อ | รายละเอียด |
|---|---|
| **Platform** | Windows Desktop (standalone .exe) |
| **UI Theme** | Blue-White (ฟ้า-ขาว) ถาวร |
| **Database** | Local SQLite (offline-first, ไม่ต้องการ server) |
| **Performance** | เปิดแอปได้ภายใน 3 วินาที |
| **Usability** | ใช้งานได้โดยไม่ต้องเชื่อมต่อ internet |
| **Packaging** | Build เป็น .exe เพื่อแจกจ่ายในทีม |

---

## 4. Tech Stack

### 4.1 Core

| Layer | Technology | หมายเหตุ |
|---|---|---|
| **UI Framework** | `Flet >= 0.21.0` | Python-based, Material Design, Cross-platform |
| **Language** | `Python 3.10+` | |
| **Database** | `SQLite` | Built-in กับ Python ไม่ต้องติดตั้งแยก |
| **ORM** | `SQLAlchemy >= 2.0.0` | จัดการ database query แบบ Pythonic |
| **DB Migration** | `Alembic >= 1.13.0` | จัดการ schema changes เมื่อ model เปลี่ยน |

### 4.2 Utilities

| Package | Version | การใช้งาน |
|---|---|---|
| `python-dateutil` | >= 2.9.0 | จัดการวันที่และ timezone ซับซ้อน |
| `openpyxl` | >= 3.1.0 | Export รายงานเป็น Excel (.xlsx) |
| `reportlab` | >= 4.0.0 | Export รายงานเป็น PDF |
| `python-docx` | >= 1.1.0 | Export บันทึกการทำงานเป็น Word (.docx) |
| `matplotlib` | >= 3.7.0 | Dashboard charts (Donut, Bar, Line) |

### 4.3 Development Tools

| Tool | การใช้งาน |
|---|---|
| `venv` | Virtual Environment แยก dependencies |
| `PyInstaller` | Build เป็น .exe สำหรับ Windows |
| `pytest >= 9.0.0` | Unit test runner |
| `pytest-cov >= 7.0.0` | Code coverage report |

---

## 5. Architecture

```
task_manager/
├── main.py                  # Entry point
├── app/
│   ├── database.py          # DB connection & session
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py
│   │   ├── team.py
│   │   ├── task.py
│   │   ├── history.py
│   │   ├── diary.py         # Phase 11: บันทึกการทำงานรายวัน
│   │   └── time_log.py      # Phase 13: Time Tracking
│   ├── repositories/        # Database CRUD operations
│   │   ├── user_repo.py
│   │   ├── team_repo.py
│   │   ├── task_repo.py
│   │   └── diary_repo.py    # Phase 11
│   ├── services/            # Business logic
│   │   ├── team_service.py
│   │   ├── task_service.py
│   │   ├── diary_service.py # Phase 11
│   │   └── time_tracking_service.py  # Phase 13: Timer + Manual log
│   ├── views/               # Flet UI components
│   │   ├── main_layout.py
│   │   ├── dashboard_view.py # Phase 13: Charts + Stat cards
│   │   ├── team_view.py
│   │   ├── task_view.py
│   │   ├── calendar_view.py
│   │   ├── diary_view.py    # Phase 11: บันทึกการทำงานรายวัน
│   │   ├── summary_view.py
│   │   └── history_view.py
│   └── utils/               # Helpers, exporters
│       ├── theme.py
│       ├── date_helpers.py
│       ├── logger.py        # Phase 12: Centralized logging
│       ├── exceptions.py    # Phase 12: Custom exception hierarchy
│       └── ui_helpers.py    # Phase 12: show_snack, confirm_dialog, show_loading
├── tests/                   # Phase 12: Unit test suite (27 tests)
│   ├── conftest.py
│   ├── test_task_service.py
│   ├── test_diary_service.py
│   └── test_exceptions.py
├── assets/
├── data/                    # SQLite file + Word export + taskflow.log
└── requirements.txt
```

**Pattern:** Repository Pattern + Service Layer  
**Data Flow:** `Views → Services → Repositories → SQLite`

---

## 6. Database Schema (ภาพรวม)

```
users ──────┐
            ├──► tasks ──► task_comments
teams ──────┘         └──► work_history
```

| Table | คำอธิบาย |
|---|---|
| `users` | ข้อมูลสมาชิกทีม, role, skills |
| `teams` | ข้อมูลทีม |
| `tasks` | งานหลัก พร้อม status, priority, deadline |
| `task_comments` | Comment/Note ต่องานแบบ timeline |
| `work_history` | Action log ทุกการเปลี่ยนแปลง |
| `diary_entries` | บันทึกการทำงานรายวัน (Phase 11) |
| `time_logs` | บันทึกเวลาทำงานต่องาน (Phase 13) |

---

## 7. Installation

```bash
# 1. สร้าง Virtual Environment
python -m venv venv
venv\Scripts\activate

# 2. ติดตั้ง dependencies
pip install -r requirements.txt

# 3. รันแอป
python main.py

# 4. Build เป็น .exe (เมื่อพร้อม deploy)
flet pack main.py --name "Task Manager"
```

---

## 8. Development Roadmap

| Phase | สิ่งที่ทำ | สถานะ |
|---|---|---|
| **Phase 1** | Core setup: DB, Models, Repositories | ✅ Done |
| **Phase 2** | Team Management UI | ✅ Done |
| **Phase 3** | Task Creation & Assignment UI | ✅ Done |
| **Phase 4** | Calendar View | ✅ Done |
| **Phase 5** | Summary & Export | ✅ Done |
| **Phase 6** | History & Search | ✅ Done |
| **Phase 7** | Bug Fix & QA Testing + Task Dependencies | ✅ Done |
| **Phase 8** | Build & Package (.exe) | ✅ Done |
| **Phase 9** | Environment Recovery & UI Color Fix | ✅ Done |
| **Phase 10** | Blue-White Theme | ✅ Done |
| **Phase 11** | JobDiary Integration + Export PDF/Excel Blue-White Theme + Thai Font Fix | ✅ Done |
| **Phase 12** | Code Quality & Architecture Hardening + UX Polish + Diary PDF Export | ✅ Done |
| **Phase 13** | UX/UI Professional Polish + Dashboard Charts + Time Tracking | ✅ Done |
| **Phase 14** | Architecture Review & Code Quality (Session mgmt, Validation, UTC fix, SQL COUNT, Tests 103) | ✅ Done |
| **Phase 15** | เลือกไฟล์ Database จากไดร์ฟกลาง (Shared SQLite + WAL + retry) | 🔜 Planned |
| **Phase 16** | ระบบล็อกอิน (Admin สร้างบัญชี / Member login) | 🔜 Planned |
| **Phase 17** | พิจารณา Web App Migration (Flet Web / FastAPI + React) | 🔜 Planned |

---

## Phase 13 — UX/UI Professional Polish + Dashboard Charts + Time Tracking (Planned)

### Part A — UX/UI Polish (ทำก่อน)

| # | รายการ | ความยาก | ไฟล์ที่เกี่ยวข้อง |
|---|--------|---------|-----------------|
| A1 | **Priority color border** บนซ้าย task card (Urgent=แดง, High=ส้ม, Medium=เหลือง, Low=เขียว) | ⭐ | `task_view.py` |
| A2 | **Hover แสดง action buttons** (Edit/Delete ซ่อน แสดงเมื่อ hover บนการ์ด) | ⭐⭐ | `task_view.py` |
| A3 | **Done/Cancelled visual** (opacity ลด + title strikethrough) | ⭐ | `task_view.py` |
| A4 | **ปุ่ม "ล้างตัวกรอง"** (แสดงเมื่อ filter ≠ ทั้งหมด ทุกตัว) | ⭐ | `task_view.py` |
| A5 | **Empty state เมื่อ filter ไม่พบผล** ("ไม่พบงานที่ตรงกับเงื่อนไข" + ปุ่ม clear) | ⭐ | `task_view.py` |
| A6 | **Form dialog grouping** (แบ่ง 2 section: ข้อมูลหลัก / รายละเอียดเพิ่มเติม) | ⭐⭐ | `task_view.py` |

### Part B — Dashboard Charts (#7)

| # | รายการ | รายละเอียด |
|---|--------|----------|
| B1 | **Status Donut Chart** | งานแยกตามสถานะ (Pie/Donut) — ใช้ `flet_contrib` หรือ `matplotlib` render เป็น image |
| B2 | **Priority Bar Chart** | งานแยกตาม Priority (Horizontal bar) |
| B3 | **Weekly Trend Line** | งานที่สร้าง vs เสร็จรายสัปดาห์ (Line chart) |
| B4 | **Team Workload Chart** | งานต่อทีม/สมาชิก (Stacked bar) |
| เทคโนโลยี | **matplotlib → PNG → ft.Image** | render chart เป็น BytesIO buffer แสดงใน `ft.Image` — ไม่ต้องติดตั้ง lib เพิ่ม |

### Part C — Time Tracking (#13)

| # | รายการ | รายละเอียด |
|---|--------|----------|
| C1 | **Model** | เพิ่มตาราง `time_logs` (id, task_id, user_id, started_at, ended_at, duration_minutes, note) |
| C2 | **Service** | `TimeTrackingService`: start/stop timer, manual log, get_logs_by_task, get_summary_by_member |
| C3 | **UI บน Task Detail Panel** | Timer button (▶ Start / ⏹ Stop) + รายการ time logs ของงานนั้น |
| C4 | **รายงาน Time** | ตารางสรุปเวลา/งาน/สมาชิก ในหน้า Summary (แยก tab หรือ section) |
| C5 | **Export** | เพิ่ม time log ใน Excel/PDF ของ summary export |
