"""Poll database layer using SQLite."""

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

DB_DIR = Path(__file__).parent / "data"
DB_PATH = DB_DIR / "polls.db"

# Regional indicator emojis for up to 10 options
EMOJI_OPTIONS = [
    "\U0001f1e6",  # 🇦
    "\U0001f1e7",  # 🇧
    "\U0001f1e8",  # 🇨
    "\U0001f1e9",  # 🇩
    "\U0001f1ea",  # 🇪
    "\U0001f1eb",  # 🇫
    "\U0001f1ec",  # 🇬
    "\U0001f1ed",  # 🇭
    "\U0001f1ee",  # 🇮
    "\U0001f1ef",  # 🇯
]


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
            CREATE TABLE IF NOT EXISTS polls (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id        INTEGER NOT NULL,
                channel_id      INTEGER NOT NULL,
                message_id      INTEGER,
                question        TEXT NOT NULL,
                options         TEXT NOT NULL,
                creator_id      INTEGER NOT NULL,
                created_at      REAL NOT NULL,
                duration_seconds INTEGER,
                anonymous       INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS votes (
                poll_id       INTEGER NOT NULL,
                user_id       INTEGER NOT NULL,
                option_index  INTEGER NOT NULL,
                PRIMARY KEY (poll_id, user_id),
                FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_votes_poll_id ON votes(poll_id);
        """)
        conn.commit()
    finally:
        conn.close()


def create_poll(
    guild_id: int,
    channel_id: int,
    question: str,
    options: list[str],
    creator_id: int,
    duration_seconds: int | None = None,
    anonymous: bool = False,
) -> int:
    """Insert a new poll and return its id."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            """
            INSERT INTO polls (guild_id, channel_id, question, options,
                               creator_id, created_at, duration_seconds, anonymous)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                channel_id,
                question,
                json.dumps(options, ensure_ascii=False),
                creator_id,
                time.time(),
                duration_seconds,
                1 if anonymous else 0,
            ),
        )
        conn.commit()
        return cur.lastrowid  # type: ignore[return-value]
    finally:
        conn.close()


def set_message_id(poll_id: int, message_id: int) -> None:
    conn = _get_conn()
    try:
        conn.execute("UPDATE polls SET message_id = ? WHERE id = ?", (message_id, poll_id))
        conn.commit()
    finally:
        conn.close()


def get_poll(poll_id: int) -> dict[str, Any] | None:
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM polls WHERE id = ?", (poll_id,)).fetchone()
        if row is None:
            return None
        return _row_to_dict(row)
    finally:
        conn.close()


def get_poll_by_message(message_id: int) -> dict[str, Any] | None:
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM polls WHERE message_id = ?", (message_id,)
        ).fetchone()
        if row is None:
            return None
        return _row_to_dict(row)
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    d: dict[str, Any] = dict(row)
    d["options"] = json.loads(d["options"])
    d["anonymous"] = bool(d["anonymous"])
    return d


def get_active_polls(guild_id: int) -> list[dict[str, Any]]:
    """Return polls that haven't expired yet."""
    conn = _get_conn()
    try:
        now = time.time()
        rows = conn.execute(
            """
            SELECT * FROM polls
            WHERE guild_id = ?
              AND (duration_seconds IS NULL
                   OR created_at + duration_seconds > ?)
            ORDER BY created_at DESC
            """,
            (guild_id, now),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def has_expired(poll: dict[str, Any]) -> bool:
    """Check if a poll has expired based on duration."""
    dur = poll.get("duration_seconds")
    if dur is None:
        return False
    return time.time() > poll["created_at"] + dur


def cast_vote(poll_id: int, user_id: int, option_index: int) -> bool:
    """Record a vote. Returns True if newly inserted, False if updated."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            """
            INSERT INTO votes (poll_id, user_id, option_index)
            VALUES (?, ?, ?)
            ON CONFLICT(poll_id, user_id)
            DO UPDATE SET option_index = excluded.option_index
            """,
            (poll_id, user_id, option_index),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_results(poll_id: int) -> dict[int, int]:
    """Return {option_index: vote_count} for a poll."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            """
            SELECT option_index, COUNT(*) as cnt
            FROM votes
            WHERE poll_id = ?
            GROUP BY option_index
            """,
            (poll_id,),
        ).fetchall()
        return {r["option_index"]: r["cnt"] for r in rows}
    finally:
        conn.close()


def get_total_voters(poll_id: int) -> int:
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM votes WHERE poll_id = ?", (poll_id,)
        ).fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()