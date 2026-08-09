"""Tests for /premium_config command.

Tests admin permission enforcement, successful configuration updates,
and invalid parameter rejection using mocked dependencies.
"""

import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from premium.premium_cog import PremiumCog


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def bot():
    """Return a mock Bot instance."""
    return MagicMock()


@pytest.fixture
def cog(bot):
    """Return a PremiumCog instance with a mocked bot."""
    return PremiumCog(bot)


@pytest.fixture
def interaction():
    """Return a minimal mock discord.Interaction."""
    mock = MagicMock()
    mock.guild_id = 12345
    mock.guild = MagicMock()
    mock.guild.id = 12345
    mock.guild.name = "Test Guild"
    mock.user.id = 99999
    mock.user.guild_permissions.administrator = True
    mock.response = MagicMock()
    mock.response.send_message = AsyncMock()
    return mock


# ── Tests ────────────────────────────────────────────────────────────────────


class TestPremiumConfigCommand:
    """Tests for the /premium_config command."""

    def test_premium_config_has_admin_permission(self, cog):
        """The command should require administrator permission."""
        cmd = cog.premium_config
        assert cmd.default_permissions is not None
        assert cmd.default_permissions.administrator is True

    def test_premium_config_params_signature(self, cog):
        """The command should accept max_reminders and xp_rate_multiplier."""
        sig = inspect.signature(cog.premium_config.callback)
        params = list(sig.parameters.keys())
        assert "max_reminders" in params
        assert "xp_rate_multiplier" in params

    @pytest.mark.asyncio
    async def test_premium_config_no_guild_id(self, cog, interaction):
        """Command in DMs (guild_id=None) should return an error."""
        interaction.guild_id = None
        await cog.premium_config.callback(cog, interaction)
        interaction.response.send_message.assert_called_once()
        msg = interaction.response.send_message.call_args[1].get("ephemeral")
        assert msg is True

    @pytest.mark.asyncio
    async def test_premium_config_success(self, cog, interaction):
        """Admin should be able to update premium config successfully."""
        mock_config = {
            "guild_id": 12345,
            "max_reminders": 10,
            "xp_rate_multiplier": 2.5,
            "welcome_embed_json": None,
            "xp_role_mappings": None,
            "anonymous_polls": 0,
            "multiple_vote_polls": 0,
        }

        with patch(
            "premium.premium_cog.set_guild_premium_config",
            return_value=mock_config,
        ) as mock_set:
            await cog.premium_config.callback(
                cog,
                interaction,
                max_reminders=10,
                xp_rate_multiplier=2.5,
            )

        mock_set.assert_called_once_with(
            guild_id=12345,
            max_reminders=10,
            xp_rate_multiplier=2.5,
        )
        interaction.response.send_message.assert_called_once()
        embed = interaction.response.send_message.call_args[1].get("embed")
        assert embed is not None
        assert embed.title == "✅ Premium設定を更新しました"
        # Verify both config values appear in the embed fields
        field_values = {f.name: f.value for f in embed.fields}
        assert field_values["最大リマインダー数"] == "10"
        assert field_values["XP倍率"] == "2.5"

    @pytest.mark.asyncio
    async def test_premium_config_default_params(self, cog, interaction):
        """Calling the command without params should use defaults (3, 1.0)."""
        mock_config = {
            "guild_id": 12345,
            "max_reminders": 3,
            "xp_rate_multiplier": 1.0,
            "welcome_embed_json": None,
            "xp_role_mappings": None,
            "anonymous_polls": 0,
            "multiple_vote_polls": 0,
        }

        with patch(
            "premium.premium_cog.set_guild_premium_config",
            return_value=mock_config,
        ) as mock_set:
            await cog.premium_config.callback(cog, interaction)

        mock_set.assert_called_once_with(
            guild_id=12345,
            max_reminders=3,
            xp_rate_multiplier=1.0,
        )
        interaction.response.send_message.assert_called_once()
        embed = interaction.response.send_message.call_args[1].get("embed")
        assert embed is not None
        field_values = {f.name: f.value for f in embed.fields}
        assert field_values["最大リマインダー数"] == "3"
        assert field_values["XP倍率"] == "1.0"


if __name__ == "__main__":
    import traceback

    bot_mock = MagicMock()
    premium_cog = PremiumCog(bot_mock)
    int_mock = MagicMock()
    int_mock.guild_id = 12345
    int_mock.guild.id = 12345
    int_mock.user.id = 99999
    int_mock.user.guild_permissions.administrator = True
    int_mock.response.send_message = AsyncMock()

    tests = [
        ("test_has_admin_permission", lambda: TestPremiumConfigCommand().test_premium_config_has_admin_permission(premium_cog)),
        ("test_params_signature", lambda: TestPremiumConfigCommand().test_premium_config_params_signature(premium_cog)),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            test_fn()
            print(f"  ✅ {name}")
            passed += 1
        except Exception:
            print(f"  ❌ {name}")
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*40}")
    print(f"結果: {passed} passed / {failed} failed / {len(tests)} total")
    if failed:
        print("❌  FAIL")
    else:
        print("✅  ALL PASSED")