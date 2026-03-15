# Changelog — Task Manager Desktop App

> ประวัติการพัฒนาและแก้ไขโปรเจกต์

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

### สิ่งที่ต้องทำเพิ่มเติม (Planned)

| รายการ | รายละเอียด |
|---|---|
| เลือกไฟล์ Database จากไดร์ฟกลาง | วางไฟล์ SQLite ไว้บน shared drive ของทีม + `PRAGMA journal_mode=WAL` + `busy_timeout` + retry logic สำหรับทีมเล็ก (2-5 คน) |
| ระบบล็อกอิน | Admin สร้างบัญชี username/password ให้สมาชิก, แบ่ง Role (Admin/Member), บันทึกผู้ใช้ใน history log อัตโนมัติ |
| พิจารณาเปลี่ยนเป็น Web App | ศึกษาความเป็นไปได้ในการ migrate จาก Desktop → Web โดยใช้ Flet Web หรือเปลี่ยน framework |
