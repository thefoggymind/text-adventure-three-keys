"""Premium subscription commands cog.

Provides the `/premium` command group for managing Premium subscriptions
via Stripe Checkout Sessions, webhook signature verification, and
subscription status management.
"""

import os
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from premium.premium_db import (
    create_premium_subscription,
    get_active_subscription,
    get_guild_premium_config,
    get_stripe_event,
    init_db,
    record_stripe_event,
    set_guild_premium_config,
    update_subscription_status,
)

# ── Configuration ────────────────────────────────────────────────────────────

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "price_test_xxxx")

# ── Premium check utilities ──────────────────────────────────────────────────


def is_premium(guild_id: int) -> bool:
    """Return True if the guild has an active premium subscription."""
    sub = get_active_subscription(guild_id)
    return sub is not None


async def require_premium(interaction: discord.Interaction) -> bool:
    """Check premium status and send an ephemeral message if not premium.

    Returns True if the guild is premium, False otherwise.
    """
    if interaction.guild_id is None:
        await interaction.response.send_message(
            "❌ このコマンドはサーバー内でのみ使用できます。",
            ephemeral=True,
        )
        return False
    if not is_premium(interaction.guild_id):
        await interaction.response.send_message(
            "🌟 この機能は **Premiumプラン**（月額500円）限定です。\n"
            "`/premium` で詳細を確認してください。",
            ephemeral=True,
        )
        return False
    return True


# ── Stripe utility functions ─────────────────────────────────────────────────


def _get_stripe() -> Any:
    """Lazy-import and return the stripe module with the secret key set.

    Returns None if STRIPE_SECRET_KEY is not configured.
    """
    if not STRIPE_SECRET_KEY:
        return None
    import stripe as stripe_module

    stripe_module.api_key = STRIPE_SECRET_KEY
    return stripe_module


def create_checkout_session(
    guild_id: int,
    owner_id: int,
    success_url: str = "https://discord.com/app",
    cancel_url: str = "https://discord.com/app",
) -> dict[str, Any] | None:
    """Create a Stripe Checkout Session and return its data.

    Returns a dict with keys ``url`` and ``session_id`` on success,
    or None if Stripe is not configured or the API call fails.
    """
    stripe = _get_stripe()
    if stripe is None:
        return None

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
            client_reference_id=str(guild_id),
            metadata={"guild_id": str(guild_id), "owner_id": str(owner_id)},
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return {"url": session.url, "session_id": session.id}
    except Exception:
        return None


def cancel_stripe_subscription(stripe_subscription_id: str) -> bool:
    """Cancel a Stripe subscription at period end.

    Returns True if the cancellation was successful, False otherwise.
    """
    stripe = _get_stripe()
    if stripe is None:
        return False

    try:
        stripe.Subscription.modify(stripe_subscription_id, cancel_at_period_end=True)
        return True
    except Exception:
        return False


def verify_webhook_signature(
    payload: bytes,
    sig_header: str,
) -> dict[str, Any] | None:
    """Verify a Stripe webhook signature and return the parsed event.

    Returns the event dict on success, or None if verification fails.
    """
    if not STRIPE_WEBHOOK_SECRET:
        return None

    try:
        import stripe as stripe_module

        event = stripe_module.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
        return event
    except Exception:
        return None


# ── The Cog ──────────────────────────────────────────────────────────────────


class PremiumCog(commands.Cog):
    """Slash commands for Premium subscription management."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        init_db()

    # ------------------------------------------------------------------
    # /premium  —  Premium plan info + checkout URL
    # ------------------------------------------------------------------

    @app_commands.command(name="premium", description="Premiumプランの案内を表示します")
    async def premium_info(self, interaction: discord.Interaction) -> None:
        """Display Premium plan info and (if configured) a checkout URL."""
        embed = discord.Embed(
            title="\U0001f319 Community Keeper Premium",
            description="月額 **500円** で全機能が使い放題！",
            color=discord.Color.gold(),
        )
        embed.add_field(
            name="\u2728 Premium特典",
            value=(
                "\u2022 ウェルカムメッセージを自由にカスタマイズ\n"
                "\u2022 匿名投票・複数選択投票\n"
                "\u2022 リマインダー無制限\n"
                "\u2022 レベル連動ロール自動付与\n"
                "\u2022 XP倍率カスタマイズ\n"
                "\u2022 自動モデレーション（近日公開）"
            ),
            inline=False,
        )

        # Generate checkout URL if Stripe is configured
        if interaction.guild_id is not None and STRIPE_SECRET_KEY:
            session_data = create_checkout_session(
                guild_id=interaction.guild_id,
                owner_id=interaction.user.id,
            )
            if session_data and session_data.get("url"):
                embed.add_field(
                    name="\U0001f517 購入はこちら",
                    value=session_data["url"],
                    inline=False,
                )
        else:
            embed.add_field(
                name="\U0001f517 購入",
                value=(
                    "現在準備中です。お問い合わせはサーバー管理者まで。"
                    if not STRIPE_SECRET_KEY
                    else "購入URLを生成できませんでした。"
                ),
                inline=False,
            )

        embed.set_footer(text="/premium status で契約状態を確認できます")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # /premium status  —  Show subscription status
    # ------------------------------------------------------------------

    @app_commands.command(name="premium_status", description="自サーバーのPremium契約状態を表示します")
    @app_commands.default_permissions(manage_guild=True)
    async def premium_status(self, interaction: discord.Interaction) -> None:
        """Display the current premium subscription status for this guild."""
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "❌ このコマンドはサーバー内でのみ使用できます。",
                ephemeral=True,
            )
            return

        sub = get_active_subscription(interaction.guild_id)

        if sub is None:
            embed = discord.Embed(
                title="\u274c Premium 未契約",
                description=(
                    "このサーバーは無料プランをご利用中です。\n"
                    "\u200b\n"
                    "\U0001f319 `/premium` でプレミアムプランの詳細を確認できます。"
                ),
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        status_emoji = {
            "active": "\u2705",
            "past_due": "\u26a0\ufe0f",
            "canceled": "\U0001f6ab",
            "incomplete": "\u23f3",
        }
        status_label = {
            "active": "有効",
            "past_due": "支払い期限超過",
            "canceled": "解約済み",
            "incomplete": "未完了",
        }
        emoji = status_emoji.get(sub["status"], "\u2753")
        label = status_label.get(sub["status"], sub["status"])

        embed = discord.Embed(
            title=f"{emoji} Premium 契約状態",
            color=discord.Color.green() if sub["status"] == "active" else discord.Color.orange(),
        )
        embed.add_field(name="ステータス", value=label, inline=True)
        embed.add_field(name="契約者", value=f"<@{sub['owner_id']}>", inline=True)

        if sub["current_period_start"]:
            embed.add_field(
                name="契約開始日",
                value=sub["current_period_start"][:10],
                inline=True,
            )
        if sub["current_period_end"]:
            embed.add_field(
                name="次回更新日",
                value=sub["current_period_end"][:10],
                inline=True,
            )
        if sub["canceled_at"]:
            embed.add_field(
                name="解約日",
                value=sub["canceled_at"][:10],
                inline=True,
            )

        embed.set_footer(text=f"サブスクリプションID: {sub['stripe_subscription_id']}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # /premium cancel  —  Cancel subscription
    # ------------------------------------------------------------------

    @app_commands.command(name="premium_cancel", description="Premium契約を解約します（Stripe側にも反映）")
    @app_commands.default_permissions(manage_guild=True)
    async def premium_cancel(self, interaction: discord.Interaction) -> None:
        """Cancel the premium subscription for this guild."""
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "❌ このコマンドはサーバー内でのみ使用できます。",
                ephemeral=True,
            )
            return

        sub = get_active_subscription(interaction.guild_id)
        if sub is None:
            await interaction.response.send_message(
                "❌ このサーバーは現在Premium契約を利用していません。",
                ephemeral=True,
            )
            return

        # Cancel on Stripe side
        stripe_ok = cancel_stripe_subscription(sub["stripe_subscription_id"])

        # Update local DB
        updated = update_subscription_status(
            sub["id"],
            "canceled",
            canceled_at=discord.utils.utcnow().isoformat(),
        )

        if updated and stripe_ok:
            msg = (
                "\u2705 Premium契約を解約しました。\n"
                f"有効期限: {updated.get('current_period_end', '?')[:10]} までは"
                "引き続きPremium機能をご利用いただけます。"
            )
        elif updated:
            msg = (
                "\u26a0\ufe0f ローカルDBの更新は完了しましたが、"
                "Stripe側の解約処理に失敗しました。"
                "お手数ですがサーバー管理者にお問い合わせください。"
            )
        else:
            msg = "\u274c 解約処理中にエラーが発生しました。"

        await interaction.response.send_message(msg, ephemeral=True)

    # ------------------------------------------------------------------
    # /premium confirm  —  Manual purchase confirmation
    # ------------------------------------------------------------------

    @app_commands.command(
        name="premium_confirm",
        description="購入完了を確認しPremiumを有効化します（Webhook受信後の手動トリガー）",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def premium_confirm(
        self,
        interaction: discord.Interaction,
        stripe_session_id: str,
    ) -> None:
        """Manually confirm a purchase after webhook receipt.

        Parameters
        ----------
        stripe_session_id:
            The Stripe Checkout Session ID to verify.
        """
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "❌ このコマンドはサーバー内でのみ使用できます。",
                ephemeral=True,
            )
            return

        # Verify we haven't already processed this session
        existing = get_stripe_event(stripe_session_id)
        if existing is not None:
            await interaction.response.send_message(
                "\u26a0\ufe0f このセッションは既に処理済みです。",
                ephemeral=True,
            )
            return

        # Check Stripe session status
        stripe = _get_stripe()
        if stripe is None:
            await interaction.response.send_message(
                "❌ Stripeが設定されていません。サーバー管理者にお問い合わせください。",
                ephemeral=True,
            )
            return

        try:
            session = stripe.checkout.Session.retrieve(stripe_session_id)
        except Exception:
            await interaction.response.send_message(
                "❌ Stripeセッションの取得に失敗しました。"
                "セッションIDを確認してください。",
                ephemeral=True,
            )
            return

        if session.payment_status != "paid":
            await interaction.response.send_message(
                "❌ このセッションはまだ支払いが完了していません。",
                ephemeral=True,
            )
            return

        # Record the event for idempotency
        record_stripe_event(stripe_session_id, "checkout.session.completed")

        # Create subscription record
        sub = create_premium_subscription(
            guild_id=interaction.guild_id,
            owner_id=interaction.user.id,
            stripe_customer_id=session.customer or "unknown",
            stripe_subscription_id=session.subscription or "unknown",
            status="active",
        )

        embed = discord.Embed(
            title="\u2705 Premium有効化完了",
            description=(
                "このサーバーで **Premiumプラン** が有効になりました！\n"
                "\u200b\n"
                "\U0001f389 全機能をご利用いただけます。"
            ),
            color=discord.Color.green(),
        )
        embed.add_field(
            name="契約者",
            value=f"<@{sub['owner_id']}>",
            inline=True,
        )
        if sub.get("current_period_end"):
            embed.add_field(
                name="有効期限",
                value=sub["current_period_end"][:10],
                inline=True,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ------------------------------------------------------------------
    # /premium_config  —  Update premium guild configuration
    # ------------------------------------------------------------------

    @app_commands.command(
        name="premium_config",
        description="サーバーのPremium設定を変更します（管理者専用）",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        max_reminders="最大リマインダー数（1〜100、デフォルト3）",
        xp_rate_multiplier="XP倍率（1.0〜10.0、デフォルト1.0）",
    )
    async def premium_config(
        self,
        interaction: discord.Interaction,
        max_reminders: app_commands.Range[int, 1, 100] = 3,
        xp_rate_multiplier: app_commands.Range[float, 1.0, 10.0] = 1.0,
    ) -> None:
        """Update premium guild configuration (admin only)."""
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "❌ このコマンドはサーバー内でのみ使用できます。",
                ephemeral=True,
            )
            return

        config = set_guild_premium_config(
            guild_id=interaction.guild_id,
            max_reminders=max_reminders,
            xp_rate_multiplier=xp_rate_multiplier,
        )

        embed = discord.Embed(
            title="✅ Premium設定を更新しました",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="最大リマインダー数",
            value=str(config["max_reminders"]),
            inline=True,
        )
        embed.add_field(
            name="XP倍率",
            value=str(config["xp_rate_multiplier"]),
            inline=True,
        )
        embed.set_footer(text=f"ギルドID: {interaction.guild_id}")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    """Load the PremiumCog."""
    await bot.add_cog(PremiumCog(bot))