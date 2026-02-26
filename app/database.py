"""
Database connection, session factory, and schema initialisation.
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ── Paths ─────────────────────────────────────────────────────────────────────
# เมื่อรันเป็น .exe (frozen) ให้ใช้ตำแหน่งของ .exe เป็น base
# เมื่อรันเป็น Python script ให้ใช้ตำแหน่งของ project root
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH  = os.path.join(DATA_DIR, "task_manager.db")

os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

# ── Engine & Session ──────────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ── Public helpers ────────────────────────────────────────────────────────────
def get_db():
    """Context-managed database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they do not exist yet."""
    # Import models so SQLAlchemy registers them before create_all
    from app.models import user, team, task, history  # noqa: F401
    Base.metadata.create_all(bind=engine)
