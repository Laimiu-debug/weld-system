"""Payment status, activation, callback, and renewal order tests."""
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.schemas.payment import PaymentCallback
from app.services.payment_service import PaymentService


def _transaction(
    *,
    status: str = "pending",
    user_id: int = 1,
    description: str = "升级到 专业版 - monthly;purpose=upgrade;duration_months=1",
    end_date: datetime | None = None,
):
    subscription = SimpleNamespace(
        id=10,
        billing_cycle="monthly",
        user_id=user_id,
        plan_id="personal_pro",
        status="pending",
        auto_renew=True,
        start_date=datetime(2026, 8, 1),
        end_date=end_date or datetime(2026, 9, 1),
        last_payment_date=None,
        next_billing_date=None,
        updated_at=None,
    )
    return SimpleNamespace(
        id=1,
        subscription_id=10,
        payment_method="alipay",
        currency="CNY",
        transaction_id="TXN1",
        status=status,
        amount=19.0,
        description=description,
        transaction_date=None,
        updated_at=None,
        subscription=subscription,
    )


def test_get_payment_status_reads_transaction_and_checks_owner():
    service = PaymentService(MagicMock())
    txn = _transaction()
    service._find_transaction = lambda order_id: txn if order_id == "TXN1" else None

    result = service.get_payment_status("TXN1", user_id=1)
    assert result.status == "pending"
    assert result.amount == 19.0
    assert result.order_id == "TXN1"

    with pytest.raises(HTTPException) as exc:
        service.get_payment_status("TXN1", user_id=99)
    assert exc.value.status_code == 403


def test_pending_confirm_is_reported_as_pending():
    service = PaymentService(MagicMock())
    txn = _transaction(status="pending_confirm")
    service._find_transaction = lambda order_id: txn
    result = service.get_payment_status("TXN1", user_id=1)
    assert result.status == "pending"


def test_activate_paid_renewal_extends_once():
    txn = _transaction(
        description="续费 专业版 - monthly;purpose=renew;duration_months=1",
        end_date=datetime(2026, 9, 1),
    )
    txn.subscription.status = "active"
    original_end = txn.subscription.end_date
    user = SimpleNamespace(
        id=1,
        name="专业版",
        auto_renewal=False,
        email=None,
        subscription_status=None,
        subscription_start_date=None,
        subscription_end_date=None,
        updated_at=None,
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = user
    service = PaymentService(db)
    service._lock_payment = lambda _: (txn, txn.subscription, user)
    service._queue_notification = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.services.payment_service.MembershipTierService") as tier_cls:
        tier_cls.return_value.update_user_tier.return_value = {"changed": True, "old_tier": "free", "new_tier": "personal_pro"}
        service.activate_paid_transaction(txn)
        first_end = txn.subscription.end_date
        assert first_end > original_end
        assert txn.status == "success"
        assert txn.subscription.status == "active"

        service.activate_paid_transaction(txn)
        assert txn.subscription.end_date == first_end


def test_callback_looks_up_merchant_order_id():
    txn = _transaction()
    service = PaymentService(MagicMock())
    service._find_transaction = lambda order_id: txn if order_id == "TXN1" else None
    service.activate_paid_transaction = MagicMock(return_value={})
    callback = PaymentCallback(
        order_id="TXN1",
        transaction_id="gateway-trade-no",
        amount=19,
        payment_method="alipay",
        status="success",
        paid_at=datetime.utcnow(),
        signature="",
    )
    result = service.handle_payment_callback(callback)
    service.activate_paid_transaction.assert_called_once_with(txn)
    assert result["transaction_id"] == "TXN1"


def test_mock_callback_signature_is_accepted():
    service = PaymentService(MagicMock())
    callback = PaymentCallback(
        order_id="TXN1",
        transaction_id="TXN1",
        amount=19,
        payment_method="mock",
        status="success",
        paid_at=datetime.utcnow(),
        signature="",
    )
    with patch("app.services.payment_service.settings") as settings:
        settings.PAYMENT_PROVIDER = "mock"
        settings.DEVELOPMENT = True
        assert service._verify_payment_signature(callback) is True


def test_renewal_order_skipped_when_pending_exists():
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = [
        SimpleNamespace(description="续费 专业版;purpose=renew;duration_months=1", status="pending")
    ]
    service = PaymentService(db)
    service.create_payment_order = MagicMock()
    result = service.create_renewal_order_if_needed(SimpleNamespace(id=10, user_id=1))
    assert result is None
    service.create_payment_order.assert_not_called()


def test_auto_renewal_creates_pending_order_without_extending():
    from app.services.notification_service import NotificationService

    end_date = datetime.utcnow() + timedelta(days=5)
    subscription = SimpleNamespace(
        id=10,
        user_id=1,
        plan_id="personal_pro",
        status="active",
        end_date=end_date,
        next_billing_date=datetime.utcnow(),
    )
    db = MagicMock()
    db.query.return_value.join.return_value.filter.return_value.all.return_value = [subscription]
    service = NotificationService(db)

    with patch("app.services.payment_service.PaymentService") as payment_cls:
        payment_cls.return_value.create_renewal_order_if_needed.return_value = {
            "transaction_id": "TXN-RENEW",
            "amount": 19,
        }
        count = service.process_auto_renewals()

    assert count == 1
    assert subscription.end_date == end_date
    payment_cls.return_value.create_renewal_order_if_needed.assert_called_once()



def test_mock_callback_preserves_development_payment_channel():
    txn = _transaction()
    service = PaymentService(MagicMock())
    service._find_transaction = lambda _: txn
    service.activate_paid_transaction = MagicMock()
    callback = PaymentCallback(order_id="TXN1", transaction_id="TXN1", amount=19, payment_method="mock",
                               status="success", paid_at=datetime.utcnow())
    with patch("app.services.payment_service.settings") as settings:
        settings.PAYMENT_PROVIDER = "mock"
        service.handle_payment_callback(callback)
    service.activate_paid_transaction.assert_called_once_with(txn)
