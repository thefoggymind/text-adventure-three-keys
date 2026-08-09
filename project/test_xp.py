"""Tests for xp_db.py and xp_cog compilation."""

import os
import shutil
import time
from pathlib import Path

# Use a temporary DB for testing
TEST_DB_DIR = Path("/tmp/test_xp_data")

# Force xp_db to use the test directory BEFORE importing
import xp_db
xp_db.DB_DIR = TEST_DB_DIR
xp_db.DB_PATH = TEST_DB_DIR / "xp.db"

from xp_db import (
    XP_COOLDOWN,
    XP_MIN,
    XP_MAX,
    LEVEL_BASE,
    award_xp,
    get_leaderboard,
    get_or_create_user,
    get_rank,
    get_total_members,
    init_db,
)


def setup_module():
    """Remove any leftover test DB before starting."""
    if TEST_DB_DIR.exists():
        shutil.rmtree(TEST_DB_DIR)


def teardown_module():
    """Clean up test DB after tests."""
    if TEST_DB_DIR.exists():
        shutil.rmtree(TEST_DB_DIR)


# ---------------------------------------------------------------------------
# DB operation tests
# ---------------------------------------------------------------------------

def test_init_db():
    init_db()
    db_path = TEST_DB_DIR / "xp.db"
    assert db_path.exists(), "DB file should be created"
    # WAL mode should be set
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    cur = conn.execute("PRAGMA journal_mode")
    assert cur.fetchone()[0] == "wal"
    conn.close()


def test_get_or_create_user_creates_default():
    init_db()
    data = get_or_create_user(10001, 20001)
    assert data["user_id"] == 10001
    assert data["guild_id"] == 20001
    assert data["xp"] == 0
    assert data["level"] == 1
    assert data["last_message_at"] is None


def test_get_or_create_user_returns_existing():
    init_db()
    get_or_create_user(10002, 20002)
    # Second call should return the same row
    data = get_or_create_user(10002, 20002)
    assert data["user_id"] == 10002
    assert data["xp"] == 0
    assert data["level"] == 1


def test_award_xp_first_message():
    init_db()
    user_id = 10003
    guild_id = 20003
    new_xp, new_level, leveled_up = award_xp(user_id, guild_id)
    assert XP_MIN <= new_xp <= XP_MAX, f"XP {new_xp} should be in range [{XP_MIN}, {XP_MAX}]"
    assert new_level == 1, "First message should be level 1"
    assert leveled_up is False, "Level 1 should not trigger level-up"


def test_award_xp_cooldown():
    init_db()
    user_id = 10004
    guild_id = 20004

    # First message awards XP
    xp1, lvl1, _ = award_xp(user_id, guild_id)

    # Immediate second message should be blocked by cooldown
    xp2, lvl2, leveled_up = award_xp(user_id, guild_id)
    assert xp2 == xp1, "XP should not change during cooldown"
    assert leveled_up is False


def test_award_xp_level_up():
    init_db()
    user_id = 10005
    guild_id = 20005

    # Manually set xp to just below level 2 threshold
    # Level 2 requires 100 XP
    import sqlite3
    conn = sqlite3.connect(str(TEST_DB_DIR / "xp.db"))
    conn.execute(
        "INSERT INTO xp_data (user_id, guild_id, xp, level, last_message_at) "
        "VALUES (?, ?, ?, 1, NULL)",
        (user_id, guild_id, LEVEL_BASE - 1),
    )
    conn.commit()
    conn.close()

    # Override XP_MIN/MAX to guarantee level-up
    orig_min = xp_db.XP_MIN
    orig_max = xp_db.XP_MAX
    xp_db.XP_MIN = 100
    xp_db.XP_MAX = 100

    try:
        new_xp, new_level, leveled_up = award_xp(user_id, guild_id)
        assert new_xp >= LEVEL_BASE, f"XP {new_xp} should be >= {LEVEL_BASE}"
        assert new_level >= 2, f"Level {new_level} should be >= 2"
        assert leveled_up is True, "Should have leveled up"
    finally:
        xp_db.XP_MIN = orig_min
        xp_db.XP_MAX = orig_max


def test_get_rank():
    init_db()
    guild_id = 20006

    # Insert two users
    import sqlite3
    conn = sqlite3.connect(str(TEST_DB_DIR / "xp.db"))
    conn.execute(
        "INSERT INTO xp_data (user_id, guild_id, xp, level, last_message_at) "
        "VALUES (?, ?, ?, 1, NULL)",
        (1, guild_id, 50),
    )
    conn.execute(
        "INSERT INTO xp_data (user_id, guild_id, xp, level, last_message_at) "
        "VALUES (?, ?, ?, 1, NULL)",
        (2, guild_id, 150),
    )
    conn.commit()
    conn.close()

    data1 = get_rank(1, guild_id)
    assert data1 is not None
    assert data1["rank"] == 2  # Second place (user 2 has more XP)
    assert data1["total"] == 2

    data2 = get_rank(2, guild_id)
    assert data2 is not None
    assert data2["rank"] == 1  # First place


def test_get_rank_nonexistent():
    init_db()
    data = get_rank(99999, 99999)
    assert data is None


def test_get_leaderboard():
    init_db()
    guild_id = 20007

    # Insert 3 users
    import sqlite3
    conn = sqlite3.connect(str(TEST_DB_DIR / "xp.db"))
    conn.execute(
        "INSERT INTO xp_data (user_id, guild_id, xp, level, last_message_at) "
        "VALUES (?, ?, ?, 1, NULL)",
        (1, guild_id, 300),
    )
    conn.execute(
        "INSERT INTO xp_data (user_id, guild_id, xp, level, last_message_at) "
        "VALUES (?, ?, ?, 1, NULL)",
        (2, guild_id, 100),
    )
    conn.execute(
        "INSERT INTO xp_data (user_id, guild_id, xp, level, last_message_at) "
        "VALUES (?, ?, ?, 1, NULL)",
        (3, guild_id, 200),
    )
    conn.commit()
    conn.close()

    top2 = get_leaderboard(guild_id, limit=2)
    assert len(top2) == 2
    assert top2[0]["user_id"] == 1  # 300 XP
    assert top2[1]["user_id"] == 3  # 200 XP

    top_all = get_leaderboard(guild_id, limit=10)
    assert len(top_all) == 3


def test_get_leaderboard_empty():
    init_db()
    entries = get_leaderboard(99999)
    assert entries == []


def test_get_total_members():
    init_db()
    guild_id = 20008

    assert get_total_members(guild_id) == 0

    import sqlite3
    conn = sqlite3.connect(str(TEST_DB_DIR / "xp.db"))
    conn.execute(
        "INSERT INTO xp_data (user_id, guild_id, xp, level, last_message_at) "
        "VALUES (?, ?, ?, 1, NULL)",
        (1, guild_id, 0),
    )
    conn.execute(
        "INSERT INTO xp_data (user_id, guild_id, xp, level, last_message_at) "
        "VALUES (?, ?, ?, 1, NULL)",
        (2, guild_id, 0),
    )
    conn.commit()
    conn.close()

    assert get_total_members(guild_id) == 2


def test_calculate_level():
    """Test the _calculate_level helper directly."""
    from xp_db import _calculate_level

    assert _calculate_level(0) == 1
    assert _calculate_level(99) == 1
    assert _calculate_level(LEVEL_BASE) == 2  # 100
    assert _calculate_level(LEVEL_BASE * 4 - 1) == 2  # 399
    assert _calculate_level(LEVEL_BASE * 4) == 3  # 400
    assert _calculate_level(LEVEL_BASE * 9) == 4  # 900


# ---------------------------------------------------------------------------
# Python compilation check for xp_cog
# ---------------------------------------------------------------------------

def test_xp_cog_compiles():
    """Verify that xp_cog.py can be parsed without syntax errors."""
    import py_compile
    xp_cog_path = Path(__file__).parent / "xp_cog.py"
    py_compile.compile(str(xp_cog_path), doraise=True)


def test_xp_db_compiles():
    """Verify that xp_db.py can be parsed without syntax errors."""
    import py_compile
    xp_db_path = Path(__file__).parent / "xp_db.py"
    py_compile.compile(str(xp_db_path), doraise=True)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import traceback

    tests = [
        test_init_db,
        test_get_or_create_user_creates_default,
        test_get_or_create_user_returns_existing,
        test_award_xp_first_message,
        test_award_xp_cooldown,
        test_award_xp_level_up,
        test_get_rank,
        test_get_rank_nonexistent,
        test_get_leaderboard,
        test_get_leaderboard_empty,
        test_get_total_members,
        test_calculate_level,
        test_xp_cog_compiles,
        test_xp_db_compiles,
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