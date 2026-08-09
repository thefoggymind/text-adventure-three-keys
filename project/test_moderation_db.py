"""Tests for moderation_db.py."""

import shutil
from pathlib import Path

# Use a temporary DB for testing
TEST_DB_DIR = Path("/tmp/test_moderation_data")

# Force moderation_db to use the test directory BEFORE importing
import premium.moderation_db as mod_db

mod_db.DB_DIR = TEST_DB_DIR
mod_db.DB_PATH = TEST_DB_DIR / "moderation.db"

from premium.moderation_db import (
    add_ng_word,
    remove_ng_word,
    list_ng_words,
    is_ng_word,
    set_mod_config,
    get_mod_config,
    delete_mod_config,
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


# ── init_db tests ────────────────────────────────────────────────────────────


def test_init_db():
    init_db()
    db_path = TEST_DB_DIR / "moderation.db"
    assert db_path.exists(), "DB file should be created"
    import sqlite3

    conn = sqlite3.connect(str(db_path))
    cur = conn.execute("PRAGMA journal_mode")
    assert cur.fetchone()[0] == "wal"
    conn.close()


# ── mod_config tests ─────────────────────────────────────────────────────────


def test_set_and_get_mod_config():
    init_db()
    config = set_mod_config(
        guild_id=100,
        keyword_filter_enabled=1,
        spam_detection_enabled=1,
        spam_threshold=5,
        spam_window_seconds=10,
        max_mentions=3,
        max_links=2,
        mod_log_channel_id=123456,
    )
    assert config["guild_id"] == 100
    assert config["keyword_filter_enabled"] == 1
    assert config["spam_detection_enabled"] == 1
    assert config["spam_threshold"] == 5
    assert config["spam_window_seconds"] == 10
    assert config["max_mentions"] == 3
    assert config["max_links"] == 2
    assert config["mod_log_channel_id"] == 123456
    assert config["created_at"] is not None
    assert config["updated_at"] is not None

    fetched = get_mod_config(100)
    assert fetched is not None
    assert fetched["spam_threshold"] == 5


def test_get_mod_config_defaults():
    """Verify defaults are applied when only guild_id is given."""
    init_db()
    config = set_mod_config(guild_id=100)
    assert config["guild_id"] == 100
    assert config["keyword_filter_enabled"] == 1
    assert config["spam_detection_enabled"] == 1
    assert config["spam_threshold"] == 3
    assert config["spam_window_seconds"] == 5
    assert config["max_mentions"] == 5
    assert config["max_links"] == 3
    assert config["mod_log_channel_id"] is None


def test_get_mod_config_nonexistent():
    init_db()
    assert get_mod_config(99999) is None


def test_set_mod_config_partial_update():
    init_db()
    set_mod_config(guild_id=100, keyword_filter_enabled=0)
    set_mod_config(guild_id=100, spam_threshold=10, max_links=0)
    config = get_mod_config(100)
    assert config is not None
    assert config["keyword_filter_enabled"] == 0
    assert config["spam_threshold"] == 10
    assert config["max_links"] == 0
    assert config["spam_detection_enabled"] == 1  # unchanged default


def test_set_mod_config_invalid_keys_ignored():
    init_db()
    config = set_mod_config(guild_id=100, invalid_key="ignored")
    assert config is not None
    assert config["guild_id"] == 100
    assert config["keyword_filter_enabled"] == 1


def test_delete_mod_config():
    init_db()
    set_mod_config(guild_id=100)
    assert get_mod_config(100) is not None
    assert delete_mod_config(100) is True
    assert get_mod_config(100) is None


def test_delete_mod_config_nonexistent():
    init_db()
    assert delete_mod_config(99999) is False


# ── ng_words tests ───────────────────────────────────────────────────────────


def test_add_and_list_ng_words():
    init_db()
    rec = add_ng_word(guild_id=100, word="badword")
    assert rec["guild_id"] == 100
    assert rec["word"] == "badword"
    assert rec["created_at"] is not None

    words = list_ng_words(100)
    assert len(words) == 1
    assert words[0]["word"] == "badword"


def test_add_ng_word_duplicate():
    init_db()
    add_ng_word(guild_id=100, word="badword")
    add_ng_word(guild_id=100, word="badword")  # should be silently ignored
    words = list_ng_words(100)
    assert len(words) == 1


def test_add_ng_word_same_word_different_guild():
    init_db()
    add_ng_word(guild_id=100, word="badword")
    add_ng_word(guild_id=200, word="badword")
    assert len(list_ng_words(100)) == 1
    assert len(list_ng_words(200)) == 1


def test_list_ng_words_empty():
    init_db()
    assert list_ng_words(100) == []


def test_list_ng_words_ordered():
    init_db()
    add_ng_word(guild_id=100, word="zeta")
    add_ng_word(guild_id=100, word="alpha")
    add_ng_word(guild_id=100, word="beta")
    words = list_ng_words(100)
    assert [w["word"] for w in words] == ["alpha", "beta", "zeta"]


def test_is_ng_word():
    init_db()
    add_ng_word(guild_id=100, word="badword")
    assert is_ng_word(100, "badword") is True
    assert is_ng_word(100, "goodword") is False
    assert is_ng_word(200, "badword") is False


def test_remove_ng_word():
    init_db()
    add_ng_word(guild_id=100, word="badword")
    assert is_ng_word(100, "badword") is True
    assert remove_ng_word(100, "badword") is True
    assert is_ng_word(100, "badword") is False
    assert len(list_ng_words(100)) == 0


def test_remove_ng_word_nonexistent():
    init_db()
    assert remove_ng_word(100, "nonexistent") is False


def test_remove_ng_word_wrong_guild():
    init_db()
    add_ng_word(guild_id=100, word="badword")
    assert remove_ng_word(200, "badword") is False
    assert is_ng_word(100, "badword") is True


# ── End-to-end test ──────────────────────────────────────────────────────────


def test_moderation_full_lifecycle():
    """Simulate a full moderation lifecycle: config → add words → verify → delete."""
    init_db()

    # 1. Set moderation config
    config = set_mod_config(
        guild_id=500,
        keyword_filter_enabled=1,
        spam_detection_enabled=1,
        spam_threshold=5,
        spam_window_seconds=10,
        max_mentions=3,
        max_links=2,
        mod_log_channel_id=999,
    )
    assert config["keyword_filter_enabled"] == 1
    assert config["mod_log_channel_id"] == 999

    # 2. Add NG words
    add_ng_word(guild_id=500, word="spam")
    add_ng_word(guild_id=500, word="badword")
    add_ng_word(guild_id=500, word="ngword")
    assert len(list_ng_words(500)) == 3

    # 3. Check specific words
    assert is_ng_word(500, "spam") is True
    assert is_ng_word(500, "good") is False

    # 4. Remove a word
    assert remove_ng_word(500, "badword") is True
    assert len(list_ng_words(500)) == 2
    assert is_ng_word(500, "badword") is False

    # 5. Update config
    set_mod_config(guild_id=500, spam_threshold=10, keyword_filter_enabled=0)
    config = get_mod_config(500)
    assert config is not None
    assert config["spam_threshold"] == 10
    assert config["keyword_filter_enabled"] == 0
    assert config["spam_detection_enabled"] == 1  # unchanged

    # 6. Delete config (words remain)
    assert delete_mod_config(500) is True
    assert get_mod_config(500) is None
    assert len(list_ng_words(500)) == 2  # words survive config deletion


if __name__ == "__main__":
    import traceback

    tests = [
        test_init_db,
        test_set_and_get_mod_config,
        test_get_mod_config_defaults,
        test_get_mod_config_nonexistent,
        test_set_mod_config_partial_update,
        test_set_mod_config_invalid_keys_ignored,
        test_delete_mod_config,
        test_delete_mod_config_nonexistent,
        test_add_and_list_ng_words,
        test_add_ng_word_duplicate,
        test_add_ng_word_same_word_different_guild,
        test_list_ng_words_empty,
        test_list_ng_words_ordered,
        test_is_ng_word,
        test_remove_ng_word,
        test_remove_ng_word_nonexistent,
        test_remove_ng_word_wrong_guild,
        test_moderation_full_lifecycle,
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