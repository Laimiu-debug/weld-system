"""Manual drawing corrections preserve revision-local part associations."""
from types import SimpleNamespace as NS
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models.engineering import Part, ProductRevision, WeldJoint
from app.schemas.engineering import JointCreate
from app.services.engineering_service import EngineeringService


def fixture_service(parts=(), approved=False, model=WeldJoint):
    db = Mock()
    def query(queried_model):
        result = Mock()
        def filtered(*criteria):
            statement = select(Part).where(*criteria).compile()
            sql = str(statement)
            assert "parts.revision_id =" in sql and "parts.is_deleted IS false" in sql
            parameters = statement.params
            result.first.return_value = next((part for part in parts
                if part.id == parameters["id_1"] and part.revision_id == parameters["revision_id_1"]
                and not part.is_deleted), None)
            return result
        result.filter.side_effect = filtered
        return result
    db.query.side_effect = query
    service = EngineeringService(db)
    revision = ProductRevision(id="r1", status="approved" if approved else "review", data_version=1,
        drawing_page_count=1, drawing_document_id="d1", drawing_filename="drawing.pdf", access_level="private")
    entity = model(id="e1", revision_id="r1", evidence={})
    service._get = Mock(side_effect=lambda kind, *args: revision if kind is ProductRevision else entity)
    service._clone_revision = Mock()
    service._invalidate = Mock()
    service._audit = Mock()
    return service, revision, entity


def part(id="p1", revision="r1", deleted=False, parent=None):
    return Part(id=id, revision_id=revision, is_deleted=deleted, parent_part_id=parent)


@pytest.mark.parametrize("candidate", [None, part(revision="another-revision"), part(deleted=True)])
@pytest.mark.parametrize("approved", [False, True])
def test_invalid_part_link_is_rejected_before_changes_or_cloning(candidate, approved):
    service, revision, entity = fixture_service([candidate] if candidate else [], approved)
    with pytest.raises(HTTPException) as error:
        service.patch_entity(WeldJoint, "e1", {"part_a_id": "p1"}, None, NS(id=7), NS())
    assert error.value.status_code == 422
    assert entity.part_a_id is None
    assert revision.data_version == 1
    service._clone_revision.assert_not_called()
    service.db.commit.assert_not_called()


def test_approved_correction_remaps_selected_part_to_new_revision():
    service, old_revision, old_joint = fixture_service([part()], approved=True)
    new_joint = WeldJoint(id="e2", revision_id="r2", evidence={})
    new_revision = ProductRevision(id="r2", data_version=1, drawing_document_id="d1", drawing_filename="drawing.pdf")
    service._clone_revision.return_value = (new_revision, {
        Part: {"p1": part(id="p2", revision="r2")}, WeldJoint: {"e1": new_joint}})
    payload = {"part_a_id": "p1"}
    result, revision = service.patch_entity(WeldJoint, "e1", payload, None, NS(id=7), NS())
    assert result.part_a_id == "p2" and revision.id == "r2"
    assert old_joint.part_a_id is None
    assert payload == {"part_a_id": "p1"}
    service.db.commit.assert_called_once()


@pytest.mark.parametrize("parents", [[part(id="e1")], [part(parent="e1")], [part(parent="p2"), part(id="p2", parent="p1")]])
def test_assembly_cycles_are_rejected(parents):
    service, _, _ = fixture_service(parents, model=Part)
    parent_id = "e1" if parents[0].id == "e1" else "p1"
    with pytest.raises(HTTPException, match="循环"):
        service.patch_entity(Part, "e1", {"parent_part_id": parent_id}, None, NS(id=7), NS())
    service.db.commit.assert_not_called()


def test_manual_joint_creation_cannot_link_another_revision():
    service, _, _ = fixture_service([part(revision="other")])
    with pytest.raises(HTTPException, match="当前图纸版本"):
        service.add_joint("r1", JointCreate(weld_number="W1", part_a_id="p1"), NS(id=7), NS())
    service.db.add.assert_not_called()


def test_draft_correction_accepts_current_revision_and_explicit_unlink():
    service, _, joint = fixture_service([part()])
    service.patch_entity(WeldJoint, "e1", {"part_a_id": "p1", "part_b_id": None}, None, NS(id=7), NS())
    assert joint.part_a_id == "p1" and joint.part_b_id is None


@pytest.mark.parametrize("invalid", [[], {}, True, 12, ""])
def test_malformed_reference_returns_422_without_database_mutation(invalid):
    service, _, _ = fixture_service()
    with pytest.raises(HTTPException) as error:
        service.patch_entity(WeldJoint, "e1", {"part_a_id": invalid}, None, NS(id=7), NS())
    assert error.value.status_code == 422
    service.db.query.assert_not_called()
    service.db.commit.assert_not_called()
