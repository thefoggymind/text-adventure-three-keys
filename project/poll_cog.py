"""Poll/Ankēto (Survey) commands cog."""

from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

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


class PollCog(commands.Cog):
    """Slash commands for creating and managing polls."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        init_db()

    # ------------------------------------------------------------------
    # /poll  –  Create a new poll
    # ------------------------------------------------------------------

    @app_commands.command(name="poll", description="投票/アンケートを作成します")
    @app_commands.describe(
        question="投票の質問",
        option1="選択肢1（必須）",
        option2="選択肢2（必須）",
        option3="選択肢3（任意）",
        option4="選択肢4（任意）",
        option5="選択肢5（任意）",
        option6="選択肢6（任意）",
        option7="選択肢7（任意）",
        option8="選択肢8（任意）",
        option9="選択肢9（任意）",
        option10="選択肢10（任意）",
        duration="投票期間（秒）。例: 3600（1時間）、86400（1日）",
        anonymous="匿名投票にする（True=匿名）",
    )
    async def poll(
        self,
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: Optional[str] = None,
        option4: Optional[str] = None,
        option5: Optional[str] = None,
        option6: Optional[str] = None,
        option7: Optional[str] = None,
        option8: Optional[str] = None,
        option9: Optional[str] = None,
        option10: Optional[str] = None,
        duration: Optional[int] = None,
        anonymous: Optional[bool] = None,
    ) -> None:
        """Create a poll with up to 10 options."""
        # Collect non-None options
        raw_options = [option1, option2]
        for opt in (option3, option4, option5, option6, option7, option8, option9, option10):
            if opt is not None:
                raw_options.append(opt)

        if len(raw_options) < 2:
            await interaction.response.send_message(
                "❌ 少なくとも2つの選択肢が必要です。", ephemeral=True
            )
            return

        options = raw_options[:10]

        # Insert into DB first to get poll_id
        anon = anonymous or False
        poll_id = create_poll(
            guild_id=interaction.guild_id or 0,
            channel_id=interaction.channel_id or 0,
            question=question,
            options=options,
            creator_id=interaction.user.id,
            duration_seconds=duration,
            anonymous=anon,
        )

        # Build embed
        desc_lines: list[str] = []
        for i, opt in enumerate(options):
            desc_lines.append(f"{EMOJI_OPTIONS[i]} {opt}")
        description = "\n".join(desc_lines)

        embed = discord.Embed(
            title=f"\U0001f4ca {question}",
            description=description,
            color=discord.Color.blue(),
        )
        embed.set_footer(
            text=f"投票ID: {poll_id} | 作成者: {interaction.user.display_name}"
        )

        if duration:
            mins = duration // 60
            secs = duration % 60
            if mins >= 60:
                hours = mins // 60
                mins %= 60
                dur_str = f"{hours}時間{mins}分"
            else:
                dur_str = f"{mins}分{secs}秒" if secs else f"{mins}分"
            embed.add_field(name="\u23f1\ufe0f 期限", value=dur_str, inline=True)

        if anon:
            embed.add_field(name="\U0001f575\ufe0f 匿名", value="ON", inline=True)

        embed.add_field(
            name="\U0001f6a9 投票方法",
            value="該当するリアクションをクリックしてください",
            inline=False,
        )

        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        # Save message_id
        set_message_id(poll_id, msg.id)

        # Add reaction options
        for i in range(len(options)):
            await msg.add_reaction(EMOJI_OPTIONS[i])

    # ------------------------------------------------------------------
    # /poll_result  –  Show poll results
    # ------------------------------------------------------------------

    @app_commands.command(name="poll_result", description="投票の結果を表示します")
    @app_commands.describe(poll_id="表示する投票のID")
    async def poll_result(
        self, interaction: discord.Interaction, poll_id: int
    ) -> None:
        """Display results for a specific poll."""
        poll = get_poll(poll_id)
        if poll is None:
            await interaction.response.send_message(
                f"❌ 投票ID `{poll_id}` が見つかりません。", ephemeral=True
            )
            return

        options: list[str] = poll["options"]
        results = get_results(poll_id)
        total = get_total_voters(poll_id)

        embed = discord.Embed(
            title=f"\U0001f4ca 結果: {poll['question']}",
            color=discord.Color.green(),
        )

        if has_expired(poll):
            embed.description = "⏰ この投票は終了しています。"
        else:
            embed.description = "\U0001f552 投票受付中"

        max_votes = max(results.values()) if results else 0
        bar_max = 20

        for i, opt in enumerate(options):
            count = results.get(i, 0)
            bar_len = int((count / max_votes * bar_max)) if max_votes > 0 else 0
            bar = "\u2588" * bar_len + "\u2591" * (bar_max - bar_len)
            embed.add_field(
                name=f"{EMOJI_OPTIONS[i]} {opt}",
                value=f"`{bar}` {count}票",
                inline=False,
            )

        embed.set_footer(text=f"投票ID: {poll_id} | 総投票数: {total}")

        if poll["anonymous"]:
            embed.add_field(
                name="\U0001f575\ufe0f 匿名投票",
                value="この投票は匿名で行われました。",
                inline=False,
            )

        await interaction.response.send_message(embed=embed)

    # ------------------------------------------------------------------
    # /poll_list  –  List active polls
    # ------------------------------------------------------------------

    @app_commands.command(name="poll_list", description="サーバーのアクティブな投票一覧を表示します")
    async def poll_list(self, interaction: discord.Interaction) -> None:
        """List all active (non-expired) polls in this guild."""
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "❌ このコマンドはサーバー内でのみ使用できます。", ephemeral=True
            )
            return

        polls = get_active_polls(interaction.guild_id)

        if not polls:
            await interaction.response.send_message(
                "\U0001f4ed アクティブな投票はありません。", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="\U0001f4ca アクティブな投票一覧",
            color=discord.Color.blue(),
        )

        for p in polls:
            channel = self.bot.get_channel(p["channel_id"])
            channel_name = f"#{channel.name}" if channel else f"<#{p['channel_id']}>"
            total = get_total_voters(p["id"])
            embed.add_field(
                name=f"ID {p['id']}: {p['question']}",
                value=(
                    f"チャンネル: {channel_name}\n"
                    f"選択肢数: {len(p['options'])} | 投票数: {total}"
                ),
                inline=False,
            )

        await interaction.response.send_message(embed=embed)

    # ------------------------------------------------------------------
    # Raw reaction listener  –  Count votes
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self, payload: discord.RawReactionActionEvent
    ) -> None:
        """Handle reaction adds to count votes on poll messages."""
        # Ignore bot's own reactions
        if payload.user_id == self.bot.user.id:
            return

        # Only track reactions on known poll messages
        poll = get_poll_by_message(payload.message_id)
        if poll is None:
            return

        # If poll has expired, ignore
        if has_expired(poll):
            return

        # Check if the reaction is a valid option emoji
        emoji_str = str(payload.emoji)
        options: list[str] = poll["options"]

        try:
            idx = EMOJI_OPTIONS.index(emoji_str)
        except ValueError:
            return  # Not a valid option emoji for our polls

        if idx >= len(options):
            return

        # For anonymous polls, don't store votes (just count reactions on the message)
        if poll["anonymous"]:
            return

        # Record the vote
        cast_vote(poll["id"], payload.user_id, idx)

        # Update the message embed footer to show new count
        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            return
        try:
            msg = await channel.fetch_message(payload.message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return

        if not msg.embeds:
            return

        embed = msg.embeds[0]
        total = get_total_voters(poll["id"])
        embed.set_footer(
            text=f"投票ID: {poll['id']} | 作成者: ... | 投票数: {total}"
        )
        try:
            await msg.edit(embed=embed)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass


async def setup(bot: commands.Bot) -> None:
    """Load the PollCog."""
    await bot.add_cog(PollCog(bot))