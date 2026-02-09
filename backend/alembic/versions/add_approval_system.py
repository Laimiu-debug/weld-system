"""Add approval system tables

Revision ID: add_approval_system
Revises: 
Create Date: 2025-10-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_approval_system'
down_revision = None  # 需要根据实际情况设置
branch_labels = None
depends_on = None


def upgrade():
    # 创建审批工作流定义表
    op.create_table(
        'approval_workflow_definitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('factory_id', sa.Integer(), nullable=True),
        sa.Column('steps', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_approval_workflow_definitions_document_type', 'approval_workflow_definitions', ['document_type'])
    op.create_index('ix_approval_workflow_definitions_company_id', 'approval_workflow_definitions', ['company_id'])
    op.create_index('ix_approval_workflow_definitions_code', 'approval_workflow_definitions', ['code'])
    
    # 创建审批实例表
    op.create_table(
        'approval_instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('document_number', sa.String(length=100), nullable=True),
        sa.Column('document_title', sa.String(length=200), nullable=True),
        sa.Column('workspace_type', sa.String(length=20), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('factory_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('current_step', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('current_step_name', sa.String(length=100), nullable=True),
        sa.Column('submitter_id', sa.Integer(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('final_approver_id', sa.Integer(), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='normal'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workflow_id'], ['approval_workflow_definitions.id'], ondelete='CASCADE')
    )
    
    op.create_index('ix_approval_instances_document_type', 'approval_instances', ['document_type'])
    op.create_index('ix_approval_instances_document_id', 'approval_instances', ['document_id'])
    op.create_index('ix_approval_instances_status', 'approval_instances', ['status'])
    op.create_index('ix_approval_instances_submitter_id', 'approval_instances', ['submitter_id'])
    op.create_index('ix_approval_instances_company_id', 'approval_instances', ['company_id'])
    
    # 创建审批历史表
    op.create_table(
        'approval_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instance_id', sa.Integer(), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('step_name', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.Column('operator_name', sa.String(length=100), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('attachments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('result', sa.String(length=20), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['instance_id'], ['approval_instances.id'], ondelete='CASCADE')
    )
    
    op.create_index('ix_approval_history_instance_id', 'approval_history', ['instance_id'])
    op.create_index('ix_approval_history_operator_id', 'approval_history', ['operator_id'])
    
    # 创建审批通知表
    op.create_table(
        'approval_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instance_id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('is_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['instance_id'], ['approval_instances.id'], ondelete='CASCADE')
    )
    
    op.create_index('ix_approval_notifications_recipient_id', 'approval_notifications', ['recipient_id'])
    op.create_index('ix_approval_notifications_is_read', 'approval_notifications', ['is_read'])


def downgrade():
    # 删除表（按照依赖关系的逆序）
    op.drop_table('approval_notifications')
    op.drop_table('approval_history')
    op.drop_table('approval_instances')
    op.drop_table('approval_workflow_definitions')

