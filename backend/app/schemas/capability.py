"""Schemas for the enterprise welding capability library."""
from typing import Any, Literal

from pydantic import BaseModel, Field


class CapabilityFilters(BaseModel):
    factory_id: int | None = Field(None, gt=0)
    process: str | None = Field(None, max_length=100)
    material_group: str | None = Field(None, max_length=100)
    position: str | None = Field(None, max_length=100)
    search: str | None = Field(None, max_length=200)


class CapabilityOverviewResponse(BaseModel):
    generated_at: str
    workspace: dict[str, Any]
    filters: dict[str, Any]
    summary: dict[str, int | float]
    health: dict[str, Any]
    dimensions: dict[str, list[Any]]
    wps_records: list[dict[str, Any]]
    pqr_records: list[dict[str, Any]]
    welders: list[dict[str, Any]]
    process_capabilities: list[dict[str, Any]]
    materials: list[dict[str, Any]]
    equipment: list[dict[str, Any]]
    issues: list[dict[str, Any]]


class CapabilityCheckRequest(BaseModel):
    standard_system: Literal["china", "asme", "ped"] = "china"
    factory_id: int | None = Field(None, gt=0)
    welding_process: str = Field(min_length=1, max_length=100)
    material_group: str = Field(min_length=1, max_length=100)
    thickness_mm: float = Field(gt=0, le=10000)
    diameter_mm: float | None = Field(None, gt=0, le=100000)
    welding_position: str = Field(min_length=1, max_length=100)
    pwht_required: bool = False
    impact_required: bool = False
    impact_temperature_c: float | None = Field(None, ge=-273.15, le=2000)


class CapabilityCheckResponse(BaseModel):
    decision: str
    process_capable: bool
    personnel_capable: bool
    resource_ready: bool
    requirement: dict[str, Any]
    matched_capabilities: list[dict[str, Any]]
    matched_welders: list[dict[str, Any]]
    matched_materials: list[dict[str, Any]]
    matched_equipment: list[dict[str, Any]]
    gaps: list[dict[str, Any]]
    explanation: list[str]
