"""API contracts for explainable deterministic WPS/PQR matching."""
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class MatchRunCreate(BaseModel):
    joint_ids: list[str] | None = Field(None, max_length=500)
    affected_only: bool = False
    trigger_type: Literal["manual", "field_change", "drawing_change"] = "manual"
    policy_weights: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy_weights(self):
        allowed = {
            "material_group",
            "thickness",
            "diameter",
            "joint",
            "process",
            "position",
            "filler",
            "pwht",
            "impact",
        }
        unknown = set(self.policy_weights) - allowed
        if unknown:
            raise ValueError(f"未知排序维度：{', '.join(sorted(unknown))}")
        if any(value < 0 or value > 100 for value in self.policy_weights.values()):
            raise ValueError("排序权重必须在 0 到 100 之间")
        return self


class CandidateConfirm(BaseModel):
    status: Literal["confirmed", "rejected"]
    note: str | None = Field(None, max_length=2000)

    @model_validator(mode="after")
    def require_note_for_rejection(self):
        if self.status == "rejected" and not (self.note or "").strip():
            raise ValueError("拒绝候选时必须填写原因")
        return self


class MatchRunApprove(BaseModel):
    note: str | None = Field(None, max_length=2000)


class CapabilityGapLink(BaseModel):
    ppqr_id: int | None = Field(None, gt=0)
    qualification_plan_reference: str | None = Field(None, max_length=200)

    @model_validator(mode="after")
    def require_target(self):
        if (
            self.ppqr_id is None
            and not (self.qualification_plan_reference or "").strip()
        ):
            raise ValueError("必须关联 pPQR 或新评定计划")
        return self
