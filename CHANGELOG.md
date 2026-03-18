# Changelog — Task Manager Desktop App

> ประวัติการพัฒนาและแก้ไขโปรเจกต์

---

## Phase 16 — Architecture Hardening + Features ✅

### Critical Architecture Fixes
- **C1/C2** `task_view.py` — ลบการเรียก `task_svc.task_repo.*` โดยตรงจาก View; เพิ่ม `get_task_or_none()` + `get_comments()` ใน `TaskService`
- **C3** `task_view.py:1312` — ย้าย raw ORM query ออกจาก View → `TaskRepository.get_deleted()` + `TaskService.get_deleted_tasks()`
- **C4** `task_service.py` — `restore_task()` ใช้ `TaskRepository.restore()` แทน raw query
- **C5** `team_service.py` — inject `TaskRepository`; แทน raw queries ด้วย `unassign_user()` + `count_active_by_assignee()`
- **C6** สร้าง `app/repositories/time_log_repo.py` — แยก DB logic ออกจาก `TimeTrackingService` ทั้งหมด

### Warnings Fixed
- `task_service.py:176` — Guard `None` ก่อนเรียก `.title` ป้องกัน `AttributeError`
- `exceptions.py` — เปลี่ยน param `id` → `entity_id` (ไม่ shadow built-in)
- `ui_helpers.py` — `show_snack` log warning แทน silent `pass`
- `team_service.py` — แก้ `if team_id:` → `if team_id is not None:` (ป้องกัน bug กับ id=0)

### Refactors
- `task_view.py` — `_dd_int()` helper ลด duplicate dropdown parse 3 จุด
- `task_view.py` — `_rebuild_filters` 4 try/except → `for ctrl in [...]: safe_update(ctrl)`
- `task_view.py` — inline `try: page.update()` 8 จุด → `safe_page_update(page)`
- `task_view.py` — date picker try/except → `safe_update()`
- `dashboard_view.py` — `STATUS_COLORS`/`PRIO_COLORS` ใช้ `status_color()`/`priority_color()` จาก `theme.py` (ซิงค์สีอัตโนมัติ)

### Features
- **Near-due Notification Panel** — banner สีส้มใน task view แสดงงานที่ครบกำหนดใน 3 วัน (dismiss ได้)
- **Near-due Badge** — badge สีส้มใน sidebar ข้างๆ badge overdue สีแดง
- **Keyboard Shortcuts** — `shortcut_registry.py`; `Ctrl+N` สร้างงาน, `Esc` ปิด dialog, `Enter` submit, `Ctrl+F` focus search

### Tests
- เพิ่ม `tests/test_task_service_phase16.py` — 36 tests ครอบคลุมทุก method ใหม่
- แก้ `tests/test_exceptions.py` — ปรับให้ตรงกับ `entity_id` rename
- **Total: 139/139 tests passed**

---

## Phase 1 — Core Setup ✅

- สร้างโครงสร้างโปรเจกต์ตาม Architecture (Repository Pattern + Service Layer)
- ตั้งค่า SQLite database + SQLAlchemy ORM (`app/database.py`)
- สร้าง Models: `User`, `Team`, `Task`, `SubTask`, `TaskComment`, `WorkHistory`
- สร้าง Repositories: `user_repo.py`, `team_repo.py`, `task_repo.py`
- สร้าง Services: `team_service.py`, `task_service.py`
- สร้าง Utilities: `date_helpers.py`, `theme.py`

---

## Phase 2 — Team Management UI ✅

- หน้าจัดการทีม (`team_view.py`)
- สร้าง / แก้ไข / ลบทีม
- เพิ่ม / แก้ไข / ลบสมาชิกในทีม
- กำหนด Role และ Skills ของสมาชิก
- Workload bar แสดงปริมาณงานของแต่ละคน
- เปิด/ปิดสถานะ Active ของสมาชิก
- Team cards แบบ expand/collapse

---

## Phase 3 — Task Creation & Assignment UI ✅

- หน้าจัดการงาน (`task_view.py`)
- สร้าง / แก้ไข / ลบงาน
- กำหนด Title, Description, Priority, Tags, Start Date, Due Date
- มอบหมายงานให้สมาชิก
- Filter bar: สถานะ / Priority / ค้นหา
- Task detail side-panel: subtasks + comment timeline
- Status chip เปลี่ยนสถานะ (Pending → In Progress → Review → Done / Cancelled)
- Deadline indicator: เกินกำหนด / ใกล้กำหนด

---

## Phase 4 — Calendar View ✅

- ปฏิทินแผนงาน (`calendar_view.py`)
- Monthly calendar grid + navigate เดือนก่อน/ถัดไป
- Task dots แสดงสีตาม Priority
- คลิกวันเพื่อดูรายการงาน (day detail panel)
- Filter bar: ทีม / สมาชิก / สถานะ / Priority
- วันนี้ highlight + overdue cells สีแดง

---

## Phase 5 — Summary & Export ✅

- หน้าสรุปงาน (`summary_view.py`)
- Overview stat cards (total / done / in-progress / overdue / cancelled)
- Status breakdown bar + Priority breakdown bar
- ตาราง per-team และ per-member
- Filter: ช่วงวันที่ + ทีม
- Export to Excel (openpyxl) + Export to PDF (reportlab)

---

## Phase 6 — History & Search ✅

- ประวัติการทำงาน (`history_view.py`)
- Timeline ของ WorkHistory entries
- ค้นหาด้วยชื่องาน / รายละเอียด
- Filter: ประเภท action / ผู้ดำเนินการ / ช่วงวันที่
- Color-coded action badges
- Pagination (50 entries per page)

---

## Phase 7 — Bug Fix & QA Testing 🔄 (20 ก.พ. 2569)

### Session: 20 กุมภาพันธ์ 2569

#### Bug Fix #1 — `ft.dropdown.Option` syntax error (5 จุด)
- **ปัญหา:** `str(t.id, text=t.name)` — วงเล็บผิดตำแหน่ง ทำให้ `text=` ถูกส่งเป็น argument ของ `str()` แทน `Option()`
- **ไฟล์ที่แก้:**
  - `calendar_view.py` — 3 จุด (team options, member options)
  - `history_view.py` — 1 จุด (actor options)
  - `summary_view.py` — 1 จุด (team options)
- **แก้ไข:** `ft.dropdown.Option(key=str(t.id), text=t.name)`

#### Bug Fix #2 — `DropdownOption.__init__() got multiple values for 'key'`
- **ปัญหา:** `ft.dropdown.Option(_action_label(a), key=a)` — positional arg แรกถูกตีว่าเป็น `key` ชนกับ `key=a`
- **ไฟล์:** `history_view.py` บรรทัด 382
- **แก้ไข:** `ft.dropdown.Option(key=a, text=_action_label(a))`

#### Bug Fix #3 — History filter `on_select` reverse lookup crash
- **ปัญหา:** `on_select` handler พยายาม reverse-lookup `e.control.value` จาก `text` list แต่ Flet 0.80 ส่ง `key` มา ไม่ใช่ `text` ทำให้ `ValueError: 'commented' is not in list`
- **ไฟล์:** `history_view.py` บรรทัด 409-413
- **แก้ไข:** ลบ complex lookup, ใช้ `e.control.value` ตรงๆ (เพราะมันคือ key อยู่แล้ว)

#### Bug Fix #4 — Filter ทีม/สมาชิก ใช้ `o.text ==` แทน key
- **ปัญหา:** Filter ใน `_get_filtered_tasks()` พยายาม match ด้วย `o.text == value` แต่ Flet dropdown ส่ง key มา ไม่ใช่ text ทำให้ filter ทีมและสมาชิกไม่ทำงาน
- **ไฟล์ที่แก้:**
  - `calendar_view.py` — team + member filter
  - `summary_view.py` — team filter
  - `history_view.py` — actor filter
- **แก้ไข:** ใช้ `int(value)` ตรงๆ เพราะ value = key ของ dropdown option

#### Bug Fix #5 — สร้างงานไม่มี Dropdown ทีม → `team_id = None`
- **ปัญหา:** ฟอร์มสร้างงาน (`task_view.py`) ไม่มี Dropdown เลือกทีม ทำให้งานทุกชิ้นที่สร้างมี `team_id = None` → filter ทีมในปฏิทินและสรุปงานไม่เจองาน
- **ไฟล์:** `task_view.py`
- **แก้ไข:**
  - เพิ่ม `dd_team_dlg` (Dropdown ทีม) ในฟอร์มสร้าง/แก้ไขงาน
  - เลือกทีม → filter สมาชิกใน Dropdown assignee ตามทีมนั้น
  - ส่ง `team_id` ไปใน `create_task()` และ `update_task()`
  - Calendar + Summary filter fallback: ดู `assignee.team_id` ด้วยถ้า `task.team_id` ไม่ตรง

---

## Phase 8 — UI Fix, Build & Deploy ✅ (23 ก.พ. 2569 / แก้ไขเพิ่มเติม 26 ก.พ. 2569)

### Session: 23 กุมภาพันธ์ 2569

#### UI Fix #1 — Calendar: Day cell แยกออกจากกันเมื่อขยายหน้าต่าง
- **ปัญหา:** Week row แต่ละแถวมี `expand=True` ใน `ft.Column` ทำให้ Flutter แบ่งพื้นที่แนวตั้งให้เท่าๆ กัน เมื่อหน้าต่างสูงขึ้น แถวยืดออก cell ที่มี `height=80` คงที่จึงแยกห่างจากกัน
- **ไฟล์:** `calendar_view.py`
- **แก้ไข:**
  - ลบ `height=80` ออกจาก day cell ทั้งหมด (ทั้ง empty cell และ normal cell)
  - คง `expand=True` ไว้บน week row เพื่อให้แบ่งพื้นที่แนวตั้งเท่าๆ กัน
  - cell จะยืดความสูงตาม row อัตโนมัติ ปฏิทินจึง fill พื้นที่ทั้งหมดและ responsive ตามขนาดหน้าต่าง

#### Build — สร้าง Standalone Executable (.exe)
- ใช้ `flet pack` (PyInstaller wrapper สำหรับ Flet) แทน PyInstaller ตรงๆ เพื่อให้รวม Flet runtime ได้ถูกต้อง
- คำสั่งที่ใช้:
  ```
  flet pack main.py --name TaskFlow --icon assets/icon.ico
    --add-data "assets;assets"
    --hidden-import sqlalchemy
    --hidden-import sqlalchemy.dialects.sqlite
    --hidden-import openpyxl
    --hidden-import reportlab
  ```
- **ผลลัพธ์:** `dist/TaskFlow.exe` ขนาด ~90 MB
- รันได้บนเครื่องที่ไม่ได้ติดตั้ง Python

#### Deploy — อัปโหลดโปรเจคขึ้น GitHub
- ตั้งค่า Git identity (`user.name`, `user.email`)
- สร้าง `.gitignore` ครอบคลุม Python, venv, build, dist, .exe, .db, .claude
- `git init` → `git add` → Initial commit (29 files)
- สร้าง public repository: `https://github.com/TheFirstzOne/task-management`
- `git remote add origin` + `git push -u origin main`

#### Documentation — เพิ่มคู่มือ GitHub
- สร้างไฟล์ `GITHUB_GUIDE.md` อธิบายขั้นตอนการ push โปรเจคขึ้น GitHub ตั้งแต่ต้นจนจบ ครอบคลุม 10 หัวข้อ

---

### Session: 26 กุมภาพันธ์ 2569

#### Bug Fix #6 — ข้อมูลหายทุกครั้งที่ปิดโปรแกรม (SQLite path ชี้ไป temp folder)
- **ปัญหา:** `database.py` ใช้ `os.path.abspath(__file__)` เพื่อหา `BASE_DIR` — เมื่อรันแบบ `.exe` (PyInstaller frozen) `__file__` จะชี้ไปที่ temp folder `_MEIxxxxx` ที่ PyInstaller แตกไฟล์ชั่วคราว ทุกครั้งที่รัน `.exe` จะได้ temp folder ใหม่ที่มีเลขต่างกัน ทำให้ SQLite database ถูกสร้างใหม่เปล่าๆ เสมอ และข้อมูลเก่าสูญหาย
- **ไฟล์:** `app/database.py`
- **แก้ไข:** เพิ่มการตรวจสอบ `sys.frozen` เพื่อแยก path logic ระหว่าง 2 โหมด
  ```python
  if getattr(sys, 'frozen', False):
      BASE_DIR = os.path.dirname(sys.executable)  # ตำแหน่งของ .exe จริงๆ
  else:
      BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # dev mode
  ```
- **ผลลัพธ์:** `data/task_manager.db` ถูกสร้างข้างๆ `.exe` และคงอยู่ข้ามการรัน

#### Bug Fix #7 — `No module named 'sqlalchemy'` เมื่อรัน .exe บนเครื่องอื่น
- **ปัญหา:** `flet pack` ครั้งก่อนใช้ System Python ซึ่งไม่มี SQLAlchemy ติดตั้งอยู่ (library ทั้งหมดอยู่ใน venv) PyInstaller จึง bundle โค้ดจาก System Python ที่ไม่มี dependency — `.exe` รันได้บนเครื่อง dev แต่ล้มเหลวบนเครื่องอื่น
- **ไฟล์:** build command
- **แก้ไข:** เปลี่ยนไปใช้ `venv\Scripts\flet.exe` แทน `flet` เพื่อให้ PyInstaller ใช้ venv Python ที่มี dependencies ครบ
  ```
  venv\Scripts\flet.exe pack main.py --name TaskFlow --icon assets/icon.ico
    --add-data "assets;assets"
    --hidden-import sqlalchemy
    --hidden-import sqlalchemy.dialects.sqlite
    --hidden-import openpyxl
    --hidden-import reportlab
  ```
- **ผลลัพธ์:** `dist/TaskFlow.exe` ขนาด ~90 MB bundle SQLAlchemy และ dependencies ครบถ้วน
- **หมายเหตุ:** สำหรับการ build ครั้งต่อไปให้ใช้ `venv\Scripts\flet.exe pack ...` เสมอ

---

## Phase 9 — Environment Recovery & UI Color Fix ✅ (5 มี.ค. 2569)

### Session: 5 มีนาคม 2569

#### Environment Fix — venv เสียเพราะ Python 3.11 ถูกถอนออก
- **ปัญหา:** `venv/` ถูกสร้างด้วย Python 3.11 ที่ถูกถอนออกจากระบบ ทำให้ `venv\Scripts\python.exe` และ `venv\Scripts\flet.exe` เปิดไม่ได้เลย โปรแกรมรันไม่ขึ้น
  ```
  Error: No Python at
  'C:\Users\Firstz\AppData\Local\Programs\Python\Python311\python.exe'
  ```
- **ไฟล์:** `venv/` (ทั้งโฟลเดอร์)
- **แก้ไข:** สร้าง venv ใหม่ด้วย System Python 3.10.11 ที่ยังมีอยู่
  ```bash
  rm -rf "D:/Task Management/venv"
  python -m venv "D:/Task Management/venv"
  "D:/Task Management/venv/Scripts/python.exe" -m pip install -r requirements.txt
  ```
- **ผลลัพธ์:** venv ใหม่พร้อมใช้งาน, ติดตั้ง dependencies ครบ (flet 0.82.0, SQLAlchemy 2.0.48, alembic 1.18.4, openpyxl 3.1.5, reportlab 4.4.10)

---

#### UI Fix #2 — Team member list: สีแสดงผลผิด เนื่องจาก Hex Alpha Format Bug

- **ปัญหา:** โค้ดใช้ `ACCENT + "44"` และ `ACCENT + "33"` เพื่อต้องการสี ACCENT แบบโปร่งใส แต่ Flet/Flutter ตีความ hex 8 หลักในรูปแบบ `#AARRGGBB` (alpha นำหน้า) ไม่ใช่ `#RRGGBBAA`
  - `"#6C63FF44"` → Flutter อ่านเป็น `alpha=0x6C, R=0x63, G=0xFF, B=0x44` = **สีเขียวสด** ❌
  - ควรได้ = purple โปร่งใส แต่กลับได้สีเขียวที่ไม่ตัดกับพื้นหลัง dark
- **ไฟล์:** `app/views/team_view.py`
- **แก้ไข 4 จุด:**

  | ส่วน | เดิม (ผิด) | ใหม่ |
  |---|---|---|
  | Avatar circle bgcolor | `ACCENT + "44"` → สีเขียว bug | `ACCENT` (solid `#6C63FF`) |
  | Avatar circle text color | `ACCENT` (purple จาง) | `"#FFFFFF"` (ขาว — contrast สูง) |
  | Role badge bgcolor | `ACCENT + "33"` → สีเขียว bug | `"#2A2870"` (dark purple solid) |
  | Role badge text color | `ACCENT` (จาง) | `"#B8B5FF"` (light purple — อ่านง่าย) |
  | Active toggle icon | `COLOR_DONE` (green `#4CAF50`) | `ACCENT2` (cyan `#00D4FF`) |
  | Workload bar (low ≤2) | `COLOR_DONE` (green `#4CAF50`) | `"#00D4FF"` (cyan — ตัดกับ dark bg ชัด) |

- **เพิ่ม import:** `ACCENT2` เข้า import list ของ `team_view.py`

---

## Phase 10 — Blue-White Theme + Task Dependencies ✅ (8 มี.ค. 2569)

### Session: 8 มีนาคม 2569

#### Feature — Task Dependencies (งานที่ต้องทำก่อน)
- **Model:** เพิ่ม `depends_on_id` (FK → tasks.id) ใน `Task` model
- **Repository:** เพิ่ม `get_dependent_tasks()`, `get_dependency_chain()` ใน `task_repo.py`
- **Service:** เพิ่ม `_validate_dependency()` ป้องกัน circular dependency, `check_dependency_warning()`, `get_dependent_tasks()` ใน `task_service.py`
- **UI (task_view.py):**
  - เพิ่ม Dropdown "ต้องทำก่อน" ในฟอร์มสร้าง/แก้ไขงาน
  - Detail panel แสดงงานที่ต้องทำก่อน + Warning ถ้ายังไม่เสร็จ
  - แสดงรายการงานที่รอ task นี้ (reverse lookup)
  - SnackBar เตือนเมื่อเปลี่ยนสถานะแต่ dependency ยังไม่เสร็จ

#### Theme — เปลี่ยนจาก Dark Mode เป็น Blue-White ถาวร
- **`theme.py`** — เขียนใหม่ทั้งหมด:
  - ลบ `DARK_PALETTE`, `LIGHT_PALETTE`, `apply_theme()`, `is_dark()`
  - กำหนดสี Blue-White ถาวร:

  | ตัวแปร | ค่า | คำอธิบาย |
  |---|---|---|
  | `BG_DARK` | `#F0F4F8` | พื้นหลังหลัก (grey-blue อ่อน) |
  | `BG_SIDEBAR` | `#FFFFFF` | Sidebar (ขาว) |
  | `BG_CARD` | `#FFFFFF` | Card (ขาว) |
  | `BG_INPUT` | `#E8EDF2` | Input field |
  | `ACCENT` | `#2563EB` | สีหลัก (น้ำเงิน) |
  | `ACCENT2` | `#0EA5E9` | สีรอง (ฟ้า) |
  | `TEXT_PRI` | `#1E293B` | ตัวหนังสือหลัก (เข้ม) |
  | `TEXT_SEC` | `#64748B` | ตัวหนังสือรอง |
  | `BORDER` | `#CBD5E1` | เส้นขอบ |

- **`main.py`** — เปลี่ยน `page.theme_mode = ft.ThemeMode.LIGHT` ถาวร
- **`main_layout.py`** — ลบโค้ด theme toggle (AlertDialog, Switch, importlib.reload) ออกทั้งหมด, เก็บปุ่ม "ตั้งค่า" ไว้เป็น dummy สำหรับอนาคต

#### UI Fix — แก้ hardcoded dark colors ให้เข้ากับ Blue-White theme
- **`task_view.py`** (3 จุด) — `bgcolor="#1A1D26"` → `bgcolor=BG_INPUT`
  - Dependency section (ต้องทำก่อน, งานที่รอ)
  - Comment bubble
- **`calendar_view.py`** (1 จุด) — `bgcolor="#1A1D26"` → `bgcolor=BG_INPUT` (task card)
- **`team_view.py`** (2 จุด):
  - `bgcolor="#1A1D26"` → `bgcolor=BG_INPUT` (member row)
  - `bgcolor="#2A2870"` → `bgcolor=ACCENT+"22"` + `color=ACCENT` (role chip)
- **ปุ่มบน ACCENT background** — เปลี่ยน `color=TEXT_PRI` → `color="#FFFFFF"` (5 จุดใน task_view + team_view)

#### Build Fix
- อัปเดต `setuptools` 65.5.0 → 82.0.0 แก้ `PyiFrozenImporter` error
- ใช้ `./venv/Scripts/python.exe -m PyInstaller` แทน system Python เพื่อให้ bundle dependencies ครบ
- **ผลลัพธ์:** `TaskFlow.exe` ขนาด 62 MB

---

---

## Phase 11 — JobDiary Integration + Export Theme Fix ✅ (15 มี.ค. 2569)

### Session: 15 มีนาคม 2569

#### Feature — บันทึกการทำงานรายวัน (JobDiary)
- รวมโปรเจค `JobdiaryRecord` เข้าเป็น feature ใหม่ใน TaskFlow
- **Model:** `app/models/diary.py` — ตาราง `diary_entries` (id, content, created_at, updated_at)
- **Repository:** `app/repositories/diary_repo.py` — CRUD + `get_grouped_by_date()`
- **Service:** `app/services/diary_service.py` — Business logic + `export_to_word()`
- **View:** `app/views/diary_view.py`
  - Custom tab bar (ไม่ใช้ `ft.Tabs` เพราะ Flet 0.82 ไม่รองรับ `text=` parameter)
  - Tab 1: "บันทึกใหม่" — กรอกข้อความ + บันทึกลง SQLite + ปุ่ม Export Word
  - Tab 2: "อ่านย้อนหลัง" — แสดงรายการตามวันที่ (left panel) + เนื้อหา (right panel)
- **Navigation:** เพิ่ม nav item "บันทึกงาน" (`ft.Icons.BOOK_OUTLINED`) ใน sidebar
- **Dependency:** เพิ่ม `python-docx>=1.1.0` ใน `requirements.txt` + `TaskFlow.spec`
- **Word Export:** บันทึกบันทึกทั้งหมดเป็น `data/job_diary.docx` พร้อมเปิดไฟล์อัตโนมัติ

#### Export Fix — PDF และ Excel ธีมฟ้า-ขาว
- **PDF (`summary_view.py`):**
  - แก้ไข hardcoded dark colors ทั้งหมดให้ตรงกับ Blue-White theme
  - **Thai Font Fix:** Register font `Tahoma` (`C:\Windows\Fonts\tahoma.ttf`) กับ ReportLab — แก้ปัญหาภาษาไทยแสดงเป็น ■■■ ใน PDF
  - ใช้ `fontName` ใน ParagraphStyle และ `FONTNAME` command ใน TableStyle ทุกตาราง

  | ส่วน | เดิม (Dark) | ใหม่ (Blue-White) |
  |---|---|---|
  | Title | `#6C63FF` (ม่วง) | `#2563EB` (น้ำเงิน) |
  | Section header BG | `#1E2028` (ดำ) | `#2563EB` (น้ำเงิน) |
  | ข้อความปกติ | `#F0F2F5` (ขาว) | `#1E293B` (ดำเข้ม) |
  | Table header BG | `#1E2028` (ดำ) | `#2563EB` (น้ำเงิน) |
  | Table header text | `#6C63FF` (ม่วง) | `#FFFFFF` (ขาว) |
  | แถวข้อมูล | `#16181F`/`#1E2028` (ดำ) | `#FFFFFF`/`#F0F4F8` (ขาว) |
  | เส้นตาราง | `#2A2D3A` (เข้ม) | `#CBD5E1` (เทาอ่อน) |

- **Excel (`summary_view.py`):**
  - Header fill: `#1E2028` → `#2563EB` (น้ำเงิน)
  - Header font: `#6C63FF` (ม่วง) → `#FFFFFF` (ขาว)

#### Build Fix
- ลบ `version=` ที่ชี้ไป temp file ที่หายไปออกจาก `TaskFlow.spec`
- เพิ่ม `docx`, `lxml`, `lxml.etree` ใน `hiddenimports`
- **ผลลัพธ์:** `TaskFlow.exe` build สำเร็จ

---

---

## Phase 12 — Code Quality & Architecture Hardening ✅ (16 มี.ค. 2569)

### Session: 16 มีนาคม 2569

#### Architecture — Abstract Base Repository
- **ไฟล์:** `app/repositories/base.py` (ใหม่)
- สร้าง `BaseRepository(ABC, Generic[T])` กำหนด interface กลาง: `get_by_id`, `get_all`, `delete`
- Repositories ทุกตัว (`task_repo`, `team_repo`, `user_repo`, `diary_repo`) inherit ทำให้มั่นใจว่าครบ interface

#### Architecture — Custom Exception Hierarchy
- **ไฟล์:** `app/utils/exceptions.py` (ใหม่)
- `TaskFlowError` (base) → `NotFoundError`, `DuplicateNameError`, `CircularDependencyError`, `SelfDependencyError`, `ValidationError`
- แทนที่ bare `ValueError` ทั้งหมดใน `task_service.py` และ `team_service.py`
- Handler ใน views จับ typed exception แทน generic Exception

#### Feature — Centralized Logging
- **ไฟล์:** `app/utils/logger.py` (ใหม่)
- Rotating file handler: `data/taskflow.log` (1 MB × 3 ไฟล์), WARNING → console, DEBUG → file
- `get_logger(name)` สร้าง child logger ภายใต้ `taskflow.` namespace
- Views และ Services ทุกตัวใช้ `logger.error/warning/debug()` แทน `print()` และ bare `except: pass`

#### Feature — UI Helper Utilities
- **ไฟล์:** `app/utils/ui_helpers.py` (ใหม่)
- `show_snack(page, message, error=False, duration=3000)` — SnackBar สำหรับทุก view
- `confirm_dialog(page, title, message, on_confirm, ...)` — AlertDialog สำหรับ destructive actions
- `show_loading(container, visible, page)` — แสดง/ซ่อน loading indicator
- Views ทุกตัว (`task_view`, `team_view`, `calendar_view`, `history_view`, `diary_view`) ใช้ `show_snack()` แทน inline SnackBar

#### Feature — Soft Delete สำหรับ Task
- **Model:** เพิ่ม `is_deleted = Column(Boolean, default=False)` ใน `Task`
- **Migration:** `init_db()` รัน `ALTER TABLE tasks ADD COLUMN is_deleted` (try/except สำหรับ DB เก่า)
- **Repository:** `task_repo.delete()` เปลี่ยนเป็น soft delete (set flag), เพิ่ม `delete_permanent()` สำหรับลบจริง
- **Queries:** `get_by_id`, `get_all`, `get_overdue`, `get_by_team`, `get_by_assignee`, `get_by_status` filter `is_deleted == False` ทั้งหมด
- **Service:** เพิ่ม `restore_task(task_id)` ใน `TaskService`

#### Feature — Interactive Dashboard
- **ไฟล์:** `app/views/main_layout.py` — `build_dashboard_view(db, navigate_fn=None)`
- Stat cards ทุกใบคลิกได้ → navigate ไปหน้า "งาน" (`navigate_fn("task")`)
- ส่ง `navigate_fn=navigate` จาก `get_view("dashboard")`

#### Testing — Unit Test Suite (27 tests)
- **ไฟล์:** `tests/conftest.py` (ใหม่) — `db` fixture, in-memory SQLite per test function
- **ไฟล์:** `tests/test_task_service.py` (ใหม่) — 20 tests ครอบคลุม create/read/update/delete/dependency validation/dashboard stats
- **ไฟล์:** `tests/test_diary_service.py` (ใหม่) — 7 tests ครอบคลุม CRUD + grouped
- **ไฟล์:** `tests/test_exceptions.py` (ใหม่) — 5 tests ตรวจสอบ exception hierarchy
- **ผลลัพธ์:** 27/27 passed ใน 0.41s (`pytest tests/ -v`)

#### Bug Fix — Test Ordering (Timing Race)
- `diary_repo.get_all()` เพิ่ม tiebreaker `order_by(created_at DESC, id DESC)` แก้ test fluke เมื่อ 2 entries ถูกสร้างใน millisecond เดียวกัน

---

---

## Phase 12 — UX Polish & Diary PDF Export ✅ (17 มี.ค. 2569)

### Session: 17 มีนาคม 2569

#### Feature — Subtask Progress Indicator (#2)
- **ไฟล์:** `app/views/task_view.py`
- แสดง `X/Y` พร้อม icon `CHECKLIST` บน task card แถวที่สอง (ข้างวันครบกำหนด)
- กรอง `is_deleted` subtasks ออกก่อนนับ
- สีเขียว (`COLOR_DONE`) เมื่อทำครบทุก subtask, สีเทา (`TEXT_SEC`) กรณีอื่น

#### Feature — Sort Filter Chips (#3)
- **ไฟล์:** `app/views/task_view.py`
- เพิ่ม Sort options: สร้างล่าสุด / เก่าสุด / ครบกำหนด / Priority / ชื่อ
- ใช้ filter chip แบบเดียวกับ Status/Priority (UX สม่ำเสมอ — ไม่ใช้ Dropdown)
- Sort logic ใน `_filtered_tasks()` รองรับ `datetime.max` fallback สำหรับงานไม่มีวันครบกำหนด

#### Feature — Collapsible Sidebar (#6)
- **ไฟล์:** `app/views/main_layout.py`
- Toggle button (`‹`/`›`) ย่อ/ขยาย sidebar
- Collapsed width=60px, padding=4px — toggle button ยังคลิกได้
- ซ่อน/แสดง label text ทุก nav item + settings
- Nav icon จัด center เมื่อ collapsed

#### Feature — Overdue Notification Badge (#8)
- **ไฟล์:** `app/views/main_layout.py`
- Badge แดงแสดงจำนวนงานเกินกำหนดบน nav item "งาน"
- อัปเดตอัตโนมัติทุกครั้งที่ navigate หรือ expand sidebar

#### Fix — Diary Export filename basename (#16)
- **ไฟล์:** `app/views/diary_view.py`
- แสดงเฉพาะชื่อไฟล์ใน status text (`os.path.basename(filepath)`) แทน full path

#### Feature — Diary Export PDF (#16 new)
- **ไฟล์:** `app/services/diary_service.py`, `app/views/diary_view.py`
- เพิ่ม `DiaryService.export_to_pdf()` ใช้ reportlab + Thai font (Tahoma) เหมือน Summary export
- สไตล์ Blue-White theme: title สีน้ำเงิน `#2563EB`, date header พื้นหลัง `#EFF6FF`, divider `#CBD5E1`
- **Concept เดียวกัน** ทั้ง Word และ PDF:
  - ปุ่มสไตล์เดียวกัน (`ElevatedButton` + icon + สีต่าง)
  - `_do_export()` helper รวม logic: เรียก service → แสดง status basename → auto-open ไฟล์
  - บันทึกลง `data/job_diary.docx` / `data/job_diary.pdf`
- Layout ปุ่ม: บันทึก + ล้างข้อความ (แถว 1) / Export Word + Export PDF (แถว 2)

#### UX — App Rename TaskFlow → VindFlow
- **ไฟล์:** `main.py`, `app/views/main_layout.py`
- เปลี่ยนชื่อแอปเป็น VindFlow ทั้ง title bar และ sidebar logo

#### UX — Filter Bar Layout Restructure
- **ไฟล์:** `app/views/task_view.py`
- จัดเรียง filter bar เป็น 2 แถว ใน `ft.Column`:
  - แถว 1: Status filter chips
  - แถว 2: Priority filter chips + Sort filter chips
- แก้ปัญหา chips ตกบรรทัดเมื่อหน้าต่างไม่เต็มจอ

#### Bug Fix — Windows asyncio ConnectionResetError on close
- **ไฟล์:** `main.py`
- Monkey-patch `_ProactorBasePipeTransport._call_connection_lost` ที่ class level
- กำจัด `[WinError 10054]` ใน console เมื่อปิดแอป โดยไม่กระทบการทำงาน

---

---

## Phase 13 — UX/UI Professional Polish + Dashboard Charts + Time Tracking ✅ (17 มี.ค. 2569)

### Part A — UX/UI Polish
- **A1** Priority color border ซ้ายการ์ด task (มีอยู่แล้ว, confirm)
- **A2** Hover reveal: ปุ่ม Edit/Delete ซ่อนโดย default, แสดงเมื่อ hover บนการ์ด (`on_hover`)
- **A3** Done/Cancelled visual: opacity 0.55 + title color TEXT_SEC (Flet 0.82 ไม่รองรับ `TextDecoration`)
- **A4** "ล้างตัวกรอง" button ปรากฏอัตโนมัติเมื่อมี filter ที่ active อยู่
- **A5** Smart empty state: แยก "ไม่มีงาน" กับ "ไม่พบงานที่ตรงกับเงื่อนไข" (+ ปุ่ม clear)
- **A6** Form dialog แบ่งเป็น 2 section (ข้อมูลหลัก / รายละเอียดเพิ่มเติม) พร้อม section header icon

### Part B — Dashboard Charts
- ย้าย Dashboard view จาก `main_layout.py` → `app/views/dashboard_view.py`
- Stat cards รูปแบบใหม่พร้อม icon badge
- **B1** Status Donut chart (matplotlib → PNG file → `ft.Image`)
- **B2** Priority Horizontal Bar chart
- **B3** Weekly Trend Line (7 วัน สร้าง vs เสร็จ, fill_between area)
- **B4** Team Workload Bar (งานที่ยังไม่เสร็จต่อสมาชิก, color gradient)
- Thai font auto-detection สำหรับ chart labels (Tahoma / Leelawadee)
- Charts saved as PNG files ใน `data/charts/` (Flet desktop ไม่รองรับ data-URI ใน Image.src)
- Professional light theme: white background, consistent figsize, balanced 2-column grid layout
- Stat cards `expand=True` กระจายเต็มแถว

### Part C — Time Tracking
- **C1** `TimeLog` model (`app/models/time_log.py`) + SQLite auto-migration
- **C2** `TimeTrackingService` (`app/services/time_tracking_service.py`): start/stop timer, manual log, query, summary by task/member
- **C3** Timer UI บน Task Detail Panel: ▶ Start / ⏹ Stop button, recent logs list, manual log input
- **C4** Time report ใน Summary View: ตาราง "เวลาต่องาน" และ "เวลาต่อสมาชิก"

### ไฟล์ที่แก้ไข/สร้างใหม่
| ไฟล์ | การเปลี่ยนแปลง |
|------|--------------|
| `app/views/task_view.py` | A2–A6, C3 Timer UI |
| `app/views/dashboard_view.py` | **NEW** — Dashboard + 4 charts |
| `app/views/main_layout.py` | ย้าย dashboard view ออก, import จาก dashboard_view |
| `app/views/summary_view.py` | C4 Time report section |
| `app/models/time_log.py` | **NEW** — TimeLog model |
| `app/models/task.py` | เพิ่ม time_logs relationship |
| `app/services/time_tracking_service.py` | **NEW** — TimeTrackingService |
| `app/database.py` | register time_log model |

---

---

## Phase 14 — Architecture Review & Code Quality Improvements ✅ (17 มี.ค. 2569)

### Session: 17 มีนาคม 2569

#### Arch#1 — Fresh DB Session Per Navigation
- **ไฟล์:** `app/views/main_layout.py`
- ย้าย `db = SessionLocal()` จาก module-level ใน `build_main_layout()` → สร้างใหม่ภายใน `get_view()` ทุกครั้งที่ navigate
- `_refresh_task_badge()` ใช้ `badge_db = SessionLocal()` แยกต่างหากพร้อม `try/finally: badge_db.close()`
- **เหตุผล:** Session เดิมค้างตลอด lifetime ของแอป → identity map โป่ง → ข้อมูลไม่ fresh เมื่อ navigate กลับมาหน้าเดิม

#### Arch#3 — Service Layer Validation
- **ไฟล์:** `app/services/task_service.py`, `app/utils/exceptions.py`
- เพิ่ม `_validate_task_input(title, start_date, due_date)` ใน `TaskService`:
  - title ว่างหรือ whitespace → raise `ValidationError("ชื่องานต้องไม่ว่าง")`
  - `start_date > due_date` → raise `ValidationError("วันเริ่มต้องไม่อยู่หลังวันครบกำหนด")`
- เรียกใช้ใน `create_task()` และ `update_task()` (ก่อน dependency check)
- Fix: `change_status()` ส่ง `.value` ของ enum เข้า `_log()` แทน enum object โดยตรง
- `ValidationError.__init__(message)` เพิ่ม body (เดิมเป็น `pass`)

#### Arch#4 — Replace `datetime.utcnow` ด้วย timezone-aware
- **ไฟล์:** models × 6, services × 2, repositories × 1, utils × 1, views × 1
- แทนที่ `datetime.utcnow` / `datetime.utcnow()` ทุกจุดด้วย `lambda: datetime.now(timezone.utc).replace(tzinfo=None)` (model defaults) และ `datetime.now(timezone.utc).replace(tzinfo=None)` (runtime calls)
- เพิ่ม `from datetime import datetime, timezone` ในทุกไฟล์ที่แก้
- **เหตุผล:** `datetime.utcnow()` deprecated ใน Python 3.12+

#### Arch#5 — Dashboard Stats ใช้ SQL COUNT
- **ไฟล์:** `app/services/task_service.py`
- เขียน `get_dashboard_stats()` ใหม่ทั้งหมด: ใช้ `func.count(Task.id)` + filter per-status แทนการโหลด task ทั้งหมดเข้า memory แล้วนับใน Python loop
- เพิ่ม `from sqlalchemy import func` ใน imports
- **เหตุผล:** เดิมโหลด N rows เพื่อนับ 5 ตัวเลข — O(N) memory → O(1) memory

#### Arch#9 — Test Coverage (27 → 103 tests)
- **ไฟล์ใหม่:**

| ไฟล์ | Tests | ครอบคลุม |
|---|---|---|
| `tests/test_team_service.py` | 23 | สร้าง/ลบ/อัปเดตทีม, เพิ่ม/ลบ/delete member, workload, toggle active, duplicate guard |
| `tests/test_time_tracking_service.py` | 24 | start/stop timer, concurrent guard, manual log, total minutes, summary by member/task |
| `tests/test_task_repository.py` | 24 | soft-delete, restore, overdue, dependency chain, subtask CRUD, validation edge cases |

- อัปเดต `conftest.py` เพิ่ม `time_log` model ใน `Base.metadata`
- **ผลลัพธ์:** 103/103 passed ใน 1.61s

#### Arch#10 — เพิ่ม matplotlib ใน requirements.txt
- **ไฟล์:** `requirements.txt`
- เพิ่ม `matplotlib>=3.7.0` ภายใต้ section `# Charts (dashboard)`

#### UX#1 — Quick-Add Inline Bar
- **ไฟล์:** `app/views/task_view.py`
- เพิ่ม `quick_add_bar` ระหว่าง filter section และ task list
- TextField + IconButton: พิมพ์ชื่องานแล้วกด Enter หรือกดปุ่ม `+` → สร้างงานทันที (Medium priority, ไม่ต้องเปิด dialog)
- เรียก `task_svc.create_task(title=title)` → `_refresh_tasks()` → `show_snack()`

#### UX#4 — Recycle Bin (กู้คืนงานที่ถูกลบ)
- **ไฟล์:** `app/views/task_view.py`
- เพิ่ม "แสดงงานที่ถูกลบ" toggle button ท้าย task list
- คลิก → แสดง/ซ่อน `trash_body` ที่แสดงรายการ soft-deleted tasks พร้อมปุ่ม "กู้คืน"
- กู้คืน → เรียก `task_svc.restore_task(id)` → refresh ทั้ง deleted list และ task list

#### UX#5 — Loading Indicator บน Dashboard Charts
- **ไฟล์:** `app/views/dashboard_view.py`
- แทนที่การ render charts แบบ synchronous → ใช้ `threading.Thread(daemon=True)`
- แสดง `ft.ProgressRing` spinner ใน placeholder ของ chart card ทุกใบระหว่างรอ
- เมื่อ chart พร้อม → `_replace_chart_placeholder()` swap content และ update UI
- **Bug Fix:** `_chart_team_workload` รับ `workload_counter: dict` แทน task objects — ป้องกัน SQLAlchemy detached instance error ใน background thread (lazy-load `task.assignee` หลัง session หมดอายุ)

### ไฟล์ที่แก้ไข
| ไฟล์ | การเปลี่ยนแปลง |
|------|--------------|
| `app/views/main_layout.py` | Fresh session per navigation, badge session cleanup |
| `app/views/task_view.py` | Quick-add bar, Recycle Bin section |
| `app/views/dashboard_view.py` | Loading spinner, background thread, workload pre-collect |
| `app/services/task_service.py` | Validation, SQL COUNT stats, enum `.value` fix |
| `app/utils/exceptions.py` | `ValidationError.__init__` body |
| `app/models/task.py` | `timezone.utc` defaults |
| `app/models/user.py` | `timezone.utc` defaults |
| `app/models/team.py` | `timezone.utc` defaults |
| `app/models/history.py` | `timezone.utc` defaults |
| `app/models/diary.py` | `timezone.utc` defaults |
| `app/models/time_log.py` | `timezone.utc` defaults |
| `app/repositories/task_repo.py` | `timezone.utc` runtime calls |
| `app/services/time_tracking_service.py` | `timezone.utc` runtime calls |
| `app/utils/date_helpers.py` | `timezone.utc` runtime call |
| `app/views/history_view.py` | `timezone.utc` runtime call |
| `requirements.txt` | เพิ่ม `matplotlib>=3.7.0` |
| `tests/conftest.py` | เพิ่ม `time_log` model import |
| `tests/test_team_service.py` | **NEW** 23 tests |
| `tests/test_time_tracking_service.py` | **NEW** 24 tests |
| `tests/test_task_repository.py` | **NEW** 24 tests |

---

---

## Phase 15 — Code Review Improvements: 4 Batches ✅ (18 มี.ค. 2569)

### Batch 1 — Foundation

#### Arch — Fix Session Leak Per Navigation (B1-T1)
- **ไฟล์:** `app/views/main_layout.py`
- เพิ่ม `_active_db` dict — track และ close session เก่าก่อนสร้างใหม่ทุกครั้ง navigate

#### Refactor — Centralize Date Parsing (B1-T2)
- **ไฟล์:** `app/utils/date_helpers.py` + 3 views
- เพิ่ม `parse_date_input()` (→ datetime, raises) และ `parse_date_field()` (→ date, รองรับ BE, ไม่ raise)
- ลบ `_parse_date()` / `_parse_date_field()` ที่ซ้ำกัน 3 ไฟล์

#### Refactor — Magic String Constants (B1-T3)
- **ไฟล์:** `app/views/task_view.py`
- `ALL_FILTER`, `NO_SELECTION`, `DEFAULT_PRIORITY` แทน hardcoded strings ทุกจุด

### Batch 2 — Performance & Architecture

#### Performance — Fix N+1 Query ใน TimeTrackingService (B2-T1)
- **ไฟล์:** `app/services/time_tracking_service.py`
- เพิ่ม `joinedload(TimeLog.user)` และ `joinedload(TimeLog.task)` ลด query จาก N+1 → 1

#### Architecture — ย้าย Dropdown Logic เข้า Service (B2-T2)
- **ไฟล์:** `app/services/team_service.py`, `app/services/task_service.py`, `app/views/task_view.py`
- `TeamService.get_members_for_dropdown()`, `TaskService.get_tasks_for_depends_dropdown()`
- View ไม่ข้าม service เพื่อเรียก repository โดยตรงอีกต่อไป

#### Fix — Typed Exception Handling (B2-T3)
- **ไฟล์:** `app/views/task_view.py`
- แยก catch: `ValidationError/CircularDependency` → dialog error, `NotFoundError` → snack, `Exception` → log

#### Fix — Dashboard Background Thread Safety (B2-T4)
- **ไฟล์:** `app/views/dashboard_view.py`
- Pre-collect `priority_counts` + `trend_created`/`trend_done` ใน main thread ก่อน spawn background thread
- ทุก chart function รับ plain dict/list แทน ORM objects — ป้องกัน DetachedInstanceError

### Batch 3 — Database & Type Safety

#### Performance — DB Indexes บน FK Columns (B3-T1)
- **ไฟล์:** `app/models/task.py`, `app/models/time_log.py`, `app/models/user.py`, `app/database.py`
- `index=True` บน FK columns ที่ filter บ่อย + `CREATE INDEX IF NOT EXISTS` migrations

#### Type Safety — TypedDict (B3-T2)
- **ไฟล์:** `app/services/time_tracking_service.py`, `app/services/task_service.py`
- `MemberSummary`, `TaskTimeSummary`, `DashboardStats` TypedDict แทน bare `Dict`

### Batch 4 — UX & Documentation

#### UX — Loading Indicator + safe_page_update (B4-T1, B4-T3)
- **ไฟล์:** `app/utils/ui_helpers.py`, `app/views/task_view.py`
- เพิ่ม `safe_page_update(page)` helper ใน ui_helpers
- `_filter_loading` Row (ProgressRing) แสดงขณะ filter/sort tasks
- แทนที่ `try: page.update() except Exception: logger.warning(...)` pattern 5+ จุดด้วย `safe_page_update`

#### Documentation — Docstrings (B4-T2)
- **ไฟล์:** `app/services/task_service.py`
- เพิ่ม docstrings ใน `create_task()`, `update_task()`, `change_status()`, `assign_task()`

### ผลลัพธ์
- **Tests:** 103/103 passed ✅
- **ไฟล์ที่แก้ไข:** 15 ไฟล์

---

### Roadmap ถัดไป

| Phase | หัวข้อ | สถานะ |
|-------|--------|-------|
| **Phase 16** | เลือกไฟล์ Database จากไดร์ฟกลาง (Shared SQLite + WAL + retry) | 🔜 Planned |
| **Phase 17** | ระบบล็อกอิน (Admin สร้างบัญชี / Member login) | 🔜 Planned |
| **Phase 18** | พิจารณา Web App Migration (Flet Web / FastAPI + React) | 🔜 Planned |
