# VindFlow — Desktop Task Management App

VindFlow is a small-team desktop task management application built with Python and Flet. It provides task & subtask management, teams, time tracking, history logs, dashboard charts, and diary export.

This repository contains the app source, database models (SQLAlchemy), repositories, services, and Flet-based views.

---

## Quick start

Prerequisites
- Python 3.11+ (recommended)
- pip
- (Optional) virtualenv or venv

Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Run the app

```bash
python main.py
```

Notes:
- On Windows the project includes an asyncio fix in `main.py` required by Flet desktop.
- The application uses a local SQLite database at `data/task_manager.db`.

Initialize the database

From the repository root you can initialize the DB (if needed) by running:

```bash
python -c "from app.database import init_db; init_db()"
```

Run tests

```bash
pytest tests/ -v
```

---

## Project structure (high level)

- main.py — application entry point
- app/
  - database.py — engine, SessionLocal, init_db(), get_db()
  - models/ — SQLAlchemy models (Task, SubTask, User, Team, TimeLog, DiaryEntry, HistoryLog)
  - repositories/ — data access layer (BaseRepository, TaskRepository, ...)
  - services/ — business logic and validation
  - views/ — Flet UI views and event handlers
  - utils/ — helpers: logger, exceptions, ui helpers, date helpers

See CLAUDE.md for additional development workflow rules and project conventions.

---

## Architecture

Views → Services → Repositories → SQLite

- Views (Flet): UI, user events, state
- Services: business rules, validation
- Repositories: CRUD and database queries
- Models: SQLAlchemy ORM definitions

---

## Development rules & tests

This project follows the guidelines in `CLAUDE.md` — plan before acting, run tests after changes, and include evidence when marking tasks done. In particular:

- For any change with 3+ steps or architectural impact: create a short plan and list files to touch.
- Run `pytest tests/ -v` after changes.
- Provide test logs or screenshots when claiming work is complete.

---

## Contributing

Contributions are welcome. When opening a PR or making changes, please:
- Follow the project conventions in `CLAUDE.md`.
- Keep changes focused and small.
- Add/adjust tests for any behavior changes.
- Explain what you changed and why in the PR description.

---

## Troubleshooting

- If Flet GUI does not start on Windows, ensure you are using the supported Python version and that any antivirus or firewall is not blocking the app.
- Read the logs printed to the console. For database issues, check `data/task_manager.db` permissions and path.

---

## License

See the LICENSE file in the repository (if present). If no license file exists, contact the maintainers to clarify terms before using this project in production.

---

## Maintainers / Contact

- Repo: TheFirstzOne/task-management
- Current user: TheFirstzOne

If you need help, open an issue with reproduction steps and test output.
