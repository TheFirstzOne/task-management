# Task Manager Desktop App — Requirements & Tech Stack

> **Project:** Team Task Management Desktop Application  
> **Platform:** Windows Desktop (Python Flet)  
> **Version:** 1.0.0  
> **Last Updated:** February 2026

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
| **UI Theme** | Dark Mode ตลอดเวลา |
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

### 4.3 Development Tools

| Tool | การใช้งาน |
|---|---|
| `venv` | Virtual Environment แยก dependencies |
| `PyInstaller` | Build เป็น .exe สำหรับ Windows |

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
│   │   └── history.py
│   ├── repositories/        # Database CRUD operations
│   │   ├── user_repo.py
│   │   ├── team_repo.py
│   │   └── task_repo.py
│   ├── services/            # Business logic
│   │   ├── team_service.py
│   │   └── task_service.py
│   ├── views/               # Flet UI components
│   │   ├── main_layout.py
│   │   ├── team_view.py
│   │   ├── task_view.py
│   │   ├── calendar_view.py
│   │   ├── summary_view.py
│   │   └── history_view.py
│   └── utils/               # Helpers, exporters
├── assets/
├── data/                    # SQLite file
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
| **Phase 7** | Bug Fix & QA Testing | 🔄 In Progress |
| **Phase 8** | Build & Package (.exe) | 🔲 TODO |
