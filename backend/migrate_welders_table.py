"""
更新焊工表结构以匹配新的焊工模型
Update welders table structure to match new welder model
"""

import asyncio
from sqlalchemy import text, inspect
from app.core.database import engine
from app.models.welder import Welder


async def migrate_welders_table():
    """迁移焊工表结构"""
    try:
        inspector = inspect(engine)

        # 检查表是否存在
        if 'welders' in inspector.get_table_names():
            print("Welders table exists, updating structure...")

            # 备份现有数据
            with engine.connect() as conn:
                conn.execute(text("BEGIN"))

                # 备份现有数据到临时表
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS welders_backup AS
                    SELECT * FROM welders
                """))
                print("Backup existing data to welders_backup")

                # 删除旧表
                conn.execute(text("DROP TABLE welders CASCADE"))
                print("Drop old welders table")

                # 创建新的焊工表
                Welder.__table__.create(engine, checkfirst=True)
                print("Create new welders table")

                # 迁移数据（如果需要的话）
                # 这里可以根据需要添加数据迁移逻辑

                conn.execute(text("COMMIT"))
                print("Database migration completed")

        else:
            print("Welders table does not exist, creating new table...")
            Welder.__table__.create(engine, checkfirst=True)
            print("Create welders table successfully")

        # 验证表结构
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'welders'
                ORDER BY ordinal_position
            """))

            print("\nNew table structure:")
            for row in result:
                print(f"  - {row[0]} ({row[1]})")

        print("\nWelders table migration completed successfully!")

    except Exception as e:
        print(f"Migration failed: {e}")
        # 如果失败，尝试恢复备份
        try:
            with engine.connect() as conn:
                conn.execute(text("BEGIN"))
                conn.execute(text("DROP TABLE IF EXISTS welders"))
                conn.execute(text("CREATE TABLE welders AS SELECT * FROM welders_backup"))
                conn.execute(text("COMMIT"))
                print("Backup data restored")
        except Exception as restore_error:
            print(f"Backup restore failed: {restore_error}")

        raise


if __name__ == "__main__":
    asyncio.run(migrate_welders_table())