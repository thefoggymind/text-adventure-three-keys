"""Tests for moderation_cog.py.

Tests Cog initialisation, command handlers, and on_message event
(keyword filter + spam detection).
"""

import importlib
import inspect
import shutil
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Use a temporary DB for testing (must happen before importing modules)
TEST_MOD_DB_DIR = Path("/tmp/test_moderation_cog_data")
TEST_PREMIUM_DB_DIR = Path("/tmp/test_moderation_cog_premium_data")

import premium.moderation_db as mod_db
import premium.premium_db as premium_db

importlib.reload(mod_db)
importlib.reload(premium_db)

# Apply DB path overrides AFTER reload so they stick
mod_db.DB_DIR = TEST_MOD_DB_DIR
mod_db.DB_PATH = TEST_MOD_DB_DIR / "moderation.db"
premium_db.DB_DIR = TEST_PREMIUM_DB_DIR
premium_db.DB_PATH = TEST_PREMIUM_DB_DIR / "premium.db"

from premium.moderation_cog import ModerationCog  # noqa: E402
from premium.moderation_db import (  # noqa: E402
    add_ng_word,
    init_db as init_mod_db,
    list_ng_words,
    remove_ng_word,
    set_mod_config,
)
from premium.premium_db import (  # noqa: E402
    create_premium_subscription,
    init_db as init_premium_db,
)


# ── DB cleanup helpers ──────────────────────────────────────────────────────


def clean_mod_db():
    """Remove and recreate the test moderation DB."""
    if TEST_MOD_DB_DIR.exists():
        shutil.rmtree(TEST_MOD_DB_DIR)
    init_mod_db()


def clean_premium_db():
    """Remove and recreate the test premium DB."""
    if TEST_PREMIUM_DB_DIR.exists():
        shutil.rmtree(TEST_PREMIUM_DB_DIR)
    init_premium_db()


def setup_function():
    """Called by pytest before each module-level test function."""
    clean_mod_db()
    clean_premium_db()


def setup_method():
    """Called by pytest before each class-based test method."""
    clean_mod_db()
    clean_premium_db()


def teardown_module():
    """Clean up test DBs after all tests."""
    if TEST_MOD_DB_DIR.exists():
        shutil.rmtree(TEST_MOD_DB_DIR)
    if TEST_PREMIUM_DB_DIR.exists():
        shutil.rmtree(TEST_PREMIUM_DB_DIR)


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def bot():
    """Return a mock Bot instance."""
    return MagicMock()


@pytest.fixture
def cog(bot):
    """Return a ModerationCog instance with a mocked bot."""
    return ModerationCog(bot)


@pytest.fixture
def interaction():
    """Return a minimal mock discord.Interaction."""
    mock = MagicMock()
    mock.guild_id = 12345
    mock.user.id = 99999
    mock.guild = MagicMock()
    mock.guild.id = 12345
    mock.guild.name = "Test Guild"
    mock.response = MagicMock()
    mock.response.send_message = AsyncMock()
    return mock


@pytest.fixture
def message():
    """Return a minimal mock discord.Message."""
    mock = MagicMock()
    mock.id = 1
    mock.content = "test message"
    mock.author = MagicMock()
    mock.author.bot = False
    mock.author.id = 77777
    mock.author.send = AsyncMock()
    mock.guild = MagicMock()
    mock.guild.id = 12345
    mock.guild.name = "Test Guild"
    mock.channel = MagicMock()
    mock.channel.id = 11111
    mock.delete = AsyncMock()
    return mock


# ── Cog initialisation ──────────────────────────────────────────────────────


class TestCogInit:
    """Tests for ModerationCog initialisation."""

    def setup_method(self):
        clean_mod_db()
        clean_premium_db()

    def test_cog_compiles(self):
        """Verify the module can be imported and the class exists."""
        assert ModerationCog is not None

    def test_cog_init_creates_db(self, bot):
        """Initialising the cog should create the moderation DB."""
        ModerationCog(bot)
        db_path = TEST_MOD_DB_DIR / "moderation.db"
        assert db_path.exists()

    def test_cog_has_bot_ref(self, cog):
        """The cog should store a reference to the bot."""
        assert cog.bot is not None

    def test_cog_commands_registered(self, cog):
        """All expected slash commands should be registered on the cog."""
        command_names = {cmd.name for cmd in cog.walk_app_commands()}
        # Groups and subcommands
        expected = {"moderation", "keyword", "config", "add", "remove", "list"}
        missing = expected - command_names
        assert not missing, f"Missing commands: {missing}"


# ── Command signatures ──────────────────────────────────────────────────────


class TestCommandSignatures:
    """Verify that each command method has the correct parameter signature."""

    def setup_method(self):
        clean_mod_db()
        clean_premium_db()

    def test_moderation_config_params(self, cog):
        """moderation_config should accept keyword_filter and spam_detection."""
        sig = inspect.signature(cog.moderation_config.callback)
        params = list(sig.parameters.keys())
        assert "keyword_filter" in params
        assert "spam_detection" in params

    def test_keyword_add_params(self, cog):
        """keyword_add should accept word."""
        sig = inspect.signature(cog.keyword_add.callback)
        params = list(sig.parameters.keys())
        assert "word" in params

    def test_keyword_remove_params(self, cog):
        """keyword_remove should accept word."""
        sig = inspect.signature(cog.keyword_remove.callback)
        params = list(sig.parameters.keys())
        assert "word" in params

    def test_keyword_list_params(self, cog):
        """keyword_list should accept only self and interaction."""
        sig = inspect.signature(cog.keyword_list.callback)
        params = list(sig.parameters.keys())
        assert params == ["self", "interaction"]


# ── /moderation config ──────────────────────────────────────────────────────


class TestModerationConfigCommand:
    """Tests for the /moderation_config command."""

    def setup_method(self):
        clean_mod_db()
        clean_premium_db()

    def test_has_admin_permission(self, cog):
        """The command should require manage_messages permission."""
        cmd = cog.moderation_config
        assert cmd.default_permissions is not None
        assert cmd.default_permissions.manage_messages is True

    @pytest.mark.asyncio
    async def test_no_guild_id(self, cog, interaction):
        """Command in DMs should return an error."""
        interaction.guild_id = None
        await cog.moderation_config.callback(cog, interaction)
        interaction.response.send_message.assert_called_once()
        msg = interaction.response.send_message.call_args[1].get("ephemeral")
        assert msg is True

    @pytest.mark.asyncio
    async def test_not_premium(self, cog, interaction):
        """Non-premium guilds should get a premium prompt."""
        await cog.moderation_config.callback(cog, interaction)
        interaction.response.send_message.assert_called_once()
        msg = interaction.response.send_message.call_args[0][0]
        assert "Premium" in msg

    @pytest.mark.asyncio
    async def test_successful_update(self, cog, interaction):
        """Admin with premium should be able to update config."""
        # Grant premium
        create_premium_subscription(
            guild_id=interaction.guild_id,
            owner_id=99999,
            stripe_customer_id="cus_test",
            stripe_subscription_id="sub_test",
            status="active",
        )

        mock_config = {
            "guild_id": 12345,
            "keyword_filter_enabled": 0,
            "spam_detection_enabled": 1,
            "spam_threshold": 3,
            "spam_window_seconds": 5,
            "max_mentions": 5,
            "max_links": 3,
            "mod_log_channel_id": None,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
        }

        with patch(
            "premium.moderation_cog.set_mod_config",
            return_value=mock_config,
        ) as mock_set:
            await cog.moderation_config.callback(
                cog,
                interaction,
                keyword_filter=0,
                spam_detection=1,
            )

        mock_set.assert_called_once_with(
            12345,
            keyword_filter_enabled=0,
            spam_detection_enabled=1,
        )
        interaction.response.send_message.assert_called_once()
        embed = interaction.response.send_message.call_args[1].get("embed")
        assert embed is not None
        assert embed.title == "✅ モデレーション設定を更新しました"

    @pytest.mark.asyncio
    async def test_partial_update(self, cog, interaction):
        """Updating only one parameter should preserve the other."""
        create_premium_subscription(
            guild_id=interaction.guild_id,
            owner_id=99999,
            stripe_customer_id="cus_test",
            stripe_subscription_id="sub_test",
            status="active",
        )

        mock_config = {
            "guild_id": 12345,
            "keyword_filter_enabled": 0,
            "spam_detection_enabled": 1,
            "spam_threshold": 3,
            "spam_window_seconds": 5,
            "max_mentions": 5,
            "max_links": 3,
            "mod_log_channel_id": None,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
        }

        with patch(
            "premium.moderation_cog.set_mod_config",
            return_value=mock_config,
        ) as mock_set:
            await cog.moderation_config.callback(
                cog,
                interaction,
                keyword_filter=0,
            )

        mock_set.assert_called_once_with(
            12345,
            keyword_filter_enabled=0,
        )
        assert mock_set.call_args[1].get("spam_detection_enabled") is None


# ── /moderation keyword add ─────────────────────────────────────────────────


class TestKeywordAddCommand:
    """Tests for the /moderation_keyword_add command."""

    def setup_method(self):
        clean_mod_db()
        clean_premium_db()

    def test_has_admin_permission(self, cog):
        cmd = cog.keyword_add
        assert cmd.default_permissions is not None
        assert cmd.default_permissions.manage_messages is True

    @pytest.mark.asyncio
    async def test_no_guild_id(self, cog, interaction):
        interaction.guild_id = None
        await cog.keyword_add.callback(cog, interaction, word="badword")
        interaction.response.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_not_premium(self, cog, interaction):
        await cog.keyword_add.callback(cog, interaction, word="badword")
        interaction.response.send_message.assert_called_once()
        msg = interaction.response.send_message.call_args[0][0]
        assert "Premium" in msg

    @pytest.mark.asyncio
    async def test_empty_word(self, cog, interaction):
        create_premium_subscription(
            guild_id=interaction.guild_id, owner_id=99999,
            stripe_customer_id="cus_test", stripe_subscription_id="sub_test",
            status="active",
        )
        await cog.keyword_add.callback(cog, interaction, word="  ")
        interaction.response.send_message.assert_called_once()
        assert "空" in interaction.response.send_message.call_args[0][0]

    @pytest.mark.asyncio
    async def test_add_success(self, cog, interaction):
        create_premium_subscription(
            guild_id=interaction.guild_id, owner_id=99999,
            stripe_customer_id="cus_test", stripe_subscription_id="sub_test",
            status="active",
        )
        with patch(
            "premium.moderation_cog.is_ng_word", return_value=False,
        ) as mock_is, patch(
            "premium.moderation_cog.add_ng_word",
        ) as mock_add:
            await cog.keyword_add.callback(cog, interaction, word="badword")

        mock_is.assert_called_once_with(12345, "badword")
        mock_add.assert_called_once_with(12345, "badword")
        interaction.response.send_message.assert_called_once()
        assert "追加" in interaction.response.send_message.call_args[0][0]

    @pytest.mark.asyncio
    async def test_add_duplicate(self, cog, interaction):
        create_premium_subscription(
            guild_id=interaction.guild_id, owner_id=99999,
            stripe_customer_id="cus_test", stripe_subscription_id="sub_test",
            status="active",
        )
        with patch(
            "premium.moderation_cog.is_ng_word", return_value=True,
        ):
            await cog.keyword_add.callback(cog, interaction, word="badword")

        interaction.response.send_message.assert_called_once()
        assert "既に登録" in interaction.response.send_message.call_args[0][0]


# ── /moderation keyword remove ──────────────────────────────────────────────


class TestKeywordRemoveCommand:
    """Tests for the /moderation_keyword_remove command."""

    def setup_method(self):
        clean_mod_db()
        clean_premium_db()

    @pytest.mark.asyncio
    async def test_no_guild_id(self, cog, interaction):
        interaction.guild_id = None
        await cog.keyword_remove.callback(cog, interaction, word="badword")
        interaction.response.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_not_premium(self, cog, interaction):
        await cog.keyword_remove.callback(cog, interaction, word="badword")
        assert "Premium" in interaction.response.send_message.call_args[0][0]

    @pytest.mark.asyncio
    async def test_remove_success(self, cog, interaction):
        create_premium_subscription(
            guild_id=interaction.guild_id, owner_id=99999,
            stripe_customer_id="cus_test", stripe_subscription_id="sub_test",
            status="active",
        )
        with patch(
            "premium.moderation_cog.remove_ng_word", return_value=True,
        ) as mock_rm:
            await cog.keyword_remove.callback(cog, interaction, word="badword")

        mock_rm.assert_called_once_with(12345, "badword")
        assert "削除" in interaction.response.send_message.call_args[0][0]

    @pytest.mark.asyncio
    async def test_remove_not_found(self, cog, interaction):
        create_premium_subscription(
            guild_id=interaction.guild_id, owner_id=99999,
            stripe_customer_id="cus_test", stripe_subscription_id="sub_test",
            status="active",
        )
        with patch(
            "premium.moderation_cog.remove_ng_word", return_value=False,
        ):
            await cog.keyword_remove.callback(cog, interaction, word="badword")

        assert "登録されていません" in interaction.response.send_message.call_args[0][0]


# ── /moderation keyword list ────────────────────────────────────────────────


class TestKeywordListCommand:
    """Tests for the /moderation_keyword_list command."""

    def setup_method(self):
        clean_mod_db()
        clean_premium_db()

    @pytest.mark.asyncio
    async def test_no_guild_id(self, cog, interaction):
        interaction.guild_id = None
        await cog.keyword_list.callback(cog, interaction)
        interaction.response.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_not_premium(self, cog, interaction):
        await cog.keyword_list.callback(cog, interaction)
        assert "Premium" in interaction.response.send_message.call_args[0][0]

    @pytest.mark.asyncio
    async def test_empty_list(self, cog, interaction):
        create_premium_subscription(
            guild_id=interaction.guild_id, owner_id=99999,
            stripe_customer_id="cus_test", stripe_subscription_id="sub_test",
            status="active",
        )
        await cog.keyword_list.callback(cog, interaction)
        msg = interaction.response.send_message.call_args[0][0]
        assert "ありません" in msg or "キーワード" in msg

    @pytest.mark.asyncio
    async def test_list_with_words(self, cog, interaction):
        create_premium_subscription(
            guild_id=interaction.guild_id, owner_id=99999,
            stripe_customer_id="cus_test", stripe_subscription_id="sub_test",
            status="active",
        )
        clean_mod_db()
        init_mod_db()
        add_ng_word(12345, "alpha")
        add_ng_word(12345, "beta")

        await cog.keyword_list.callback(cog, interaction)
        embed = interaction.response.send_message.call_args[1].get("embed")
        assert embed is not None
        assert "alpha" in embed.description
        assert "beta" in embed.description
        assert "2" in embed.footer.text


# ── on_message: keyword filter ──────────────────────────────────────────────


class TestOnMessageKeywordFilter:
    """Tests for the on_message keyword filter."""

    def setup_method(self):
        clean_mod_db()
        clean_premium_db()

    def _setup_premium_and_config(self, guild_id=12345):
        create_premium_subscription(
            guild_id=guild_id, owner_id=99999,
            stripe_customer_id="cus_test", stripe_subscription_id="sub_test",
            status="active",
        )
        init_mod_db()
        set_mod_config(guild_id=guild_id, keyword_filter_enabled=1)

    @pytest.mark.asyncio
    async def test_bot_message_ignored(self, cog, message):
        """Bot messages should be skipped entirely."""
        message.author.bot = True
        await cog.on_message(message)
        message.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_dm_ignored(self, cog, message):
        """DMs (guild is None) should be skipped."""
        message.guild = None
        await cog.on_message(message)
        message.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_premium_ignored(self, cog, message):
        """Non-premium guilds should be skipped."""
        # No subscription created → should not delete anything
        init_mod_db()
        set_mod_config(guild_id=12345, keyword_filter_enabled=1)
        add_ng_word(12345, "badword")
        message.content = "this contains badword"
        await cog.on_message(message)
        message.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_disabled_filter_ignored(self, cog, message):
        """When keyword filter is disabled, do not delete."""
        self._setup_premium_and_config()
        set_mod_config(guild_id=12345, keyword_filter_enabled=0)
        add_ng_word(12345, "badword")
        message.content = "this contains badword"
        await cog.on_message(message)
        message.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_matched_keyword_deleted(self, cog, message):
        """A message containing an NG word should be deleted."""
        self._setup_premium_and_config()
        add_ng_word(12345, "badword")
        message.content = "this contains badword here"
        await cog.on_message(message)
        message.delete.assert_called_once()
        message.author.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_case_insensitive_match(self, cog, message):
        """Matching should be case-insensitive."""
        self._setup_premium_and_config()
        add_ng_word(12345, "badword")
        message.content = "This Contains BADWORD Here"
        await cog.on_message(message)
        message.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_match_passes(self, cog, message):
        """A clean message should not be deleted."""
        self._setup_premium_and_config()
        add_ng_word(12345, "badword")
        message.content = "this is a clean message"
        await cog.on_message(message)
        message.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_content_ignored(self, cog, message):
        """Empty content messages should be skipped."""
        self._setup_premium_and_config()
        add_ng_word(12345, "badword")
        message.content = ""
        await cog.on_message(message)
        message.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_guild_scoped_filtering(self, cog, message):
        """Keywords should be scoped per guild."""
        self._setup_premium_and_config(guild_id=12345)
        add_ng_word(12345, "badword")
        message.guild.id = 99999  # Different guild
        message.content = "this contains badword"
        await cog.on_message(message)
        message.delete.assert_not_called()


# ── on_message: spam detection ──────────────────────────────────────────────


class TestOnMessageSpamDetection:
    """Tests for the on_message spam detection."""

    def setup_method(self):
        clean_mod_db()
        clean_premium_db()
        # Create a fresh cog per test to reset _spam_tracker
        self._bot = MagicMock()
        self._cog = ModerationCog(self._bot)

    def _setup_premium_and_config(self, guild_id=12345):
        create_premium_subscription(
            guild_id=guild_id, owner_id=99999,
            stripe_customer_id="cus_test", stripe_subscription_id="sub_test",
            status="active",
        )
        init_mod_db()
        set_mod_config(
            guild_id=guild_id,
            spam_detection_enabled=1,
            spam_threshold=3,
            spam_window_seconds=5,
        )

    @pytest.mark.asyncio
    async def test_spam_disabled_ignored(self):
        """When spam detection is disabled, do not track or delete."""
        self._setup_premium_and_config()
        set_mod_config(12345, spam_detection_enabled=0)

        msg = MagicMock()
        msg.content = "spammy"
        msg.author.bot = False
        msg.author.id = 77777
        msg.author.send = AsyncMock()
        msg.guild = MagicMock()
        msg.guild.id = 12345
        msg.guild.name = "Test Guild"
        msg.delete = AsyncMock()

        await self._cog.on_message(msg)
        msg.delete.assert_not_called()
        assert self._cog._spam_tracker == {}  # No tracking when disabled

    @pytest.mark.asyncio
    async def test_spam_threshold_not_reached(self):
        """Messages below the spam threshold should not be deleted."""
        self._setup_premium_and_config()

        msg = MagicMock()
        msg.content = "hello"
        msg.author.bot = False
        msg.author.id = 77777
        msg.author.send = AsyncMock()
        msg.guild = MagicMock()
        msg.guild.id = 12345
        msg.guild.name = "Test Guild"
        msg.delete = AsyncMock()

        # First message — should not be deleted
        await self._cog.on_message(msg)
        msg.delete.assert_not_called()

        # Second identical message — should not be deleted (threshold=3)
        await self._cog.on_message(msg)
        msg.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_spam_threshold_reached(self):
        """After threshold duplicate messages, the message should be deleted."""
        self._setup_premium_and_config()

        msg = MagicMock()
        msg.content = "spammy"
        msg.author.bot = False
        msg.author.id = 77777
        msg.author.send = AsyncMock()
        msg.guild = MagicMock()
        msg.guild.id = 12345
        msg.guild.name = "Test Guild"
        msg.delete = AsyncMock()

        # Message 1
        await self._cog.on_message(msg)
        # Message 2
        await self._cog.on_message(msg)
        # Message 3 — should trigger delete (threshold=3)
        await self._cog.on_message(msg)
        msg.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_spam_different_content_resets(self):
        """Different content between messages should reset the counter."""
        self._setup_premium_and_config()

        msg1 = MagicMock()
        msg1.content = "hello"
        msg1.author.bot = False
        msg1.author.id = 77777
        msg1.author.send = AsyncMock()
        msg1.guild = MagicMock()
        msg1.guild.id = 12345
        msg1.guild.name = "Test Guild"
        msg1.delete = AsyncMock()

        msg2 = MagicMock()
        msg2.content = "world"
        msg2.author.bot = False
        msg2.author.id = 77777
        msg2.author.send = AsyncMock()
        msg2.guild = MagicMock()
        msg2.guild.id = 12345
        msg2.guild.name = "Test Guild"
        msg2.delete = AsyncMock()

        await self._cog.on_message(msg1)  # "hello" count=1
        await self._cog.on_message(msg2)  # "world" count=1 (reset)
        await self._cog.on_message(msg1)  # "hello" count=1 (reset from "world")
        # None should have been deleted
        msg1.delete.assert_not_called()
        msg2.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_spam_different_users_independent(self):
        """Spam tracking should be per-user."""
        self._setup_premium_and_config()

        def make_msg(user_id, content):
            m = MagicMock()
            m.content = content
            m.author.bot = False
            m.author.id = user_id
            m.author.send = AsyncMock()
            m.guild = MagicMock()
            m.guild.id = 12345
            m.guild.name = "Test Guild"
            m.delete = AsyncMock()
            return m

        user1_msg = make_msg(100, "spammy")
        user2_msg = make_msg(200, "spammy")

        # Both users send the same content
        await self._cog.on_message(user1_msg)
        await self._cog.on_message(user2_msg)
        await self._cog.on_message(user1_msg)
        await self._cog.on_message(user2_msg)
        await self._cog.on_message(user1_msg)  # user1 hits threshold
        user1_msg.delete.assert_called_once()
        user2_msg.delete.assert_not_called()  # user2 at 2/3

    @pytest.mark.asyncio
    async def test_premium_not_required_message_passes(self):
        """Without premium, spam detection should be skipped."""
        # No subscription created
        init_mod_db()
        set_mod_config(12345, spam_detection_enabled=1)

        msg = MagicMock()
        msg.content = "spammy"
        msg.author.bot = False
        msg.author.id = 77777
        msg.author.send = AsyncMock()
        msg.guild = MagicMock()
        msg.guild.id = 12345
        msg.guild.name = "Test Guild"
        msg.delete = AsyncMock()

        await self._cog.on_message(msg)
        msg.delete.assert_not_called()


# ── Run directly ────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import traceback

    bot_mock = MagicMock()
    cog_instance = ModerationCog(bot_mock)

    int_mock = MagicMock()
    int_mock.guild_id = 12345
    int_mock.guild.id = 12345
    int_mock.guild.name = "Test Guild"
    int_mock.user.id = 99999
    int_mock.user.guild_permissions.administrator = True
    int_mock.response.send_message = AsyncMock()

    tests = [
        # Cog init
        ("test_cog_compiles", lambda: TestCogInit().test_cog_compiles()),
        ("test_cog_init_creates_db", lambda: TestCogInit().test_cog_init_creates_db(bot_mock)),
        ("test_cog_has_bot_ref", lambda: TestCogInit().test_cog_has_bot_ref(cog_instance)),
        ("test_cog_commands_registered", lambda: TestCogInit().test_cog_commands_registered(cog_instance)),
        # Command signatures
        ("test_moderation_config_params", lambda: TestCommandSignatures().test_moderation_config_params(cog_instance)),
        ("test_keyword_add_params", lambda: TestCommandSignatures().test_keyword_add_params(cog_instance)),
        ("test_keyword_remove_params", lambda: TestCommandSignatures().test_keyword_remove_params(cog_instance)),
        ("test_keyword_list_params", lambda: TestCommandSignatures().test_keyword_list_params(cog_instance)),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            clean_mod_db()
            clean_premium_db()
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