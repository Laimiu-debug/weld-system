"""P7 production release API contracts."""
from typing import Literal

from pydantic import BaseModel, Field


class ReleaseSequenceRequest(BaseModel):
    consumable_issue_list_id: str | None = None


class ResourceAssignmentRequest(BaseModel):
    welder_id: int = Field(gt=0)
    equipment_id: int | None = Field(None, gt=0)
    override_reason: str | None = Field(None, min_length=5, max_length=1000)


class ResourceOverrideDecision(BaseModel):
    approve: bool


class ExecutionRecordRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=64)
    status: Literal["recorded", "completed"] = "recorded"
    actual_parameters: dict = Field(default_factory=dict)
    consumable_usage_event_ids: list[str] = Field(default_factory=list, max_length=1000)
    repair_snapshot: dict = Field(default_factory=dict)
    quality_snapshot: dict = Field(default_factory=dict)


class SequenceChangeRequestCreate(BaseModel):
    reason: str = Field(min_length=5, max_length=2000)
    impact_snapshot: dict = Field(default_factory=dict)
    workflow_id: int | None = Field(None, gt=0)


class SequenceChangeApply(BaseModel):
    proposed_sequence_revision_id: str
