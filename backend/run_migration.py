"""
执行 WPS 数据库迁移脚本
"""
import sys
from pathlib import Path
from sqlalchemy import text
from app.core.database import engine

def run_migration(sql_file: str):
    """执行 SQL 迁移文件"""
    sql_path = Path(__file__).parent / sql_file

    if not sql_path.exists():
        print(f"❌ SQL文件不存在: {sql_path}")
        return False

    print(f"📄 读取SQL文件: {sql_path}")
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print(f"🚀 开始执行迁移...")
    try:
        with engine.begin() as conn:
            # 执行 SQL（使用 text() 包装）
            conn.execute(text(sql_content))
        print(f"✅ 迁移成功完成！")
        return True
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        sql_file = sys.argv[1]
    else:
        # 默认执行 WPS 字段扩展迁移
        sql_file = "migrations/add_wps_json_fields.sql"
    
    success = run_migration(sql_file)
    sys.exit(0 if success else 1)

