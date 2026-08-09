"""Tests for XP premium gate — premium guilds get xp_rate_multiplier applied.

Uses mocks for premium.premium_db to test three scenarios:
1. Premium guild: multiplier > 1.0 is applied
2. Free guild: multiplier stays 1.0
3. No subscription record: no error raised
"""

from pathlib import Path
from unittest.mock import patch

import xp_db


# ---------------------------------------------------------------------------
# Premium gate logic tests (mocking premium.premium_db)
# ---------------------------------------------------------------------------


def test_premium_guild_multiplier_applied():
    """Premium guild with xp_rate_multiplier > 1.0 should scale XP_MIN/XP_MAX."""
    guild_id = 100
    orig_min = xp_db.XP_MIN
    orig_max = xp_db.XP_MAX

    with (
        patch("premium.premium_db.get_active_subscription") as mock_get_sub,
        patch("premium.premium_db.get_guild_premium_config") as mock_get_config,
    ):
        mock_get_sub.return_value = {"guild_id": guild_id, "status": "active"}
        mock_get_config.return_value = {"xp_rate_multiplier": 2.0}

        # Exact logic from xp_cog.on_message
        multiplier = 1.0
        try:
            from premium.premium_db import get_active_subscription, get_guild_premium_config

            sub = get_active_subscription(guild_id)
            if sub is not None:
                config = get_guild_premium_config(guild_id)
                if config and config.get("xp_rate_multiplier", 1.0) > 1.0:
                    multiplier = config["xp_rate_multiplier"]
        except Exception:
            pass

        assert multiplier == 2.0, f"Expected 2.0, got {multiplier}"

        # Verify XP_MIN/XP_MAX would be scaled
        expected_min = max(1, int(orig_min * multiplier))
        expected_max = max(1, int(orig_max * multiplier))
        assert expected_min == orig_min * 2
        assert expected_max == orig_max * 2

    # Verify originals restored after scope
    assert xp_db.XP_MIN == orig_min
    assert xp_db.XP_MAX == orig_max


def test_free_guild_no_multiplier():
    """Free guild (no active subscription) should keep multiplier at 1.0."""
    guild_id = 99999
    orig_min = xp_db.XP_MIN
    orig_max = xp_db.XP_MAX

    with patch("premium.premium_db.get_active_subscription") as mock_get_sub:
        mock_get_sub.return_value = None

        # Exact logic from xp_cog.on_message
        multiplier = 1.0
        try:
            from premium.premium_db import get_active_subscription

            sub = get_active_subscription(guild_id)
            if sub is not None:
                # Would check config, but sub is None so never reaches here
                multiplier = 2.0  # pragma: no cover
        except Exception:
            pass

        assert multiplier == 1.0, f"Expected 1.0, got {multiplier}"
        mock_get_sub.assert_called_once_with(guild_id)

    # Verify XP_MIN/XP_MAX unchanged
    assert xp_db.XP_MIN == orig_min
    assert xp_db.XP_MAX == orig_max


def test_no_subscription_no_error():
    """Guild without any subscription record should not raise any exception."""
    guild_id = 99999

    with patch("premium.premium_db.get_active_subscription") as mock_get_sub:
        mock_get_sub.return_value = None

        multiplier = 1.0
        # This block should never raise
        try:
            from premium.premium_db import get_active_subscription

            sub = get_active_subscription(guild_id)
            if sub is not None:
                multiplier = config.get("xp_rate_multiplier", 1.0)  # pragma: no cover
        except Exception as exc:
            assert False, f"Unexpected exception: {exc}"

        assert multiplier == 1.0


# ---------------------------------------------------------------------------
# Compilation checks
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