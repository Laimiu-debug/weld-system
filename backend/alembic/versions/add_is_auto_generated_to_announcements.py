"""add is_auto_generated to system_announcements

Revision ID: add_auto_generated_flag
Revises: 
Create Date: 2025-10-29 12:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_auto_generated_flag'
down_revision = "add_approval_system"
branch_labels = None
depends_on = None


def upgrade():
    # 添加 is_auto_generated 字段
    op.add_column('system_announcements', 
        sa.Column('is_auto_generated', sa.Boolean(), nullable=True, server_default='false')
    )
    
    # 更新现有数据：如果 created_by 为 NULL，则设置为自动生成
    op.execute("""
        UPDATE system_announcements 
        SET is_auto_generated = true 
        WHERE created_by IS NULL
    """)
    
    # 设置默认值为 false
    op.alter_column('system_announcements', 'is_auto_generated',
        server_default='false'
    )


def downgrade():
    # 删除 is_auto_generated 字段
    op.drop_column('system_announcements', 'is_auto_generated')

