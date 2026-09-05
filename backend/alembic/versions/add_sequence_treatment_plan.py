"""Reviewed multi-stage PWHT and NDE plans."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "add_sequence_treatment_plan"
down_revision = "allow_unknown_part_quantity"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "weld_requirements", sa.Column("treatment_plan", JSONB(), nullable=True)
    )


def downgrade():
    if (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT 1 FROM weld_requirements WHERE treatment_plan IS NOT NULL AND treatment_plan <> '[]'::jsonb LIMIT 1"
            )
        )
        .first()
    ):
        raise RuntimeError("存在已保存热处理计划，不能直接降级删除")
    op.drop_column("weld_requirements", "treatment_plan")
