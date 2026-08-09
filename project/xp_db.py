"""XP database layer using SQLite."""

import math
import sqlite3
import time
from pathlib import Path
from typing import Any

DB_DIR = Path(__file__).parent / "data"
DB_PATH = DB_DIR / "xp.db"

# XP awarded per message (random between MIN and MAX)
XP_MIN = 10
XP_MAX = 20

# Cooldown in seconds between XP grants
XP_COOLDOWN = 60

# XP required for level N: xp_for_level(N) = LEVEL_BASE * (N - 1) ** 2
LEVEL_BASE = 100


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
            CREATE TABLE IF NOT EXISTS xp_data (
                user_id         INTEGER NOT NULL,
                guild_id        INTEGER NOT NULL,
                xp              INTEGER NOT NULL DEFAULT 0,
                level           INTEGER NOT NULL DEFAULT 1,
                last_message_at REAL,
                PRIMARY KEY (user_id, guild_id)
            );

            CREATE INDEX IF NOT EXISTS idx_xp_data_guild_xp
                ON xp_data(guild_id, xp DESC);
        """)
        conn.commit()
    finally:
        conn.close()


def get_or_create_user(user_id: int, guild_id: int) -> dict[str, Any]:
    """Return xp_data row for a user, creating a default row if missing."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM xp_data WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO xp_data (user_id, guild_id, xp, level, last_message_at) "
                "VALUES (?, ?, 0, 1, NULL)",
                (user_id, guild_id),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM xp_data WHERE user_id = ? AND guild_id = ?",
                (user_id, guild_id),
            ).fetchone()
        return dict(row)
    finally:
        conn.close()


def _calculate_level(xp: int) -> int:
    """Calculate level from total XP.

    Level 1: 0 XP
    Level 2: 100 XP
    Level 3: 400 XP
    Level 4: 900 XP
    ...
    """
    return int(math.isqrt(xp // LEVEL_BASE)) + 1


def award_xp(user_id: int, guild_id: int) -> tuple[int, int, bool]:
    """Award XP to a user. Returns (new_xp, new_level, leveled_up).

    Respects XP_COOLDOWN via last_message_at.
    """
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM xp_data WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        ).fetchone()

        now = time.time()
        if row is None:
            # Create new user with first XP grant
            xp_gained = __import__("random").randint(XP_MIN, XP_MAX)
            new_xp = xp_gained
            new_level = _calculate_level(new_xp)
            conn.execute(
                "INSERT INTO xp_data (user_id, guild_id, xp, level, last_message_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, guild_id, new_xp, new_level, now),
            )
            conn.commit()
            return new_xp, new_level, new_level > 1

        # Check cooldown
        last_msg = row["last_message_at"]
        if last_msg is not None and (now - last_msg) < XP_COOLDOWN:
            return row["xp"], row["level"], False

        # Award XP
        xp_gained = __import__("random").randint(XP_MIN, XP_MAX)
        new_xp = row["xp"] + xp_gained
        old_level = row["level"]
        new_level = _calculate_level(new_xp)

        conn.execute(
            "UPDATE xp_data SET xp = ?, level = ?, last_message_at = ? "
            "WHERE user_id = ? AND guild_id = ?",
            (new_xp, new_level, now, user_id, guild_id),
        )
        conn.commit()
        return new_xp, new_level, new_level > old_level
    finally:
        conn.close()


def get_rank(user_id: int, guild_id: int) -> dict[str, Any] | None:
    """Return the rank and XP info for a user in a guild."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM xp_data WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        ).fetchone()
        if row is None:
            return None

        # Count users with more XP to determine rank
        rank_row = conn.execute(
            "SELECT COUNT(*) AS rank FROM xp_data "
            "WHERE guild_id = ? AND xp > ?",
            (guild_id, row["xp"]),
        ).fetchone()

        total_row = conn.execute(
            "SELECT COUNT(*) AS total FROM xp_data WHERE guild_id = ?",
            (guild_id,),
        ).fetchone()

        result = dict(row)
        result["rank"] = (rank_row["rank"] if rank_row else 0) + 1
        result["total"] = total_row["total"] if total_row else 0
        return result
    finally:
        conn.close()


def get_leaderboard(guild_id: int, limit: int = 10) -> list[dict[str, Any]]:
    """Return top N users by XP in a guild."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM xp_data "
            "WHERE guild_id = ? "
            "ORDER BY xp DESC "
            "LIMIT ?",
            (guild_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_total_members(guild_id: int) -> int:
    """Return total number of tracked members in a guild."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM xp_data WHERE guild_id = ?",
            (guild_id,),
        ).fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()