"""Reminder database layer using SQLite."""

import sqlite3
import time
from pathlib import Path
from typing import Any

DB_DIR = Path(__file__).parent / "data"
DB_PATH = DB_DIR / "reminders.db"


def _get_conn() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = _get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS reminders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                channel_id  INTEGER NOT NULL,
                guild_id    INTEGER NOT NULL DEFAULT 0,
                message     TEXT NOT NULL,
                remind_at   REAL NOT NULL,
                created_at  REAL NOT NULL,
                triggered   INTEGER NOT NULL DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_reminders_triggered
                ON reminders(triggered);
            CREATE INDEX IF NOT EXISTS idx_reminders_remind_at
                ON reminders(remind_at);
            CREATE INDEX IF NOT EXISTS idx_reminders_user_id
                ON reminders(user_id);
        """)
        conn.commit()
    finally:
        conn.close()


def create_reminder(
    user_id: int,
    channel_id: int,
    message: str,
    remind_at: float,
    guild_id: int = 0,
) -> int:
    """Insert a new reminder and return its id."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            """
            INSERT INTO reminders (user_id, channel_id, guild_id,
                                   message, remind_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, channel_id, guild_id, message, remind_at, time.time()),
        )
        conn.commit()
        return cur.lastrowid  # type: ignore[return-value]
    finally:
        conn.close()


def get_reminder(reminder_id: int) -> dict[str, Any] | None:
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM reminders WHERE id = ?", (reminder_id,)
        ).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()


def get_active_reminders(user_id: int) -> list[dict[str, Any]]:
    """Return non-triggered reminders for a user."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            """
            SELECT * FROM reminders
            WHERE user_id = ? AND triggered = 0
            ORDER BY remind_at ASC
            """,
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_due_reminders() -> list[dict[str, Any]]:
    """Return reminders that are due and not yet triggered."""
    conn = _get_conn()
    try:
        now = time.time()
        rows = conn.execute(
            """
            SELECT * FROM reminders
            WHERE triggered = 0 AND remind_at <= ?
            ORDER BY remind_at ASC
            """,
            (now,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def mark_triggered(reminder_id: int) -> None:
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE reminders SET triggered = 1 WHERE id = ?", (reminder_id,)
        )
        conn.commit()
    finally:
        conn.close()


def get_active_reminders_count_by_guild(guild_id: int) -> int:
    """Return the number of non-triggered reminders in a guild."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM reminders WHERE guild_id = ? AND triggered = 0",
            (guild_id,),
        ).fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()


def cancel_reminder(reminder_id: int, user_id: int) -> bool:
    """Delete a reminder if it belongs to the user. Returns True if deleted."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            "DELETE FROM reminders WHERE id = ? AND user_id = ? AND triggered = 0",
            (reminder_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()