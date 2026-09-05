"""API contracts for P3 engineering drawings and review."""
from typing import Any, Literal

from pydantic import BaseModel, Field, StrictInt, model_validator

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
    page_numbers: list[StrictInt] | None = Field(None, min_length=1, max_length=500)
    region: list[float] | None = Field(None, min_length=4, max_length=4)
    page_rotations: dict[int, Literal[0, 90, 180, 270]] = Field(default_factory=dict)
    retry_job_id: str | None = Field(None, max_length=36)

    @model_validator(mode="after")
    def validate_scope(self):
        if self.page_numbers and (
            min(self.page_numbers) < 1
            or len(set(self.page_numbers)) != len(self.page_numbers)
        ):
            raise ValueError("页码必须为不重复的正整数")
        if any(page < 1 for page in self.page_rotations):
            raise ValueError("旋转页码必须为正整数")
        if self.region is not None:
            x1, y1, x2, y2 = self.region
            if (
                not self.page_numbers
                or len(self.page_numbers) != 1
                or not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1)
            ):
                raise ValueError("局部识别须指定单页及有效的归一化区域坐标")
        if self.retry_job_id and (
            self.page_numbers or self.region or self.page_rotations
        ):
            raise ValueError("阶段重试沿用原任务范围和方向，不能同时修改")
        if self.extracted_payload is not None and (
            self.page_numbers or self.region or self.page_rotations or self.retry_job_id
        ):
            raise ValueError("手工结果不能与局部识别或重试参数混用")
        return self


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
