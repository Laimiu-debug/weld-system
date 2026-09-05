"""Explicit structure selection and executable, length-based weld strategies."""
from copy import deepcopy
from math import ceil, isfinite

from fastapi import HTTPException


def resolve_structure(parts, joints, options=None):
    options = options or {}
    roles = options.get("part_roles") or {}
    if set(roles) - set(parts):
        raise HTTPException(422, "结构角色引用了当前版本以外的零件")
    joint_ids = {joint.id for joint in joints}
    closing = set(options.get("closure_joint_ids") or [])
    if closing - joint_ids:
        raise HTTPException(422, "最终封闭焊缝不属于当前版本")
    connections = []
    for joint in joints:
        ids = [joint.part_a_id, joint.part_b_id]
        if any(value and value not in parts for value in ids):
            raise HTTPException(422, "焊缝连接引用失效，请先核对产品结构")
        connections.append({"joint_id": joint.id, "part_ids": [p for p in ids if p]})
    vessel = any(
        {roles.get(p) for p in connection["part_ids"]} >= {"shell", "head"}
        for connection in connections
    )
    template = options.get("template", "auto")
    if template == "auto":
        template = "pressure_vessel" if vessel else "generic"
    if template == "pressure_vessel" and not vessel:
        raise HTTPException(422, "压力容器模板需要已确认且相互连接的筒体、封头角色")
    if closing and template != "pressure_vessel":
        raise HTTPException(422, "最终封闭焊缝仅适用于已确认的容器结构")
    if template == "pressure_vessel" and not closing:
        raise HTTPException(422, "请选择实际最终封闭焊缝，不能按封头名称推断封闭位置")
    for connection in connections:
        if connection["joint_id"] in closing and "head" not in {
            roles.get(p) for p in connection["part_ids"]
        }:
            raise HTTPException(422, "最终封闭焊缝必须关联已确认的封头")
    return {
        **options,
        "template": template,
        "part_roles": roles,
        "closure_joint_ids": sorted(closing),
        "connections": connections,
        "basis": "confirmed_part_roles_and_connections"
        if vessel
        else "generic_without_vessel_assumptions",
    }


def structure_joint_family(joint, structure):
    roles = structure.get("part_roles", {})
    values = {roles.get(joint.part_a_id), roles.get(joint.part_b_id)}
    if structure["template"] == "generic":
        return "主体焊接", 25, "general"
    if joint.id in structure.get("closure_joint_ids", []):
        return "最终封闭焊接", 50, "head"
    if "nozzle" in values:
        return "接管安装", 40, "nozzle"
    if "head" in values:
        return "封头组装", 30, "head"
    if "shell" in values:
        return "筒体组装", 20, "shell"
    return "主体焊接", 25, "general"


def expand_weld_strategies(steps, dependencies, joints, policy, segment_length=500):
    """Segments cover the source length exactly; ordering is a mandatory edge."""
    by_joint = {joint.id: joint for joint in joints}
    expanded = []
    replacement = {}
    chains = []
    for step in steps:
        if step["step_type"] != "weld":
            expanded.append(step)
            continue
        joint = by_joint[step["weld_joint_id"]]
        split = policy.get("segmented") or policy.get("skip_weld")
        length = getattr(joint, "length_mm", None)
        if split and (
            not isinstance(length, (int, float)) or not isfinite(length) or length <= 0
        ):
            raise HTTPException(422, f"焊缝 {joint.weld_number} 缺少有效长度，不能生成分段/跳焊步骤")
        count = max(1, ceil(length / segment_length)) if split else 1
        if count > 100:
            raise HTTPException(422, "单条焊缝分段超过 100 段，请增大分段长度")
        indexes = list(range(count))
        if policy.get("skip_weld"):
            indexes = indexes[::2] + indexes[1::2]
        elif policy.get("symmetric") and count > 1:
            indexes = []
            pending = list(range(count))
            while pending:
                indexes.append(pending.pop(0))
                if pending:
                    indexes.append(pending.pop())
        codes = []
        for index in indexes:
            item = deepcopy(step)
            if split:
                item["step_code"] = f"{step['step_code']}-S{index + 1:03d}"
                start, end = index * segment_length, min(
                    (index + 1) * segment_length, length
                )
                item["title"] += f" 第 {index + 1}/{count} 段（{start:g}–{end:g} mm）"
                item["process_parameters"]["segment"] = {
                    "index": index + 1,
                    "count": count,
                    "start_mm": start,
                    "end_mm": end,
                    "length_mm": end - start,
                    "source_length_mm": length,
                    "reference": "工程师须在施工图上确认起点和方向",
                }
            codes.append(item["step_code"])
            expanded.append(item)
        replacement[step["step_code"]] = codes
        chains.append(codes)
    mapped = []
    for edge in dependencies:
        # All original prerequisites apply to every segment; NDE waits for every segment.
        for before in replacement.get(
            edge["predecessor_code"], [edge["predecessor_code"]]
        ):
            for after in replacement.get(
                edge["successor_code"], [edge["successor_code"]]
            ):
                mapped.append(
                    {**edge, "predecessor_code": before, "successor_code": after}
                )
    if policy.get("symmetric"):
        # The blueprint already interleaves joints within each phase. Keep that
        # order within the same phase, without imposing cross-phase cycles.
        groups = {}
        for step in expanded:
            if step["step_type"] == "weld":
                groups.setdefault(step["phase"], []).append(step["step_code"])
        chains.extend(groups.values())
    existing = {(e["predecessor_code"], e["successor_code"]) for e in mapped}
    for chain in chains:
        for before, after in zip(chain, chain[1:]):
            if (before, after) not in existing:
                mapped.append(
                    {
                        "predecessor_code": before,
                        "successor_code": after,
                        "dependency_type": "manual",
                        "is_mandatory": True,
                        "explanation": "按已选分段、跳焊或交错策略施工，不得通过拖动跳过",
                    }
                )
                existing.add((before, after))
    return expanded, mapped
