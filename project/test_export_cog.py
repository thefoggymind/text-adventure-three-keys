"""Tests for export_cog.py.

Tests Cog initialisation, command registration, permission checks, and
data export flows (with mocked database functions).
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Module under test ─────────────────────────────────────────────────────────
from premium.export_cog import ExportCog

# Sample data returned by mocked export_db functions ──────────────────────────

SAMPLE_XP = [
    {"user_id": 1001, "guild_id": 12345, "xp": 150, "level": 5},
    {"user_id": 1002, "guild_id": 12345, "xp": 80, "level": 3},
]

SAMPLE_REMINDERS = [
    {
        "id": 1,
        "user_id": 1001,
        "channel_id": 2001,
        "guild_id": 12345,
        "message": "Hello",
        "remind_at": "2025-01-01T00:00:00",
        "created_at": "2024-12-01T00:00:00",
        "triggered": 0,
    }
]

SAMPLE_CONFIG = {
    "guild_id": 12345,
    "keywords": ["badword"],
    "spam_threshold": 3,
    "auto_mod_enabled": True,
}

SAMPLE_PREMIUM = {
    "guild_id": 12345,
    "owner_id": 99999,
    "status": "active",
    "current_period_start": "2025-01-01",
    "current_period_end": "2025-02-01",
}

EMPTY_XP: list[dict] = []
EMPTY_REMINDERS: list[dict] = []


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def bot():
    """Return a mock Bot instance."""
    return MagicMock()


@pytest.fixture
def cog(bot):
    """Return an ExportCog instance with a mocked bot."""
    return ExportCog(bot)


def _make_interaction(
    guild_id: int = 12345,
    user_id: int = 99999,
    is_admin: bool = False,
    is_owner: bool = False,
    guild_none: bool = False,
):
    """Build a standardised mock discord.Interaction.

    Parameters control permission attributes so tests can simulate
    various user roles.
    """
    mock = MagicMock()
    mock.guild_id = guild_id if not guild_none else None
    mock.user.id = user_id

    if guild_none:
        mock.guild = None
    else:
        mock.guild = MagicMock()
        mock.guild.id = guild_id
        mock.guild.owner_id = user_id if is_owner else 11111  # different owner
        perm = MagicMock()
        perm.administrator = is_admin
        mock.user.guild_permissions = perm

    mock.response = MagicMock()
    mock.response.send_message = AsyncMock()
    mock.followup = MagicMock()
    mock.followup.send_message = AsyncMock()
    return mock


@pytest.fixture
def admin_interaction():
    """Return an interaction where the user is an admin (not owner)."""
    return _make_interaction(is_admin=True, is_owner=False)


@pytest.fixture
def owner_interaction():
    """Return an interaction where the user is the guild owner."""
    return _make_interaction(is_admin=False, is_owner=True)


@pytest.fixture
def non_admin_interaction():
    """Return an interaction where the user has no special perms."""
    return _make_interaction(is_admin=False, is_owner=False)


@pytest.fixture
def dm_interaction():
    """Return an interaction where guild is None (DM)."""
    return _make_interaction(guild_none=True)


# ── Cog initialisation ───────────────────────────────────────────────────────


class TestCogInit:
    """Tests for ExportCog initialisation."""

    def test_cog_compiles(self):
        """Verify the module can be imported and the class exists."""
        assert ExportCog is not None

    def test_cog_init_accepts_bot(self, bot):
        """Initialising the cog with a bot reference should work."""
        c = ExportCog(bot)
        assert c.bot is bot

    def test_cog_has_bot_ref(self, cog):
        """The cog should store a reference to the bot."""
        assert cog.bot is not None

    def test_cog_commands_registered(self, cog):
        """All expected subcommands should be registered under the export group."""
        # Walk all app commands on the cog
        cmd_names = {cmd.name for cmd in cog.walk_app_commands()}
        expected = {"export", "xp", "reminders", "config", "all"}
        missing = expected - cmd_names
        assert not missing, f"Missing commands: {missing}"


# ── Command signatures ───────────────────────────────────────────────────────


class TestCommandSignatures:
    """Verify that each command callback has the correct parameters."""

    # Helper: get callback signature parameter names
    @staticmethod
    def _param_names(cog, attr: str) -> list[str]:
        import inspect

        callback = getattr(cog, attr).callback
        return list(inspect.signature(callback).parameters.keys())

    def test_export_xp_params(self, cog):
        """export_xp_cmd should accept only self and interaction."""
        assert self._param_names(cog, "export_xp_cmd") == ["self", "interaction"]

    def test_export_reminders_params(self, cog):
        """export_reminders_cmd should accept only self and interaction."""
        assert self._param_names(cog, "export_reminders_cmd") == ["self", "interaction"]

    def test_export_config_params(self, cog):
        """export_config_cmd should accept only self and interaction."""
        assert self._param_names(cog, "export_config_cmd") == ["self", "interaction"]

    def test_export_all_params(self, cog):
        """export_all_cmd should accept only self and interaction."""
        assert self._param_names(cog, "export_all_cmd") == ["self", "interaction"]


# ── Permission helpers ───────────────────────────────────────────────────────


class TestPermissionHelpers:
    """Tests for _is_admin_or_owner, _is_owner, and _check_permission."""

    def test_is_admin_or_owner_admin(self, admin_interaction):
        """An admin user should pass _is_admin_or_owner."""
        assert ExportCog._is_admin_or_owner(admin_interaction) is True

    def test_is_admin_or_owner_owner(self, owner_interaction):
        """The guild owner should pass _is_admin_or_owner."""
        assert ExportCog._is_admin_or_owner(owner_interaction) is True

    def test_is_admin_or_owner_fails(self, non_admin_interaction):
        """A regular user should fail _is_admin_or_owner."""
        assert ExportCog._is_admin_or_owner(non_admin_interaction) is False

    def test_is_owner_owner(self, owner_interaction):
        """The guild owner should pass _is_owner."""
        assert ExportCog._is_owner(owner_interaction) is True

    def test_is_owner_admin(self, admin_interaction):
        """An admin who is not the owner should fail _is_owner."""
        assert ExportCog._is_owner(admin_interaction) is False

    @pytest.mark.asyncio
    async def test_check_permission_dm(self, cog, dm_interaction):
        """_check_permission should return False in DMs."""
        result = await cog._check_permission(dm_interaction)
        assert result is False
        dm_interaction.response.send_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_check_permission_admin(self, cog, admin_interaction):
        """_check_permission should return True for admins."""
        result = await cog._check_permission(admin_interaction)
        assert result is True
        admin_interaction.response.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_permission_owner(self, cog, owner_interaction):
        """_check_permission should return True for the guild owner."""
        result = await cog._check_permission(owner_interaction)
        assert result is True
        owner_interaction.response.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_permission_non_admin(self, cog, non_admin_interaction):
        """_check_permission should return False for regular users."""
        result = await cog._check_permission(non_admin_interaction)
        assert result is False
        non_admin_interaction.response.send_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_check_permission_require_owner_owner(self, cog, owner_interaction):
        """_check_permission(require_owner=True) should pass for owner."""
        result = await cog._check_permission(owner_interaction, require_owner=True)
        assert result is True

    @pytest.mark.asyncio
    async def test_check_permission_require_owner_admin(self, cog, admin_interaction):
        """_check_permission(require_owner=True) should fail for non-owner admin."""
        result = await cog._check_permission(admin_interaction, require_owner=True)
        assert result is False


# ── File helpers ─────────────────────────────────────────────────────────────


class TestFileHelpers:
    """Tests for _dicts_to_csv and _make_file."""

    def test_dicts_to_csv_empty(self):
        """An empty list should produce an empty string."""
        assert ExportCog._dicts_to_csv([]) == ""

    def test_dicts_to_csv_content(self):
        """A non-empty list should produce valid CSV."""
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        result = ExportCog._dicts_to_csv(data)
        assert "a,b" in result
        assert "1,2" in result
        assert "3,4" in result

    def test_make_file_within_limit(self):
        """A small payload should produce a discord.File."""
        result = ExportCog._make_file("hello", "test.txt")
        assert result is not None
        assert result.filename == "test.txt"

    def test_make_file_exceeds_limit(self):
        """A payload larger than 10 MB should return None."""
        big = "x" * (12 * 1024 * 1024)
        result = ExportCog._make_file(big, "big.txt")
        assert result is None


# ── /export xp ───────────────────────────────────────────────────────────────


class TestExportXpCommand:
    """Tests for the /export xp subcommand."""

    @pytest.mark.asyncio
    async def test_non_admin_rejected(self, cog, non_admin_interaction):
        """A user without admin or owner permissions should be rejected."""
        with patch("premium.export_cog.export_xp_data") as mock_xp:
            await cog.export_xp_cmd.callback(cog, non_admin_interaction)
            mock_xp.assert_not_called()
            non_admin_interaction.response.send_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_dm_rejected(self, cog, dm_interaction):
        """The command should be rejected in DMs."""
        with patch("premium.export_cog.export_xp_data") as mock_xp:
            await cog.export_xp_cmd.callback(cog, dm_interaction)
            mock_xp.assert_not_called()
            dm_interaction.response.send_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_db_error_shows_embed(self, cog, admin_interaction):
        """A database exception should produce an error Embed."""
        with patch(
            "premium.export_cog.export_xp_data",
            side_effect=Exception("DB down"),
        ):
            await cog.export_xp_cmd.callback(cog, admin_interaction)
            admin_interaction.response.send_message.assert_awaited_once()
            kwargs = admin_interaction.response.send_message.call_args.kwargs
            assert "embed" in kwargs
            assert "エラー" in kwargs["embed"].title

    @pytest.mark.asyncio
    async def test_empty_data_shows_embed(self, cog, admin_interaction):
        """Empty data should show an embed instead of sending files."""
        with patch("premium.export_cog.export_xp_data", return_value=[]):
            await cog.export_xp_cmd.callback(cog, admin_interaction)
            admin_interaction.response.send_message.assert_awaited_once()
            kwargs = admin_interaction.response.send_message.call_args.kwargs
            assert "embed" in kwargs
            assert "データはありません" in kwargs["embed"].title

    @pytest.mark.asyncio
    async def test_success_sends_csv_and_json(self, cog, admin_interaction):
        """A successful export should send both CSV and JSON files."""
        with patch("premium.export_cog.export_xp_data", return_value=SAMPLE_XP):
            await cog.export_xp_cmd.callback(cog, admin_interaction)
            admin_interaction.response.send_message.assert_awaited_once()
            kwargs = admin_interaction.response.send_message.call_args.kwargs
            assert "files" in kwargs
            files = kwargs["files"]
            assert len(files) == 2
            # Verify filenames
            fnames = [f.filename for f in files]
            assert any("xp_data" in n and n.endswith(".csv") for n in fnames)
            assert any("xp_data" in n and n.endswith(".json") for n in fnames)
            # Verify content
            for f in files:
                payload = f.fp.read()
                assert len(payload) > 0

    @pytest.mark.asyncio
    async def test_file_size_limit(self, cog, admin_interaction):
        """If generated files exceed 10 MB an error embed should be shown."""
        huge_data = [{"user_id": i, "xp": 0, "level": 0, "guild_id": 12345}
                     for i in range(500_000)]
        with patch("premium.export_cog.export_xp_data", return_value=huge_data):
            await cog.export_xp_cmd.callback(cog, admin_interaction)
            admin_interaction.response.send_message.assert_awaited_once()
            kwargs = admin_interaction.response.send_message.call_args.kwargs
            assert "embed" in kwargs
            assert "サイズ超過" in kwargs["embed"].title


# ── /export reminders ────────────────────────────────────────────────────────


class TestExportRemindersCommand:
    """Tests for the /export reminders subcommand."""

    @pytest.mark.asyncio
    async def test_non_admin_rejected(self, cog, non_admin_interaction):
        """A user without admin or owner permissions should be rejected."""
        with patch("premium.export_cog.export_reminders") as mock_rem:
            await cog.export_reminders_cmd.callback(cog, non_admin_interaction)
            mock_rem.assert_not_called()

    @pytest.mark.asyncio
    async def test_dm_rejected(self, cog, dm_interaction):
        """The command should be rejected in DMs."""
        with patch("premium.export_cog.export_reminders") as mock_rem:
            await cog.export_reminders_cmd.callback(cog, dm_interaction)
            mock_rem.assert_not_called()

    @pytest.mark.asyncio
    async def test_db_error_shows_embed(self, cog, admin_interaction):
        """A database exception should produce an error Embed."""
        with patch(
            "premium.export_cog.export_reminders",
            side_effect=Exception("DB down"),
        ):
            await cog.export_reminders_cmd.callback(cog, admin_interaction)
            kwargs = admin_interaction.response.send_message.call_args.kwargs
            assert "embed" in kwargs
            assert "エラー" in kwargs["embed"].title

    @pytest.mark.asyncio
    async def test_success_sends_csv_and_json(self, cog, admin_interaction):
        """A successful export should send both CSV and JSON files."""
        with patch("premium.export_cog.export_reminders", return_value=SAMPLE_REMINDERS):
            await cog.export_reminders_cmd.callback(cog, admin_interaction)
            kwargs = admin_interaction.response.send_message.call_args.kwargs
            files = kwargs["files"]
            assert len(files) == 2
            fnames = [f.filename for f in files]
            assert any("reminders" in n and n.endswith(".csv") for n in fnames)
            assert any("reminders" in n and n.endswith(".json") for n in fnames)

    @pytest.mark.asyncio
    async def test_empty_data_shows_embed(self, cog, admin_interaction):
        """Empty data should show an embed instead of sending files."""
        with patch("premium.export_cog.export_reminders", return_value=[]):
            await cog.export_reminders_cmd.callback(cog, admin_interaction)
            kwargs = admin_interaction.response.send_message.call_args.kwargs
            assert "embed" in kwargs
            assert "データはありません" in kwargs["embed"].title


# ── /export config ───────────────────────────────────────────────────────────


class TestExportConfigCommand:
    """Tests for the /export config subcommand."""

    @pytest.mark.asyncio
    async def test_non_admin_rejected(self, cog, non_admin_interaction):
        """A user without admin or owner permissions should be rejected."""
        with patch("premium.export_cog.export_moderation_config") as mock_cfg:
            await cog.export_config_cmd.callback(cog, non_admin_interaction)
            mock_cfg.assert_not_called()

    @pytest.mark.asyncio
    async def test_dm_rejected(self, cog, dm_interaction):
        """The command should be rejected in DMs."""
        with patch("premium.export_cog.export_moderation_config") as mock_cfg:
            await cog.export_config_cmd.callback(cog, dm_interaction)
            mock_cfg.assert_not_called()

    @pytest.mark.asyncio
    async def test_db_error_shows_embed(self, cog, admin_interaction):
        """A database exception should produce an error Embed."""
        with patch(
            "premium.export_cog.export_moderation_config",
            side_effect=Exception("DB down"),
        ):
            await cog.export_config_cmd.callback(cog, admin_interaction)
            kwargs = admin_interaction.response.send_message.call_args.kwargs
            assert "embed" in kwargs

    @pytest.mark.asyncio
    async def test_success_sends_json(self, cog, admin_interaction):
        """A successful export should send a JSON file."""
        with patch(
            "premium.export_cog.export_moderation_config",
            return_value=SAMPLE_CONFIG,
        ):
            await cog.export_config_cmd.callback(cog, admin_interaction)
            kwargs = admin_interaction.response.send_message.call_args.kwargs
            files = kwargs["files"]
            assert len(files) == 1
            assert files[0].filename.endswith(".json")

    @pytest.mark.asyncio
    async def test_file_size_limit(self, cog, admin_interaction):
        """If the file exceeds 10 MB an error embed should be shown."""
        # ~12 MB of keywords value → JSON string > 10 MB
        huge = {"guild_id": 12345, "keywords": ["x" * 12_000_000],
                "spam_threshold": 3, "auto_mod_enabled": True}
        with patch(
            "premium.export_cog.export_moderation_config",
            return_value=huge,
        ):
            await cog.export_config_cmd.callback(cog, admin_interaction)
            admin_interaction.response.send_message.assert_awaited_once()
            kwargs = admin_interaction.response.send_message.call_args.kwargs
            assert "embed" in kwargs
            assert "サイズ超過" in kwargs["embed"].title


# ── /export all ──────────────────────────────────────────────────────────────


class TestExportAllCommand:
    """Tests for the /export all subcommand."""

    @pytest.mark.asyncio
    async def test_non_admin_rejected(self, cog, non_admin_interaction):
        """A user without admin or owner permissions should be rejected."""
        with patch("premium.export_cog.export_xp_data") as m:
            await cog.export_all_cmd.callback(cog, non_admin_interaction)
            m.assert_not_called()

    @pytest.mark.asyncio
    async def test_dm_rejected(self, cog, dm_interaction):
        """The command should be rejected in DMs."""
        with patch("premium.export_cog.export_xp_data") as m:
            await cog.export_all_cmd.callback(cog, dm_interaction)
            m.assert_not_called()

    @pytest.mark.asyncio
    async def test_owner_gets_premium_file(self, cog, owner_interaction):
        """The guild owner should receive the premium-info file."""
        patches = [
            patch("premium.export_cog.export_xp_data", return_value=SAMPLE_XP),
            patch("premium.export_cog.export_reminders", return_value=SAMPLE_REMINDERS),
            patch("premium.export_cog.export_moderation_config", return_value=SAMPLE_CONFIG),
            patch("premium.export_cog.export_premium_info", return_value=SAMPLE_PREMIUM),
        ]
        with contextlib_patch_multi(patches):
            await cog.export_all_cmd.callback(cog, owner_interaction)
            owner_interaction.response.send_message.assert_awaited_once()
            kwargs = owner_interaction.response.send_message.call_args.kwargs
            files = kwargs["files"]
            # Expect 5 files: xp.csv + xp.json + reminders.csv + reminders.json
            # + mod_config.json + premium_info.json = 6
            assert len(files) == 6
            fnames = [f.filename for f in files]
            assert any("premium_info" in n for n in fnames)

    @pytest.mark.asyncio
    async def test_admin_does_not_get_premium_file(self, cog, admin_interaction):
        """A non-owner admin should NOT receive the premium-info file."""
        patches = [
            patch("premium.export_cog.export_xp_data", return_value=SAMPLE_XP),
            patch("premium.export_cog.export_reminders", return_value=SAMPLE_REMINDERS),
            patch("premium.export_cog.export_moderation_config", return_value=SAMPLE_CONFIG),
            patch("premium.export_cog.export_premium_info", return_value=SAMPLE_PREMIUM),
        ]
        with contextlib_patch_multi(patches):
            await cog.export_all_cmd.callback(cog, admin_interaction)
            admin_interaction.response.send_message.assert_awaited_once()
            kwargs = admin_interaction.response.send_message.call_args.kwargs
            files = kwargs["files"]
            fnames = [f.filename for f in files]
            assert all("premium" not in n for n in fnames), (
                f"Admin should not get premium file, got: {fnames}"
            )
            # 5 files without premium: xp.csv, xp.json, reminders.csv,
            # reminders.json, mod_config.json
            assert len(files) == 5

    @pytest.mark.asyncio
    async def test_partial_failure_still_sends_files(self, cog, admin_interaction):
        """If one data source fails, the command should still send others."""
        patches = [
            patch(
                "premium.export_cog.export_xp_data",
                side_effect=Exception("XP error"),
            ),
            patch("premium.export_cog.export_reminders", return_value=SAMPLE_REMINDERS),
            patch(
                "premium.export_cog.export_moderation_config",
                return_value=SAMPLE_CONFIG,
            ),
        ]
        with contextlib_patch_multi(patches):
            await cog.export_all_cmd.callback(cog, admin_interaction)
            admin_interaction.response.send_message.assert_awaited_once()
            call = admin_interaction.response.send_message.call_args
            # Should have reminders.csv, reminders.json, mod_config.json = 3
            assert len(call.kwargs["files"]) == 3
            # Message content (positional arg) should mention errors
            msg = call.args[0]
            assert "エラー" in msg

    @pytest.mark.asyncio
    async def test_all_fail_sends_embed(self, cog, admin_interaction):
        """If all data sources fail, an error embed should be shown."""
        patches = [
            patch(
                "premium.export_cog.export_xp_data",
                side_effect=Exception("XP error"),
            ),
            patch(
                "premium.export_cog.export_reminders",
                side_effect=Exception("Rem error"),
            ),
            patch(
                "premium.export_cog.export_moderation_config",
                side_effect=Exception("Cfg error"),
            ),
        ]
        with contextlib_patch_multi(patches):
            await cog.export_all_cmd.callback(cog, admin_interaction)
            admin_interaction.response.send_message.assert_awaited_once()
            kwargs = admin_interaction.response.send_message.call_args.kwargs
            assert "embed" in kwargs
            assert "エクスポート失敗" in kwargs["embed"].title


# ── Helper ───────────────────────────────────────────────────────────────────


class contextlib_patch_multi:
    """Context manager to apply multiple mock patches at once."""

    def __init__(self, patches: list):
        self._patches = patches

    def __enter__(self):
        return [p.__enter__() for p in self._patches]

    def __exit__(self, *exc_info):
        for p in self._patches:
            p.__exit__(*exc_info)


# ── pytest __main__ support ──────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])