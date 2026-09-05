"""Explicit, reviewed heat-treatment stages and inspection dependencies."""
from typing import Literal

from fastapi import HTTPException
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

Method = Literal["VT", "RT", "UT", "MT", "PT", "ET", "LT", "AT"]


class TreatmentStage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(pattern=r"^[A-Za-z0-9_-]{1,30}$")
    scope: Literal["local", "global"]
    group: str | None = Field(None, pattern=r"^[A-Za-z0-9_-]{1,30}$")
    temperature_min: float = Field(ge=0, le=2000, allow_inf_nan=False)
    temperature_max: float = Field(ge=0, le=2000, allow_inf_nan=False)
    hold_minutes: float = Field(gt=0, le=100000, allow_inf_nan=False)
    nde_before: list[Method] = Field(default_factory=list, max_length=8)
    nde_after: list[Method] = Field(default_factory=list, max_length=8)

    @field_validator("group", mode="before")
    @classmethod
    def empty_group(cls, value):
        return None if value == "" else value

    @model_validator(mode="after")
    def consistent(self):
        if self.temperature_min > self.temperature_max:
            raise ValueError("热处理温度下限不能超过上限")
        if self.scope == "global" and not self.group:
            raise ValueError("整体热处理必须指定共同批组编号")
        if self.scope == "local" and self.group:
            raise ValueError("局部热处理不能使用整体批组编号")
        if len(set(self.nde_before)) != len(self.nde_before) or len(
            set(self.nde_after)
        ) != len(self.nde_after):
            raise ValueError("同一阶段的检测方法不能重复")
        return self


def validate_treatment_plan(value):
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > 12:
        raise HTTPException(422, "热处理计划须为最多 12 个阶段的列表")
    try:
        stages = [TreatmentStage.model_validate(row).model_dump() for row in value]
    except ValidationError as exc:
        raise HTTPException(
            422,
            {"message": "热处理阶段参数不完整或无效", "issues": [e["msg"] for e in exc.errors()]},
        ) from exc
    if len({row["code"] for row in stages}) != len(stages):
        raise HTTPException(422, "热处理阶段编号不能重复")
    return stages


def add_treatment_steps(
    joint, requirement, freeze, add_step, add_edge, shared, all_welds
):
    plan = validate_treatment_plan(getattr(requirement, "treatment_plan", None))
    if not plan:
        raise HTTPException(
            422, f"焊缝 {joint.weld_number} 需要明确热处理范围、温度、保温时间及检测阶段，请先完善并审核工艺要求"
        )
    if getattr(requirement, "review_status", "accepted") not in {
        "accepted",
        "corrected",
    }:
        raise HTTPException(422, f"焊缝 {joint.weld_number} 的热处理计划尚未审核")
    methods = set(getattr(requirement, "nde_methods", None) or [])
    planned = {m for row in plan for m in row["nde_before"] + row["nde_after"]}
    if not methods <= planned:
        raise HTTPException(422, f"焊缝 {joint.weld_number} 的热处理计划遗漏已规定检测方法")
    terminal = f"WELD-{joint.id}"
    for stage in plan:

        def inspection(method, when, previous):
            code = f"NDE-{joint.id}-{stage['code']}-{when}-{method}"
            add_step(
                code,
                "nde",
                f"{joint.weld_number} · {stage['code']} {'热前' if when == 'before' else '热后'} {method}",
                "阶段检测",
                850,
                weld_joint_id=joint.id,
                match_freeze_id=getattr(freeze, "id", None),
                inspection_node={
                    "methods": [method],
                    "rate": getattr(requirement, "nde_rate", None),
                    "stage": stage["code"],
                    "timing": when,
                },
                source_snapshot={"treatment_stage": stage},
                explanation="来自已审核热处理阶段的必检项",
            )
            if previous != f"WELD-{joint.id}":
                add_edge(f"WELD-{joint.id}", code, "nde", "检测须关联已完成的焊接工序")
            add_edge(previous, code, "nde", "必须先完成对应阶段再执行检测")
            return code

        for method in stage["nde_before"]:
            terminal = inspection(method, "before", terminal)
        code = f"PWHT-{stage['scope'].upper()}-{stage['group'] if stage['scope'] == 'global' else joint.id}-{stage['code']}"
        profile = {
            key: stage[key]
            for key in ("scope", "temperature_min", "temperature_max", "hold_minutes")
        }
        if code in shared:
            if shared[code]["profile"] != profile:
                raise HTTPException(422, "同一整体热处理批组存在温度或保温时间冲突")
            shared[code]["joint_ids"].append(joint.id)
        else:
            members = [joint.id]
            shared[code] = {"profile": profile, "joint_ids": members}
            add_step(
                code,
                "pwht",
                f"{'整体' if stage['scope'] == 'global' else joint.weld_number + ' 局部'}热处理 · {stage['code']}",
                "热处理",
                900,
                weld_joint_id=joint.id if stage["scope"] == "local" else None,
                is_locked=True,
                process_parameters={
                    "treatment": profile,
                    "affected_joint_ids": members,
                },
                inspection_node={"type": "heat_treatment_record", **profile},
                source_snapshot={"treatment_stage": stage},
                explanation="热处理范围和参数来自已审核的阶段计划",
            )
            if stage["scope"] == "global":
                for weld in all_welds:
                    add_edge(weld, code, "pwht", "整体热处理须等待产品全部焊接完成")
        add_edge(terminal, code, "pwht", "前一阶段及规定热前检测完成后才能热处理")
        terminal = code
        for method in stage["nde_after"]:
            terminal = inspection(method, "after", terminal)
    return terminal
