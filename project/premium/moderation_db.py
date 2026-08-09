"""Moderation database layer using SQLite.

Tables: mod_config, ng_words, moderation_keywords
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "moderation.db"


def _get_conn() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = _get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS mod_config (
                guild_id                INTEGER PRIMARY KEY,
                keyword_filter_enabled  INTEGER NOT NULL DEFAULT 1,
                spam_detection_enabled  INTEGER NOT NULL DEFAULT 1,
                spam_threshold          INTEGER NOT NULL DEFAULT 3,
                spam_window_seconds     INTEGER NOT NULL DEFAULT 5,
                max_mentions            INTEGER NOT NULL DEFAULT 5,
                max_links               INTEGER NOT NULL DEFAULT 3,
                mod_log_channel_id      INTEGER,
                created_at              TEXT NOT NULL,
                updated_at              TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ng_words (
                guild_id    INTEGER NOT NULL,
                word        TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                PRIMARY KEY (guild_id, word)
            );

            CREATE INDEX IF NOT EXISTS idx_ng_words_guild
                ON ng_words(guild_id);

            CREATE TABLE IF NOT EXISTS moderation_keywords (
                guild_id    INTEGER NOT NULL,
                keyword     TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                PRIMARY KEY (guild_id, keyword)
            );

            CREATE INDEX IF NOT EXISTS idx_moderation_keywords_guild
                ON moderation_keywords(guild_id);
        """)
        conn.commit()
    finally:
        conn.close()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── mod_config CRUD ──────────────────────────────────────────────────────────


def set_mod_config(guild_id: int, **kwargs: Any) -> dict[str, Any]:
    """Upsert moderation config for a guild. Returns the config record."""
    allowed_keys = {
        "keyword_filter_enabled",
        "spam_detection_enabled",
        "spam_threshold",
        "spam_window_seconds",
        "max_mentions",
        "max_links",
        "mod_log_channel_id",
    }
    filtered = {k: v for k, v in kwargs.items() if k in allowed_keys}

    now = _now_iso()
    conn = _get_conn()
    try:
        if filtered:
            columns = ", ".join(filtered.keys())
            placeholders = ", ".join("?" for _ in filtered)
            updates = ", ".join(f"{k} = excluded.{k}" for k in filtered)
            values = list(filtered.values())
            conn.execute(
                f"""
                INSERT INTO mod_config (guild_id, {columns}, created_at, updated_at)
                VALUES (?, {placeholders}, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    {updates}, updated_at = excluded.updated_at
                """,
                [guild_id] + values + [now, now],
            )
        else:
            conn.execute(
                """
                INSERT OR IGNORE INTO mod_config (guild_id, created_at, updated_at)
                VALUES (?, ?, ?)
                """,
                (guild_id, now, now),
            )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM mod_config WHERE guild_id = ?",
            (guild_id,),
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def get_mod_config(guild_id: int) -> dict[str, Any] | None:
    """Return moderation config for a guild, or None."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM mod_config WHERE guild_id = ?",
            (guild_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_mod_config(guild_id: int) -> bool:
    """Delete moderation config for a guild. Returns True if deleted."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            "DELETE FROM mod_config WHERE guild_id = ?",
            (guild_id,),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ── ng_words CRUD ────────────────────────────────────────────────────────────


def add_ng_word(guild_id: int, word: str) -> dict[str, Any]:
    """Add an NG word for a guild. Returns the word record."""
    now = _now_iso()
    conn = _get_conn()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO ng_words (guild_id, word, created_at)
            VALUES (?, ?, ?)
            """,
            (guild_id, word, now),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM ng_words WHERE guild_id = ? AND word = ?",
            (guild_id, word),
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def remove_ng_word(guild_id: int, word: str) -> bool:
    """Remove an NG word for a guild. Returns True if deleted."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            "DELETE FROM ng_words WHERE guild_id = ? AND word = ?",
            (guild_id, word),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def list_ng_words(guild_id: int) -> list[dict[str, Any]]:
    """Return all NG words for a guild."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM ng_words WHERE guild_id = ? ORDER BY word ASC",
            (guild_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def is_ng_word(guild_id: int, word: str) -> bool:
    """Check if a word is registered as NG for a guild."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT 1 FROM ng_words WHERE guild_id = ? AND word = ?",
            (guild_id, word),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


# ── moderation_keywords CRUD ──────────────────────────────────────────────────


def add_moderation_keyword(guild_id: int, keyword: str) -> dict[str, Any]:
    """Add a moderation keyword for a guild. Returns the keyword record."""
    now = _now_iso()
    conn = _get_conn()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO moderation_keywords (guild_id, keyword, created_at)
            VALUES (?, ?, ?)
            """,
            (guild_id, keyword, now),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM moderation_keywords WHERE guild_id = ? AND keyword = ?",
            (guild_id, keyword),
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def remove_moderation_keyword(guild_id: int, keyword: str) -> bool:
    """Remove a moderation keyword for a guild. Returns True if deleted."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            "DELETE FROM moderation_keywords WHERE guild_id = ? AND keyword = ?",
            (guild_id, keyword),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def list_moderation_keywords(guild_id: int) -> list[dict[str, Any]]:
    """Return all moderation keywords for a guild, ordered alphabetically."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM moderation_keywords WHERE guild_id = ? ORDER BY keyword ASC",
            (guild_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def is_moderation_keyword(guild_id: int, keyword: str) -> bool:
    """Check if a keyword is registered as a moderation keyword for a guild."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT 1 FROM moderation_keywords WHERE guild_id = ? AND keyword = ?",
            (guild_id, keyword),
        ).fetchone()
        return row is not None
    finally:
        conn.close()