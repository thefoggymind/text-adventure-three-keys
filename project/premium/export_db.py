"""Database layer for data export (Phase4).

Provides read-only access to all bot databases for CSV/JSON export.
"""

import sqlite3
from pathlib import Path

# Database paths (mirror actual DB locations)
_BASE_DIR = Path(__file__).resolve().parent.parent / "data"
XP_DB_PATH = _BASE_DIR / "xp.db"
REMINDER_DB_PATH = _BASE_DIR / "reminders.db"
MOD_DB_PATH = _BASE_DIR / "moderation.db"
PREMIUM_DB_PATH = _BASE_DIR / "premium.db"


def _connect(db_path: Path) -> sqlite3.Connection:
    """Open a read-only connection to the given database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def export_xp_data(guild_id: int) -> list[dict]:
    """Export all XP data for a guild.

    Returns a list of dicts with keys: user_id, guild_id, xp, level.
    """
    conn = _connect(XP_DB_PATH)
    try:
        cur = conn.execute(
            "SELECT user_id, guild_id, xp, level FROM xp_data WHERE guild_id = ?",
            (guild_id,),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def export_reminders(guild_id: int) -> list[dict]:
    """Export all reminders for a guild.

    Returns a list of dicts with keys: id, user_id, channel_id, guild_id,
    message, remind_at, created_at, triggered.
    """
    conn = _connect(REMINDER_DB_PATH)
    try:
        cur = conn.execute(
            "SELECT id, user_id, channel_id, guild_id, message, "
            "remind_at, created_at, triggered "
            "FROM reminders WHERE guild_id = ?",
            (guild_id,),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def export_moderation_config(guild_id: int) -> dict:
    """Export moderation configuration for a guild.

    Returns a dict with keys: guild_id, keywords (list), spam_threshold,
    auto_mod_enabled. If no config exists, returns a default config.
    """
    conn = _connect(MOD_DB_PATH)
    try:
        # Fetch moderation keywords
        cur = conn.execute(
            "SELECT keyword FROM moderation_keywords WHERE guild_id = ?",
            (guild_id,),
        )
        keywords = [row["keyword"] for row in cur.fetchall()]

        # Fetch config
        cur = conn.execute(
            "SELECT spam_threshold, keyword_filter_enabled, spam_detection_enabled "
            "FROM mod_config WHERE guild_id = ?",
            (guild_id,),
        )
        row = cur.fetchone()
        if row is None:
            return {
                "guild_id": guild_id,
                "keywords": keywords,
                "spam_threshold": 3,
                "auto_mod_enabled": False,
            }
        auto_mod = bool(row["keyword_filter_enabled"]) or bool(row["spam_detection_enabled"])
        return {
            "guild_id": guild_id,
            "keywords": keywords,
            "spam_threshold": row["spam_threshold"],
            "auto_mod_enabled": auto_mod,
        }
    finally:
        conn.close()


def export_premium_info(guild_id: int) -> dict | None:
    """Export premium subscription info for a guild.

    Returns a dict with keys: guild_id, owner_id, status,
    current_period_start, current_period_end, or None if not found.
    """
    conn = _connect(PREMIUM_DB_PATH)
    try:
        cur = conn.execute(
            "SELECT guild_id, owner_id, status, "
            "current_period_start, current_period_end "
            "FROM premium_subscriptions WHERE guild_id = ?",
            (guild_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()