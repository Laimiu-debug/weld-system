"""
临时脚本：添加 is_auto_generated 字段到 system_announcements 表
"""
from app.core.database import engine
from sqlalchemy import text

def add_field():
    with engine.connect() as conn:
        try:
            # 添加字段
            conn.execute(text("""
                ALTER TABLE system_announcements 
                ADD COLUMN IF NOT EXISTS is_auto_generated BOOLEAN DEFAULT FALSE
            """))
            conn.commit()
            print("✅ 字段 is_auto_generated 添加成功！")
        except Exception as e:
            print(f"❌ 添加字段失败: {e}")

if __name__ == "__main__":
    add_field()

