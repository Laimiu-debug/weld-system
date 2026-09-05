"""Regression tests for workflow validation, snapshots and strict report semantics."""
import json
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.data_access import WorkspaceContext
from app.models.production import ProductionPlan
from app.models.quality import QualityStandard
from app.schemas.business_workflows import PerformanceInput, StandardInput, PlanTasksInput
from app.services.business_workflow_service import PlanService, StandardService, standard_snapshot
from app.services.report_template_runner import report_config, run_report
from app.services.quality_service import QualityService


@pytest.mark.parametrize('period', ['2026-00', '2026-13', '2026-Q5', 'Q1', '2026', '0000-01'])
def test_performance_rejects_invalid_period(period):
    with pytest.raises(ValidationError):
        PerformanceInput(employee_user_id=1, review_period=period)


@pytest.mark.parametrize('score', [-1, 101, float('inf'), float('nan')])
def test_performance_rejects_invalid_score(score):
    with pytest.raises(ValidationError):
        PerformanceInput(employee_user_id=1, review_period='2026-Q1', overall_score=score)


@pytest.mark.parametrize('payload', [{'task_ids': [1, 1]}, {'task_ids': [-1]}, {'task_ids': [0]}])
def test_duplicate_or_invalid_plan_tasks(payload):
    with pytest.raises(ValidationError):
        PlanTasksInput(**payload)


def test_standard_rejects_reversed_dates():
    with pytest.raises(ValidationError):
        StandardInput(standard_code='S', standard_name='Test', version='1', effective_date='2026-09-05', expiry_date='2026-09-04')


@pytest.mark.parametrize('criteria', ['{}', '[null]', '[""]', 'not-json'])
def test_standard_rejects_invalid_criteria(criteria):
    with pytest.raises(ValidationError):
        StandardInput(standard_code='S', standard_name='Test', version='1', acceptance_criteria=criteria)


def plan(status='draft'):
    return ProductionPlan(id=1, plan_number='P', plan_name='Plan', priority='normal', status=status,
                          plan_start_date=date(2026, 9, 1), plan_end_date=date(2026, 9, 5), progress_percentage=0)


@pytest.mark.parametrize('payload', [{'progress_percentage': 25}, {'tasks': '[1]'}, {'updated_by': 9}, {'status': 'in_progress'}])
def test_plan_rejects_manual_progress_audit_and_skipped_transition(payload):
    service = PlanService(MagicMock(), ProductionPlan)
    service.progress = lambda _: {'progress_percentage': 0, 'task_count': 1, 'completed_tasks': 0}
    with pytest.raises(HTTPException):
        service.prepare(payload, None, None, plan())


def test_plan_cannot_complete_without_any_tasks():
    service = PlanService(MagicMock(), ProductionPlan)
    service.progress = lambda _: {'progress_percentage': 100, 'task_count': 0, 'completed_tasks': 0}
    with pytest.raises(HTTPException):
        service.prepare({'status': 'completed'}, None, None, plan('in_progress'))


def test_plan_completion_uses_actual_tasks():
    service = PlanService(MagicMock(), ProductionPlan)
    service.progress = lambda _: {'progress_percentage': 100, 'task_count': 2, 'completed_tasks': 2}
    data = service.prepare({'status': 'completed'}, None, None, plan('in_progress'))
    assert data['status'] == 'completed' and data['progress_percentage'] == 100


def standard():
    return QualityStandard(id=1, standard_code='S', standard_name='Standard', version='1', status='active',
                           is_active=True, effective_date=date(2026, 9, 1), expiry_date=date(2026, 9, 30),
                           test_methods='["visual"]', acceptance_criteria='["no cracks"]')


def test_change_criteria_requires_new_version():
    service = StandardService(MagicMock(), QualityStandard)
    with pytest.raises(HTTPException):
        service.prepare({'acceptance_criteria': '["changed"]'}, None, None, standard())
    assert service.prepare({'version': '2', 'acceptance_criteria': '["changed"]'}, None, None, standard())['version'] == '2'


@pytest.mark.parametrize('when', ['2026-08-31', '2026-10-01', None])
def test_snapshot_requires_standard_valid_on_inspection_date(when):
    db, access = MagicMock(), MagicMock()
    db.query.return_value.filter.return_value.first.return_value = standard()
    with pytest.raises(HTTPException):
        standard_snapshot(db, access, 1, when, None, None)


def test_snapshot_remains_independent_of_master_changes():
    db, access = MagicMock(), MagicMock()
    item = standard()
    db.query.return_value.filter.return_value.first.return_value = item
    snapshot = standard_snapshot(db, access, 1, date(2026, 9, 5), None, None)
    item.version = '2'; item.acceptance_criteria = '["changed"]'
    assert snapshot['version'] == '1' and snapshot['acceptance_criteria'] == '["no cracks"]'


@pytest.mark.parametrize('payload', [{'standard_snapshot': {}}, {'standard_id': None}, {'standard_id': 2}, {'inspection_date': '2026-10-01'}])
def test_existing_inspection_snapshot_cannot_be_replaced(payload):
    service = QualityService(MagicMock())
    inspection = SimpleNamespace(standard_id=1, inspection_date=date(2026, 9, 5), standard_snapshot={'expiry_date': '2026-09-30'})
    with pytest.raises(HTTPException):
        service._bind_standard(payload, None, None, inspection)


@pytest.mark.parametrize('change', [
    {'data_sources': '["unknown"]'}, {'data_sources': '[]'}, {'data_sources': '["wps","wps"]'},
    {'metrics': '["sum"]'}, {'filters': '{}'}, {'filters': '[{"field":"unknown","value":"x"}]'},
    {'filters': '[{"field":"status","operator":"wrong","value":"x"}]'},
    {'filters': '[{"field":"created_at","value":"bad-date"}]'},
    {'filters': '[{"source":"quality","field":"status","value":"x"}]'},
    {'group_by': 'unknown'}, {'time_range': '{}'},
])
def test_report_invalid_configuration_is_explicit_error(change):
    template = {'data_sources': '["wps"]', **change}
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        run_report(db, template, SimpleNamespace(id=1), WorkspaceContext(user_id=1, workspace_type='personal'))
    assert exc.value.status_code == 422
    db.query.assert_not_called()


def test_filters_must_apply_to_every_target_source():
    with pytest.raises(HTTPException):
        report_config({'data_sources': '["wps","quality"]', 'filters': '[{"field":"status","value":"draft"}]'})
    sources, filters, _ = report_config({'data_sources': '["wps","quality"]',
        'filters': '[{"source":"wps","field":"status","value":"draft"}]'})
    assert len(filters['wps']) == 1 and filters['quality'] == []


@pytest.mark.parametrize('status', ['completed', 'cancelled'])
def test_ended_plan_prevents_task_execution_changes(status):
    from app.services.production_service import ProductionService
    service = ProductionService(MagicMock())
    service.db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(status=status)
    with pytest.raises(HTTPException) as exc:
        service._guard_plan_execution(SimpleNamespace(plan_id=1))
    assert exc.value.status_code == 409


def test_unlinked_tasks_do_not_query_a_plan():
    from app.services.production_service import ProductionService
    service = ProductionService(MagicMock())
    service._guard_plan_execution(SimpleNamespace(plan_id=None))
    service.db.query.assert_not_called()


def test_invitation_legacy_without_token_has_no_broken_link():
    from app.services.invitation_service import InvitationService
    item = SimpleNamespace(id=1, factory_id=None, email='test@example.com', invitation_code='OLD',
        role='employee', department=None, status='pending', permissions={}, message=None,
        expires_at=None, accepted_at=None, created_at=None)
    assert InvitationService(MagicMock()).serialize(item)['invite_url'] is None
