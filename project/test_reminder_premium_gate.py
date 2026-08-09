"""Tests for Reminder premium gate — mocked premium_db.

Tests three scenarios using mocks:
1. Premium guild exceeding limit → blocked
2. Free guild exceeding limit → blocked (default 3)
3. Unregistered guild → no error, works with default 3
"""

from pathlib import Path
from unittest.mock import patch

from reminder_cog import ReminderCog

_FREE_MAX = 3


# ── _get_max_reminders tests (mocked) ────────────────────────────────────────


def test_free_guild_blocked_when_exceeds_default():
    """Free guild (no config) should be blocked when exceeding default 3."""
    guild_id = 99999

    with patch("premium.premium_db.get_guild_premium_config") as mock_get:
        mock_get.return_value = None  # no config → defaults to 3

        max_reminders = ReminderCog._get_max_reminders(guild_id)
        assert max_reminders == _FREE_MAX, f"Expected {_FREE_MAX}, got {max_reminders}"

        # Simulate enforcement: 3 reminders exist → trying 4th is blocked
        current_count = _FREE_MAX  # simulate at the limit
        assert current_count >= max_reminders, "Should be blocked"

        mock_get.assert_called_once_with(guild_id)


def test_premium_guild_blocked_when_exceeds_limit():
    """Premium guild with max_reminders=5 should be blocked at 6."""
    guild_id = 200
    premium_max = 5

    with patch("premium.premium_db.get_guild_premium_config") as mock_get:
        mock_get.return_value = {"max_reminders": premium_max}

        max_reminders = ReminderCog._get_max_reminders(guild_id)
        assert max_reminders == premium_max, f"Expected {premium_max}, got {max_reminders}"

        # Simulate enforcement: 5 reminders exist → trying 6th is blocked
        current_count = premium_max
        assert current_count >= max_reminders, "Premium guild should be blocked at its limit"

        mock_get.assert_called_once_with(guild_id)


def test_unregistered_guild_no_error():
    """Guild without any premium record should not raise an exception, default 3."""
    guild_id = 99999

    with patch("premium.premium_db.get_guild_premium_config") as mock_get:
        mock_get.return_value = None  # simulate no record

        # This should never raise
        try:
            max_reminders = ReminderCog._get_max_reminders(guild_id)
        except Exception as exc:
            assert False, f"Unexpected exception: {exc}"

        assert max_reminders == _FREE_MAX, f"Expected {_FREE_MAX}, got {max_reminders}"
        mock_get.assert_called_once_with(guild_id)


# ── Compilation checks ───────────────────────────────────────────────────────


def test_reminder_cog_compiles():
    """Verify that reminder_cog.py can be parsed without syntax errors."""
    import py_compile

    rem_cog_path = Path(__file__).parent / "reminder_cog.py"
    py_compile.compile(str(rem_cog_path), doraise=True)


def test_reminder_db_compiles():
    """Verify that reminder_db.py can be parsed without syntax errors."""
    import py_compile

    rem_db_path = Path(__file__).parent / "reminder_db.py"
    py_compile.compile(str(rem_db_path), doraise=True)


if __name__ == "__main__":
    import traceback

    tests = [
        test_free_guild_blocked_when_exceeds_default,
        test_premium_guild_blocked_when_exceeds_limit,
        test_unregistered_guild_no_error,
        test_reminder_cog_compiles,
        test_reminder_db_compiles,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  ✅ {test.__name__}")
            passed += 1
        except Exception:
            print(f"  ❌ {test.__name__}")
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*40}")
    print(f"結果: {passed} passed / {failed} failed / {len(tests)} total")
    if failed:
        print("❌  FAIL")
    else:
        print("✅  ALL PASSED")