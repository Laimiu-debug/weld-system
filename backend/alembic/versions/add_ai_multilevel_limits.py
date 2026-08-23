"""Add daily, workspace, user, task, and concurrency AI limits.

Revision ID: add_ai_multilevel_limits
Revises: add_document_artifacts
Create Date: 2026-08-23
"""
from alembic import op


revision = "add_ai_multilevel_limits"
down_revision = "add_document_artifacts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE ai_plan_entitlements
          ADD COLUMN daily_points INTEGER NOT NULL DEFAULT 0,
          ADD COLUMN max_tasks_per_day INTEGER NOT NULL DEFAULT 0,
          ADD COLUMN max_tasks_per_month INTEGER NOT NULL DEFAULT 0,
          ADD COLUMN max_concurrent_tasks INTEGER NOT NULL DEFAULT 0,
          ADD COLUMN max_user_tasks_per_day INTEGER NOT NULL DEFAULT 0,
          ADD COLUMN max_user_tasks_per_month INTEGER NOT NULL DEFAULT 0,
          ADD COLUMN max_user_concurrent_tasks INTEGER NOT NULL DEFAULT 0;

        UPDATE ai_plan_entitlements SET
          daily_points = CASE
            WHEN tier_key IN ('free', 'personal_free') THEN 5
            WHEN workspace_type = 'personal' THEN LEAST(monthly_points, 50)
            ELSE LEAST(monthly_points, 500)
          END,
          max_tasks_per_day = CASE WHEN workspace_type = 'enterprise' THEN 300 ELSE 30 END,
          max_tasks_per_month = CASE WHEN workspace_type = 'enterprise' THEN 3000 ELSE 300 END,
          max_concurrent_tasks = CASE WHEN workspace_type = 'enterprise' THEN 10 ELSE 2 END,
          max_user_tasks_per_day = CASE WHEN workspace_type = 'enterprise' THEN 50 ELSE 30 END,
          max_user_tasks_per_month = CASE WHEN workspace_type = 'enterprise' THEN 500 ELSE 300 END,
          max_user_concurrent_tasks = 2;

        ALTER TABLE ai_plan_entitlements DROP CONSTRAINT IF EXISTS ck_ai_entitlement_nonnegative;
        ALTER TABLE ai_plan_entitlements ADD CONSTRAINT ck_ai_entitlement_nonnegative CHECK (
          daily_points >= 0 AND monthly_points >= 0 AND max_points_per_task >= 0
          AND max_pages_per_task >= 0 AND max_tasks_per_day >= 0
          AND max_tasks_per_month >= 0 AND max_concurrent_tasks >= 0
          AND max_user_tasks_per_day >= 0 AND max_user_tasks_per_month >= 0
          AND max_user_concurrent_tasks >= 0
        );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE ai_plan_entitlements DROP CONSTRAINT IF EXISTS ck_ai_entitlement_nonnegative;
        ALTER TABLE ai_plan_entitlements
          DROP COLUMN IF EXISTS daily_points,
          DROP COLUMN IF EXISTS max_tasks_per_day,
          DROP COLUMN IF EXISTS max_tasks_per_month,
          DROP COLUMN IF EXISTS max_concurrent_tasks,
          DROP COLUMN IF EXISTS max_user_tasks_per_day,
          DROP COLUMN IF EXISTS max_user_tasks_per_month,
          DROP COLUMN IF EXISTS max_user_concurrent_tasks;
        ALTER TABLE ai_plan_entitlements ADD CONSTRAINT ck_ai_entitlement_nonnegative CHECK (
          monthly_points >= 0 AND max_points_per_task >= 0 AND max_pages_per_task >= 0
        );
        """
    )
