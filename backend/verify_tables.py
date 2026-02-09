"""验证数据库表结构"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text, inspect
from app.core.database import engine

def verify_tables():
    """验证表结构"""
    print("=" * 80)
    print("验证数据库表结构")
    print("=" * 80)
    
    inspector = inspect(engine)
    
    # 检查WPS表
    print("\n✅ WPS表字段:")
    wps_columns = inspector.get_columns('wps')
    for col in wps_columns:
        print(f"  - {col['name']}: {col['type']}")
    
    # 检查PQR表
    print("\n✅ PQR表字段:")
    pqr_columns = inspector.get_columns('pqr')
    for col in pqr_columns:
        print(f"  - {col['name']}: {col['type']}")
    
    # 检查pPQR表
    print("\n✅ pPQR表字段:")
    ppqr_columns = inspector.get_columns('ppqr')
    for col in ppqr_columns:
        print(f"  - {col['name']}: {col['type']}")
    
    # 检查新业务模块表
    tables = ['welding_materials', 'welders', 'equipment', 'production_tasks', 'quality_inspections']
    print("\n✅ 新业务模块表:")
    for table in tables:
        if table in inspector.get_table_names():
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table}")
    
    print("\n" + "=" * 80)
    print("验证完成！")
    print("=" * 80)

if __name__ == "__main__":
    verify_tables()

