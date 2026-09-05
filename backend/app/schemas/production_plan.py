"""Validated production plan inputs, separate from database/audit fields."""
from datetime import date
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

PlanStatus = Literal["draft", "approved", "in_progress", "completed", "cancelled"]
PlanPriority = Literal["low", "normal", "high", "urgent"]
PlanNumber = Annotated[str, Field(min_length=1, max_length=100)]
PlanName = Annotated[str, Field(min_length=1, max_length=255)]
Progress = Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]
Quantity = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class ProductionPlanCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    plan_number: PlanNumber
    plan_name: PlanName
    plan_start_date: date
    plan_end_date: date
    plan_type: Optional[str] = Field(None, max_length=100)
    priority: PlanPriority = "normal"
    status: PlanStatus = "draft"
    progress_percentage: Progress = 0
    planned_quantity: Optional[Quantity] = None
    unit: Optional[str] = Field(None, max_length=50)
    assigned_team: Optional[str] = Field(None, max_length=255)
    quality_standards: Optional[str] = None
    description: Optional[str] = None
    objectives: Optional[str] = None
    tasks: Optional[str] = None

    @model_validator(mode="after")
    def validate_business_rules(self):
        if self.plan_end_date < self.plan_start_date:
            raise ValueError("结束日期不能早于开始日期")
        if self.status == "completed" and self.progress_percentage != 100:
            raise ValueError("已完成计划的进度必须为100%")
        if self.planned_quantity and not self.unit:
            raise ValueError("填写计划数量时必须填写单位")
        return self


class ProductionPlanUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    plan_number: Optional[PlanNumber] = None
    plan_name: Optional[PlanName] = None
    plan_start_date: Optional[date] = None
    plan_end_date: Optional[date] = None
    plan_type: Optional[str] = Field(None, max_length=100)
    priority: Optional[PlanPriority] = None
    status: Optional[PlanStatus] = None
    progress_percentage: Optional[Progress] = None
    planned_quantity: Optional[Quantity] = None
    unit: Optional[str] = Field(None, max_length=50)
    assigned_team: Optional[str] = Field(None, max_length=255)
    quality_standards: Optional[str] = None
    description: Optional[str] = None
    objectives: Optional[str] = None
    tasks: Optional[str] = None

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        required = {"plan_number", "plan_name", "plan_start_date", "plan_end_date", "priority", "status", "progress_percentage"}
        if any(getattr(self, key) is None for key in required & self.model_fields_set):
            raise ValueError("编号、名称、日期、优先级、状态和进度不能清空")
        return self
