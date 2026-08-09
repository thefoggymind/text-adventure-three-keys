"""XP/Leveling system cog."""

import math
import random

import discord
from discord import app_commands
from discord.ext import commands

import xp_db
from xp_db import (
    XP_COOLDOWN,
    LEVEL_BASE,
    award_xp,
    get_leaderboard,
    get_or_create_user,
    get_rank,
    get_total_members,
    init_db,
)

# Emoji medals for top 3
_MEDALS = ["\U0001f947", "\U0001f948", "\U0001f949"]  # 🥇🥈🥉


def _xp_for_level(level: int) -> int:
    """Return the minimum XP required for a given level."""
    return LEVEL_BASE * (level - 1) ** 2


def _progress_bar(current_xp: int, level: int, bar_max: int = 10) -> str:
    """Return a progress bar string showing XP progress to next level."""
    current_level_xp = _xp_for_level(level)
    next_level_xp = _xp_for_level(level + 1)
    progress = current_xp - current_level_xp
    needed = next_level_xp - current_level_xp
    if needed <= 0:
        return "\u2588" * bar_max  # filled (shouldn't happen)
    filled = int(progress / needed * bar_max)
    return "\u2588" * filled + "\u2591" * (bar_max - filled)


class XPCog(commands.Cog):
    """Manage XP and leveling for server members."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        init_db()

    # ------------------------------------------------------------------
    # Message listener — award XP with cooldown
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Award XP when a user sends a message (with cooldown)."""
        # Ignore bot messages and DMs
        if message.author.bot or message.guild is None:
            return

        guild_id = message.guild.id

        # ── Premium multiplier ──────────────────────────────────────────
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

        if multiplier != 1.0:
            orig_min = xp_db.XP_MIN
            orig_max = xp_db.XP_MAX
            xp_db.XP_MIN = max(1, int(orig_min * multiplier))
            xp_db.XP_MAX = max(1, int(orig_max * multiplier))
            try:
                new_xp, new_level, leveled_up = award_xp(
                    message.author.id, guild_id
                )
            finally:
                xp_db.XP_MIN = orig_min
                xp_db.XP_MAX = orig_max
        else:
            new_xp, new_level, leveled_up = award_xp(
                message.author.id, guild_id
            )

        if leveled_up:
            embed = discord.Embed(
                title="\U0001f389 レベルアップ！",
                description=(
                    f"{message.author.mention} が "
                    f"**レベル {new_level}** に到達しました！"
                ),
                color=discord.Color.gold(),
            )
            embed.add_field(
                name="\u2b50 現在のXP",
                value=str(new_xp),
                inline=True,
            )
            embed.add_field(
                name="\U0001f3af 次のレベルまで",
                value=f"{_xp_for_level(new_level + 1) - new_xp} XP",
                inline=True,
            )
            embed.set_footer(text="メッセージを送信してXPを獲得しましょう！")

            channel = message.channel
            if channel is not None and channel.permissions_for(
                message.guild.me
            ).send_messages:
                await channel.send(embed=embed)

    # ------------------------------------------------------------------
    # /rank  –  Show own rank
    # ------------------------------------------------------------------

    @app_commands.command(name="rank", description="サーバー内の自分のランクとXPを表示します")
    async def rank(self, interaction: discord.Interaction) -> None:
        """Display the user's rank, XP, and level in this guild."""
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "\u274c このコマンドはサーバー内でのみ使用できます。", ephemeral=True
            )
            return

        data = get_rank(interaction.user.id, interaction.guild_id)
        if data is None:
            await interaction.response.send_message(
                "\U0001f4ed まだXPを獲得していません。"
                "メッセージを送信してXPを獲得しましょう！",
                ephemeral=True,
            )
            return

        rank_pos = data["rank"]
        total = data["total"]
        xp = data["xp"]
        level = data["level"]
        bar = _progress_bar(xp, level)

        # Pick an emoji for the rank
        if rank_pos == 1:
            rank_emoji = "\U0001f451"  # 👑
        elif rank_pos <= 3:
            rank_emoji = _MEDALS[rank_pos - 1]
        elif rank_pos <= 10:
            rank_emoji = "\U0001f539"  # 🔹
        else:
            rank_emoji = "\U0001f538"  # 🔸

        embed = discord.Embed(
            title=f"{interaction.user.display_name} のランク",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="\U0001f3c6 ランク",
            value=f"{rank_emoji} **{rank_pos}/{total}**",
            inline=True,
        )
        embed.add_field(name="\U0001f396\ufe0f レベル", value=str(level), inline=True)
        embed.add_field(name="\u2b50 XP", value=str(xp), inline=False)
        embed.add_field(
            name="\U0001f4c8 次のレベルまで",
            value=f"`{bar}`\n残り {_xp_for_level(level + 1) - xp} XP",
            inline=False,
        )

        await interaction.response.send_message(embed=embed)

    # ------------------------------------------------------------------
    # /leaderboard  –  Show top 10
    # ------------------------------------------------------------------

    @app_commands.command(name="leaderboard", description="サーバー内のXPランキングトップ10を表示します")
    async def leaderboard(self, interaction: discord.Interaction) -> None:
        """Display the top 10 users by XP in this guild."""
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "\u274c このコマンドはサーバー内でのみ使用できます。", ephemeral=True
            )
            return

        entries = get_leaderboard(interaction.guild_id, limit=10)
        total_members = get_total_members(interaction.guild_id)

        if not entries:
            await interaction.response.send_message(
                "\U0001f4ed まだデータがありません。メッセージを送信してXPを獲得しましょう！",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"\U0001f3c6 ランキング — {interaction.guild.name}",
            description=f"トップ10 （全{total_members}人中）",
            color=discord.Color.gold(),
        )

        lines: list[str] = []
        for i, entry in enumerate(entries):
            user_id = entry["user_id"]
            xp = entry["xp"]
            level = entry["level"]

            # Try to fetch member name, fallback to user_id
            member = interaction.guild.get_member(user_id)
            name = member.display_name if member else f"<@{user_id}>"

            if i < 3:
                prefix = f"{_MEDALS[i]} **#{i + 1}**"
            else:
                prefix = f"`#{i + 1:>2}`"

            bar = _progress_bar(xp, level, bar_max=5)
            lines.append(f"{prefix} {name}  Lv.{level}  `{bar}` {xp}XP")

        embed.description += "\n\n" + "\n".join(lines)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Load the XPCog."""
    await bot.add_cog(XPCog(bot))