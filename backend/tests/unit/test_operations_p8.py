"""P8 observability, privacy, deployment and lifecycle contracts."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import zipfile

import pytest
from fastapi import FastAPI, HTTPException

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.data_access import WorkspaceContext
from app.models.operations import (
    AIProviderHealthCheck,
    BackupVerification,
    CredentialRotationAudit,
    DataOutboundConsent,
    DeploymentProfile,
    OperationalAlert,
    OperationalTaskEvent,
    TenantLifecycleJob,
)
from app.schemas.smart_import import AIExtractionRequest
from app.services.ai_credential_service import AIProviderConfigService
from app.services.ai_extraction_service import build_provider
from app.services.operations_service import (
    OperationsService,
    REQUIRED_BACKUP_CATEGORIES,
    deployment_capabilities,
    sanitize_log_context,
    validate_backup_manifest,
)


def test_operational_event_covers_ai_ocr_rule_and_import_metrics():
    columns = set(OperationalTaskEvent.__table__.c.keys())
    assert {
        "task_kind",
        "status",
        "queue_wait_ms",
        "duration_ms",
        "retry_count",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "estimated_cost_micros",
        "error_code",
        "log_context",
    } <= columns
    task_check = next(
        item
        for item in OperationalTaskEvent.__table__.constraints
        if item.name == "ck_operational_task_kind"
    )
    assert all(
        kind in str(task_check.sqltext) for kind in ("ai", "ocr", "rule", "import")
    )


def test_log_context_redacts_nested_secrets():
    result = sanitize_log_context(
        {
            "api_key": "sk-secret",
            "nested": {"access_token": "token", "safe": "ok"},
            "items": [{"password": "p"}],
        }
    )
    assert result == {
        "api_key": "[REDACTED]",
        "nested": {"access_token": "[REDACTED]", "safe": "ok"},
        "items": [{"password": "[REDACTED]"}],
    }


def test_alert_and_health_models_keep_admin_audit_state():
    assert {
        "fingerprint",
        "severity",
        "status",
        "acknowledged_by",
        "resolved_at",
    } <= set(OperationalAlert.__table__.c.keys())
    assert {
        "provider_config_id",
        "status",
        "latency_ms",
        "error_code",
        "safe_message",
    } <= set(AIProviderHealthCheck.__table__.c.keys())


def test_backup_manifest_requires_every_critical_category_and_checksums():
    complete = {
        "coverage": {key: True for key in REQUIRED_BACKUP_CATEGORIES},
        "checksums_verified": True,
    }
    status, coverage, missing = validate_backup_manifest(complete, restore_tested=True)
    assert status == "passed"
    assert all(coverage.values())
    assert missing == []

    partial = {"coverage": {"database": True}, "checksums_verified": False}
    status, _, missing = validate_backup_manifest(partial, restore_tested=False)
    assert status == "partial"
    assert "original_files" in missing
    assert "restore_drill" in missing


def test_backup_verification_persists_restore_drill_evidence():
    assert {
        "manifest_hash",
        "coverage",
        "missing_categories",
        "restore_tested",
        "restore_target",
    } <= set(BackupVerification.__table__.c.keys())


@pytest.mark.parametrize(
    ("mode", "network", "local_ai", "external", "manual"),
    [
        ("saas", "external_allowed", False, True, True),
        ("private", "allowlist_only", True, True, True),
        ("offline", "offline", True, False, True),
        ("offline", "offline", False, False, True),
    ],
)
def test_deployment_modes_have_explicit_capabilities(
    mode, network, local_ai, external, manual
):
    result = deployment_capabilities(mode, network, local_ai, local_ocr=True)
    assert result["external_ai"] is external
    assert result["manual_entry"] is manual
    assert result["local_ai"] is local_ai


def test_external_storage_capability_respects_tenant_switch():
    result = deployment_capabilities(
        "private",
        "allowlist_only",
        local_ai=True,
        local_ocr=True,
        external_storage_allowed=False,
    )
    assert result["external_storage"] is False


def test_external_document_backend_is_blocked_by_tenant_policy(monkeypatch):
    monkeypatch.setattr(settings, "DOCUMENT_STORAGE_BACKEND", "s3")
    profile = SimpleNamespace(
        deployment_mode="private",
        network_policy="allowlist_only",
        external_storage_allowed=False,
    )
    service = OperationsService(Mock())
    service.get_deployment_profile = Mock(return_value=profile)
    with pytest.raises(HTTPException, match="禁止向外部文档存储"):
        service.ensure_document_storage_allowed(SimpleNamespace(company_id=9))


def test_outbound_consent_is_versioned_revocable_and_document_bound():
    assert {
        "document_id",
        "document_type",
        "provider_host",
        "purpose",
        "privacy_notice_version",
        "privacy_notice_hash",
        "authorized_by",
        "authorized_at",
        "expires_at",
        "revoked_at",
    } <= set(DataOutboundConsent.__table__.c.keys())
    request = AIExtractionRequest(mode="platform", outbound_consent_id="consent-1")
    assert request.outbound_consent_id == "consent-1"


def test_tenant_lifecycle_requires_audited_export_delete_states():
    assert {
        "operation",
        "status",
        "confirmation",
        "export_manifest",
        "deletion_plan",
        "requested_by",
        "approved_by",
        "executed_by",
    } <= set(TenantLifecycleJob.__table__.c.keys())


def test_active_alert_uniqueness_does_not_block_multiple_resolved_rows():
    index = next(
        item
        for item in OperationalAlert.__table__.indexes
        if item.name == "uq_operational_alert_active_fingerprint"
    )
    assert index.unique is True
    assert "acknowledged" in str(index.dialect_options["postgresql"]["where"])


def test_tenant_export_creates_and_validates_real_zip(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    db = Mock()
    result = Mock()
    result.mappings.return_value = []
    db.execute.return_value = result
    query = Mock()
    query.filter.return_value.order_by.return_value.all.return_value = []
    db.query.return_value = query
    service = OperationsService(db)
    service._tenant_table_rows = Mock(
        return_value={"companies": [{"id": 9, "name": "Tenant 9"}]}
    )
    job = TenantLifecycleJob(id="job-export", company_id=9, operation="export")

    manifest = service._create_tenant_export(job, 9)
    artifact = service._validate_tenant_export(manifest, job, 9)

    assert artifact.is_file()
    assert manifest["artifact_size_bytes"] > 0
    assert len(manifest["artifact_sha256"]) == 64
    with zipfile.ZipFile(artifact) as archive:
        content = archive.read("manifest.json")
        assert b'"job_id":"job-export"' in content


def test_tenant_delete_requires_dry_run_export_manifest():
    job = TenantLifecycleJob(
        id="job-1",
        company_id=9,
        operation="delete",
        status="approved",
        export_manifest={},
    )
    query = Mock()
    query.filter.return_value.first.return_value = job
    db = Mock()
    db.query.return_value = query
    service = OperationsService(db)
    service.ensure_manager = Mock()
    with pytest.raises(HTTPException) as exc:
        service.execute_lifecycle_job(
            "job-1",
            "EXECUTE DELETE 9",
            False,
            SimpleNamespace(id=7),
            SimpleNamespace(company_id=9),
        )
    assert exc.value.status_code == 409


def test_credential_rotation_never_stores_secret_and_increments_version():
    columns = set(CredentialRotationAudit.__table__.c.keys())
    assert {
        "credential_type",
        "credential_ref",
        "old_version",
        "new_version",
        "rotated_by",
    } <= columns
    assert not any("key_value" in name or "ciphertext" in name for name in columns)


def test_deployment_profile_supports_saas_private_and_offline():
    constraint = next(
        item
        for item in DeploymentProfile.__table__.constraints
        if item.name == "ck_deployment_profile_mode"
    )
    assert all(
        mode in str(constraint.sqltext) for mode in ("saas", "private", "offline")
    )


def test_offline_model_uses_local_endpoint_and_blocks_external_policy(monkeypatch):
    monkeypatch.setattr(settings, "AI_OFFLINE_BASE_URL", "http://127.0.0.1:11434/v1")
    monkeypatch.setattr(settings, "AI_OFFLINE_MODEL", "local-weld-model")
    provider = build_provider(AIExtractionRequest(mode="offline"))
    try:
        assert provider.config.base_url == "http://127.0.0.1:11434/v1"
        assert provider.config.model == "local-weld-model"
    finally:
        provider.close()

    monkeypatch.setattr(settings, "DEPLOYMENT_MODE", "offline")
    with pytest.raises(HTTPException) as exc:
        AIProviderConfigService(None).enforce_policy(
            "platform", None, WorkspaceContext(user_id=1)
        )
    assert exc.value.status_code == 503


def test_p8_api_exposes_dashboard_health_privacy_backup_and_lifecycle():
    probe = FastAPI()
    probe.include_router(api_router)
    paths = set(probe.openapi()["paths"])
    assert {
        "/operations/dashboard",
        "/operations/alerts/detect",
        "/operations/providers/{config_id}/health-check",
        "/operations/providers/fallback-plan",
        "/operations/outbound-consents",
        "/operations/deployment-profile",
        "/operations/backup-verifications",
        "/operations/tenant-lifecycle",
        "/operations/tenant-lifecycle/{job_id}/execute",
        "/operations/tenant-lifecycle/{job_id}/artifact",
    } <= paths


def test_approval_snapshot_migration_executes_colon_literals_as_raw_sql():
    path = (
        Path(__file__).parents[2]
        / "alembic"
        / "versions"
        / "add_approval_version_snapshots.py"
    )
    spec = spec_from_file_location("approval_snapshot_migration", path)
    assert spec is not None and spec.loader is not None
    migration = module_from_spec(spec)
    spec.loader.exec_module(migration)
    connection = Mock()

    with patch.object(migration.op, "get_bind", return_value=connection):
        migration.upgrade()

    sql = connection.exec_driver_sql.call_args.args[0]
    assert "':legacy'" in sql
