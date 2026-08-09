"""Tests for moderation_keywords table in moderation_db.py."""

import shutil
from pathlib import Path

# Use a temporary DB for testing
TEST_DB_DIR = Path("/tmp/test_moderation_keywords_data")

# Force moderation_db to use the test directory BEFORE importing
import premium.moderation_db as mod_db

mod_db.DB_DIR = TEST_DB_DIR
mod_db.DB_PATH = TEST_DB_DIR / "moderation.db"

from premium.moderation_db import (
    add_moderation_keyword,
    remove_moderation_keyword,
    list_moderation_keywords,
    is_moderation_keyword,
    init_db,
)


def setup_module():
    """Remove any leftover test DB before starting."""
    if TEST_DB_DIR.exists():
        shutil.rmtree(TEST_DB_DIR)


def setup_function():
    """Ensure a clean DB before each test function (for pytest)."""
    if TEST_DB_DIR.exists():
        shutil.rmtree(TEST_DB_DIR)


def teardown_module():
    """Clean up test DB after tests."""
    if TEST_DB_DIR.exists():
        shutil.rmtree(TEST_DB_DIR)


# ── Table creation test ──────────────────────────────────────────────────────


def test_moderation_keywords_table_created():
    """Verify the moderation_keywords table is created by init_db()."""
    init_db()
    import sqlite3

    conn = sqlite3.connect(str(mod_db.DB_PATH))
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='moderation_keywords'"
        )
        assert cur.fetchone() is not None, "moderation_keywords table should exist"
    finally:
        conn.close()


# ── CRUD tests ───────────────────────────────────────────────────────────────


def test_add_and_list_moderation_keyword():
    init_db()
    rec = add_moderation_keyword(guild_id=100, keyword="badword")
    assert rec["guild_id"] == 100
    assert rec["keyword"] == "badword"
    assert rec["created_at"] is not None

    keywords = list_moderation_keywords(100)
    assert len(keywords) == 1
    assert keywords[0]["keyword"] == "badword"


def test_add_moderation_keyword_duplicate():
    init_db()
    add_moderation_keyword(guild_id=100, keyword="badword")
    add_moderation_keyword(guild_id=100, keyword="badword")  # should be silently ignored
    keywords = list_moderation_keywords(100)
    assert len(keywords) == 1


def test_add_moderation_keyword_same_keyword_different_guild():
    init_db()
    add_moderation_keyword(guild_id=100, keyword="badword")
    add_moderation_keyword(guild_id=200, keyword="badword")
    assert len(list_moderation_keywords(100)) == 1
    assert len(list_moderation_keywords(200)) == 1


def test_list_moderation_keywords_empty():
    init_db()
    assert list_moderation_keywords(100) == []


def test_list_moderation_keywords_ordered():
    init_db()
    add_moderation_keyword(guild_id=100, keyword="zeta")
    add_moderation_keyword(guild_id=100, keyword="alpha")
    add_moderation_keyword(guild_id=100, keyword="beta")
    keywords = list_moderation_keywords(100)
    assert [k["keyword"] for k in keywords] == ["alpha", "beta", "zeta"]


def test_is_moderation_keyword():
    init_db()
    add_moderation_keyword(guild_id=100, keyword="badword")
    assert is_moderation_keyword(100, "badword") is True
    assert is_moderation_keyword(100, "goodword") is False
    assert is_moderation_keyword(200, "badword") is False


def test_remove_moderation_keyword():
    init_db()
    add_moderation_keyword(guild_id=100, keyword="badword")
    assert is_moderation_keyword(100, "badword") is True
    assert remove_moderation_keyword(100, "badword") is True
    assert is_moderation_keyword(100, "badword") is False
    assert len(list_moderation_keywords(100)) == 0


def test_remove_moderation_keyword_nonexistent():
    init_db()
    assert remove_moderation_keyword(100, "nonexistent") is False


def test_remove_moderation_keyword_wrong_guild():
    init_db()
    add_moderation_keyword(guild_id=100, keyword="badword")
    assert remove_moderation_keyword(200, "badword") is False
    assert is_moderation_keyword(100, "badword") is True


# ── End-to-end test ──────────────────────────────────────────────────────────


def test_moderation_keywords_full_lifecycle():
    """Simulate a full lifecycle: add keywords → verify → list → remove."""
    init_db()

    # 1. Add keywords
    add_moderation_keyword(guild_id=500, keyword="spam")
    add_moderation_keyword(guild_id=500, keyword="badword")
    add_moderation_keyword(guild_id=500, keyword="inappropriate")
    assert len(list_moderation_keywords(500)) == 3

    # 2. Check specific keywords
    assert is_moderation_keyword(500, "spam") is True
    assert is_moderation_keyword(500, "good") is False

    # 3. Remove a keyword
    assert remove_moderation_keyword(500, "badword") is True
    assert len(list_moderation_keywords(500)) == 2
    assert is_moderation_keyword(500, "badword") is False

    # 4. Verify ordering
    keywords = list_moderation_keywords(500)
    assert [k["keyword"] for k in keywords] == ["inappropriate", "spam"]

    # 5. Different guild isolation
    add_moderation_keyword(guild_id=600, keyword="other")
    assert len(list_moderation_keywords(500)) == 2
    assert len(list_moderation_keywords(600)) == 1


if __name__ == "__main__":
    import traceback

    tests = [
        test_moderation_keywords_table_created,
        test_add_and_list_moderation_keyword,
        test_add_moderation_keyword_duplicate,
        test_add_moderation_keyword_same_keyword_different_guild,
        test_list_moderation_keywords_empty,
        test_list_moderation_keywords_ordered,
        test_is_moderation_keyword,
        test_remove_moderation_keyword,
        test_remove_moderation_keyword_nonexistent,
        test_remove_moderation_keyword_wrong_guild,
        test_moderation_keywords_full_lifecycle,
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