"""SQLite connection and schema management."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "expenses.db"


def database_path() -> Path:
    configured = os.getenv("EXPENSE_DB_PATH", "").strip()
    path = Path(configured).expanduser() if configured else DEFAULT_DB_PATH
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    return path


def get_connection() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def initialize_database() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount_paise INTEGER NOT NULL CHECK(amount_paise > 0),
                category TEXT NOT NULL CHECK(length(category) BETWEEN 1 AND 60),
                description TEXT NOT NULL CHECK(length(description) BETWEEN 1 AND 500),
                expense_date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_expenses_date
            ON expenses(expense_date DESC)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_expenses_category_date
            ON expenses(category, expense_date DESC)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                month TEXT NOT NULL,
                limit_paise INTEGER NOT NULL CHECK(limit_paise > 0),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(category, month)
            )
        """)
