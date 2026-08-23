"""P5 weld sequence API contracts."""
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SequenceGenerate(BaseModel):
    strategies: dict[str, bool] = Field(default_factory=dict)
    ai_step_codes: list[str] | None = Field(None, max_length=1000)
    ai_explanation: str | None = Field(None, max_length=4000)

    @model_validator(mode="after")
    def validate_strategies(self):
        allowed = {"symmetric", "segmented", "skip_weld", "closed_space_first"}
        unknown = set(self.strategies) - allowed
        if unknown:
            raise ValueError(f"未知焊序策略：{', '.join(sorted(unknown))}")
        if self.ai_step_codes and len(self.ai_step_codes) != len(
            set(self.ai_step_codes)
        ):
            raise ValueError("AI 候选步骤不能重复")
        return self


class SequenceReorder(BaseModel):
    ordered_step_ids: list[str] = Field(min_length=1, max_length=2000)
    locked_step_ids: list[str] = Field(default_factory=list, max_length=2000)
    change_summary: str = Field(min_length=2, max_length=1000)

    @model_validator(mode="after")
    def validate_unique(self):
        if len(self.ordered_step_ids) != len(set(self.ordered_step_ids)):
            raise ValueError("步骤顺序不能包含重复项")
        if not set(self.locked_step_ids) <= set(self.ordered_step_ids):
            raise ValueError("锁定步骤必须属于当前方案")
        return self


class SequenceRecalculate(BaseModel):
    strategies: dict[str, bool] | None = None
    change_summary: str = Field(default="按当前数据重新计算", max_length=1000)


class SequenceSubmit(BaseModel):
    notes: str | None = Field(None, max_length=2000)
    priority: Literal["low", "normal", "high", "urgent"] = "normal"
    workflow_id: int | None = Field(None, gt=0)
