"""Premium database layer using SQLite.

Tables: premium_subscriptions, stripe_events, guild_premium_config
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "premium.db"


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
            CREATE TABLE IF NOT EXISTS premium_subscriptions (
                id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id                INTEGER NOT NULL UNIQUE,
                owner_id                INTEGER NOT NULL,
                stripe_customer_id      TEXT NOT NULL,
                stripe_subscription_id  TEXT NOT NULL,
                status                  TEXT NOT NULL DEFAULT 'active',
                current_period_start    TEXT,
                current_period_end      TEXT,
                canceled_at             TEXT,
                created_at              TEXT NOT NULL,
                updated_at              TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_premium_guild_id
                ON premium_subscriptions(guild_id);
            CREATE INDEX IF NOT EXISTS idx_premium_stripe_customer
                ON premium_subscriptions(stripe_customer_id);
            CREATE INDEX IF NOT EXISTS idx_premium_status
                ON premium_subscriptions(status);

            CREATE TABLE IF NOT EXISTS stripe_events (
                id              TEXT PRIMARY KEY,
                type            TEXT NOT NULL,
                processed_at    TEXT NOT NULL,
                status          TEXT NOT NULL DEFAULT 'processed'
            );

            CREATE TABLE IF NOT EXISTS guild_premium_config (
                guild_id                INTEGER PRIMARY KEY,
                welcome_embed_json      TEXT,
                xp_role_mappings        TEXT,
                xp_rate_multiplier      REAL DEFAULT 1.0,
                max_reminders           INTEGER DEFAULT 3,
                anonymous_polls         INTEGER DEFAULT 0,
                multiple_vote_polls     INTEGER DEFAULT 0
            );
        """)
        conn.commit()
    finally:
        conn.close()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── premium_subscriptions CRUD ──────────────────────────────────────────────


def create_premium_subscription(
    guild_id: int,
    owner_id: int,
    stripe_customer_id: str,
    stripe_subscription_id: str,
    status: str = "active",
    current_period_start: str | None = None,
    current_period_end: str | None = None,
) -> dict[str, Any]:
    """Insert a new premium subscription and return its record."""
    now = _now_iso()
    conn = _get_conn()
    try:
        conn.execute(
            """
            INSERT INTO premium_subscriptions
                (guild_id, owner_id, stripe_customer_id,
                 stripe_subscription_id, status,
                 current_period_start, current_period_end,
                 created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                owner_id,
                stripe_customer_id,
                stripe_subscription_id,
                status,
                current_period_start,
                current_period_end,
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM premium_subscriptions WHERE guild_id = ?",
            (guild_id,),
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def get_active_subscription(
    guild_id: int,
) -> dict[str, Any] | None:
    """Return the active subscription for a guild, or None."""
    conn = _get_conn()
    try:
        row = conn.execute(
            """
            SELECT * FROM premium_subscriptions
            WHERE guild_id = ? AND status IN ('active', 'past_due')
            """,
            (guild_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_subscription_status(
    subscription_id: int,
    status: str,
    **kwargs: Any,
) -> dict[str, Any] | None:
    """Update subscription status and optional fields. Returns updated record."""
    allowed_extra = {
        "stripe_subscription_id",
        "current_period_start",
        "current_period_end",
        "canceled_at",
    }
    sets = ["status = ?", "updated_at = ?"]
    params: list[Any] = [status, _now_iso()]

    for key in kwargs:
        if key in allowed_extra:
            sets.append(f"{key} = ?")
            params.append(kwargs[key])

    params.append(subscription_id)
    conn = _get_conn()
    try:
        conn.execute(
            f"UPDATE premium_subscriptions SET {', '.join(sets)} WHERE id = ?",
            params,
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM premium_subscriptions WHERE id = ?",
            (subscription_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ── stripe_events CRUD ──────────────────────────────────────────────────────


def record_stripe_event(
    event_id: str,
    event_type: str,
    status: str = "processed",
) -> dict[str, Any]:
    """Record a Stripe event for idempotency. Returns the event record."""
    now = _now_iso()
    conn = _get_conn()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO stripe_events (id, type, processed_at, status)
            VALUES (?, ?, ?, ?)
            """,
            (event_id, event_type, now, status),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM stripe_events WHERE id = ?", (event_id,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def get_stripe_event(event_id: str) -> dict[str, Any] | None:
    """Return a Stripe event record, or None."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM stripe_events WHERE id = ?", (event_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ── guild_premium_config CRUD ───────────────────────────────────────────────


def set_guild_premium_config(
    guild_id: int,
    **kwargs: Any,
) -> dict[str, Any]:
    """Upsert premium config for a guild. Returns the config record."""
    allowed_keys = {
        "welcome_embed_json",
        "xp_role_mappings",
        "xp_rate_multiplier",
        "max_reminders",
        "anonymous_polls",
        "multiple_vote_polls",
    }
    filtered = {k: v for k, v in kwargs.items() if k in allowed_keys}

    if not filtered:
        return get_guild_premium_config(guild_id)

    columns = ", ".join(filtered.keys())
    placeholders = ", ".join("?" for _ in filtered)
    updates = ", ".join(f"{k} = excluded.{k}" for k in filtered)
    values = list(filtered.values())

    conn = _get_conn()
    try:
        conn.execute(
            f"""
            INSERT INTO guild_premium_config (guild_id, {columns})
            VALUES (?, {placeholders})
            ON CONFLICT(guild_id) DO UPDATE SET
                {updates}
            """,
            [guild_id] + values,
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM guild_premium_config WHERE guild_id = ?",
            (guild_id,),
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def get_guild_premium_config(
    guild_id: int,
) -> dict[str, Any] | None:
    """Return premium config for a guild, or None."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM guild_premium_config WHERE guild_id = ?",
            (guild_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_guild_premium_config(guild_id: int) -> bool:
    """Delete premium config for a guild. Returns True if deleted."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            "DELETE FROM guild_premium_config WHERE guild_id = ?",
            (guild_id,),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()