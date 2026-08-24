"""Stateless calculator / quote API contracts (weldmoney-style + P6 layers)."""
from typing import Literal

from pydantic import BaseModel, Field


class CalculatorOperationIn(BaseModel):
    role: Literal["face", "gouge", "tack", "custom"] = "face"
    name: str = "正面填充"
    method: str = "GMAW"
    material: str = "ER50-6"
    density_g_cm3: float = Field(7.85, gt=0)
    deposition_efficiency: float = Field(0.95, gt=0, le=1)
    unit_price: float = Field(0, ge=0)
    flux_wire_ratio: float = Field(0, ge=0)
    flux_unit_price: float = Field(0, ge=0)
    custom_area_mm2: float = Field(0, ge=0)
    stub_loss_ratio: float = Field(0, ge=0, lt=1)
    spatter_loss_ratio: float = Field(0, ge=0, lt=1)
    flux_loss_ratio: float = Field(0, ge=0, lt=1)
    enterprise_correction_factor: float = Field(1.0, gt=0)
    package_size_kg: float | None = Field(None, gt=0)
    deposition_rate_kg_h: float | None = Field(None, gt=0)
    arc_time_ratio: float | None = Field(None, gt=0, le=1)
    gas_flow_l_min: float | None = Field(None, ge=0)


class CalculatorJointIn(BaseModel):
    name: str = "焊缝"
    groove: str = "V"
    thickness_mm: float = Field(12, gt=0)
    included_angle_deg: float = Field(60, ge=0, lt=180)
    root_gap_mm: float = Field(0, ge=0)
    root_face_mm: float = Field(0, ge=0)
    radius_mm: float = Field(0, ge=0)
    upper_bevel_height_mm: float = Field(0, ge=0)
    leg_size_mm: float = Field(0, ge=0)
    reinforcement_mm: float = Field(0, ge=0)
    back_gouge_depth_mm: float = Field(0, ge=0)
    gouge_opening_width_mm: float = Field(0, ge=0)
    face_extra_each_side_mm: float = Field(0, ge=0)
    fill_factor: float = Field(1.05, gt=0)
    length_mm: float = Field(0, ge=0)
    operations: list[CalculatorOperationIn] = Field(min_length=1)


class CostParamsIn(BaseModel):
    labor_rate_per_hour: float = Field(80, ge=0)
    overhead_rate: float = Field(0.15, ge=0)
    gas_price_per_l: float = Field(0.02, ge=0)
    machine_power_kw: float = Field(15, ge=0)
    electricity_price: float = Field(1.0, ge=0)
    daily_depreciation: float = Field(200, ge=0)
    daily_work_hours: float = Field(8, gt=0)
    profit_margin: float = Field(0.12, ge=0)
    tax_rate: float = Field(0.13, ge=0)


class CalculatorQuoteRequest(BaseModel):
    joints: list[CalculatorJointIn] = Field(min_length=1)
    cost_params: CostParamsIn = Field(default_factory=CostParamsIn)
    customer: str | None = None
    project_name: str | None = None
