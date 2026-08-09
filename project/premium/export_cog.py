"""Data export commands cog for Premium users.

Provides the ``/export`` command group for exporting server data in CSV
and JSON format.  Every subcommand requires **administrator** permission
or guild-owner status; premium-subscription information is further
restricted to the guild owner.
"""

from __future__ import annotations

import csv
import io
import json

import discord
from discord import app_commands
from discord.ext import commands

from premium.export_db import (
    export_moderation_config,
    export_premium_info,
    export_reminders,
    export_xp_data,
)

_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ── Cog ──────────────────────────────────────────────────────────────────────


class ExportCog(commands.Cog):
    """Slash commands for data export (Premium)."""

    export = app_commands.Group(
        name="export",
        description="サーバーデータをエクスポートします（管理者専用、Premum）",
        guild_only=True,
    )

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------
    # Permission helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_admin_or_owner(interaction: discord.Interaction) -> bool:
        """Return True if the user is an admin or the guild owner."""
        assert interaction.guild is not None
        return (
            interaction.guild.owner_id == interaction.user.id
            or interaction.user.guild_permissions.administrator
        )

    @staticmethod
    def _is_owner(interaction: discord.Interaction) -> bool:
        """Return True if the user is the guild owner."""
        assert interaction.guild is not None
        return interaction.guild.owner_id == interaction.user.id

    async def _check_permission(
        self,
        interaction: discord.Interaction,
        *,
        require_owner: bool = False,
    ) -> bool:
        """Check permissions and send an ephemeral error embed if insufficient.

        Returns ``True`` when the check passes.
        """
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ このコマンドはサーバー内でのみ使用できます。",
                ephemeral=True,
            )
            return False

        if require_owner:
            if not self._is_owner(interaction):
                embed = discord.Embed(
                    title="❌ 権限がありません",
                    description=(
                        "この操作はサーバーオーナーのみ実行できます。"
                    ),
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return False
        else:
            if not self._is_admin_or_owner(interaction):
                embed = discord.Embed(
                    title="❌ 権限がありません",
                    description=(
                        "このコマンドは管理者または"
                        "サーバーオーナーのみ実行できます。"
                    ),
                    color=discord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return False

        return True

    # ------------------------------------------------------------------
    # File helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _dicts_to_csv(data: list[dict]) -> str:
        """Convert a list of dicts to a CSV string."""
        if not data:
            return ""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()

    @staticmethod
    def _make_file(content: str, filename: str) -> discord.File | None:
        """Build a :class:`discord.File` from *content*, or ``None`` if
        the UTF-8 encoded payload exceeds 10 MB."""
        encoded = content.encode("utf-8")
        if len(encoded) > _MAX_FILE_SIZE:
            return None
        return discord.File(io.BytesIO(encoded), filename=filename)

    # ------------------------------------------------------------------
    # /export xp
    # ------------------------------------------------------------------

    @export.command(
        name="xp",
        description="XPデータをCSV/JSONでエクスポートします（管理者専用）",
    )
    @app_commands.default_permissions(administrator=True)
    async def export_xp_cmd(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """Export XP data as CSV + JSON."""
        if not await self._check_permission(interaction):
            return
        assert interaction.guild_id is not None

        try:
            data = export_xp_data(interaction.guild_id)
        except Exception as exc:
            embed = discord.Embed(
                title="❌ データ取得エラー",
                description=f"XPデータの取得に失敗しました: {exc}",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not data:
            embed = discord.Embed(
                title="📭 データはありません",
                description="このサーバーにはエクスポート可能なXPデータがまだありません。",
                color=discord.Color.orange(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        csv_str = self._dicts_to_csv(data)
        json_str = json.dumps(data, ensure_ascii=False, indent=2)

        csv_file = self._make_file(csv_str, f"xp_data_{interaction.guild_id}.csv")
        json_file = self._make_file(json_str, f"xp_data_{interaction.guild_id}.json")

        if csv_file is None or json_file is None:
            embed = discord.Embed(
                title="❌ ファイルサイズ超過",
                description="生成されたファイルが10MBを超えているため送信できません。",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.send_message(
            f"📊 XPデータ（{len(data)}件）をエクスポートしました。",
            files=[csv_file, json_file],
            ephemeral=True,
        )

    # ------------------------------------------------------------------
    # /export reminders
    # ------------------------------------------------------------------

    @export.command(
        name="reminders",
        description="リマインダー一覧をCSV/JSONでエクスポートします（管理者専用）",
    )
    @app_commands.default_permissions(administrator=True)
    async def export_reminders_cmd(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """Export reminders as CSV + JSON."""
        if not await self._check_permission(interaction):
            return
        assert interaction.guild_id is not None

        try:
            data = export_reminders(interaction.guild_id)
        except Exception as exc:
            embed = discord.Embed(
                title="❌ データ取得エラー",
                description=f"リマインダーデータの取得に失敗しました: {exc}",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not data:
            embed = discord.Embed(
                title="📭 データはありません",
                description="このサーバーにはエクスポート可能なリマインダーデータがまだありません。",
                color=discord.Color.orange(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        csv_str = self._dicts_to_csv(data)
        json_str = json.dumps(data, ensure_ascii=False, indent=2)

        csv_file = self._make_file(csv_str, f"reminders_{interaction.guild_id}.csv")
        json_file = self._make_file(json_str, f"reminders_{interaction.guild_id}.json")

        if csv_file is None or json_file is None:
            embed = discord.Embed(
                title="❌ ファイルサイズ超過",
                description="生成されたファイルが10MBを超えているため送信できません。",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.send_message(
            f"📝 リマインダー一覧（{len(data)}件）をエクスポートしました。",
            files=[csv_file, json_file],
            ephemeral=True,
        )

    # ------------------------------------------------------------------
    # /export config
    # ------------------------------------------------------------------

    @export.command(
        name="config",
        description="モデレーション設定をJSONでエクスポートします（管理者専用）",
    )
    @app_commands.default_permissions(administrator=True)
    async def export_config_cmd(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """Export moderation configuration as JSON."""
        if not await self._check_permission(interaction):
            return
        assert interaction.guild_id is not None

        try:
            data = export_moderation_config(interaction.guild_id)
        except Exception as exc:
            embed = discord.Embed(
                title="❌ データ取得エラー",
                description=f"モデレーション設定の取得に失敗しました: {exc}",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        json_file = self._make_file(json_str, f"mod_config_{interaction.guild_id}.json")

        if json_file is None:
            embed = discord.Embed(
                title="❌ ファイルサイズ超過",
                description="生成されたファイルが10MBを超えているため送信できません。",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.send_message(
            "⚙️ モデレーション設定をエクスポートしました。",
            files=[json_file],
            ephemeral=True,
        )

    # ------------------------------------------------------------------
    # /export all
    # ------------------------------------------------------------------

    @export.command(
        name="all",
        description="全データを一括エクスポートします（管理者専用）",
    )
    @app_commands.default_permissions(administrator=True)
    async def export_all_cmd(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """Export all data (XP, reminders, config, and optionally premium
        info for the guild owner)."""
        if not await self._check_permission(interaction):
            return
        assert interaction.guild_id is not None

        files: list[discord.File] = []
        errors: list[str] = []
        gid = interaction.guild_id

        # XP data ──────────────────────────────────────────────────────
        try:
            data = export_xp_data(gid)
            csv_str = self._dicts_to_csv(data)
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            f1 = self._make_file(csv_str, f"xp_data_{gid}.csv")
            f2 = self._make_file(json_str, f"xp_data_{gid}.json")
            if f1:
                files.append(f1)
            if f2:
                files.append(f2)
        except Exception as exc:
            errors.append(f"XPデータ: {exc}")

        # Reminders ────────────────────────────────────────────────────
        try:
            data = export_reminders(gid)
            csv_str = self._dicts_to_csv(data)
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            f1 = self._make_file(csv_str, f"reminders_{gid}.csv")
            f2 = self._make_file(json_str, f"reminders_{gid}.json")
            if f1:
                files.append(f1)
            if f2:
                files.append(f2)
        except Exception as exc:
            errors.append(f"リマインダー: {exc}")

        # Moderation config ────────────────────────────────────────────
        try:
            data = export_moderation_config(gid)
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            f = self._make_file(json_str, f"mod_config_{gid}.json")
            if f:
                files.append(f)
        except Exception as exc:
            errors.append(f"モデレーション設定: {exc}")

        # Premium info (owner only) ────────────────────────────────────
        if self._is_owner(interaction):
            try:
                data = export_premium_info(gid)
                if data is not None:
                    json_str = json.dumps(data, ensure_ascii=False, indent=2)
                    f = self._make_file(json_str, f"premium_info_{gid}.json")
                    if f:
                        files.append(f)
            except Exception as exc:
                errors.append(f"プレミアム情報: {exc}")

        # Response ─────────────────────────────────────────────────────
        if not files:
            embed = discord.Embed(
                title="❌ エクスポート失敗",
                description="エクスポート可能なデータがありませんでした。"
                + ("\n" + "\n".join(errors) if errors else ""),
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        desc = f"📦 全データ（{len(files)}ファイル）をエクスポートしました。"
        if errors:
            desc += "\n⚠️ 一部のデータでエラーが発生しました:\n" + "\n".join(
                f"  - {e}" for e in errors
            )

        await interaction.response.send_message(
            desc,
            files=files,
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    """Load ExportCog."""
    await bot.add_cog(ExportCog(bot))