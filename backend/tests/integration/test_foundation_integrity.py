"""Opt-in real PostgreSQL checks. Only a generated local QA schema is written."""
import os
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.database import Base, engine
import app.models
from app.models.user import User
from app.models.company import Company, CompanyEmployee, Factory
from app.models.subscription import Subscription, SubscriptionTransaction
from app.models.payment_delivery import PaymentActivation, PaymentNotification
from app.models.attachment import Attachment
from app.models.quality import QualityInspection
from app.models.production import ProductionPlan
from app.services.payment_service import PaymentService
from app.services.membership_tier_service import MembershipTierService
from app.services.payment_notification_service import deliver_pending_payment_notifications
from app.core.data_access import DataAccessMiddleware, WorkspaceContext
from app.api.v1.schemas.payment import PaymentCallback

pytestmark = pytest.mark.skipif(os.getenv("RUN_LOCAL_DB_TESTS") != "1", reason="opt-in local PostgreSQL only")


@pytest.fixture(scope="module")
def sessions():
    assert engine.url.host in {"127.0.0.1", "localhost"}
    schema = "qa_foundation_" + uuid.uuid4().hex[:12]
    assert re.fullmatch(r"qa_foundation_[0-9a-f]{12}", schema)
    admin = create_engine(engine.url, echo=False)
    with admin.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    local = create_engine(engine.url, echo=False, connect_args={"options": f"-c search_path={schema} -c lock_timeout=10000"})
    try:
        with local.begin() as conn:
            assert conn.execute(text("SELECT current_schema()")).scalar() == schema
            Base.metadata.create_all(conn)
        yield sessionmaker(local, autoflush=False, expire_on_commit=False)
    finally:
        local.dispose()
        with admin.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


@pytest.fixture
def db(sessions):
    with sessions() as session:
        yield session
        session.rollback()


def user(db):
    key = uuid.uuid4().hex
    row = User(email=f"{key}@example.invalid", username=key, hashed_password="!disabled", is_active=True,
               member_tier="free", membership_type="personal")
    db.add(row)
    db.flush()
    return row


def order(db, plan="personal_pro", renewal=False, owner=None):
    owner = owner or user(db)
    sub = Subscription(user_id=owner.id, plan_id=plan, status="active" if renewal else "pending",
                       billing_cycle="monthly", price=19, start_date=datetime.utcnow(),
                       end_date=datetime.utcnow()+timedelta(days=40))
    db.add(sub)
    db.flush()
    txn = SubscriptionTransaction(subscription_id=sub.id, transaction_id=uuid.uuid4().hex,
                                  amount=19, payment_method="alipay", status="pending", currency="CNY",
                                  description=f"purpose={'renew' if renewal else 'upgrade'};duration_months=1")
    db.add(txn)
    db.commit()
    return owner, sub, txn


def callback(txn, status="success", **changes):
    data = dict(order_id=txn.transaction_id, transaction_id="gateway", amount=19, currency="CNY",
                payment_method="alipay", status=status, paid_at=datetime.utcnow())
    data.update(changes)
    return PaymentCallback(**data)


def test_settlement_is_atomic_and_retry_compensates(db):
    owner, sub, txn = order(db, plan="enterprise")
    original = MembershipTierService._update_enterprise_tier
    with patch.object(MembershipTierService, "_update_enterprise_tier", side_effect=RuntimeError("injected provisioning failure")):
        with pytest.raises(RuntimeError):
            PaymentService(db).activate_paid_transaction(txn)
    db.expire_all()
    assert txn.status == "pending"
    assert sub.status == "pending"
    assert owner.member_tier == "free"
    assert db.query(Company).filter_by(owner_id=owner.id).count() == 0
    assert db.query(PaymentActivation).filter_by(transaction_id=txn.id).count() == 0
    assert db.query(PaymentNotification).filter_by(user_id=owner.id).count() == 0
    PaymentService(db).activate_paid_transaction(txn)
    db.expire_all()
    assert owner.member_tier == "enterprise"
    company = db.query(Company).filter_by(owner_id=owner.id).one()
    assert company.subscription_end_date == sub.end_date
    assert db.query(Factory).filter_by(company_id=company.id).count() == 1
    assert db.query(CompanyEmployee).filter_by(company_id=company.id).count() == 1
    assert db.query(PaymentActivation).filter_by(transaction_id=txn.id).count() == 1


def test_concurrent_duplicate_callbacks_extend_once(db, sessions):
    owner, sub, txn = order(db, renewal=True)
    old_end = sub.end_date
    barrier = Barrier(2)
    def settle():
        with sessions() as connection:
            loaded = connection.query(SubscriptionTransaction).filter_by(id=txn.id).one()
            barrier.wait(timeout=10)
            return PaymentService(connection).activate_paid_transaction(loaded)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: settle(), range(2)))
    db.expire_all()
    from dateutil.relativedelta import relativedelta
    assert sub.end_date == old_end + relativedelta(months=1)
    assert sorted(row["already_active"] for row in results) == [False, True]
    assert db.query(PaymentActivation).filter_by(transaction_id=txn.id).count() == 1
    assert db.query(PaymentNotification).filter_by(user_id=owner.id).count() == 1


def test_two_renewal_orders_on_same_subscription_are_serialized(db, sessions):
    owner, sub, txn = order(db, renewal=True)
    other = SubscriptionTransaction(subscription_id=sub.id, transaction_id=uuid.uuid4().hex, amount=19,
                                    payment_method="alipay", status="pending", description="purpose=renew;duration_months=1")
    db.add(other); db.commit()
    old_end = sub.end_date
    barrier = Barrier(2)
    def settle(txn_id):
        with sessions() as connection:
            loaded = connection.query(SubscriptionTransaction).filter_by(id=txn_id).one()
            barrier.wait(timeout=10)
            return PaymentService(connection).activate_paid_transaction(loaded)
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(settle, [txn.id, other.id]))
    db.expire_all()
    from dateutil.relativedelta import relativedelta
    assert sub.end_date == old_end + relativedelta(months=1) + relativedelta(months=1)
    assert owner.subscription_end_date == sub.end_date


@pytest.mark.parametrize("changes", [{"amount":18}, {"amount":float("nan")}, {"currency":"USD"}, {"payment_method":"wechat"}])
def test_mismatched_callback_never_activates(db, changes):
    owner, sub, txn = order(db)
    with patch.object(PaymentService, "_verify_payment_signature", return_value=True):
        with pytest.raises(HTTPException) as exc:
            PaymentService(db).handle_payment_callback(callback(txn, **changes))
    assert exc.value.status_code == 400
    assert txn.status == "pending" and owner.member_tier == "free"


def test_late_failure_and_repeat_after_expiry_do_not_reactivate(db):
    owner, sub, txn = order(db)
    service = PaymentService(db)
    service.activate_paid_transaction(txn)
    end = sub.end_date
    sub.status = "expired"; db.commit()
    with patch.object(PaymentService, "_verify_payment_signature", return_value=True):
        service.handle_payment_callback(callback(txn, "failed"))
        assert service.activate_paid_transaction(txn)["already_active"]
    assert txn.status == "success" and sub.status == "expired" and sub.end_date == end


def test_notification_failure_does_not_undo_settlement_and_is_retryable(db):
    owner, sub, txn = order(db)
    PaymentService(db).activate_paid_transaction(txn)
    # Isolate this test's queue from other queued QA events without delivering anything externally.
    db.query(PaymentNotification).filter(PaymentNotification.user_id != owner.id).update(
        {"next_attempt_at": datetime.utcnow()+timedelta(days=1)}, synchronize_session=False)
    db.commit()
    with patch("app.services.payment_notification_service.NotificationService") as service:
        service.return_value.deliver_user_notification.side_effect = RuntimeError("injected delivery failure")
        assert deliver_pending_payment_notifications(db) == 0
    item = db.query(PaymentNotification).filter_by(user_id=owner.id).one()
    assert item.attempts == 1 and item.delivered_at is None and item.last_error == "RuntimeError"
    assert txn.status == "success" and owner.member_tier == "personal_pro"
    item.next_attempt_at = datetime.utcnow()-timedelta(seconds=1); db.commit()
    with patch("app.services.payment_notification_service.NotificationService") as service:
        assert deliver_pending_payment_notifications(db) == 1
        assert deliver_pending_payment_notifications(db) == 0
        assert service.return_value.deliver_user_notification.call_count == 1
    assert item.delivered_at is not None


def test_same_enterprise_tier_renewal_updates_company_expiry(db):
    owner, sub, txn = order(db, plan="enterprise")
    PaymentService(db).activate_paid_transaction(txn)
    company = db.query(Company).filter_by(owner_id=owner.id).one()
    old_end = company.subscription_end_date
    renewal = SubscriptionTransaction(subscription_id=sub.id, transaction_id=uuid.uuid4().hex, amount=19,
                                      payment_method="alipay", status="pending", description="purpose=renew;duration_months=1")
    db.add(renewal); db.commit()
    PaymentService(db).activate_paid_transaction(renewal)
    assert company.subscription_end_date == sub.end_date > old_end


def test_attachment_real_http_ownership_and_deleted_parent(db, tmp_path, monkeypatch):
    from app.api import deps
    from app.api.v1.endpoints import files
    owner, other = user(db), user(db)
    inspection = QualityInspection(inspection_number=uuid.uuid4().hex, inspection_type="visual",
                                   inspection_date=datetime.utcnow(), result="pending", owner_id=owner.id)
    db.add(inspection); db.commit()
    app = FastAPI(); app.include_router(files.router, prefix="/files")
    app.dependency_overrides[deps.get_db] = lambda: db
    app.dependency_overrides[deps.get_current_active_user] = lambda: owner
    monkeypatch.setattr(files.settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(files, "enforce_rate_limit", lambda *a, **k: None)
    client = TestClient(app)
    def upload():
        return client.post("/files/upload", data={"resource_type":"quality", "resource_id":inspection.id},
                           files={"file":("test.png", b"private-content", "image/png")})
    response = upload()
    assert response.status_code == 200, response.text
    file_id = response.json()["data"]["file_id"]
    assert client.get(f"/files/{file_id}").content == b"private-content"
    assert db.query(Attachment).filter_by(id=file_id).one().user_id == owner.id
    app.dependency_overrides[deps.get_current_active_user] = lambda: other
    assert client.get(f"/files/{file_id}").status_code == 403
    assert upload().status_code == 403
    app.dependency_overrides[deps.get_current_active_user] = lambda: owner
    db.delete(inspection); db.commit()
    assert client.get(f"/files/{file_id}").status_code == 404
    (tmp_path/"files"/"legacy.png").write_bytes(b"legacy")
    assert client.get("/files/legacy.png").status_code == 404


@pytest.mark.parametrize("kind", ["plan", "standard", "performance", "report"])
def test_regular_employee_business_crud_contract_and_tenant_boundary(db, kind):
    from app.models.quality import QualityStandard
    from app.models.business_extensions import EmployeePerformance, ReportTemplate
    from app.services.workspace_entity_service import WorkspaceEntityService
    owner, member, outsider = user(db), user(db), user(db)
    company = Company(name="QA company", owner_id=owner.id)
    db.add(company); db.flush()
    factory = Factory(name="QA factory", company_id=company.id)
    db.add(factory); db.flush()
    employee = CompanyEmployee(company_id=company.id, user_id=member.id, role="employee", status="active",
                               factory_id=factory.id, data_access_scope="factory")
    db.add(employee)
    common = dict(user_id=owner.id, created_by=owner.id, workspace_type="enterprise", company_id=company.id, factory_id=None)
    rows = {
        "plan": lambda: ProductionPlan(**common, plan_number=uuid.uuid4().hex, plan_name="QA plan",
                                       plan_start_date=datetime.utcnow().date(), plan_end_date=datetime.utcnow().date()),
        "standard": lambda: QualityStandard(**common, standard_code=uuid.uuid4().hex, standard_name="QA standard"),
        "performance": lambda: EmployeePerformance(**common, employee_name="QA", review_period="2026-09"),
        "report": lambda: ReportTemplate(**common, name="QA report"),
    }
    row = rows[kind](); db.add(row); db.commit()
    service = WorkspaceEntityService(db, type(row))
    ctx = WorkspaceContext(member.id, "enterprise", company.id)
    assert service.get_item(row.id, member, ctx)["id"] == row.id
    listed, count = service.list_items(member, ctx)
    assert any(item["id"] == row.id for item in listed)
    for operation in [lambda: service.update_item(row.id, {"is_active":False}, member, ctx),
                      lambda: service.delete_item(row.id, member, ctx)]:
        with pytest.raises(HTTPException) as exc:
            operation()
        assert exc.value.status_code == 403
    assert row.is_active
    with pytest.raises(HTTPException) as exc:
        service.get_item(row.id, outsider, WorkspaceContext(outsider.id, "enterprise", company.id))
    assert exc.value.status_code == 403


def test_private_enterprise_record_cannot_leak_through_list(db):
    from app.models.wps import WPS
    owner, member = user(db), user(db)
    company = Company(name="QA", owner_id=owner.id); db.add(company); db.flush()
    db.add(CompanyEmployee(company_id=company.id, user_id=member.id, role="employee", status="active", data_access_scope="company"))
    record = WPS(wps_number=uuid.uuid4().hex, title="private", user_id=owner.id, created_by=owner.id, company_id=company.id,
                 workspace_type="enterprise", access_level="private")
    db.add(record); db.commit()
    query = DataAccessMiddleware(db).apply_workspace_filter(db.query(WPS), WPS, member, WorkspaceContext(member.id, "enterprise", company.id))
    assert record.id not in [item.id for item in query.all()]


def test_foundation_migration_repeated_upgrade_and_downgrade(sessions):
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    import importlib.util
    from pathlib import Path
    from sqlalchemy import inspect
    path = Path(__file__).parents[2] / "alembic/versions/add_attachment_payment_integrity.py"
    spec = importlib.util.spec_from_file_location("foundation_migration", path)
    migration = importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
    # A fresh isolated schema has the tables from bootstrap; upgrade must be repeatable.
    with sessions.kw["bind"].begin() as conn:
        with Operations.context(MigrationContext.configure(conn)):
            migration.upgrade(); migration.upgrade()
            assert {"attachments", "payment_activations", "payment_notifications"} <= set(inspect(conn).get_table_names())
            # Exercise the migration without deleting any previous test evidence: rollback DDL savepoint.
            savepoint = conn.begin_nested()
            migration.downgrade()
            assert "attachments" not in inspect(conn).get_table_names()
            migration.upgrade()
            assert "attachments" in inspect(conn).get_table_names()
            savepoint.rollback()



def test_notification_savepoint_rolls_back_announcement_before_retry(db):
    from app.models.system_announcement import SystemAnnouncement
    from app.services.email_service import email_service
    owner, sub, txn = order(db)
    PaymentService(db).activate_paid_transaction(txn)
    db.query(PaymentNotification).filter(PaymentNotification.user_id != owner.id).update(
        {"next_attempt_at": datetime.utcnow()+timedelta(days=1)}, synchronize_session=False)
    db.commit()
    with patch("app.services.notification_service.should_create_in_app", return_value=True), \
         patch("app.services.notification_service.should_send_email", return_value=True), \
         patch("app.services.notification_service.should_send_sms", return_value=False), \
         patch.object(email_service, "send_email", side_effect=[False, True]) as send:
        assert deliver_pending_payment_notifications(db) == 0
        assert db.query(SystemAnnouncement).filter_by(created_by=owner.id).count() == 0
        item = db.query(PaymentNotification).filter_by(user_id=owner.id).one()
        item.next_attempt_at = datetime.utcnow()-timedelta(seconds=1); db.commit()
        assert deliver_pending_payment_notifications(db) == 1
        assert deliver_pending_payment_notifications(db) == 0
        assert send.call_count == 2
    assert db.query(SystemAnnouncement).filter_by(created_by=owner.id).count() == 1
    assert txn.status == "success"


def test_enterprise_attachment_rechecks_membership_and_record_scope(db, tmp_path, monkeypatch):
    from app.api.v1.endpoints import files
    from fastapi import UploadFile
    from io import BytesIO
    owner, member = user(db), user(db)
    company = Company(name="Attachment QA", owner_id=owner.id); db.add(company); db.flush()
    employee = CompanyEmployee(company_id=company.id, user_id=member.id, role="employee", status="active", data_access_scope="company")
    db.add(employee)
    inspection = QualityInspection(inspection_number=uuid.uuid4().hex, inspection_type="visual", inspection_date=datetime.utcnow(),
                                   owner_id=owner.id, company_id=company.id)
    db.add(inspection); db.commit()
    monkeypatch.setattr(files.settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(files, "enforce_rate_limit", lambda *a, **k: None)
    result = files.upload_file(UploadFile(filename="inspection.png", file=BytesIO(b"private")), "quality", inspection.id, db, owner)
    file_id = result["data"]["file_id"]
    assert files.download_file(file_id, db, member).filename == "inspection.png"
    employee.status = "inactive"; db.commit()
    with pytest.raises(HTTPException) as exc:
        files.download_file(file_id, db, member)
    assert exc.value.status_code == 403
    inspection.company_id = None; db.commit()
    with pytest.raises(HTTPException) as exc:
        files.download_file(file_id, db, owner)
    assert exc.value.status_code == 403



def test_legacy_success_repairs_entitlements_without_extending_subscription(db):
    owner, sub, txn = order(db)
    txn.status = "success"
    sub.status = "active"
    original_end = sub.end_date
    db.commit()
    result = PaymentService(db).activate_paid_transaction(txn)
    assert result["already_active"] is True
    assert owner.member_tier == "personal_pro"
    assert owner.subscription_end_date == sub.end_date == original_end
    assert db.query(PaymentActivation).filter_by(transaction_id=txn.id).count() == 1
    assert db.query(PaymentNotification).filter_by(user_id=owner.id).count() == 0
