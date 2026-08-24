from types import SimpleNamespace
from unittest.mock import Mock

from app.models.smart_import import ExtractedField, ExtractionJob, ImportReviewRecord
from app.schemas.smart_import import ManualWorkbenchFieldCreate
from app.services.smart_import_workbench_service import SmartImportWorkbenchService


class _Query:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self.rows

    def first(self):
        return self.rows[0] if self.rows else None


def _field(field_id, key, value, canonical=None, module="basic", status="accepted"):
    return SimpleNamespace(
        id=field_id,
        instance_id=None,
        module_id=module,
        field_key=key,
        canonical_field_key=canonical,
        normalized_value=value,
        confidence=0.9,
        review_status=status,
        raw_value=None,
    )


def test_workbench_reports_required_range_semantic_and_unmapped_states() -> None:
    fields = [
        _field("f1", "heat_a", 80, "thermal.preheat_temperature"),
        _field("f2", "heat_b", 90, "thermal.preheat_temperature"),
        _field("f3", "legacy_note", "extra", module="unmapped", status="pending"),
    ]
    snapshot = {
        "json_schema": {
            "type": "object",
            "properties": {
                "heat_a": {
                    "title": "预热温度",
                    "properties": {"value": {"type": "number", "maximum": 60}},
                },
                "required_code": {
                    "title": "必填编号",
                    "properties": {"value": {"type": "string"}},
                },
            },
            "required": ["required_code"],
        },
        "field_bindings": [
            {
                "field_id": "id-a",
                "field_key": "heat_a",
                "module_id": "basic",
                "instance_id": None,
                "canonical_field_key": "thermal.preheat_temperature",
                "extractable": True,
            },
            {
                "field_id": "id-r",
                "field_key": "required_code",
                "module_id": "basic",
                "instance_id": None,
                "extractable": True,
            },
        ],
    }
    entity = SimpleNamespace(id="entity-1", job_id="job-1", entity_type="welder")
    job = SimpleNamespace(schema_snapshot=snapshot)
    db = Mock()
    db.query.side_effect = lambda model: _Query(
        fields if model is ExtractedField else [job] if model is ExtractionJob else []
    )
    service = SmartImportWorkbenchService(db)
    service.review = Mock()
    service.review.get_entity.return_value = entity

    result = service.validate("entity-1", SimpleNamespace(id=1), SimpleNamespace())

    codes = {item["code"] for item in result["issues"]}
    assert {"required_missing", "range_violation", "semantic_conflict"}.issubset(codes)
    assert result["counts"]["unmapped"] == 1
    assert result["counts"]["unconfirmed"] == 1
    assert result["field_states"]["f3"]["is_unmapped"] is True
    assert result["can_publish"] is False


def test_accepted_unmapped_field_is_warning_and_does_not_block_publish() -> None:
    fields = [_field("f1", "report_number", "HGP-21-622B", module="unmapped")]
    fields[0].raw_value = {"label": "报告编号", "value": "HGP-21-622B"}
    entity = SimpleNamespace(id="entity-1", job_id="job-1", entity_type="pqr")
    job = SimpleNamespace(
        schema_snapshot={
            "field_bindings": [
                {
                    "field_key": "pqr_number",
                    "instance_id": None,
                    "required": True,
                    "label": "PQR编号",
                },
                {
                    "field_key": "title",
                    "instance_id": None,
                    "required": True,
                    "label": "标题",
                },
            ]
        }
    )
    db = Mock()
    db.query.side_effect = lambda model: _Query(
        fields if model is ExtractedField else [job] if model is ExtractionJob else []
    )
    service = SmartImportWorkbenchService(db)
    service.review = Mock()
    service.review.get_entity.return_value = entity
    service.review.smart_import._scope_query.return_value = _Query([])

    result = service.validate("entity-1", SimpleNamespace(id=1), SimpleNamespace())

    assert result["can_publish"] is True
    assert not any(item["code"] == "required_missing" for item in result["issues"])
    assert result["issues"][0]["severity"] == "warning"
    assert result["field_states"]["f1"]["label"] == "报告编号"
    assert "report_number" not in result["issues"][0]["message"]


def test_duplicate_issue_uses_chinese_business_label() -> None:
    fields = [
        _field("f1", "ndt_report_number", "20010724-1", status="pending"),
        _field("f2", "ndt_report_number", "20010724-2", status="pending"),
    ]
    entity = SimpleNamespace(id="entity-1", job_id="job-1", entity_type="pqr")
    job = SimpleNamespace(schema_snapshot={"field_bindings": []})
    db = Mock()
    db.query.side_effect = lambda model: _Query(
        fields if model is ExtractedField else [job] if model is ExtractionJob else []
    )
    service = SmartImportWorkbenchService(db)
    service.review = Mock()
    service.review.get_entity.return_value = entity

    result = service.validate("entity-1", SimpleNamespace(id=1), SimpleNamespace())

    duplicate = next(item for item in result["issues"] if item["code"] == "duplicate_field")
    assert duplicate["message"] == "字段“无损检测报告编号”出现多条待发布值"
    assert "ndt_report_number" not in duplicate["message"]


def test_schema_metadata_supports_old_snapshots_without_rich_bindings() -> None:
    metadata = SmartImportWorkbenchService._schema_metadata(
        {
            "json_schema": {
                "properties": {
                    "voltage": {
                        "title": "电压",
                        "properties": {
                            "value": {"type": "number", "minimum": 10, "maximum": 40}
                        },
                    }
                },
                "required": ["voltage"],
            }
        },
        {"field_key": "voltage", "instance_id": None},
    )

    assert metadata == {
        "label": "电压",
        "field_type": "number",
        "required": True,
        "minimum": 10,
        "maximum": 40,
        "options": [],
    }


def test_manual_field_can_fill_non_extractable_schema_binding() -> None:
    entity = SimpleNamespace(id="entity-1", job_id="job-1", source_mode="ai")
    job = SimpleNamespace(
        schema_version="1.0",
        schema_snapshot={
            "field_bindings": [
                {
                    "field_id": "field-disabled",
                    "module_id": "module-1",
                    "instance_id": "instance-1",
                    "field_key": "internal_note",
                    "canonical_field_key": None,
                    "ai_extract_mode": "disabled",
                    "extractable": False,
                }
            ]
        },
    )
    db = Mock()
    db.query.side_effect = [_Query([job]), _Query([])]
    service = SmartImportWorkbenchService(db)
    service.review = Mock()
    service.review.get_entity.return_value = entity
    service.review._workspace.return_value = {
        "user_id": 7,
        "workspace_type": "personal",
        "company_id": None,
        "factory_id": None,
        "access_level": "private",
    }

    result = service.add_manual_field(
        "entity-1",
        ManualWorkbenchFieldCreate(
            target_field_id="field-disabled",
            target_field_key="internal_note",
            value="仅人工维护",
        ),
        SimpleNamespace(id=7),
        SimpleNamespace(),
    )

    added = [call.args[0] for call in db.add.call_args_list]
    field = next(item for item in added if isinstance(item, ExtractedField))
    history = next(item for item in added if isinstance(item, ImportReviewRecord))
    assert field.normalized_value == "仅人工维护"
    assert field.review_status == "accepted"
    assert history.new_value == "仅人工维护"
    assert result.source_mode == "mixed"
