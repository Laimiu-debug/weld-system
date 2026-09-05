"""Preserve unknown drawing quantities as NULL."""
from alembic import op
import sqlalchemy as sa

revision = "allow_unknown_part_quantity"
down_revision = "add_attachment_payment_integrity"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "parts",
        "quantity",
        existing_type=sa.Integer(),
        nullable=True,
        server_default=None,
    )


def downgrade():
    if (
        op.get_bind()
        .execute(sa.text("SELECT 1 FROM parts WHERE quantity IS NULL LIMIT 1"))
        .first()
    ):
        raise RuntimeError("请先人工补齐未知零件数量，不能自动改为 1")
    op.alter_column("parts", "quantity", existing_type=sa.Integer(), nullable=False)
