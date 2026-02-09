#!/usr/bin/env python
"""Verify that modules_data field has been properly added to WPS table."""

from sqlalchemy import text, inspect
from app.core.database import engine

def verify_modules_data_field():
    """Verify the modules_data field exists and has correct properties."""
    inspector = inspect(engine)
    columns = inspector.get_columns('wps')
    
    # Find modules_data column
    modules_data_col = None
    for col in columns:
        if col['name'] == 'modules_data':
            modules_data_col = col
            break
    
    if modules_data_col:
        print('✅ modules_data 字段存在')
        print(f'   类型: {modules_data_col.get("type")}')
        print(f'   可为空: {modules_data_col.get("nullable")}')
        print(f'   默认值: {modules_data_col.get("default")}')
    else:
        print('❌ modules_data 字段不存在')
        return False
    
    # Check if index exists
    with engine.connect() as conn:
        result = conn.execute(text('''
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'wps' AND indexname = 'idx_wps_modules_data'
        '''))
        if result.fetchone():
            print('✅ GIN 索引已创建')
        else:
            print('❌ GIN 索引不存在')
            return False
    
    return True

if __name__ == '__main__':
    print("验证 modules_data 字段...")
    print("=" * 60)
    success = verify_modules_data_field()
    print("=" * 60)
    if success:
        print("✅ 所有验证通过！")
    else:
        print("❌ 验证失败！")

