from app.models.engineering import (
    EngineeringDependencyState,
    EngineeringProject,
    EngineeringReviewRecord,
    Part,
    Product,
    ProductRevision,
    WeldJoint,
    WeldRequirement,
)
from app.models.smart_import import ImportBatch, SourceDocument
from app.services.engineering_service import (
    DRAWING_SCHEMA,
    clean_evidence,
    drawing_risks,
)


def test_engineering_models_include_workspace_and_version_isolation() -> None:
    for model in (
        EngineeringProject,
        Product,
        ProductRevision,
        Part,
        WeldJoint,
        WeldRequirement,
        EngineeringReviewRecord,
        EngineeringDependencyState,
    ):
        columns = set(model.__table__.columns.keys())
        assert {
            "user_id",
            "workspace_type",
            "company_id",
            "factory_id",
            "access_level",
            "created_by",
        } <= columns
    assert {
        "drawing_document_id",
        "drawing_sha256",
        "revision_number",
        "data_version",
    } <= set(ProductRevision.__table__.columns.keys())
    assert Part.__table__.columns["parent_part_id"].foreign_keys


def test_smart_import_storage_accepts_drawing_documents() -> None:
    batch_constraint = " ".join(
        str(c.sqltext)
        for c in ImportBatch.__table__.constraints
        if hasattr(c, "sqltext")
    )
    document_constraint = " ".join(
        str(c.sqltext)
        for c in SourceDocument.__table__.constraints
        if hasattr(c, "sqltext")
    )
    assert "drawing" in batch_constraint
    assert "drawing" in document_constraint


def test_evidence_is_normalized_and_invalid_boxes_remain_unlocated() -> None:
    assert clean_evidence({"page": 2, "bbox": [-1, 0.2, 1.4, 0.8], "text": "A"}, 3) == {
        "page": 2,
        "bbox": [0.0, 0.2, 1.0, 0.8],
        "text": "A",
    }
    assert clean_evidence({"page": 9, "bbox": [0.4, 0.4, 0.2, 0.3]}, 3)["bbox"] == []


def test_drawing_risks_flag_duplicates_missing_critical_data_and_evidence() -> None:
    payload = {
        "parts": [{"ref": "P1"}],
        "weld_joints": [
            {
                "weld_number": "W1",
                "part_a_ref": "P1",
                "part_b_ref": None,
                "joint_type": None,
                "groove_type": None,
                "evidence": {},
            },
            {
                "weld_number": "W1",
                "part_a_ref": "P1",
                "part_b_ref": "P2",
                "joint_type": "butt",
                "groove_type": "V",
                "evidence": {"page": 1, "bbox": [0.1, 0.1, 0.2, 0.2]},
            },
        ],
        "unresolved_regions": [],
    }
    codes = {risk["code"] for risk in drawing_risks(payload, 1)}
    assert {
        "duplicate_weld_number",
        "insufficient_weld_data",
        "unresolved_part",
        "missing_evidence",
    } <= codes


def test_pressure_vessel_schema_requires_traceable_structured_sections() -> None:
    assert set(DRAWING_SCHEMA["required"]) == {
        "product",
        "parts",
        "weld_joints",
        "unresolved_regions",
    }
    weld = DRAWING_SCHEMA["properties"]["weld_joints"]["items"]
    assert {"nde_methods", "pwht_required", "impact_required", "evidence"} <= set(
        weld["required"]
    )
