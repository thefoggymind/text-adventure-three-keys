"""Tests for poll_db.py."""

import json
import os
import shutil
import time
from pathlib import Path

# Use a temporary DB for testing
TEST_DB_DIR = Path("/tmp/test_poll_data")

# Force poll_db to use the test directory BEFORE importing
import poll_db
poll_db.DB_DIR = TEST_DB_DIR
poll_db.DB_PATH = TEST_DB_DIR / "polls.db"

from poll_db import (
    EMOJI_OPTIONS,
    cast_vote,
    create_poll,
    get_active_polls,
    get_poll,
    get_poll_by_message,
    get_results,
    get_total_voters,
    has_expired,
    init_db,
    set_message_id,
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


def test_init_db():
    init_db()
    db_path = TEST_DB_DIR / "polls.db"
    assert db_path.exists(), "DB file should be created"
    # WAL mode should be set
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    cur = conn.execute("PRAGMA journal_mode")
    assert cur.fetchone()[0] == "wal"
    conn.close()


def test_create_and_get_poll():
    init_db()
    pid = create_poll(
        guild_id=100,
        channel_id=200,
        question="Best color?",
        options=["Red", "Blue", "Green"],
        creator_id=300,
    )
    assert isinstance(pid, int) and pid > 0, f"Expected positive int, got {pid}"

    poll = get_poll(pid)
    assert poll is not None
    assert poll["guild_id"] == 100
    assert poll["channel_id"] == 200
    assert poll["question"] == "Best color?"
    assert poll["options"] == ["Red", "Blue", "Green"]
    assert poll["creator_id"] == 300
    assert poll["anonymous"] is False
    assert poll["duration_seconds"] is None
    assert poll["message_id"] is None
    assert isinstance(poll["created_at"], float)


def test_create_poll_with_duration():
    init_db()
    pid = create_poll(
        guild_id=100,
        channel_id=200,
        question="Limited poll?",
        options=["Yes", "No"],
        creator_id=300,
        duration_seconds=3600,
        anonymous=True,
    )
    poll = get_poll(pid)
    assert poll is not None
    assert poll["duration_seconds"] == 3600
    assert poll["anonymous"] is True


def test_set_message_id():
    init_db()
    pid = create_poll(100, 200, "Test", ["A", "B"], 300)
    set_message_id(pid, 98765)
    poll = get_poll(pid)
    assert poll is not None
    assert poll["message_id"] == 98765


def test_get_poll_by_message():
    init_db()
    pid = create_poll(100, 200, "Find me", ["X", "Y"], 300)
    set_message_id(pid, 55555)
    poll = get_poll_by_message(55555)
    assert poll is not None
    assert poll["id"] == pid
    # Non-existent message
    assert get_poll_by_message(99999) is None


def test_get_poll_nonexistent():
    init_db()
    poll = get_poll(99999)
    assert poll is None


def test_cast_vote_and_get_results():
    init_db()
    pid = create_poll(100, 200, "Vote test", ["A", "B", "C"], 300)

    # Initial results should be empty
    assert get_results(pid) == {}

    # Cast votes
    cast_vote(pid, 1, 0)  # User 1 votes for option 0 (A)
    cast_vote(pid, 2, 1)  # User 2 votes for option 1 (B)
    cast_vote(pid, 3, 0)  # User 3 votes for option 0 (A)

    results = get_results(pid)
    assert results == {0: 2, 1: 1}, f"Expected {{0: 2, 1: 1}}, got {results}"


def test_cast_vote_update():
    init_db()
    pid = create_poll(100, 200, "Change vote", ["A", "B"], 300)

    cast_vote(pid, 1, 0)  # Vote for A
    cast_vote(pid, 1, 1)  # Change to B

    results = get_results(pid)
    assert results == {1: 1}, "Vote should be updated, not duplicated"


def test_get_total_voters():
    init_db()
    pid = create_poll(100, 200, "Voter count", ["A", "B"], 300)
    assert get_total_voters(pid) == 0
    cast_vote(pid, 1, 0)
    assert get_total_voters(pid) == 1
    cast_vote(pid, 2, 1)
    assert get_total_voters(pid) == 2


def test_get_active_polls():
    init_db()
    guild_id = 100

    # Active poll (no duration = never expires)
    pid1 = create_poll(guild_id, 200, "Never expires", ["A", "B"], 300)

    # Active poll (future expiration)
    pid2 = create_poll(
        guild_id, 200, "Future expiry", ["A", "B"], 300,
        duration_seconds=3600,
    )

    # Expired poll: use a deliberately ancient created_at by manipulating
    # the DB directly so the poll is definitely expired regardless of timing.
    import sqlite3
    expired_pid = create_poll(
        guild_id, 200, "Expired", ["A", "B"], 300,
        duration_seconds=10,
    )
    conn = sqlite3.connect(str(poll_db.DB_PATH))
    conn.execute(
        "UPDATE polls SET created_at = ? WHERE id = ?",
        (time.time() - 60, expired_pid),
    )
    conn.commit()
    conn.close()

    active = get_active_polls(guild_id)
    active_ids = {p["id"] for p in active}
    assert pid1 in active_ids, "No-duration poll should be active"
    assert pid2 in active_ids, "Future poll should be active"
    assert expired_pid not in active_ids, "Expired poll should not be active"


def test_get_active_polls_other_guild():
    init_db()
    create_poll(100, 200, "Guild 100", ["A", "B"], 300)
    create_poll(200, 200, "Guild 200", ["A", "B"], 300)
    active = get_active_polls(100)
    assert len(active) == 1
    assert active[0]["question"] == "Guild 100"


def test_has_expired():
    now = time.time()
    poll_no_dur = {"created_at": now - 3600, "duration_seconds": None}
    assert has_expired(poll_no_dur) is False, "No duration = never expires"

    poll_not_expired = {"created_at": now, "duration_seconds": 3600}
    assert has_expired(poll_not_expired) is False

    poll_expired = {"created_at": now - 10, "duration_seconds": 1}
    assert has_expired(poll_expired) is True


def test_emoji_options_count():
    assert len(EMOJI_OPTIONS) == 10, "Should have exactly 10 emoji options"


def test_all_operations_e2e():
    """End-to-end: create → set message → vote → get results → active check."""
    init_db()
    pid = create_poll(500, 600, "E2E test", ["Option1", "Option2"], 700)
    assert pid > 0

    set_message_id(pid, 123456)
    poll = get_poll(pid)
    assert poll is not None
    assert poll["message_id"] == 123456

    cast_vote(pid, 1001, 0)
    cast_vote(pid, 1002, 0)
    cast_vote(pid, 1003, 1)
    assert get_total_voters(pid) == 3
    results = get_results(pid)
    assert results == {0: 2, 1: 1}

    retrieved = get_poll_by_message(123456)
    assert retrieved is not None
    assert retrieved["id"] == pid

    active = get_active_polls(500)
    assert any(p["id"] == pid for p in active)


if __name__ == "__main__":
    import traceback

    tests = [
        test_init_db,
        test_create_and_get_poll,
        test_create_poll_with_duration,
        test_set_message_id,
        test_get_poll_by_message,
        test_get_poll_nonexistent,
        test_cast_vote_and_get_results,
        test_cast_vote_update,
        test_get_total_voters,
        test_get_active_polls,
        test_get_active_polls_other_guild,
        test_has_expired,
        test_emoji_options_count,
        test_all_operations_e2e,
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