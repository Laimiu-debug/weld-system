"""Stable semantic field registry for document extraction and rules.

Display labels and custom module keys may change.  These semantic keys are the
stable contract shared by extraction, review, publishing and future rule packs.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SemanticField:
    key: str
    label: str
    data_type: str
    document_types: tuple[str, ...]
    unit: str | None = None
    description: str = ""
    aliases: tuple[str, ...] = ()
    rule_input: bool = False
    enum: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["document_types"] = list(self.document_types)
        value["aliases"] = list(self.aliases)
        value["enum"] = list(self.enum)
        return value


_FIELDS = (
    SemanticField(
        "document.number",
        "文件编号",
        "string",
        ("wps", "pqr", "ppqr"),
        description="WPS、PQR 或 pPQR 的正式编号",
        aliases=("编号", "工艺编号", "评定编号"),
    ),
    SemanticField(
        "document.revision",
        "版本",
        "string",
        ("wps", "pqr", "ppqr"),
        aliases=("版次", "修订", "Revision", "Rev."),
    ),
    SemanticField(
        "document.date",
        "文件日期",
        "date",
        ("wps", "pqr", "ppqr"),
        aliases=("编制日期", "试验日期", "批准日期"),
    ),
    SemanticField(
        "standard.code",
        "适用标准",
        "string",
        ("wps", "pqr", "ppqr"),
        aliases=("标准", "规范", "执行标准"),
        rule_input=True,
    ),
    SemanticField(
        "standard.version",
        "标准版本",
        "string",
        ("wps", "pqr", "ppqr"),
        aliases=("标准年份", "规范版本"),
        rule_input=True,
    ),
    SemanticField(
        "base_material.specification",
        "母材牌号",
        "string",
        ("wps", "pqr", "ppqr"),
        aliases=("母材", "材料牌号", "材质"),
        rule_input=True,
    ),
    SemanticField(
        "base_material.group",
        "母材组别",
        "string",
        ("wps", "pqr", "ppqr"),
        aliases=("材料组别", "P-No.", "组号"),
        rule_input=True,
    ),
    SemanticField(
        "base_material.thickness",
        "母材厚度",
        "number",
        ("pqr", "ppqr"),
        unit="mm",
        aliases=("试件厚度", "板厚"),
        rule_input=True,
    ),
    SemanticField(
        "base_material.thickness_range",
        "母材厚度范围",
        "string",
        ("wps",),
        unit="mm",
        aliases=("适用厚度", "厚度范围"),
        rule_input=True,
    ),
    SemanticField(
        "base_material.diameter",
        "管径",
        "number",
        ("pqr", "ppqr"),
        unit="mm",
        aliases=("试件直径", "外径"),
        rule_input=True,
    ),
    SemanticField(
        "joint.type",
        "接头形式",
        "string",
        ("wps", "pqr", "ppqr"),
        aliases=("接头类型", "接头设计"),
        rule_input=True,
    ),
    SemanticField(
        "joint.groove_type",
        "坡口形式",
        "string",
        ("wps", "pqr", "ppqr"),
        aliases=("坡口类型", "坡口型式"),
        rule_input=True,
    ),
    SemanticField(
        "joint.groove_angle",
        "坡口角度",
        "number",
        ("wps", "pqr", "ppqr"),
        unit="degree",
        aliases=("夹角", "角度"),
    ),
    SemanticField(
        "joint.root_gap",
        "根部间隙",
        "number",
        ("wps", "pqr", "ppqr"),
        unit="mm",
        aliases=("根间隙", "间隙"),
    ),
    SemanticField(
        "joint.root_face",
        "钝边",
        "number",
        ("wps", "pqr", "ppqr"),
        unit="mm",
        aliases=("根部钝边",),
    ),
    SemanticField(
        "welding.process",
        "焊接方法",
        "string",
        ("wps", "pqr", "ppqr"),
        aliases=("焊接工艺", "方法", "Process"),
        rule_input=True,
    ),
    SemanticField(
        "welding.position",
        "焊接位置",
        "string",
        ("wps", "pqr", "ppqr"),
        aliases=("焊位", "位置"),
        rule_input=True,
    ),
    SemanticField(
        "filler.specification",
        "焊材牌号",
        "string",
        ("wps", "pqr", "ppqr"),
        aliases=("填充金属", "焊丝", "焊条"),
        rule_input=True,
    ),
    SemanticField(
        "filler.classification",
        "焊材分类",
        "string",
        ("wps", "pqr", "ppqr"),
        aliases=("填充金属分类",),
        rule_input=True,
    ),
    SemanticField(
        "filler.diameter",
        "焊材直径",
        "number",
        ("wps", "pqr", "ppqr"),
        unit="mm",
        aliases=("焊丝直径", "焊条直径"),
    ),
    SemanticField(
        "shielding.gas",
        "保护气体",
        "string",
        ("wps", "pqr", "ppqr"),
        aliases=("气体", "保护气体组成"),
    ),
    SemanticField(
        "electrical.current",
        "焊接电流",
        "number",
        ("pqr", "ppqr"),
        unit="A",
        aliases=("电流",),
    ),
    SemanticField(
        "electrical.voltage",
        "电弧电压",
        "number",
        ("pqr", "ppqr"),
        unit="V",
        aliases=("电压",),
    ),
    SemanticField(
        "thermal.preheat_temperature",
        "预热温度",
        "number",
        ("wps", "pqr", "ppqr"),
        unit="degC",
        aliases=("最低预热温度",),
        rule_input=True,
    ),
    SemanticField(
        "thermal.interpass_temperature",
        "层间温度",
        "number",
        ("wps", "pqr", "ppqr"),
        unit="degC",
        aliases=("最高层间温度",),
        rule_input=True,
    ),
    SemanticField(
        "thermal.pwht_required",
        "是否焊后热处理",
        "boolean",
        ("wps", "pqr", "ppqr"),
        aliases=("PWHT", "焊后热处理"),
        rule_input=True,
    ),
    SemanticField(
        "thermal.pwht_temperature",
        "焊后热处理温度",
        "number",
        ("wps", "pqr", "ppqr"),
        unit="degC",
        aliases=("PWHT温度",),
        rule_input=True,
    ),
    SemanticField(
        "thermal.pwht_duration",
        "焊后热处理时间",
        "number",
        ("wps", "pqr", "ppqr"),
        unit="h",
        aliases=("保温时间", "PWHT时间"),
        rule_input=True,
    ),
    SemanticField(
        "test.tensile.result",
        "拉伸试验结果",
        "string",
        ("pqr", "ppqr"),
        aliases=("拉伸结果",),
        rule_input=True,
    ),
    SemanticField(
        "test.bend.result",
        "弯曲试验结果",
        "string",
        ("pqr", "ppqr"),
        aliases=("弯曲结果",),
        rule_input=True,
    ),
    SemanticField(
        "test.impact.temperature",
        "冲击试验温度",
        "number",
        ("pqr", "ppqr"),
        unit="degC",
        aliases=("冲击温度",),
        rule_input=True,
    ),
    SemanticField(
        "test.impact.energy",
        "冲击功",
        "number",
        ("pqr", "ppqr"),
        unit="J",
        aliases=("冲击吸收功",),
        rule_input=True,
    ),
    SemanticField(
        "test.hardness.values",
        "硬度值",
        "array",
        ("pqr", "ppqr"),
        aliases=("硬度试验",),
        rule_input=True,
    ),
)

SEMANTIC_FIELDS = {field.key: field for field in _FIELDS}


def get_semantic_field(key: str | None) -> SemanticField | None:
    if not key:
        return None
    return SEMANTIC_FIELDS.get(key)


def list_semantic_fields(document_type: str | None = None) -> list[SemanticField]:
    values = list(SEMANTIC_FIELDS.values())
    if document_type:
        values = [field for field in values if document_type in field.document_types]
    return sorted(values, key=lambda item: item.key)
