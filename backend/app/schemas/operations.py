"""P8 operations and governance API contracts."""
from typing import Literal

from pydantic import BaseModel, Field


class AlertDecision(BaseModel):
    action: Literal["acknowledge", "resolve"]


class OutboundConsentCreate(BaseModel):
    document_id: str
    provider_host: str = Field(min_length=3, max_length=255)
    purpose: str = Field(min_length=5, max_length=200)
    privacy_notice_version: str = Field(min_length=1, max_length=40)
    privacy_notice_hash: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    authorized: bool
    expires_at: str | None = None


class DeploymentProfileUpdate(BaseModel):
    deployment_mode: Literal["saas", "private", "offline"]
    network_policy: Literal["external_allowed", "allowlist_only", "offline"]
    local_ai_base_url: str | None = Field(None, max_length=500)
    local_ai_model: str | None = Field(None, max_length=120)
    local_ocr_enabled: bool = False
    external_storage_allowed: bool = True
    config_snapshot: dict = Field(default_factory=dict)


class BackupVerificationCreate(BaseModel):
    backup_ref: str = Field(min_length=3, max_length=255)
    manifest: dict
    restore_tested: bool = False
    restore_target: str | None = Field(None, max_length=100)
    notes: str | None = Field(None, max_length=2000)


class TenantLifecycleCreate(BaseModel):
    operation: Literal["export", "delete"]
    confirmation: str | None = Field(None, max_length=200)


class TenantLifecycleDecision(BaseModel):
    approve: bool


class TenantLifecycleExecute(BaseModel):
    confirmation: str = Field(min_length=8, max_length=200)
    dry_run: bool = True


class ProviderFallbackRequest(BaseModel):
    preferred_config_id: str | None = None
    allow_manual_fallback: bool = True
