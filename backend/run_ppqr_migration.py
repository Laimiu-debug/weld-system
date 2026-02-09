"""
运行pPQR迁移脚本
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine

def run_migration():
    """运行pPQR迁移"""
    migration_file = "migrations/add_ppqr_missing_fields.sql"
    
    try:
        # 读取迁移文件
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # 执行迁移
        with engine.connect() as conn:
            # 分割SQL语句（按分号分割）
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            
            for statement in statements:
                if statement:
                    print(f"执行: {statement[:100]}...")
                    conn.execute(text(statement))
            
            conn.commit()
        
        print(f"\n✅ 迁移成功: {migration_file}")
        return True
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

