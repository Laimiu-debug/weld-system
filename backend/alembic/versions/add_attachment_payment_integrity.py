"""Private attachment ownership and atomic payment delivery records."""
from alembic import op
from app.models.attachment import Attachment
from app.models.payment_delivery import PaymentActivation, PaymentNotification

revision = "add_attachment_payment_integrity"
down_revision = "fix_welder_record_edit_audit"
branch_labels = None
depends_on = None


def upgrade():
    for model in (Attachment, PaymentActivation, PaymentNotification):
        model.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    for model in (PaymentNotification, PaymentActivation, Attachment):
        model.__table__.drop(op.get_bind(), checkfirst=True)
