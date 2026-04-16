# CLAUDE.md — VindFlow Project Guide

คู่มือนี้ให้บริบทที่จำเป็นสำหรับการทำงานกับโค้ดใน repository นี้

---

## 0. Claude Workflow Rules

### Plan Before Acting
- งานที่มี 3+ ขั้นตอน หรือมีผลกระทบต่อ architecture → วางแผนก่อนเสมอ พร้อมระบุไฟล์ที่จะแตะ
- ถ้าติดขัดระหว่างทาง → หยุดและ re-plan ทันที ห้าม brute-force ด้วยการลองซ้ำแบบเดิม
- เขียน spec ให้ชัดก่อน implement เพื่อลด ambiguity

### Verification Before Done
- ห้าม mark task เสร็จโดยไม่มีหลักฐาน (run test / screenshot / log output)
- หลังแก้ไข service หรือ repository ให้รัน `pytest tests/ -v` ทุกครั้ง
- ถามตัวเองก่อน commit: "Staff engineer จะ approve โค้ดนี้ไหม?"

### Autonomous Bug Fixing
- อ่าน error message ครบก่อนเสมอ → วินิจฉัย root cause → แก้ที่จุดเดียว
- ห้าม retry คำสั่งที่ fail ซ้ำๆ โดยไม่เข้าใจสาเหตุ — ให้อ่าน log แล้ว diagnose ก่อน
- ชี้ที่ log / error / failing test แล้วแก้ โดยไม่ต้องถามให้ user นำทาง

### Elegance Check
- ก่อน implement ทุกครั้ง: "มีวิธีที่ simple กว่านี้ไหม?"
- ถ้า fix รู้สึก hacky → หยุด แล้ว implement วิธีที่ถูกต้องแทน
- ห้าม add utility / helper สำหรับการใช้งานครั้งเดียว
- ห้าม over-engineer: สาม lines ที่ซ้ำกันดีกว่า abstraction ที่ไม่จำเป็น

### Self-Improvement Loop
- หลังถูกแก้ไขหรือ correct จาก user → บันทึก pattern ลง memory ทันที
- เขียน rule ที่ป้องกันความผิดพลาดเดิมในครั้งถัดไป
- อ่าน memory ที่บันทึกไว้ก่อนเริ่ม session ใหม่เสมอ

### No Git Operations by Agents
- Agents (sub-processes spawned via Agent tool) **ห้ามรัน git commands ทุกชนิด**
- ห้าม: `git commit`, `git push`, `git add`, `git reset`, `git checkout`, `git merge`, `git rebase`
- เหตุผล: Git history ต้องผ่านการตรวจสอบจาก human เสมอ — agents ไม่มีบริบทครบถ้วนในการ craft commit message ที่ถูกต้อง
- Agents ทำได้เฉพาะ: อ่านไฟล์, แก้ไขโค้ด, รัน tests, รัน builds
- การ commit ทุกครั้งต้องทำโดย Claude หลัก (main session) หลังจาก user approve เท่านั้น

### Task Management
1. **Plan First** — วางแผนพร้อมระบุไฟล์และขั้นตอนก่อนลงมือ
2. **Track Progress** — mark แต่ละ task เสร็จทันทีหลังทำเสร็จจริง
3. **Explain Changes** — สรุป high-level ว่าทำอะไรและทำไม
4. **Document Results** — อัปเดต CHANGELOG.md เมื่อ feature/fix เสร็จ

---

## 1. Project Overview

**VindFlow** — Desktop Task Management App สำหรับทีมขนาดเล็ก
สร้างด้วย Python + Flet (desktop UI framework)
รองรับ: Task/Subtask (due_date+assignee), Team, Milestone, Time Tracking, Dashboard Charts, Workload Heatmap, Diary Export

- **Entry point:** `main.py`
- **UI Framework:** Flet 0.82 (function-based views, ไม่ใช่ class-based)
- **Database:** SQLite (`data/task_manager.db`)
- **ORM:** SQLAlchemy 2.x

---

## 2. Architecture

```
Views  →  Services  →  Repositories  →  SQLite
         (business logic)  (data access)
```

### Layer responsibilities
| Layer | ไดเรกทอรี | บทบาท |
|-------|-----------|-------|
| Views | `app/views/` | Flet UI controls, event handlers, state (mutable dicts) |
| Services | `app/services/` | Validation, business rules, orchestration |
| Repositories | `app/repositories/` | SQL queries, CRUD, soft-delete |
| Models | `app/models/` | SQLAlchemy ORM models |
| Utils | `app/utils/` | theme, logger, exceptions, ui_helpers, date_helpers |

---

## 3. File Structure

```
D:\Task Management\
├── main.py                          # Entry point, asyncio fix สำหรับ Windows
├── requirements.txt
├── CHANGELOG.md
├── task_manager_requirements.md
│
├── app/
│   ├── database.py                  # engine, SessionLocal, init_db(), get_db()
│   ├── models/
│   │   ├── task.py                  # Task, SubTask, task_dependencies (M2M)
│   │   ├── user.py                  # User
│   │   ├── team.py                  # Team, team_members (M2M)
│   │   ├── history.py               # HistoryLog
│   │   ├── diary.py                 # DiaryEntry
│   │   ├── time_log.py              # TimeLog (time tracking)
│   │   └── milestone.py             # Milestone
│   ├── repositories/
│   │   ├── base.py                  # BaseRepository(ABC, Generic[T])
│   │   ├── task_repo.py             # TaskRepository
│   │   ├── user_repo.py             # UserRepository
│   │   ├── team_repo.py             # TeamRepository
│   │   ├── diary_repo.py            # DiaryRepository
│   │   ├── time_log_repo.py         # TimeLogRepository
│   │   └── milestone_repo.py        # MilestoneRepository
│   ├── services/
│   │   ├── task_service.py          # TaskService — หลัก
│   │   ├── team_service.py          # TeamService
│   │   ├── diary_service.py         # DiaryService + export Word/PDF
│   │   ├── time_tracking_service.py # TimeTrackingService (start/stop/log)
│   │   ├── auth_service.py          # AuthService — PBKDF2 hash, login, JWT-ready (Phase 19)
│   │   └── milestone_service.py     # MilestoneService
│   ├── views/
│   │   ├── main_layout.py           # Sidebar nav + fresh session per navigation
│   │   ├── dashboard_view.py        # 4 matplotlib charts (background thread)
│   │   ├── task_view.py             # Task list, quick-add bar, recycle bin
│   │   ├── team_view.py             # Team CRUD
│   │   ├── calendar_view.py         # Calendar
│   │   ├── summary_view.py          # Export Excel/PDF + time report
│   │   ├── diary_view.py            # Job diary + export Word/PDF
│   │   ├── login_view.py            # Split-panel login (Phase 19)
│   │   ├── settings_view.py         # User management — admin only (Phase 19)
│   │   ├── account_view.py          # Profile + เปลี่ยนรหัสผ่าน (Phase 19)
│   │   ├── history_view.py          # Activity log
│   │   └── milestone_view.py        # Milestone management (Phase 22)
│   └── utils/
│       ├── theme.py                 # Color constants (Blue-White theme)
│       ├── exceptions.py            # Custom exception hierarchy
│       ├── logger.py                # Rotating file logger → data/taskflow.log
│       ├── ui_helpers.py            # show_snack(), confirm_dialog(), safe_page_update()
│       ├── date_helpers.py          # Thai date utilities
│       └── shortcut_registry.py     # Keyboard shortcut registry (register/clear/dispatch)
│
├── tests/
│   ├── conftest.py                  # in-memory SQLite fixture (per test function)
│   ├── test_task_service.py              # 15 tests
│   ├── test_task_service_phase16.py      # 36 tests (new repo/service methods)
│   ├── test_team_service.py              # 25 tests
│   ├── test_time_tracking_service.py     # 24 tests
│   ├── test_task_repository.py           # 24 tests
│   ├── test_diary_service.py             # 7 tests
│   ├── test_exceptions.py               # 5 tests
│   ├── test_auth_service.py             # 18 tests
│   ├── test_milestone_service.py        # 18 tests
│   ├── test_subtask_fields.py           # 12 tests
│   └── test_search_tasks.py             # 8 tests
│
└── data/
    ├── task_manager.db              # SQLite database
    ├── charts/                      # PNG files จาก matplotlib (auto-generated)
    ├── job_diary.docx               # Diary export
    ├── job_diary.pdf                # Diary export
    └── taskflow.log                 # Application log (rotating)
```

---

## 4. Development Setup

```bash
# สร้าง virtual environment
python -m venv venv
venv\Scripts\activate          # Windows

# ติดตั้ง dependencies
pip install -r requirements.txt

# รันแอป
python main.py

# รัน tests ทั้งหมด
pytest tests/ -v

# รัน tests พร้อม coverage
pytest tests/ --cov=app --cov-report=term-missing
```

**Current test count:** 229 tests, ทุกตัวผ่าน

---

## 5. Critical Conventions

### 5.1 Session Management
**สร้าง session ใหม่ทุกครั้งที่ navigate** — ห้ามเก็บ session ไว้ใน module-level หรือ closure ยาว

```python
# ✅ ถูก — ใน get_view() ของ main_layout.py
def get_view(key: str) -> ft.Control:
    db = SessionLocal()          # fresh per navigation
    ...

# ✅ ถูก — badge refresh ใช้ session แยก
def _refresh_task_badge():
    badge_db = SessionLocal()
    try:
        ...
    finally:
        badge_db.close()

# ❌ ผิด — session เดียวตลอด lifetime
db = SessionLocal()              # module-level ห้ามทำ
```

### 5.2 Datetime — ห้ามใช้ `utcnow`

```python
# ✅ ถูก
from datetime import datetime, timezone
datetime.now(timezone.utc).replace(tzinfo=None)

# ✅ ถูก (model defaults)
from datetime import datetime, timezone
Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# ❌ ผิด — deprecated ใน Python 3.12+
datetime.utcnow()
```

### 5.3 Soft Delete
- `task_repo.delete(id)` → set `is_deleted = True` (soft)
- `task_repo.delete_permanent(id)` → ลบจริง
- query ทั้งหมด filter `is_deleted == False` อัตโนมัติ
- `task_svc.restore_task(id)` → กู้คืน soft-deleted task

### 5.4 Dashboard Charts — ห้ามใช้ data-URI

```python
# ✅ ถูก — บันทึกเป็นไฟล์ PNG
fig.savefig("/path/data/charts/chart_name.png", ...)
ft.Image(src="/path/data/charts/chart_name.png")

# ❌ ผิด — Flet desktop ไม่รองรับ data-URI ใน Image.src
ft.Image(src="data:image/png;base64,...")
```

**Background thread:** Charts render ใน daemon thread แยก ป้องกัน UI block
**Pre-collect lazy-load data:** ดึงข้อมูล relationship (เช่น `task.assignee.name`) ก่อน spawn thread เพื่อป้องกัน SQLAlchemy detached instance error

**Chart caching (module-level):** `_CACHE_KEY` เก็บ hash ของ input data ข้ามการ navigate — ถ้า data ไม่เปลี่ยน จะไม่ re-render matplotlib เลย (ประหยัด ~1.5s)
**Parallel rendering:** 4 charts render ใน 4 threads พร้อมกัน (แทน sequential) — ครั้งแรกที่ต้อง render จะเร็วกว่า ~4x
**Stale-but-instant display:** ถ้า PNG file อยู่บน disk แล้ว จะแสดงทันที (0ms) แทน spinner ขณะรอ re-render
**`_MATPLOTLIB_LOCK`:** `threading.Lock()` ป้องกัน concurrent pyplot state corruption (Agg backend ไม่ thread-safe 100%)

### 5.5 Service Validation
ใช้ custom exceptions จาก `app.utils.exceptions` — ไม่ throw bare `ValueError`/`Exception`

```python
from app.utils.exceptions import ValidationError, NotFoundError, DuplicateNameError

# ใน services
if not title.strip():
    raise ValidationError("ชื่องานต้องไม่ว่าง")

# ใน views — จับ base class
from app.utils.exceptions import TaskFlowError
try:
    svc.create_task(...)
except TaskFlowError as e:
    show_snack(page, str(e), error=True)
```

**Exception hierarchy:**
```
TaskFlowError
├── NotFoundError(entity, entity_id)    # ← entity_id ไม่ใช่ id (ป้องกัน shadow built-in)
├── DuplicateNameError(entity, name)
├── CircularDependencyError(task_id, depends_on_id)
├── SelfDependencyError(task_id)
└── ValidationError(message)
```

### 5.6 Layer Boundaries — กฎเด็ดขาด
```
Views → Services → Repositories → DB
```

**Views ห้ามทำ:**
```python
# ❌ View เรียก repo ผ่าน service
task_svc.task_repo.get_by_id(...)          # ห้าม — ข้าม layer

# ❌ View รัน ORM query เอง
db.query(Task).filter(...).all()            # ห้าม — ต้องผ่าน service

# ❌ View import model โดยตรงเพื่อ query
from app.models.task import Task as TaskModel
db.query(TaskModel).filter(...)             # ห้าม
```

**Views ทำได้เฉพาะ:**
```python
# ✅ เรียกผ่าน service เท่านั้น
task_svc.get_task_or_none(task_id)
task_svc.get_deleted_tasks()
task_svc.get_comments(task_id)
```

**Services ห้ามทำ:**
```python
# ❌ Service รัน ORM query เอง (ยกเว้น aggregate ที่ยังไม่มี repo method)
self.db.query(Task).filter(...)             # ห้าม — ใช้ self.task_repo แทน
```

### 5.7 Phase 19 — Auth Pattern

```python
# ✅ ถูก — เก็บ current user ใน session store
page.session.store.set("current_user", {
    "id": user.id, "name": user.name,
    "is_admin": user.is_admin, "username": user.username,
})

# ✅ ถูก — อ่านกลับ
current = page.session.store.get("current_user") or {}
is_admin = current.get("is_admin", False)

# ✅ ถูก — logout
page.session.store.remove("current_user")

# ❌ ผิด — API นี้ไม่มีใน Flet 0.27.6
page.session.set("current_user", ...)  # AttributeError!
```

**AuthService** (`app/services/auth_service.py`):
- `hash_password(pwd)` → `"{salt}:{hash}"` (PBKDF2-SHA256, 260k iterations)
- `verify_password(pwd, stored_hash)` → `bool`
- `login(username, password)` → `User` หรือ raise `InvalidCredentialsError`
- `create_admin(username, name, password)` → `User`
- `has_any_login_user()` → `bool` (ใช้ใน first-run check)

**Default admin** — สร้างอัตโนมัติเมื่อ DB ว่าง (username=`admin`, password=`admin`)

### 5.8 SQL COUNT แทน Python loop
```python
# ✅ ถูก
from sqlalchemy import func
count = db.query(func.count(Task.id)).filter(Task.status == ...).scalar()

# ❌ ผิด
tasks = repo.get_all()
count = sum(1 for t in tasks if t.status == ...)
```

---

## 6. UI Patterns

### 6.1 Theme — Blue-White
ดู `app/utils/theme.py` สำหรับค่าสีทั้งหมด

| ค่าคงที่ | hex | ใช้งาน |
|---------|-----|--------|
| `BG_DARK` | `#F0F4F8` | Page background |
| `BG_CARD` | `#FFFFFF` | Card background |
| `BG_SIDEBAR` | `#FFFFFF` | Sidebar background |
| `ACCENT` | `#2563EB` | ปุ่มหลัก, icon active |
| `ACCENT2` | `#0EA5E9` | Highlight รอง |
| `TEXT_PRI` | `#1E293B` | เนื้อหาหลัก |
| `TEXT_SEC` | `#64748B` | เนื้อหารอง |
| `BORDER` | `#CBD5E1` | ขอบ card/divider |

### 6.2 UI Helpers
```python
from app.utils.ui_helpers import show_snack, confirm_dialog, show_loading

show_snack(page, "บันทึกสำเร็จ")
show_snack(page, "เกิดข้อผิดพลาด", error=True)

confirm_dialog(
    page, title="ยืนยัน", message="ต้องการลบ?",
    on_confirm=lambda: do_delete()
)
```

### 6.3 View Pattern (Function-based)
Views ทุกหน้าเป็น function ที่รับ `db, page` และ return `ft.Control`
State จัดการผ่าน mutable dict หรือ list (`selected_task_id = {}`, `filter_status = {}`)

### 6.4 Admin-only Nav Item Pattern
ซ่อน nav item จาก non-admin ใน `build_nav_btn()` โดยใช้ `visible=`:

```python
# ใน build_nav_btn() — main_layout.py
_is_admin = (page.session.store.get("current_user") or {}).get("is_admin", False)

c = ft.Container(
    ...
    visible=True if key != "settings" else _is_admin,
)

# สำหรับ bottom-section button เฉพาะ admin:
settings_btn = ft.Container(visible=_is_admin, ...)   # "จัดการ Users" — admin only
account_btn  = ft.Container(visible=True, ...)         # "บัญชี" — ทุก user
logout_btn   = ft.Container(visible=on_logout is not None, ...)
```

---

## 7. Database Schema (สรุป)

| ตาราง | ไฟล์ | หมายเหตุ |
|-------|------|---------|
| `tasks` | `models/task.py` | มี `is_deleted`, `subtasks` rel, `dependencies` M2M |
| `subtasks` | `models/task.py` | มี `is_deleted`, FK → tasks |
| `users` | `models/user.py` | มี `is_deleted`, `username`, `password_hash`, `is_admin` (Phase 19) |
| `teams` | `models/team.py` | มี `is_deleted`, M2M กับ users |
| `task_history` | `models/history.py` | log การเปลี่ยนแปลง |
| `diary_entries` | `models/diary.py` | บันทึกประจำวัน |
| `time_logs` | `models/time_log.py` | time tracking (started_at, ended_at, duration_minutes) |

**Migrations:** ทำผ่าน `init_db()` ใน `database.py` (ALTER TABLE try/except สำหรับ DB เก่า)

---

## 8. Known Constraints

| ข้อจำกัด | รายละเอียด |
|---------|------------|
| Flet version | 0.27.6 (installed) — ยังไม่รองรับ `TextDecoration.LINE_THROUGH` (strikethrough) |
| Flet Button API | `ElevatedButton` รับ label เป็น **positional arg แรก** — ห้ามใช้ `text=` keyword |
| Flet Alignment | `ft.alignment.center` ไม่มีใน 0.27.6 — ใช้ `ft.Alignment(0, 0)` แทน |
| Flet Session | `page.session.set()` ไม่มี — ใช้ `page.session.store.set()` / `.get()` / `.remove()` |
| Flet TextField.focus() | เป็น coroutine — ห้ามเรียกตรงใน sync handler; ใช้ได้ใน `on_submit` event |
| Flet ButtonStyle | ไม่รองรับ `shape=` และ `text_style=` ใน 0.27.6 — ใช้แค่ `bgcolor`, `color`, `padding` |
| Flet Color ARGB | 8-digit hex ใช้รูปแบบ **ARGB** ไม่ใช่ RGBA — `#FFFFFF22` = เหลือง (A=FF,R=FF,G=FF,B=22) → ต้องใช้ `#33FFFFFF` (A=33, white 20%) |
| Flet Image | ไม่รองรับ `data:image/png;base64,...` ใน `Image.src` บน desktop |
| SQLAlchemy lazy-load | ห้าม access relationship attribute หลัง session ปิด หรือใน background thread |
| Windows asyncio | `main.py` มี monkey-patch `_ProactorBasePipeTransport` ป้องกัน `WinError 10054` เมื่อปิดแอป |
| Thai font (charts) | `dashboard_view.py` auto-detect Tahoma/Leelawadee สำหรับ matplotlib |
| matplotlib thread safety | Agg backend ไม่ thread-safe 100% — ใช้ `_MATPLOTLIB_LOCK` ก่อน `fig.savefig()` + `plt.close()` เสมอ |
| Dashboard cache scope | `_CACHE_KEY` เป็น module-level (process-wide) — reset เองเมื่อ date เปลี่ยน หรือ data เปลี่ยน |
| Flet AlertDialog | เปิดด้วย `dlg.open = True` + `safe_page_update(page)` เสมอ (ไม่ใช้ `page.show_dialog()` สำหรับ AlertDialog) — ปิดด้วย `dlg.open = False` + `safe_page_update(page)` |

---

## 9. Testing

```bash
pytest tests/ -v                          # รันทั้งหมด (229 tests)
pytest tests/test_task_service.py -v      # เฉพาะ file
pytest tests/ -k "test_create" -v         # เฉพาะ test ที่ชื่อตรง
```

**Fixture:** `conftest.py` ให้ `db` fixture เป็น in-memory SQLite สร้างใหม่ต่อ test function
ห้าม mock database ใน tests — ใช้ real in-memory SQLite เท่านั้น

| Test file | Tests | ครอบคลุม |
|-----------|-------|---------|
| `test_task_service.py` | 15 | TaskService core CRUD |
| `test_task_service_phase16.py` | 36 | get_task_or_none, get_near_due_*, restore, repo methods |
| `test_team_service.py` | 25 | TeamService, workload, delete_member |
| `test_time_tracking_service.py` | 24 | start/stop timer, summary |
| `test_task_repository.py` | 24 | TaskRepository direct queries |
| `test_time_log_repository.py` | 16 | TimeLogRepository direct queries |
| `test_dashboard_stats.py` | 8 | get_dashboard_stats() inc. review key |
| `test_diary_service.py` | 7 | DiaryService |
| `test_shortcut_registry.py` | 10 | register/dispatch/clear |
| `test_exceptions.py` | 5 | Custom exception hierarchy |
| `test_auth_service.py` | 18 | AuthService login, hash, admin |
| `test_milestone_service.py` | 18 | MilestoneService CRUD + progress |
| `test_subtask_fields.py` | 12 | SubTask due_date + assignee |
| `test_search_tasks.py` | 8 | Full-text search |

---

## 10. Data Directory

| ไฟล์/โฟลเดอร์ | สร้างโดย | หมายเหตุ |
|--------------|---------|---------|
| `data/task_manager.db` | `init_db()` | auto-created เมื่อรันแอป |
| `data/charts/*.png` | `dashboard_view.py` | auto-generated เมื่อเปิด Dashboard |
| `data/taskflow.log` | `logger.py` | rotating 1MB × 3 ไฟล์ |
| `data/job_diary.docx` | `diary_service.py` | export |
| `data/job_diary.pdf` | `diary_service.py` | export |
