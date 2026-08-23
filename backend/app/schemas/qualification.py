"""Schemas for versioned procedure-qualification calculations and support links."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class QualificationRulePackResponse(BaseModel):
    id: str
    code: str
    name: str
    standard_code: str
    edition: str
    version: str
    status: Literal["draft", "review", "published", "retired"]
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    rules: list[dict[str, Any]]
    clause_references: list[dict[str, Any]]
    compliance_metadata: dict[str, Any]
    published_at: datetime | None

    model_config = {"from_attributes": True}


class QualificationRulePackStatusUpdate(BaseModel):
    status: Literal["draft", "review", "published", "retired"]


class PQRQualificationCalculateRequest(BaseModel):
    rule_pack_id: str | None = Field(None, max_length=36)
    force_recalculate: bool = False
    fact_overrides: dict[str, Any] = Field(default_factory=dict)


class PQRQualificationResultResponse(BaseModel):
    id: str
    pqr_id: int
    pqr_version_key: str
    pqr_snapshot_hash: str
    rule_pack_id: str
    rule_pack_version: str
    calculation_key: str
    outcome: Literal[
        "qualified", "not_qualified", "needs_confirmation", "insufficient_data"
    ]
    input_snapshot: dict[str, Any]
    result: dict[str, Any]
    basis: list[dict[str, Any]]
    missing_fields: list[str]
    boundary_conditions: list[dict[str, Any]]
    requires_human_confirmation: bool
    supersedes_result_id: str | None
    is_current: bool
    calculated_by: int | None
    calculated_at: datetime

    model_config = {"from_attributes": True}


class WPSPQRSupportCreate(BaseModel):
    pqr_id: int = Field(gt=0)
    qualification_result_id: str | None = Field(None, max_length=36)
    supported_processes: list[str] = Field(default_factory=list, max_length=20)
    qualified_scope: dict[str, Any] = Field(default_factory=dict)
    source: Literal["manual", "smart_import", "rule_match"] = "manual"
    confirmation_status: Literal["pending", "confirmed"] = "pending"
    confirmation_note: str | None = Field(None, max_length=2000)

    @model_validator(mode="after")
    def confirmed_link_requires_result(self):
        if self.confirmation_status == "confirmed" and not self.qualification_result_id:
            raise ValueError("确认支持关系必须绑定资格计算结果")
        return self


class WPSPQRSupportConfirm(BaseModel):
    confirmation_status: Literal["confirmed", "rejected"]
    confirmation_note: str | None = Field(None, max_length=2000)


class WPSPQRSupportResponse(BaseModel):
    id: str
    wps_id: int
    pqr_id: int
    qualification_result_id: str | None
    wps_version_key: str
    pqr_version_key: str
    wps_snapshot_hash: str
    pqr_snapshot_hash: str
    wps_snapshot: dict[str, Any]
    pqr_snapshot: dict[str, Any]
    supported_processes: list[str]
    qualified_scope: dict[str, Any]
    source: str
    confirmation_status: str
    confirmation_note: str | None
    confirmed_by: int | None
    confirmed_at: datetime | None
    is_active: bool
    created_by: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class WPSQualificationTraceResponse(BaseModel):
    wps_id: int
    current_wps_version_key: str
    valid_support_count: int
    stale_support_count: int
    links: list[WPSPQRSupportResponse]
