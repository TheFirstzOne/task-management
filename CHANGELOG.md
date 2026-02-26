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
