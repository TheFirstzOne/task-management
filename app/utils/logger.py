"""
Centralised logging setup for TaskFlow.
All modules import get_logger() to get a named logger.
Logs are written to:
  - Console (WARNING+)
  - data/taskflow.log (DEBUG+, rotating, max 1 MB × 3 files)
"""

import logging
import logging.handlers
import os
import sys


def _setup_root_logger() -> None:
    """Configure root logger once at import time."""
    # Resolve log path same logic as database.py (frozen vs script)
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    log_dir = os.path.join(base_dir, "data")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "taskflow.log")

    root = logging.getLogger("taskflow")
    if root.handlers:
        return  # Already configured (e.g. when module is reloaded)

    root.setLevel(logging.DEBUG)

    # ── File handler (rotating, DEBUG level) ──
    fh = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=1_048_576, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    root.addHandler(fh)

    # ── Console handler (WARNING+ only, avoids cluttering terminal) ──
    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    root.addHandler(ch)


_setup_root_logger()


def get_logger(name: str) -> logging.Logger:
    """
    Return a child logger under the 'taskflow' namespace.

    Usage:
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.error("something went wrong: %s", e, exc_info=True)
    """
    return logging.getLogger(f"taskflow.{name}")
