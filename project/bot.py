"""Community Keeper - Discord Bot

Discordサーバーの管理・コミュニティ活性化を支援する多機能Bot。
This module implements the MVP features: welcome messages and polls.
"""

import os
import sys

import discord
from discord import Intents
from discord.ext import commands


class CommunityKeeper(commands.Bot):
    """Community Keeper Bot"""

    def __init__(self) -> None:
        intents = Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="/", intents=intents)

    async def on_ready(self) -> None:
        """Bot起動時の処理"""
        assert self.user is not None
        print(f"✅ Community Keeper 起動完了", file=sys.stderr)
        print(f"   Bot名: {self.user.name}", file=sys.stderr)
        print(f"   BotID: {self.user.id}", file=sys.stderr)
        print(f"   サーバー数: {len(self.guilds)}", file=sys.stderr)

        # Load cogs and sync slash commands
        await self.load_extension("poll_cog")
        await self.load_extension("reminder_cog")
        await self.load_extension("xp_cog")
        await self.load_extension("premium.premium_cog")
        await self.load_extension("premium.moderation_cog")
        await self.load_extension("premium.export_cog")
        await self.tree.sync()
        print(f"   ✅ スラッシュコマンド同期完了", file=sys.stderr)

    async def on_member_join(self, member: discord.Member) -> None:
        """新メンバー参加時のウェルカムメッセージ送信"""
        welcome_message = f"{member.mention}さん、ようこそ！{member.guild.name}へ！"
        channel = member.guild.system_channel
        if channel is not None and channel.permissions_for(member.guild.me).send_messages:
            await channel.send(welcome_message)

    async def on_member_remove(self, member: discord.Member) -> None:
        """メンバー退出時のメッセージ送信"""
        goodbye_message = f"{member.display_name}さんがサーバーを退出しました。"
        channel = member.guild.system_channel
        if channel is not None and channel.permissions_for(member.guild.me).send_messages:
            await channel.send(goodbye_message)


def main() -> None:
    """Botを起動する"""
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        print(
            "❌ 環境変数 DISCORD_BOT_TOKEN が設定されていません。",
            file=sys.stderr,
        )
        print("   export DISCORD_BOT_TOKEN='your_token_here'", file=sys.stderr)
        sys.exit(1)

    bot = CommunityKeeper()
    bot.run(token, log_handler=None)


if __name__ == "__main__":
    main()