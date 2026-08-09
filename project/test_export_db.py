"""Tests for premium/export_db.py data export functions."""

import os
import shutil
import sqlite3
from pathlib import Path

# Use a temporary DB for testing
TEST_DB_DIR = Path("/tmp/test_export_data")

# Force export_db to use the test directory BEFORE importing
import premium.export_db

premium.export_db.XP_DB_PATH = TEST_DB_DIR / "xp.db"
premium.export_db.REMINDER_DB_PATH = TEST_DB_DIR / "reminders.db"
premium.export_db.MOD_DB_PATH = TEST_DB_DIR / "moderation.db"
premium.export_db.PREMIUM_DB_PATH = TEST_DB_DIR / "premium.db"

from premium.export_db import (
    export_xp_data,
    export_reminders,
    export_moderation_config,
    export_premium_info,
)


def setup_module():
    """Remove any leftover test DB before starting."""
    if TEST_DB_DIR.exists():
        shutil.rmtree(TEST_DB_DIR)


def teardown_module():
    """Clean up test DB after tests."""
    if TEST_DB_DIR.exists():
        shutil.rmtree(TEST_DB_DIR)


def _create_xp_db():
    """Create and populate the test XP database."""
    TEST_DB_DIR.mkdir(parents=True, exist_ok=True)
    # Remove existing DB to ensure clean state
    (TEST_DB_DIR / "xp.db").unlink(missing_ok=True)
    conn = sqlite3.connect(str(TEST_DB_DIR / "xp.db"))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS xp_data ("
        "user_id INTEGER NOT NULL, "
        "guild_id INTEGER NOT NULL, "
        "xp INTEGER NOT NULL DEFAULT 0, "
        "level INTEGER NOT NULL DEFAULT 1, "
        "last_message_at REAL, "
        "PRIMARY KEY (user_id, guild_id))"
    )
    conn.execute(
        "INSERT OR REPLACE INTO xp_data (user_id, guild_id, xp, level) VALUES (?, ?, ?, ?)",
        (1001, 2001, 150, 2),
    )
    conn.execute(
        "INSERT OR REPLACE INTO xp_data (user_id, guild_id, xp, level) VALUES (?, ?, ?, ?)",
        (1002, 2001, 320, 3),
    )
    conn.execute(
        "INSERT OR REPLACE INTO xp_data (user_id, guild_id, xp, level) VALUES (?, ?, ?, ?)",
        (1003, 2001, 50, 1),
    )
    # Different guild
    conn.execute(
        "INSERT OR REPLACE INTO xp_data (user_id, guild_id, xp, level) VALUES (?, ?, ?, ?)",
        (2001, 9999, 500, 5),
    )
    conn.commit()
    conn.close()


def _create_reminders_db():
    """Create and populate the test reminders database."""
    TEST_DB_DIR.mkdir(parents=True, exist_ok=True)
    (TEST_DB_DIR / "reminders.db").unlink(missing_ok=True)
    conn = sqlite3.connect(str(TEST_DB_DIR / "reminders.db"))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS reminders ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "user_id INTEGER NOT NULL, "
        "channel_id INTEGER NOT NULL, "
        "guild_id INTEGER NOT NULL DEFAULT 0, "
        "message TEXT NOT NULL, "
        "remind_at REAL NOT NULL, "
        "created_at REAL NOT NULL, "
        "triggered INTEGER NOT NULL DEFAULT 0)"
    )
    conn.execute(
        "INSERT INTO reminders (user_id, channel_id, guild_id, message, remind_at, created_at, triggered) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1001, 3001, 2001, "Hello", 1000.0, 500.0, 0),
    )
    conn.execute(
        "INSERT INTO reminders (user_id, channel_id, guild_id, message, remind_at, created_at, triggered) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1002, 3001, 2001, "World", 2000.0, 600.0, 1),
    )
    # Different guild
    conn.execute(
        "INSERT INTO reminders (user_id, channel_id, guild_id, message, remind_at, created_at, triggered) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (2001, 3001, 9999, "Other", 1500.0, 700.0, 0),
    )
    conn.commit()
    conn.close()


def _create_moderation_db():
    """Create and populate the test moderation database."""
    TEST_DB_DIR.mkdir(parents=True, exist_ok=True)
    (TEST_DB_DIR / "moderation.db").unlink(missing_ok=True)
    conn = sqlite3.connect(str(TEST_DB_DIR / "moderation.db"))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS mod_config ("
        "guild_id INTEGER PRIMARY KEY, "
        "keyword_filter_enabled INTEGER NOT NULL DEFAULT 1, "
        "spam_detection_enabled INTEGER NOT NULL DEFAULT 1, "
        "spam_threshold INTEGER NOT NULL DEFAULT 3, "
        "spam_window_seconds INTEGER NOT NULL DEFAULT 5, "
        "max_mentions INTEGER NOT NULL DEFAULT 5, "
        "max_links INTEGER NOT NULL DEFAULT 3, "
        "mod_log_channel_id INTEGER, "
        "created_at TEXT NOT NULL, "
        "updated_at TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS moderation_keywords ("
        "guild_id INTEGER NOT NULL, "
        "keyword TEXT NOT NULL, "
        "created_at TEXT NOT NULL, "
        "PRIMARY KEY (guild_id, keyword))"
    )
    # Insert mod_config for guild 2001
    conn.execute(
        "INSERT OR REPLACE INTO mod_config (guild_id, keyword_filter_enabled, spam_detection_enabled, "
        "spam_threshold, spam_window_seconds, max_mentions, max_links, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (2001, 1, 0, 5, 5, 5, 3, "2026-01-01", "2026-01-01"),
    )
    # Insert keywords for guild 2001
    conn.execute(
        "INSERT OR REPLACE INTO moderation_keywords (guild_id, keyword, created_at) VALUES (?, ?, ?)",
        (2001, "badword1", "2026-01-01"),
    )
    conn.execute(
        "INSERT OR REPLACE INTO moderation_keywords (guild_id, keyword, created_at) VALUES (?, ?, ?)",
        (2001, "badword2", "2026-01-01"),
    )
    # Insert config for guild 9999 (all features disabled)
    conn.execute(
        "INSERT OR REPLACE INTO mod_config (guild_id, keyword_filter_enabled, spam_detection_enabled, "
        "spam_threshold, spam_window_seconds, max_mentions, max_links, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (9999, 0, 0, 3, 5, 5, 3, "2026-01-01", "2026-01-01"),
    )
    conn.execute(
        "INSERT OR REPLACE INTO moderation_keywords (guild_id, keyword, created_at) VALUES (?, ?, ?)",
        (9999, "spamword", "2026-01-01"),
    )
    conn.commit()
    conn.close()


def _create_premium_db():
    """Create and populate the test premium database."""
    TEST_DB_DIR.mkdir(parents=True, exist_ok=True)
    (TEST_DB_DIR / "premium.db").unlink(missing_ok=True)
    conn = sqlite3.connect(str(TEST_DB_DIR / "premium.db"))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS premium_subscriptions ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "guild_id INTEGER NOT NULL UNIQUE, "
        "owner_id INTEGER NOT NULL, "
        "stripe_customer_id TEXT NOT NULL, "
        "stripe_subscription_id TEXT NOT NULL, "
        "status TEXT NOT NULL DEFAULT 'active', "
        "current_period_start TEXT, "
        "current_period_end TEXT, "
        "canceled_at TEXT, "
        "created_at TEXT NOT NULL, "
        "updated_at TEXT NOT NULL)"
    )
    conn.execute(
        "INSERT OR REPLACE INTO premium_subscriptions (guild_id, owner_id, stripe_customer_id, "
        "stripe_subscription_id, status, current_period_start, current_period_end, "
        "created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (2001, 1001, "cus_abc", "sub_xyz", "active",
         "2026-08-01T00:00:00+00:00", "2026-09-01T00:00:00+00:00",
         "2026-08-01T00:00:00+00:00", "2026-08-01T00:00:00+00:00"),
    )
    conn.execute(
        "INSERT OR REPLACE INTO premium_subscriptions (guild_id, owner_id, stripe_customer_id, "
        "stripe_subscription_id, status, current_period_start, current_period_end, "
        "created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (9999, 2001, "cus_xyz", "sub_abc", "canceled",
         "2026-07-01T00:00:00+00:00", "2026-08-01T00:00:00+00:00",
         "2026-07-01T00:00:00+00:00", "2026-07-15T00:00:00+00:00"),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Tests: export_xp_data
# ---------------------------------------------------------------------------

def test_export_xp_data_returns_all_users_in_guild():
    _create_xp_db()
    result = export_xp_data(2001)
    assert len(result) == 3, f"Expected 3 users, got {len(result)}"
    # Check contents
    xp_map = {r["user_id"]: r for r in result}
    assert xp_map[1001]["xp"] == 150
    assert xp_map[1001]["level"] == 2
    assert xp_map[1002]["xp"] == 320
    assert xp_map[1002]["level"] == 3
    assert xp_map[1003]["xp"] == 50
    assert xp_map[1003]["level"] == 1


def test_export_xp_data_other_guild_not_included():
    _create_xp_db()
    result = export_xp_data(2001)
    guild_ids = {r["guild_id"] for r in result}
    assert guild_ids == {2001}


def test_export_xp_data_empty_guild():
    _create_xp_db()
    result = export_xp_data(7777)
    assert result == []


def test_export_xp_data_columns():
    _create_xp_db()
    result = export_xp_data(2001)
    assert len(result) > 0
    expected_keys = {"user_id", "guild_id", "xp", "level"}
    assert set(result[0].keys()) == expected_keys


# ---------------------------------------------------------------------------
# Tests: export_reminders
# ---------------------------------------------------------------------------

def test_export_reminders_returns_all_for_guild():
    _create_reminders_db()
    result = export_reminders(2001)
    assert len(result) == 2, f"Expected 2 reminders, got {len(result)}"
    messages = {r["message"] for r in result}
    assert messages == {"Hello", "World"}


def test_export_reminders_columns():
    _create_reminders_db()
    result = export_reminders(2001)
    assert len(result) > 0
    expected_keys = {"id", "user_id", "channel_id", "guild_id", "message",
                     "remind_at", "created_at", "triggered"}
    assert set(result[0].keys()) == expected_keys


def test_export_reminders_other_guild_not_included():
    _create_reminders_db()
    result = export_reminders(2001)
    guild_ids = {r["guild_id"] for r in result}
    assert guild_ids == {2001}


def test_export_reminders_empty_guild():
    _create_reminders_db()
    result = export_reminders(7777)
    assert result == []


def test_export_reminders_triggered_status():
    _create_reminders_db()
    result = export_reminders(2001)
    triggered = {r["message"]: r["triggered"] for r in result}
    assert triggered["Hello"] == 0
    assert triggered["World"] == 1


# ---------------------------------------------------------------------------
# Tests: export_moderation_config
# ---------------------------------------------------------------------------

def test_export_moderation_config_returns_config():
    _create_moderation_db()
    result = export_moderation_config(2001)
    assert result["guild_id"] == 2001
    assert result["spam_threshold"] == 5
    assert result["auto_mod_enabled"] is True  # keyword_filter_enabled=1
    assert sorted(result["keywords"]) == ["badword1", "badword2"]


def test_export_moderation_config_auto_mod_disabled():
    """When both filter and detection are disabled, auto_mod_enabled=False."""
    _create_moderation_db()
    result = export_moderation_config(9999)
    assert result["guild_id"] == 9999
    assert result["auto_mod_enabled"] is False
    assert result["keywords"] == ["spamword"]
    assert result["spam_threshold"] == 3


def test_export_moderation_config_no_config_defaults():
    """Guild with no config row should return defaults."""
    _create_moderation_db()
    result = export_moderation_config(5555)
    assert result["guild_id"] == 5555
    assert result["keywords"] == []
    assert result["spam_threshold"] == 3
    assert result["auto_mod_enabled"] is False


def test_export_moderation_config_no_keywords():
    """Guild with config but no keywords should return empty list."""
    _create_moderation_db()
    # Guild 7777: has config but no keywords
    conn = sqlite3.connect(str(TEST_DB_DIR / "moderation.db"))
    conn.execute(
        "INSERT OR REPLACE INTO mod_config (guild_id, keyword_filter_enabled, spam_detection_enabled, "
        "spam_threshold, spam_window_seconds, max_mentions, max_links, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (7777, 1, 1, 10, 5, 5, 3, "2026-01-01", "2026-01-01"),
    )
    conn.commit()
    conn.close()
    result = export_moderation_config(7777)
    assert result["keywords"] == []
    assert result["spam_threshold"] == 10
    assert result["auto_mod_enabled"] is True


# ---------------------------------------------------------------------------
# Tests: export_premium_info
# ---------------------------------------------------------------------------

def test_export_premium_info_returns_subscription():
    _create_premium_db()
    result = export_premium_info(2001)
    assert result is not None
    assert result["guild_id"] == 2001
    assert result["owner_id"] == 1001
    assert result["status"] == "active"
    assert result["current_period_start"] == "2026-08-01T00:00:00+00:00"
    assert result["current_period_end"] == "2026-09-01T00:00:00+00:00"


def test_export_premium_info_canceled():
    _create_premium_db()
    result = export_premium_info(9999)
    assert result is not None
    assert result["status"] == "canceled"


def test_export_premium_info_not_found():
    _create_premium_db()
    result = export_premium_info(5555)
    assert result is None


def test_export_premium_info_columns():
    _create_premium_db()
    result = export_premium_info(2001)
    expected_keys = {"guild_id", "owner_id", "status",
                     "current_period_start", "current_period_end"}
    assert set(result.keys()) == expected_keys


# ---------------------------------------------------------------------------
# Compilation check
# ---------------------------------------------------------------------------

def test_export_db_compiles():
    import py_compile
    path = Path(__file__).parent / "premium" / "export_db.py"
    py_compile.compile(str(path), doraise=True)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import traceback

    tests = [
        test_export_xp_data_returns_all_users_in_guild,
        test_export_xp_data_other_guild_not_included,
        test_export_xp_data_empty_guild,
        test_export_xp_data_columns,
        test_export_reminders_returns_all_for_guild,
        test_export_reminders_columns,
        test_export_reminders_other_guild_not_included,
        test_export_reminders_empty_guild,
        test_export_reminders_triggered_status,
        test_export_moderation_config_returns_config,
        test_export_moderation_config_auto_mod_disabled,
        test_export_moderation_config_no_config_defaults,
        test_export_moderation_config_no_keywords,
        test_export_premium_info_returns_subscription,
        test_export_premium_info_canceled,
        test_export_premium_info_not_found,
        test_export_premium_info_columns,
        test_export_db_compiles,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            setup_module()
            test()
            print(f"  ✅ {test.__name__}")
            passed += 1
        except Exception:
            print(f"  ❌ {test.__name__}")
            traceback.print_exc()
            failed += 1
        finally:
            teardown_module()

    print(f"\n{'='*40}")
    print(f"結果: {passed} passed / {failed} failed / {len(tests)} total")
    if failed:
        print("❌  FAIL")
    else:
        print("✅  ALL PASSED")