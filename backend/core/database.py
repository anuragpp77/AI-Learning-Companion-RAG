"""
backend/core/database.py
─────────────────────────
SQLite persistence layer. Replaces the volatile in-memory defaultdict
so topic stats and uploaded-file records survive server restarts.
"""

import sqlite3
import os
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", "data/study_companion.db")


def get_connection() -> sqlite3.Connection:
    """Return a thread-safe SQLite connection with row factory."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all tables if they don't exist. Safe to call on every startup."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS topics (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT    UNIQUE NOT NULL,
            ask_count    INTEGER DEFAULT 0,
            quiz_attempts INTEGER DEFAULT 0,
            quiz_score   REAL    DEFAULT 0.0,
            last_seen    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS flashcards (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            topic      TEXT NOT NULL,
            question   TEXT NOT NULL,
            answer     TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS uploaded_files (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            original_name TEXT NOT NULL,
            stored_name   TEXT NOT NULL,
            chunk_count   INTEGER DEFAULT 0,
            file_type     TEXT,
            uploaded_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()
