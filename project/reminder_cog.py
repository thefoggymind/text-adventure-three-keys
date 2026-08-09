"""Reminder commands cog with background notification loop."""

import re
import time
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

from reminder_db import (
    cancel_reminder,
    create_reminder,
    get_active_reminders,
    get_active_reminders_count_by_guild,
    get_due_reminders,
    init_db,
    mark_triggered,
)

_FREE_MAX_REMINDERS = 3

_JST = timezone(timedelta(hours=9))

_RELATIVE_PATTERNS: list[tuple[re.Pattern[str], float]] = [
    (re.compile(r"(\d+)\s*分"), 60),
    (re.compile(r"(\d+)\s*時間"), 3600),
    (re.compile(r"(\d+)\s*日"), 86400),
    (re.compile(r"(\d+)\s*週間?"), 604800),
    (re.compile(r"(\d+)\s*秒"), 1),
]


def _parse_relative_time(text: str) -> float | None:
    """Parse a relative time string like '30分' or '2時間' into seconds."""
    total = 0.0
    matched = False
    for pattern, multiplier in _RELATIVE_PATTERNS:
        m = pattern.search(text)
        if m:
            total += int(m.group(1)) * multiplier
            matched = True
    return total if matched else None


def _format_remind_at(timestamp: float) -> str:
    dt = datetime.fromtimestamp(timestamp, tz=_JST)
    return dt.strftime("%Y-%m-%d %H:%M (%a)")


class ReminderCog(commands.Cog):
    """Slash commands for managing reminders."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        init_db()
        self.reminder_loop.start()

    def cog_unload(self) -> None:
        self.reminder_loop.cancel()

    # ------------------------------------------------------------------
    # Background loop: check due reminders every 60 seconds
    # ------------------------------------------------------------------

    @tasks.loop(seconds=60)
    async def reminder_loop(self) -> None:
        """Check for due reminders and send notifications."""
        due = get_due_reminders()
        for rem in due:
            try:
                user = await self.bot.fetch_user(rem["user_id"])
                channel = self.bot.get_channel(rem["channel_id"])
                if channel is None:
                    try:
                        channel = await self.bot.fetch_channel(rem["channel_id"])
                    except Exception:
                        channel = None

                embed = discord.Embed(
                    title="\u23f0 \u304a\u77e5\u3089\u305b",
                    description=rem["message"],
                    color=discord.Color.gold(),
                    timestamp=datetime.fromtimestamp(rem["created_at"], tz=_JST),
                )
                embed.set_footer(text="\u4f5c\u6210\u65e5\u6642")

                # Try DM first, fall back to the original channel
                if user is not None:
                    try:
                        await user.send(embed=embed)
                    except (discord.Forbidden, discord.HTTPException):
                        if channel is not None:
                            await channel.send(
                                f"{user.mention} \u23f0 \u30ea\u30de\u30a4\u30f3\u30c0\u30fc\u3067\u3059\uff01",
                                embed=embed,
                            )
                elif channel is not None:
                    await channel.send(
                        embed=embed,
                    )

                mark_triggered(rem["id"])
            except Exception:
                # Don't let one failure block the rest
                mark_triggered(rem["id"])

    @reminder_loop.before_loop
    async def before_reminder_loop(self) -> None:
        await self.bot.wait_until_ready()

    # ── Premium gate: check reminder limit ─────────────────────────────

    @staticmethod
    def _get_max_reminders(guild_id: int) -> int:
        """Return max_reminders for the guild (free default=3, premium=config)."""
        try:
            from premium.premium_db import get_guild_premium_config
            config = get_guild_premium_config(guild_id)
            if config and config.get("max_reminders") is not None:
                return config["max_reminders"]
        except Exception:
            pass
        return _FREE_MAX_REMINDERS

    # ------------------------------------------------------------------
    # /remind  –  Absolute datetime reminder
    # ------------------------------------------------------------------

    @app_commands.command(name="remind", description="\u6307\u5b9a\u65e5\u6642\u306b\u30ea\u30de\u30a4\u30f3\u30c0\u30fc\u3092\u8a2d\u5b9a\u3057\u307e\u3059")
    @app_commands.describe(
        datetime_str="\u65e5\u6642\uff08\u4f8b: 2026-08-10 15:00 \u307e\u305f\u306f 08-10 15:00\uff09",
        message="\u30ea\u30de\u30a4\u30f3\u30c0\u30fc\u30e1\u30c3\u30bb\u30fc\u30b8",
    )
    async def remind(
        self,
        interaction: discord.Interaction,
        datetime_str: str,
        message: str,
    ) -> None:
        """Set a reminder for an absolute date/time."""
        parsed = self._parse_absolute(datetime_str)
        if parsed is None:
            await interaction.response.send_message(
                "\u274c \u65e5\u6642\u306e\u30d5\u30a9\u30fc\u30de\u30c3\u30c8\u304c\u8a8d\u8b58\u3067\u304d\u307e\u305b\u3093\u3002"
                "\u4f8b: `2026-08-10 15:00` \u307e\u305f\u306f `08-10 15:00`",
                ephemeral=True,
            )
            return

        now = time.time()
        if parsed <= now:
            await interaction.response.send_message(
                "\u274c \u904e\u53bb\u306e\u65e5\u6642\u306f\u6307\u5b9a\u3067\u304d\u307e\u305b\u3093\u3002",
                ephemeral=True,
            )
            return

        # Premium gate: enforce max_reminders
        guild_id = interaction.guild_id or 0
        max_reminders = self._get_max_reminders(guild_id)
        current_count = get_active_reminders_count_by_guild(guild_id)
        if current_count >= max_reminders:
            await interaction.response.send_message(
                f"\u274c \u3053\u306e\u30ae\u30eb\u30c9\u306e\u6700\u5927\u30ea\u30de\u30a4\u30f3\u30c0\u30fc\u6570\u306f{max_reminders}\u3067\u3059\u3002"
                "\u30d7\u30ec\u30df\u30a2\u30e0\u306b\u30a2\u30c3\u30d7\u30b0\u30ec\u30fc\u30c9\u3059\u308b\u3068\u5236\u9650\u304c\u89e3\u9664\u3055\u308c\u307e\u3059\u3002",
                ephemeral=True,
            )
            return

        reminder_id = create_reminder(
            user_id=interaction.user.id,
            channel_id=interaction.channel_id or 0,
            message=message,
            remind_at=parsed,
            guild_id=guild_id,
        )

        embed = discord.Embed(
            title="\u2705 \u30ea\u30de\u30a4\u30f3\u30c0\u30fc\u3092\u8a2d\u5b9a\u3057\u307e\u3057\u305f",
            description=message,
            color=discord.Color.green(),
        )
        embed.add_field(
            name="\u23f0 \u5b9f\u884c\u65e5\u6642",
            value=_format_remind_at(parsed),
            inline=True,
        )
        embed.add_field(
            name="ID",
            value=str(reminder_id),
            inline=True,
        )

        await interaction.response.send_message(embed=embed)

    # ------------------------------------------------------------------
    # /remind_in  –  Relative time reminder
    # ------------------------------------------------------------------

    @app_commands.command(name="remind_in", description="\u76f8\u5bfe\u6642\u9593\u3067\u30ea\u30de\u30a4\u30f3\u30c0\u30fc\u3092\u8a2d\u5b9a\u3057\u307e\u3059")
    @app_commands.describe(
        relative="\u76f8\u5bfe\u6642\u9593\uff08\u4f8b: 30\u5206\u5f8c\u30012\u6642\u9593\u5f8c\u30011\u65e5\u5f8c\uff09",
        message="\u30ea\u30de\u30a4\u30f3\u30c0\u30fc\u30e1\u30c3\u30bb\u30fc\u30b8",
    )
    async def remind_in(
        self,
        interaction: discord.Interaction,
        relative: str,
        message: str,
    ) -> None:
        """Set a reminder using relative time like '30\u5206\u5f8c'."""
        seconds = _parse_relative_time(relative)
        if seconds is None:
            await interaction.response.send_message(
                "\u274c \u6642\u9593\u306e\u30d5\u30a9\u30fc\u30de\u30c3\u30c8\u304c\u8a8d\u8b58\u3067\u304d\u307e\u305b\u3093\u3002"
                "\u4f8b: `30\u5206` `2\u6642\u9593` `1\u65e5`",
                ephemeral=True,
            )
            return

        if seconds < 60:
            await interaction.response.send_message(
                "\u274c \u6700\u77ed\u3067\u3080\u309360\u79d2\u4ee5\u4e0a\u3092\u6307\u5b9a\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
                ephemeral=True,
            )
            return

        # Premium gate: enforce max_reminders
        guild_id = interaction.guild_id or 0
        max_reminders = self._get_max_reminders(guild_id)
        current_count = get_active_reminders_count_by_guild(guild_id)
        if current_count >= max_reminders:
            await interaction.response.send_message(
                f"\u274c \u3053\u306e\u30ae\u30eb\u30c9\u306e\u6700\u5927\u30ea\u30de\u30a4\u30f3\u30c0\u30fc\u6570\u306f{max_reminders}\u3067\u3059\u3002"
                "\u30d7\u30ec\u30df\u30a2\u30e0\u306b\u30a2\u30c3\u30d7\u30b0\u30ec\u30fc\u30c9\u3059\u308b\u3068\u5236\u9650\u304c\u89e3\u9664\u3055\u308c\u307e\u3059\u3002",
                ephemeral=True,
            )
            return

        remind_at = time.time() + seconds
        reminder_id = create_reminder(
            user_id=interaction.user.id,
            channel_id=interaction.channel_id or 0,
            message=message,
            remind_at=remind_at,
            guild_id=guild_id,
        )

        embed = discord.Embed(
            title="\u2705 \u30ea\u30de\u30a4\u30f3\u30c0\u30fc\u3092\u8a2d\u5b9a\u3057\u307e\u3057\u305f",
            description=message,
            color=discord.Color.green(),
        )
        embed.add_field(
            name="\u23f0 \u5b9f\u884c\u65e5\u6642",
            value=_format_remind_at(remind_at),
            inline=True,
        )
        embed.add_field(
            name="ID",
            value=str(reminder_id),
            inline=True,
        )

        await interaction.response.send_message(embed=embed)

    # ------------------------------------------------------------------
    # /reminders  –  List active reminders
    # ------------------------------------------------------------------

    @app_commands.command(name="reminders", description="\u81ea\u5206\u306e\u30a2\u30af\u30c6\u30a3\u30d6\u306a\u30ea\u30de\u30a4\u30f3\u30c0\u30fc\u4e00\u89a7\u3092\u8868\u793a\u3057\u307e\u3059")
    async def list_reminders(self, interaction: discord.Interaction) -> None:
        """Show all active (non-triggered) reminders for the user."""
        reminders = get_active_reminders(interaction.user.id)

        if not reminders:
            await interaction.response.send_message(
                "\U0001f4ed \u30a2\u30af\u30c6\u30a3\u30d6\u306a\u30ea\u30de\u30a4\u30f3\u30c0\u30fc\u306f\u3042\u308a\u307e\u305b\u3093\u3002",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="\u23f0 \u30a2\u30af\u30c6\u30a3\u30d6\u306a\u30ea\u30de\u30a4\u30f3\u30c0\u30fc",
            color=discord.Color.blue(),
        )

        for rem in reminders:
            embed.add_field(
                name=f"ID {rem['id']}: {_format_remind_at(rem['remind_at'])}",
                value=rem["message"][:200],
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # /cancel_reminder  –  Cancel a reminder by ID
    # ------------------------------------------------------------------

    @app_commands.command(name="cancel_reminder", description="\u30ea\u30de\u30a4\u30f3\u30c0\u30fc\u3092\u30ad\u30e3\u30f3\u30bb\u30eb\u3057\u307e\u3059")
    @app_commands.describe(reminder_id="\u30ad\u30e3\u30f3\u30bb\u30eb\u3059\u308b\u30ea\u30de\u30a4\u30f3\u30c0\u30fc\u306eID")
    async def cancel(
        self, interaction: discord.Interaction, reminder_id: int
    ) -> None:
        """Cancel a reminder by its ID (only own reminders)."""
        deleted = cancel_reminder(reminder_id, interaction.user.id)

        if deleted:
            await interaction.response.send_message(
                f"\u2705 \u30ea\u30de\u30a4\u30f3\u30c0\u30fc ID `{reminder_id}` \u3092\u30ad\u30e3\u30f3\u30bb\u30eb\u3057\u307e\u3057\u305f\u3002",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"\u274c \u30ea\u30de\u30a4\u30f3\u30c0\u30fc ID `{reminder_id}` \u304c\u898b\u3064\u304b\u308a\u307e\u305b\u3093\u3002"
                "\u307e\u305f\u306f\u65e2\u306b\u30ad\u30e3\u30f3\u30bb\u30eb\u6e08\u307f\u3067\u3059\u3002",
                ephemeral=True,
            )

    # ------------------------------------------------------------------
    # Helper: parse absolute datetime strings
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_absolute(text: str) -> float | None:
        """Try to parse a datetime string into a Unix timestamp."""
        text = text.strip()
        formats = [
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%m-%d %H:%M",
            "%m-%d %H:%M:%S",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(text, fmt)
                # If year not specified, use current year
                if "%Y" not in fmt:
                    now = datetime.now(_JST)
                    dt = dt.replace(year=now.year)
                dt = dt.replace(tzinfo=_JST)
                return dt.timestamp()
            except ValueError:
                continue
        return None


async def setup(bot: commands.Bot) -> None:
    """Load the ReminderCog."""
    await bot.add_cog(ReminderCog(bot))