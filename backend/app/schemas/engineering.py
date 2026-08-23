"""API contracts for P3 engineering drawings and review."""
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.smart_import import AIExtractionRequest


class ProjectCreate(BaseModel):
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    access_level: Literal["private", "factory", "company"] = "private"


class ProductCreate(BaseModel):
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    product_type: str | None = Field(None, max_length=100)
    access_level: Literal["private", "factory", "company"] = "private"


class DrawingAIRequest(AIExtractionRequest):
    # Kept optional for deterministic integrations/tests and manual-only customers.
    extracted_payload: dict[str, Any] | None = None


class EntityPatch(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = Field(None, max_length=1000)


class JointCreate(BaseModel):
    weld_number: str = Field(min_length=1, max_length=100)
    part_a_id: str | None = None
    part_b_id: str | None = None
    joint_type: str | None = None
    groove_type: str | None = None
    groove_angle: float | None = None
    root_gap: float | None = None
    root_face: float | None = None
    weld_size: float | None = None
    length_mm: float | None = None
    weld_position: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class JointSplit(BaseModel):
    weld_numbers: list[str] = Field(min_length=2, max_length=20)
    lengths_mm: list[float] | None = None
    reason: str | None = Field(None, max_length=1000)

    @model_validator(mode="after")
    def validate_lengths(self):
        if self.lengths_mm is not None and len(self.lengths_mm) != len(
            self.weld_numbers
        ):
            raise ValueError("拆分长度数量必须与新焊缝数量一致")
        return self


class JointMerge(BaseModel):
    joint_ids: list[str] = Field(min_length=2, max_length=20)
    weld_number: str = Field(min_length=1, max_length=100)
    reason: str | None = Field(None, max_length=1000)


class RevisionApprove(BaseModel):
    note: str | None = Field(None, max_length=1000)
    force: bool = False
