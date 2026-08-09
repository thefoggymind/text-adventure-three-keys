"""Tests for premium_cog.py.

Tests Cog initialisation, command registration, and Stripe-related utility
functions (with mocked Stripe API calls).
"""

import json
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Use a temporary DB for testing (must happen before importing premium_db)
TEST_DB_DIR = Path("/tmp/test_premium_cog_data")

import premium.premium_db as premium_db

premium_db.DB_DIR = TEST_DB_DIR
premium_db.DB_PATH = TEST_DB_DIR / "premium.db"


# Now safe to import the module under test
from premium.premium_cog import (  # noqa: E402
    STRIPE_PRICE_ID,
    PremiumCog,
    cancel_stripe_subscription,
    create_checkout_session,
    is_premium,
    require_premium,
    verify_webhook_signature,
)
from premium.premium_db import (  # noqa: E402
    create_premium_subscription,
    get_active_subscription,
    init_db,
)


# ── DB cleanup helpers ──────────────────────────────────────────────────────


def clean_db():
    """Remove and recreate the test DB so each test starts clean."""
    if TEST_DB_DIR.exists():
        shutil.rmtree(TEST_DB_DIR)
    init_db()


def setup_function():
    """Called by pytest before each module-level test function."""
    clean_db()


def setup_method():
    """Called by pytest before each class-based test method."""
    clean_db()


def teardown_module():
    """Clean up test DB after all tests."""
    if TEST_DB_DIR.exists():
        shutil.rmtree(TEST_DB_DIR)


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
    mock.user.id = 99999
    mock.guild = MagicMock()
    mock.guild.id = 12345
    mock.guild.name = "Test Guild"
    mock.response = MagicMock()
    mock.response.send_message = AsyncMock()
    return mock


# ── Cog initialisation ──────────────────────────────────────────────────────


class TestCogInit:
    """Tests for PremiumCog initialisation."""

    def setup_method(self):
        clean_db()

    def test_cog_compiles(self):
        """Verify the module can be imported and the class exists."""
        assert PremiumCog is not None

    def test_cog_init_creates_db(self, bot):
        """Initialising the cog should call init_db and create tables."""
        PremiumCog(bot)
        db_path = TEST_DB_DIR / "premium.db"
        assert db_path.exists(), "init_db() should create the DB file"

    def test_cog_has_bot_ref(self, cog):
        """The cog should store a reference to the bot."""
        assert cog.bot is not None

    def test_cog_commands_registered(self, cog):
        """All expected slash commands should be registered on the cog."""
        command_names = {cmd.name for cmd in cog.walk_app_commands()}
        expected = {"premium", "premium_status", "premium_cancel", "premium_confirm"}
        missing = expected - command_names
        assert not missing, f"Missing commands: {missing}"


# ── is_premium ──────────────────────────────────────────────────────────────


class TestIsPremium:
    """Tests for the is_premium helper."""

    def setup_method(self):
        clean_db()

    def test_no_subscription(self):
        """A guild with no subscription should not be premium."""
        assert is_premium(99999) is False

    def test_active_subscription(self):
        """A guild with an active subscription should be premium."""
        create_premium_subscription(
            guild_id=100,
            owner_id=200,
            stripe_customer_id="cus_test",
            stripe_subscription_id="sub_test",
            status="active",
        )
        assert is_premium(100) is True

    def test_past_due_subscription(self):
        """A guild with a past_due subscription should still be premium."""
        create_premium_subscription(
            guild_id=100,
            owner_id=200,
            stripe_customer_id="cus_test",
            stripe_subscription_id="sub_test",
            status="past_due",
        )
        assert is_premium(100) is True

    def test_canceled_subscription(self):
        """A guild with a canceled subscription should NOT be premium."""
        create_premium_subscription(
            guild_id=100,
            owner_id=200,
            stripe_customer_id="cus_test",
            stripe_subscription_id="sub_test",
            status="canceled",
        )
        assert is_premium(100) is False


# ── require_premium ─────────────────────────────────────────────────────────


class TestRequirePremium:
    """Tests for the require_premium helper."""

    def setup_method(self):
        clean_db()

    @pytest.mark.asyncio
    async def test_no_guild_id(self, interaction):
        """require_premium should return False if guild_id is None."""
        interaction.guild_id = None
        result = await require_premium(interaction)
        assert result is False
        interaction.response.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_not_premium(self, interaction):
        """require_premium should return False if the guild is not premium."""
        result = await require_premium(interaction)
        assert result is False
        interaction.response.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_premium(self, interaction):
        """require_premium should return True if the guild is premium."""
        create_premium_subscription(
            guild_id=interaction.guild_id,
            owner_id=99999,
            stripe_customer_id="cus_test",
            stripe_subscription_id="sub_test",
            status="active",
        )
        result = await require_premium(interaction)
        assert result is True
        interaction.response.send_message.assert_not_called()


# ── create_checkout_session ─────────────────────────────────────────────────


class TestCreateCheckoutSession:
    """Tests for create_checkout_session with mocked Stripe API."""

    @patch("premium.premium_cog.STRIPE_SECRET_KEY", "sk_test_xxxx")
    def test_success(self):
        """A successful Stripe Checkout Session creation."""
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/c/pay_cs_test_001"
        mock_session.id = "cs_test_001"

        with patch(
            "premium.premium_cog._get_stripe"
        ) as mock_get_stripe:
            mock_stripe = MagicMock()
            mock_stripe.checkout.Session.create.return_value = mock_session
            mock_get_stripe.return_value = mock_stripe

            result = create_checkout_session(guild_id=100, owner_id=200)

        assert result is not None
        assert result["url"] == "https://checkout.stripe.com/c/pay_cs_test_001"
        assert result["session_id"] == "cs_test_001"
        mock_stripe.checkout.Session.create.assert_called_once_with(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
            client_reference_id="100",
            metadata={"guild_id": "100", "owner_id": "200"},
            success_url="https://discord.com/app",
            cancel_url="https://discord.com/app",
        )

    def test_no_stripe_key(self):
        """If there is no secret key, the function should return None."""
        with patch("premium.premium_cog.STRIPE_SECRET_KEY", ""):
            result = create_checkout_session(guild_id=100, owner_id=200)
        assert result is None

    @patch("premium.premium_cog.STRIPE_SECRET_KEY", "sk_test_xxxx")
    def test_api_exception(self):
        """If the Stripe API raises an exception, return None."""
        with patch(
            "premium.premium_cog._get_stripe"
        ) as mock_get_stripe:
            mock_stripe = MagicMock()
            mock_stripe.checkout.Session.create.side_effect = Exception("API error")
            mock_get_stripe.return_value = mock_stripe

            result = create_checkout_session(guild_id=100, owner_id=200)

        assert result is None


# ── cancel_stripe_subscription ──────────────────────────────────────────────


class TestCancelStripeSubscription:
    """Tests for cancel_stripe_subscription with mocked Stripe API."""

    @patch("premium.premium_cog.STRIPE_SECRET_KEY", "sk_test_xxxx")
    def test_success(self):
        """A successful subscription cancellation."""
        with patch(
            "premium.premium_cog._get_stripe"
        ) as mock_get_stripe:
            mock_stripe = MagicMock()
            mock_get_stripe.return_value = mock_stripe

            result = cancel_stripe_subscription("sub_test_001")

        assert result is True
        mock_stripe.Subscription.modify.assert_called_once_with(
            "sub_test_001", cancel_at_period_end=True
        )

    def test_no_stripe_key(self):
        """If there is no secret key, the function should return False."""
        with patch("premium.premium_cog.STRIPE_SECRET_KEY", ""):
            result = cancel_stripe_subscription("sub_test_001")
        assert result is False

    @patch("premium.premium_cog.STRIPE_SECRET_KEY", "sk_test_xxxx")
    def test_api_exception(self):
        """If the Stripe API raises an exception, return False."""
        with patch(
            "premium.premium_cog._get_stripe"
        ) as mock_get_stripe:
            mock_stripe = MagicMock()
            mock_stripe.Subscription.modify.side_effect = Exception("API error")
            mock_get_stripe.return_value = mock_stripe

            result = cancel_stripe_subscription("sub_test_001")

        assert result is False


# ── verify_webhook_signature ────────────────────────────────────────────────


class TestVerifyWebhookSignature:
    """Tests for verify_webhook_signature with mocked Stripe."""

    @patch("premium.premium_cog.STRIPE_WEBHOOK_SECRET", "whsec_test")
    def test_success(self):
        """A valid signature should return the parsed event."""
        payload = json.dumps({"id": "evt_test", "type": "checkout.session.completed"}).encode()
        mock_event = MagicMock()
        mock_event.id = "evt_test"

        with patch(
            "stripe.Webhook.construct_event"
        ) as mock_construct:
            mock_construct.return_value = mock_event
            result = verify_webhook_signature(payload, "dummy_sig")

        assert result is not None
        assert result.id == "evt_test"
        mock_construct.assert_called_once_with(payload, "dummy_sig", "whsec_test")

    def test_no_webhook_secret(self):
        """If there is no webhook secret, the function should return None."""
        with patch("premium.premium_cog.STRIPE_WEBHOOK_SECRET", ""):
            result = verify_webhook_signature(b"{}", "sig")
        assert result is None

    @patch("premium.premium_cog.STRIPE_WEBHOOK_SECRET", "whsec_test")
    def test_invalid_signature(self):
        """An invalid signature should return None."""
        payload = b"{}"
        with patch(
            "stripe.Webhook.construct_event"
        ) as mock_construct:
            mock_construct.side_effect = Exception("Invalid signature")
            result = verify_webhook_signature(payload, "bad_sig")

        assert result is None


# ── _get_stripe ─────────────────────────────────────────────────────────────


class TestGetStripe:
    """Tests for the internal _get_stripe helper."""

    def test_no_key_returns_none(self):
        """If STRIPE_SECRET_KEY is empty, _get_stripe should return None."""
        with patch("premium.premium_cog.STRIPE_SECRET_KEY", ""):
            from premium.premium_cog import _get_stripe

            assert _get_stripe() is None

    @patch("premium.premium_cog.STRIPE_SECRET_KEY", "sk_test_xxxx")
    def test_key_set_sets_api_key(self):
        """If the key is set, the stripe module api_key should be configured."""
        from premium.premium_cog import _get_stripe

        stripe_module = _get_stripe()
        assert stripe_module is not None
        assert stripe_module.api_key == "sk_test_xxxx"


# ── Command call behaviours (verify they compile and accept params) ─────────


class TestCommandSignatures:
    """Verify that each command method has the correct parameter signature."""

    def test_premium_info_params(self, cog):
        """premium_info should accept only self and interaction."""
        import inspect

        sig = inspect.signature(cog.premium_info.callback)
        params = list(sig.parameters.keys())
        assert params == ["self", "interaction"]

    def test_premium_status_params(self, cog):
        """premium_status should accept only self and interaction."""
        import inspect

        sig = inspect.signature(cog.premium_status.callback)
        params = list(sig.parameters.keys())
        assert params == ["self", "interaction"]

    def test_premium_cancel_params(self, cog):
        """premium_cancel should accept only self and interaction."""
        import inspect

        sig = inspect.signature(cog.premium_cancel.callback)
        params = list(sig.parameters.keys())
        assert params == ["self", "interaction"]

    def test_premium_confirm_params(self, cog):
        """premium_confirm should accept self, interaction, and stripe_session_id."""
        import inspect

        sig = inspect.signature(cog.premium_confirm.callback)
        params = list(sig.parameters.keys())
        assert params == ["self", "interaction", "stripe_session_id"]


if __name__ == "__main__":
    import traceback

    bot_mock = MagicMock()
    premium_cog = PremiumCog(bot_mock)

    # Each entry: (test_instance, test_method, *extra_args)
    tests: list[tuple] = [
        # Cog init
        (TestCogInit(), TestCogInit.test_cog_compiles),
        (TestCogInit(), TestCogInit.test_cog_init_creates_db, bot_mock),
        (TestCogInit(), TestCogInit.test_cog_has_bot_ref, premium_cog),
        (TestCogInit(), TestCogInit.test_cog_commands_registered, premium_cog),
        # is_premium
        (TestIsPremium(), TestIsPremium.test_no_subscription),
        (TestIsPremium(), TestIsPremium.test_active_subscription),
        (TestIsPremium(), TestIsPremium.test_past_due_subscription),
        (TestIsPremium(), TestIsPremium.test_canceled_subscription),
        # create_checkout_session
        (TestCreateCheckoutSession(), TestCreateCheckoutSession.test_success),
        (TestCreateCheckoutSession(), TestCreateCheckoutSession.test_no_stripe_key),
        (TestCreateCheckoutSession(), TestCreateCheckoutSession.test_api_exception),
        # cancel_stripe_subscription
        (TestCancelStripeSubscription(), TestCancelStripeSubscription.test_success),
        (
            TestCancelStripeSubscription(),
            TestCancelStripeSubscription.test_no_stripe_key,
        ),
        (
            TestCancelStripeSubscription(),
            TestCancelStripeSubscription.test_api_exception,
        ),
        # verify_webhook_signature
        (
            TestVerifyWebhookSignature(),
            TestVerifyWebhookSignature.test_success,
        ),
        (
            TestVerifyWebhookSignature(),
            TestVerifyWebhookSignature.test_no_webhook_secret,
        ),
        (
            TestVerifyWebhookSignature(),
            TestVerifyWebhookSignature.test_invalid_signature,
        ),
        # _get_stripe
        (TestGetStripe(), TestGetStripe.test_no_key_returns_none),
        (TestGetStripe(), TestGetStripe.test_key_set_sets_api_key),
        # command signatures
        (
            TestCommandSignatures(),
            TestCommandSignatures.test_premium_info_params,
            premium_cog,
        ),
        (
            TestCommandSignatures(),
            TestCommandSignatures.test_premium_status_params,
            premium_cog,
        ),
        (
            TestCommandSignatures(),
            TestCommandSignatures.test_premium_cancel_params,
            premium_cog,
        ),
        (
            TestCommandSignatures(),
            TestCommandSignatures.test_premium_confirm_params,
            premium_cog,
        ),
    ]

    passed = 0
    failed = 0
    for entry in tests:
        instance, method = entry[0], entry[1]
        args = entry[2:]
        try:
            clean_db()
            method(instance, *args)
            print(f"  \u2705 {method.__name__}")
            passed += 1
        except Exception:
            print(f"  \u274c {method.__name__}")
            traceback.print_exc()
            failed += 1
        finally:
            teardown_module()

    print(f"\n{'='*40}")
    print(f"\u7d50\u679c: {passed} passed / {failed} failed / {len(tests)} total")
    if failed:
        print("\u274c  FAIL")
    else:
        print("\u2705  ALL PASSED")