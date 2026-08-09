"""Automatic moderation cog — keyword filter and spam detection (Premium)."""

from __future__ import annotations

import time

import discord
from discord import app_commands
from discord.ext import commands

from premium.moderation_db import (
    add_ng_word,
    get_mod_config,
    init_db,
    is_ng_word,
    list_ng_words,
    remove_ng_word,
    set_mod_config,
)
from premium.premium_db import get_active_subscription


# ── Helpers ──────────────────────────────────────────────────────────────────


def _is_premium(guild_id: int) -> bool:
    """Return True if the guild has an active premium subscription."""
    sub = get_active_subscription(guild_id)
    return sub is not None


# ── The Cog ──────────────────────────────────────────────────────────────────


class ModerationCog(commands.Cog):
    """Slash commands for automatic moderation (Premium)."""

    moderation = app_commands.Group(
        name="moderation",
        description="自動モデレーションの管理を行います（管理者専用、Premium）",
        guild_only=True,
    )

    keyword = app_commands.Group(
        name="keyword",
        description="フィルターキーワードの管理",
        parent=moderation,
    )

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        init_db()
        # Per-guild spam tracking: {(guild_id, user_id): (last_msg_time, last_msg_content, repeat_count)}
        self._spam_tracker: dict[tuple[int, int], tuple[float, str, int]] = {}

    # ------------------------------------------------------------------
    # /moderation config  —  Toggle filter & spam detection
    # ------------------------------------------------------------------

    @moderation.command(
        name="config",
        description="自動モデレーションの設定を行います（管理者専用、Premium）",
    )
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(
        keyword_filter="キーワードフィルターのON/OFF（1=ON, 0=OFF）",
        spam_detection="スパム検出のON/OFF（1=ON, 0=OFF）",
    )
    async def moderation_config(
        self,
        interaction: discord.Interaction,
        keyword_filter: app_commands.Range[int, 0, 1] | None = None,
        spam_detection: app_commands.Range[int, 0, 1] | None = None,
    ) -> None:
        """Update moderation config (admin only, Premium required)."""
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "❌ このコマンドはサーバー内でのみ使用できます。",
                ephemeral=True,
            )
            return

        if not _is_premium(interaction.guild_id):
            await interaction.response.send_message(
                "🌟 この機能は **Premiumプラン**（月額500円）限定です。\n"
                "`/premium` で詳細を確認してください。",
                ephemeral=True,
            )
            return

        kwargs: dict[str, int] = {}
        if keyword_filter is not None:
            kwargs["keyword_filter_enabled"] = keyword_filter
        if spam_detection is not None:
            kwargs["spam_detection_enabled"] = spam_detection

        config = set_mod_config(interaction.guild_id, **kwargs)

        embed = discord.Embed(
            title="✅ モデレーション設定を更新しました",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="キーワードフィルター",
            value="ON" if config["keyword_filter_enabled"] else "OFF",
            inline=True,
        )
        embed.add_field(
            name="スパム検出",
            value="ON" if config["spam_detection_enabled"] else "OFF",
            inline=True,
        )
        embed.set_footer(text=f"ギルドID: {interaction.guild_id}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # /moderation keyword add  —  Add a keyword to the filter list
    # ------------------------------------------------------------------

    @keyword.command(
        name="add",
        description="フィルター対象のキーワードを追加します（管理者専用、Premium）",
    )
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(word="追加するキーワード")
    async def keyword_add(
        self,
        interaction: discord.Interaction,
        word: str,
    ) -> None:
        """Add a keyword to the NG list (admin only, Premium)."""
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "❌ このコマンドはサーバー内でのみ使用できます。",
                ephemeral=True,
            )
            return

        if not _is_premium(interaction.guild_id):
            await interaction.response.send_message(
                "🌟 この機能は **Premiumプラン**（月額500円）限定です。\n"
                "`/premium` で詳細を確認してください。",
                ephemeral=True,
            )
            return

        normalized = word.lower().strip()
        if not normalized:
            await interaction.response.send_message(
                "❌ 空のキーワードは追加できません。",
                ephemeral=True,
            )
            return

        if is_ng_word(interaction.guild_id, normalized):
            await interaction.response.send_message(
                f"⚠️ キーワード `{normalized}` は既に登録されています。",
                ephemeral=True,
            )
            return

        add_ng_word(interaction.guild_id, normalized)
        await interaction.response.send_message(
            f"✅ キーワード `{normalized}` を追加しました。",
            ephemeral=True,
        )

    # ------------------------------------------------------------------
    # /moderation keyword remove  —  Remove a keyword from the filter list
    # ------------------------------------------------------------------

    @keyword.command(
        name="remove",
        description="フィルター対象のキーワードを削除します（管理者専用、Premium）",
    )
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(word="削除するキーワード")
    async def keyword_remove(
        self,
        interaction: discord.Interaction,
        word: str,
    ) -> None:
        """Remove a keyword from the NG list (admin only, Premium)."""
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "❌ このコマンドはサーバー内でのみ使用できます。",
                ephemeral=True,
            )
            return

        if not _is_premium(interaction.guild_id):
            await interaction.response.send_message(
                "🌟 この機能は **Premiumプラン**（月額500円）限定です。\n"
                "`/premium` で詳細を確認してください。",
                ephemeral=True,
            )
            return

        normalized = word.lower().strip()
        if remove_ng_word(interaction.guild_id, normalized):
            await interaction.response.send_message(
                f"✅ キーワード `{normalized}` を削除しました。",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ キーワード `{normalized}` は登録されていません。",
                ephemeral=True,
            )

    # ------------------------------------------------------------------
    # /moderation keyword list  —  List all keywords
    # ------------------------------------------------------------------

    @keyword.command(
        name="list",
        description="登録されているフィルターキーワード一覧を表示します（Premium）",
    )
    @app_commands.default_permissions(manage_messages=True)
    async def keyword_list(self, interaction: discord.Interaction) -> None:
        """List all registered NG keywords (Premium)."""
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "❌ このコマンドはサーバー内でのみ使用できます。",
                ephemeral=True,
            )
            return

        if not _is_premium(interaction.guild_id):
            await interaction.response.send_message(
                "🌟 この機能は **Premiumプラン**（月額500円）限定です。\n"
                "`/premium` で詳細を確認してください。",
                ephemeral=True,
            )
            return

        words = list_ng_words(interaction.guild_id)
        if not words:
            await interaction.response.send_message(
                "📭 登録されているキーワードはありません。",
                ephemeral=True,
            )
            return

        lines = [f"{i + 1}. `{w['word']}`" for i, w in enumerate(words)]
        embed = discord.Embed(
            title="📋 フィルターキーワード一覧",
            description="\n".join(lines),
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"全{len(words)}件")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # on_message  —  Keyword filter + Spam detection
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Filter messages containing NG keywords and detect spam.

        Only acts on guild text messages when moderation is enabled and
        the guild has an active Premium subscription.
        """
        # Ignore bot messages and DMs
        if message.author.bot or message.guild is None:
            return

        guild_id = message.guild.id

        # Premium check
        if not _is_premium(guild_id):
            return

        config = get_mod_config(guild_id)
        if config is None:
            return

        keyword_enabled = config.get("keyword_filter_enabled", 0)
        spam_enabled = config.get("spam_detection_enabled", 0)
        spam_threshold = config.get("spam_threshold", 3)
        spam_window = config.get("spam_window_seconds", 5)

        content_lower = message.content.lower().strip()
        if not content_lower:
            return

        # ── Keyword filter ─────────────────────────────────────────────
        if keyword_enabled:
            words = list_ng_words(guild_id)
            for entry in words:
                if entry["word"] in content_lower:
                    try:
                        await message.delete()
                    except (discord.NotFound, discord.Forbidden):
                        pass
                    # Notify the user
                    try:
                        await message.author.send(
                            f"⚠️ あなたのメッセージが **{message.guild.name}** で"
                            f"自動削除されました（禁止ワードを含むため）。"
                        )
                    except (discord.Forbidden, discord.HTTPException):
                        pass
                    return

        # ── Spam detection (consecutive duplicate messages) ───────────
        if spam_enabled:
            key = (guild_id, message.author.id)
            now = time.time()
            last_time, last_content, repeat_count = self._spam_tracker.get(
                key, (0.0, "", 0),
            )

            if (
                now - last_time < spam_window
                and content_lower == last_content
            ):
                repeat_count += 1
                # +1 because repeat_count counts duplicates (0‑based) while
                # spam_threshold is a 1‑based count of total identical messages
                if repeat_count + 1 >= spam_threshold:
                    try:
                        await message.delete()
                    except (discord.NotFound, discord.Forbidden):
                        pass
                    try:
                        await message.author.send(
                            f"⚠️ **{message.guild.name}** でスパムと判断された"
                            f"メッセージを自動削除しました。"
                        )
                    except (discord.Forbidden, discord.HTTPException):
                        pass
                    # Reset counter after action so next non-duplicate starts fresh
                    self._spam_tracker[key] = (now, content_lower, 0)
                    return
            else:
                repeat_count = 0

            self._spam_tracker[key] = (now, content_lower, repeat_count)

            # Clean up stale entries periodically
            if len(self._spam_tracker) > 1000:
                cutoff = now - 60
                stale_keys = [
                    k for k, (t, _, _) in self._spam_tracker.items() if t < cutoff
                ]
                for k in stale_keys:
                    del self._spam_tracker[k]


async def setup(bot: commands.Bot) -> None:
    """Load the ModerationCog."""
    await bot.add_cog(ModerationCog(bot))