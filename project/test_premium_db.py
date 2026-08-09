"""Tests for premium_db.py."""

import shutil
from pathlib import Path

# Use a temporary DB for testing
TEST_DB_DIR = Path("/tmp/test_premium_data")

# Force premium_db to use the test directory BEFORE importing
import premium.premium_db as premium_db

premium_db.DB_DIR = TEST_DB_DIR
premium_db.DB_PATH = TEST_DB_DIR / "premium.db"

from premium.premium_db import (
    create_premium_subscription,
    get_active_subscription,
    update_subscription_status,
    record_stripe_event,
    get_stripe_event,
    set_guild_premium_config,
    get_guild_premium_config,
    delete_guild_premium_config,
    init_db,
)


def setup_module():
    """Remove any leftover test DB before starting."""
    if TEST_DB_DIR.exists():
        shutil.rmtree(TEST_DB_DIR)


def setup_function():
    """Ensure a clean DB before each test function (for pytest)."""
    if TEST_DB_DIR.exists():
        shutil.rmtree(TEST_DB_DIR)


def teardown_module():
    """Clean up test DB after tests."""
    if TEST_DB_DIR.exists():
        shutil.rmtree(TEST_DB_DIR)


# ── premium_subscriptions tests ─────────────────────────────────────────────


def test_init_db():
    init_db()
    db_path = TEST_DB_DIR / "premium.db"
    assert db_path.exists(), "DB file should be created"
    import sqlite3

    conn = sqlite3.connect(str(db_path))
    cur = conn.execute("PRAGMA journal_mode")
    assert cur.fetchone()[0] == "wal"
    conn.close()


def test_create_premium_subscription():
    init_db()
    sub = create_premium_subscription(
        guild_id=100,
        owner_id=200,
        stripe_customer_id="cus_test001",
        stripe_subscription_id="sub_test001",
        status="active",
        current_period_start="2026-08-01T00:00:00+00:00",
        current_period_end="2026-09-01T00:00:00+00:00",
    )
    assert sub["guild_id"] == 100
    assert sub["owner_id"] == 200
    assert sub["stripe_customer_id"] == "cus_test001"
    assert sub["stripe_subscription_id"] == "sub_test001"
    assert sub["status"] == "active"
    assert sub["current_period_start"] == "2026-08-01T00:00:00+00:00"
    assert sub["current_period_end"] == "2026-09-01T00:00:00+00:00"
    assert isinstance(sub["id"], int) and sub["id"] > 0
    assert sub["created_at"] is not None
    assert sub["updated_at"] is not None
    assert sub["canceled_at"] is None


def test_create_premium_subscription_duplicate_guild():
    init_db()
    create_premium_subscription(
        guild_id=100,
        owner_id=200,
        stripe_customer_id="cus_test001",
        stripe_subscription_id="sub_test001",
    )
    import sqlite3

    try:
        create_premium_subscription(
            guild_id=100,
            owner_id=300,
            stripe_customer_id="cus_test002",
            stripe_subscription_id="sub_test002",
        )
        assert False, "Expected IntegrityError for duplicate guild_id"
    except sqlite3.IntegrityError:
        pass


def test_get_active_subscription():
    init_db()
    # No subscription yet
    assert get_active_subscription(100) is None

    create_premium_subscription(
        guild_id=100,
        owner_id=200,
        stripe_customer_id="cus_test001",
        stripe_subscription_id="sub_test001",
        status="active",
    )
    sub = get_active_subscription(100)
    assert sub is not None
    assert sub["guild_id"] == 100
    assert sub["status"] == "active"


def test_get_active_subscription_past_due_included():
    init_db()
    create_premium_subscription(
        guild_id=100,
        owner_id=200,
        stripe_customer_id="cus_test001",
        stripe_subscription_id="sub_test001",
        status="past_due",
    )
    sub = get_active_subscription(100)
    assert sub is not None
    assert sub["status"] == "past_due"


def test_get_active_subscription_canceled_excluded():
    init_db()
    create_premium_subscription(
        guild_id=100,
        owner_id=200,
        stripe_customer_id="cus_test001",
        stripe_subscription_id="sub_test001",
        status="canceled",
    )
    assert get_active_subscription(100) is None


def test_update_subscription_status():
    init_db()
    sub = create_premium_subscription(
        guild_id=100,
        owner_id=200,
        stripe_customer_id="cus_test001",
        stripe_subscription_id="sub_test001",
        status="active",
    )
    updated = update_subscription_status(sub["id"], "canceled")
    assert updated is not None
    assert updated["status"] == "canceled"
    assert updated["id"] == sub["id"]

    # Verify it's no longer active
    assert get_active_subscription(100) is None


def test_update_subscription_status_with_extra():
    init_db()
    sub = create_premium_subscription(
        guild_id=100,
        owner_id=200,
        stripe_customer_id="cus_test001",
        stripe_subscription_id="sub_test001",
        status="active",
    )
    updated = update_subscription_status(
        sub["id"],
        "canceled",
        canceled_at="2026-08-15T00:00:00+00:00",
    )
    assert updated["status"] == "canceled"
    assert updated["canceled_at"] == "2026-08-15T00:00:00+00:00"


def test_update_subscription_status_nonexistent():
    init_db()
    result = update_subscription_status(99999, "canceled")
    assert result is None


# ── stripe_events tests ─────────────────────────────────────────────────────


def test_record_and_get_stripe_event():
    init_db()
    event = record_stripe_event(
        event_id="evt_test001",
        event_type="checkout.session.completed",
    )
    assert event["id"] == "evt_test001"
    assert event["type"] == "checkout.session.completed"
    assert event["status"] == "processed"
    assert event["processed_at"] is not None

    fetched = get_stripe_event("evt_test001")
    assert fetched is not None
    assert fetched["id"] == "evt_test001"


def test_record_stripe_event_duplicate():
    init_db()
    record_stripe_event("evt_test001", "checkout.session.completed")
    # Second insert should be silently ignored (INSERT OR IGNORE)
    record_stripe_event("evt_test001", "invoice.payment_failed")
    events = get_stripe_event("evt_test001")
    assert events is not None
    assert events["type"] == "checkout.session.completed"


def test_get_stripe_event_nonexistent():
    init_db()
    assert get_stripe_event("evt_nonexistent") is None


# ── guild_premium_config tests ──────────────────────────────────────────────


def test_set_and_get_guild_premium_config():
    init_db()
    config = set_guild_premium_config(
        guild_id=100,
        xp_rate_multiplier=2.0,
        max_reminders=0,
        anonymous_polls=1,
    )
    assert config["guild_id"] == 100
    assert config["xp_rate_multiplier"] == 2.0
    assert config["max_reminders"] == 0
    assert config["anonymous_polls"] == 1
    assert config["multiple_vote_polls"] == 0
    assert config["welcome_embed_json"] is None
    assert config["xp_role_mappings"] is None

    fetched = get_guild_premium_config(100)
    assert fetched is not None
    assert fetched["xp_rate_multiplier"] == 2.0


def test_get_guild_premium_config_nonexistent():
    init_db()
    assert get_guild_premium_config(99999) is None


def test_set_guild_premium_config_update():
    init_db()
    set_guild_premium_config(guild_id=100, xp_rate_multiplier=1.5)
    set_guild_premium_config(guild_id=100, xp_rate_multiplier=3.0, max_reminders=10)
    config = get_guild_premium_config(100)
    assert config is not None
    assert config["xp_rate_multiplier"] == 3.0
    assert config["max_reminders"] == 10


def test_delete_guild_premium_config():
    init_db()
    set_guild_premium_config(guild_id=100, xp_rate_multiplier=1.5)
    assert get_guild_premium_config(100) is not None
    assert delete_guild_premium_config(100) is True
    assert get_guild_premium_config(100) is None


def test_delete_guild_premium_config_nonexistent():
    init_db()
    assert delete_guild_premium_config(99999) is False


# ── End-to-end test ─────────────────────────────────────────────────────────


def test_premium_full_lifecycle():
    """Simulate a full premium lifecycle: subscribe → verify → update → cancel."""
    init_db()

    # 1. Create subscription
    sub = create_premium_subscription(
        guild_id=500,
        owner_id=600,
        stripe_customer_id="cus_e2e",
        stripe_subscription_id="sub_e2e",
        status="active",
        current_period_start="2026-08-01T00:00:00+00:00",
        current_period_end="2026-09-01T00:00:00+00:00",
    )
    assert sub["status"] == "active"

    # 2. Verify active
    assert get_active_subscription(500) is not None

    # 3. Configure premium features
    cfg = set_guild_premium_config(
        guild_id=500,
        xp_rate_multiplier=2.0,
        max_reminders=0,
        anonymous_polls=1,
        multiple_vote_polls=1,
    )
    assert cfg["xp_rate_multiplier"] == 2.0

    # 4. Record Stripe events
    evt1 = record_stripe_event("evt_e2e_1", "checkout.session.completed")
    assert evt1["type"] == "checkout.session.completed"
    evt2 = record_stripe_event("evt_e2e_2", "invoice.paid")
    assert evt2["type"] == "invoice.paid"

    # 5. Cancel subscription
    updated = update_subscription_status(
        sub["id"],
        "canceled",
        canceled_at="2026-08-15T00:00:00+00:00",
    )
    assert updated["status"] == "canceled"

    # 6. Verify inactive
    assert get_active_subscription(500) is None

    # 7. Config still exists after cancellation
    assert get_guild_premium_config(500) is not None

    # 8. Clean up config
    assert delete_guild_premium_config(500) is True
    assert get_guild_premium_config(500) is None


if __name__ == "__main__":
    import traceback

    tests = [
        test_init_db,
        test_create_premium_subscription,
        test_create_premium_subscription_duplicate_guild,
        test_get_active_subscription,
        test_get_active_subscription_past_due_included,
        test_get_active_subscription_canceled_excluded,
        test_update_subscription_status,
        test_update_subscription_status_with_extra,
        test_update_subscription_status_nonexistent,
        test_record_and_get_stripe_event,
        test_record_stripe_event_duplicate,
        test_get_stripe_event_nonexistent,
        test_set_and_get_guild_premium_config,
        test_get_guild_premium_config_nonexistent,
        test_set_guild_premium_config_update,
        test_delete_guild_premium_config,
        test_delete_guild_premium_config_nonexistent,
        test_premium_full_lifecycle,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            setup_module()
            test()
            print(f"  ✅ {test.__name__}")
            passed += 1
        except Exception:
            print(f"  ❌ {test.__name__}")
            traceback.print_exc()
            failed += 1
        finally:
            teardown_module()

    print(f"\n{'='*40}")
    print(f"結果: {passed} passed / {failed} failed / {len(tests)} total")
    if failed:
        print("❌  FAIL")
    else:
        print("✅  ALL PASSED")