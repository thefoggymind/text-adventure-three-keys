"""Tests for reminder_db.py."""

import os
import shutil
import time
from pathlib import Path

# Use a temporary DB for testing
TEST_DB_DIR = Path("/tmp/test_reminder_data")

# Force reminder_db to use the test directory BEFORE importing
import reminder_db
reminder_db.DB_DIR = TEST_DB_DIR
reminder_db.DB_PATH = TEST_DB_DIR / "reminders.db"

from reminder_db import (
    cancel_reminder,
    create_reminder,
    get_active_reminders,
    get_due_reminders,
    get_reminder,
    init_db,
    mark_triggered,
)


def setup_module():
    """Remove any leftover test DB before starting."""
    if TEST_DB_DIR.exists():
        shutil.rmtree(TEST_DB_DIR)


def teardown_module():
    """Clean up test DB after tests."""
    if TEST_DB_DIR.exists():
        shutil.rmtree(TEST_DB_DIR)


def test_init_db():
    init_db()
    db_path = TEST_DB_DIR / "reminders.db"
    assert db_path.exists(), "DB file should be created"
    # WAL mode should be set
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    cur = conn.execute("PRAGMA journal_mode")
    assert cur.fetchone()[0] == "wal"
    conn.close()


def test_create_and_get_reminder():
    init_db()
    now = time.time()
    remind_at = now + 3600  # 1 hour from now

    rid = create_reminder(
        user_id=12345,
        channel_id=67890,
        message="Test reminder message",
        remind_at=remind_at,
    )
    assert isinstance(rid, int) and rid > 0, f"Expected positive int, got {rid}"

    # Fetch by ID
    rem = get_reminder(rid)
    assert rem is not None, "Reminder should exist"
    assert rem["user_id"] == 12345
    assert rem["channel_id"] == 67890
    assert rem["message"] == "Test reminder message"
    assert rem["remind_at"] == remind_at
    assert rem["triggered"] == 0
    assert isinstance(rem["created_at"], float)


def test_get_active_reminders():
    init_db()
    user_id = 99999
    now = time.time()

    # Create two active reminders
    r1 = create_reminder(user_id, 111, "Active 1", now + 3600)
    r2 = create_reminder(user_id, 222, "Active 2", now + 7200)

    # Create one for another user (shouldn't appear)
    create_reminder(88888, 333, "Other user", now + 3600)

    # Create one already triggered (shouldn't appear)
    r_triggered = create_reminder(user_id, 444, "Triggered", now + 3600)
    mark_triggered(r_triggered)

    active = get_active_reminders(user_id)
    assert len(active) == 2, f"Expected 2 active reminders, got {len(active)}"
    ids = {r["id"] for r in active}
    assert r1 in ids
    assert r2 in ids
    assert r_triggered not in ids


def test_get_due_reminders():
    init_db()
    now = time.time()
    user_id = 77777

    # Create a past-due reminder
    r_due = create_reminder(user_id, 111, "Due reminder", now - 60)

    # Create a future reminder (should not be due)
    create_reminder(user_id, 222, "Future reminder", now + 3600)

    # Create a due but already triggered reminder (should not appear)
    r_due_triggered = create_reminder(user_id, 333, "Due but triggered", now - 120)
    mark_triggered(r_due_triggered)

    due = get_due_reminders()
    due_ids = {r["id"] for r in due}
    assert r_due in due_ids, "Past-due reminder should be in due list"
    assert r_due_triggered not in due_ids, "Triggered reminder should not appear"


def test_cancel_reminder():
    init_db()
    user_id = 55555
    now = time.time()

    rid = create_reminder(user_id, 111, "To cancel", now + 3600)

    # Wrong user should not cancel
    assert cancel_reminder(rid, 99999) is False
    assert get_reminder(rid) is not None, "Reminder should still exist"

    # Correct user should cancel
    assert cancel_reminder(rid, user_id) is True
    assert get_reminder(rid) is None, "Reminder should be deleted"

    # Canceling again should fail
    assert cancel_reminder(rid, user_id) is False


def test_mark_triggered():
    init_db()
    user_id = 44444
    now = time.time()

    rid = create_reminder(user_id, 111, "To trigger", now + 3600)
    assert get_reminder(rid)["triggered"] == 0

    mark_triggered(rid)
    assert get_reminder(rid)["triggered"] == 1


def test_all_operations():
    """End-to-end: create → verify → list active → mark triggered → verify gone."""
    init_db()
    user_id = 33333
    now = time.time()
    remind_at = now + 1800  # 30 minutes

    # Create
    rid = create_reminder(user_id, 111, "E2E test", remind_at)
    assert rid > 0

    # Verify via get
    rem = get_reminder(rid)
    assert rem is not None
    assert rem["message"] == "E2E test"

    # List active
    active = get_active_reminders(user_id)
    assert any(r["id"] == rid for r in active)

    # Due check (future reminder should NOT be due)
    due = get_due_reminders()
    assert not any(r["id"] == rid for r in due)

    # Cancel
    assert cancel_reminder(rid, user_id) is True
    assert get_reminder(rid) is None


if __name__ == "__main__":
    # Run tests manually
    import traceback

    tests = [
        test_init_db,
        test_create_and_get_reminder,
        test_get_active_reminders,
        test_get_due_reminders,
        test_cancel_reminder,
        test_mark_triggered,
        test_all_operations,
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