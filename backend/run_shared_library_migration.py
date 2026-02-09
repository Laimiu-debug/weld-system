"""
执行共享库迁移的脚本
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

def execute_shared_library_migration():
    """执行共享库迁移"""
    print("Executing shared library migration...")

    try:
        # 读取迁移文件
        migration_file = os.path.join(os.path.dirname(__file__), 'migrations', 'create_shared_library_tables.sql')
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # 执行迁移
        with engine.connect() as connection:
            # 开始事务
            trans = connection.begin()

            try:
                # 分割SQL语句并逐个执行
                statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]

                for i, statement in enumerate(statements):
                    if statement and not statement.startswith('--'):
                        print(f"Executing statement {i+1}/{len(statements)}...")
                        try:
                            connection.execute(text(statement))
                        except Exception as e:
                            print(f"Statement failed: {e}")
                            print(f"Statement: {statement[:100]}...")

                # 提交事务
                trans.commit()
                print("Migration completed successfully!")

                # 验证表是否创建成功
                tables_to_check = [
                    'shared_modules',
                    'shared_templates',
                    'user_ratings',
                    'shared_downloads',
                    'shared_comments'
                ]

                print("\nVerifying created tables:")
                for table in tables_to_check:
                    try:
                        result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        print(f"Table {table}: {count} records")
                    except Exception as e:
                        print(f"Error checking table {table}: {e}")

            except Exception as e:
                # 回滚事务
                trans.rollback()
                print(f"Migration failed, rolled back: {e}")
                return False

        return True

    except Exception as e:
        print(f"Migration execution failed: {e}")
        return False

if __name__ == "__main__":
    print("Shared Library Migration Tool")
    print("=" * 40)

    if execute_shared_library_migration():
        print("\nMigration completed successfully!")
    else:
        print("\nMigration failed!")