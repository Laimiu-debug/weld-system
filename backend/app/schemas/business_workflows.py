"""Writable contracts for standards, employee reviews and custom reports."""
import json
import re
from datetime import date
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Score = Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]


class BusinessInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, allow_inf_nan=False)


class StandardInput(BusinessInput):
    standard_code: str = Field(min_length=1, max_length=100)
    standard_name: str = Field(min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    version: str = Field(min_length=1, max_length=50)
    level: Optional[str] = Field(None, max_length=50)
    status: Literal['active', 'inactive', 'draft'] = 'active'
    description: Optional[str] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    test_methods: str = '[]'
    acceptance_criteria: str = '[]'

    @field_validator('test_methods', 'acceptance_criteria', mode='before')
    @classmethod
    def text_list(cls, value):
        items = json.loads(value) if isinstance(value, str) else value
        if not isinstance(items, list) or any(not isinstance(x, str) or not x.strip() for x in items):
            raise ValueError('检验方法和验收项必须是非空文本列表')
        return json.dumps([x.strip() for x in items], ensure_ascii=False)

    @model_validator(mode='after')
    def dates(self):
        if self.effective_date and self.expiry_date and self.expiry_date < self.effective_date:
            raise ValueError('失效日期不能早于生效日期')
        return self


class PerformanceInput(BusinessInput):
    employee_user_id: int = Field(gt=0)
    review_period: str
    overall_score: Score = 0
    quality_score: Optional[Score] = None
    efficiency_score: Optional[Score] = None
    safety_score: Optional[Score] = None
    teamwork_score: Optional[Score] = None
    status: Literal['draft', 'submitted', 'reviewed', 'finalized'] = 'draft'
    goals: Optional[str] = None
    achievements: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    reviewer_comment: Optional[str] = None
    adjustment_reason: Optional[str] = None

    @field_validator('review_period')
    @classmethod
    def period(cls, value):
        if not re.fullmatch(r'\d{4}-(?:0[1-9]|1[0-2]|Q[1-4])', value):
            raise ValueError('考核周期须为 YYYY-MM 或 YYYY-Q1 至 YYYY-Q4')
        if not 1900 <= int(value[:4]) <= 9998:
            raise ValueError('考核年份超出范围')
        return value


class ReportInput(BusinessInput):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    data_sources: str
    metrics: str = '["count"]'
    filters: str = '[]'
    group_by: Optional[str] = None
    chart_type: Literal['table', 'bar', 'line', 'pie'] = 'table'
    time_range: Optional[str] = None
    is_public: bool = False


class PlanTasksInput(BusinessInput):
    task_ids: list[int] = Field(max_length=200)

    @field_validator('task_ids')
    @classmethod
    def task_ids_valid(cls, value):
        if len(value) != len(set(value)) or any(x <= 0 for x in value):
            raise ValueError('任务 ID 必须是互不重复的正整数')
        return value
