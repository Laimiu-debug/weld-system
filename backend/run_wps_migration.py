"""
执行WPS缺失字段迁移
"""
import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.core.database import engine

def execute_migration():
    """执行迁移"""
    try:
        # 读取SQL文件
        sql_file = 'migrations/add_missing_wps_json_fields.sql'
        print(f"读取SQL文件: {sql_file}")
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # 使用app的数据库引擎
        print("连接数据库...")

        # 执行SQL脚本
        print("执行迁移脚本...")
        with engine.connect() as conn:
            # 执行整个脚本
            result = conn.execute(text(sql_script))
            conn.commit()
            
            # 获取结果
            try:
                for row in result:
                    print(row)
            except:
                pass
        
        print("\n✅ 迁移执行完成！")
        
        # 验证字段是否添加成功
        print("\n验证字段...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'wps' 
                AND column_name IN ('header_info', 'diagram_info')
                ORDER BY column_name
            """))
            
            fields = [row[0] for row in result]
            print(f"找到的字段: {fields}")
            
            if 'header_info' in fields and 'diagram_info' in fields:
                print("✅ 所有字段都已成功添加！")
            else:
                print("❌ 部分字段未添加成功")

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    execute_migration()

