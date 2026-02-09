"""
修复共享库表结构 - 添加缺失的字段
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

def fix_shared_library_tables():
    """修复共享库表结构"""
    with engine.connect() as conn:
        try:
        
            print("检查 shared_templates 表结构...")

            # 检查 uploader_id 字段是否存在
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'shared_templates'
                AND column_name = 'uploader_id'
            """))

            if result.fetchone():
                print("uploader_id 字段已存在")
            else:
                print("uploader_id 字段不存在，正在添加...")

                # 添加 uploader_id 字段
                conn.execute(text("""
                    ALTER TABLE shared_templates
                    ADD COLUMN uploader_id INTEGER NOT NULL DEFAULT 1
                """))

                # 添加外键约束
                conn.execute(text("""
                    ALTER TABLE shared_templates
                    ADD CONSTRAINT fk_shared_templates_uploader
                    FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE CASCADE
                """))

                print("uploader_id 字段添加成功")

            # 检查 upload_time 字段
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'shared_templates'
                AND column_name = 'upload_time'
            """))

            if result.fetchone():
                print("upload_time 字段已存在")
            else:
                print("upload_time 字段不存在，正在添加...")

                conn.execute(text("""
                    ALTER TABLE shared_templates
                    ADD COLUMN upload_time TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                """))

                print("upload_time 字段添加成功")

            # 提交更改
            conn.commit()
            print("\n共享库表结构修复完成！")

        except Exception as e:
            conn.rollback()
            print(f"\n错误: {e}")
            raise

if __name__ == "__main__":
    fix_shared_library_tables()

