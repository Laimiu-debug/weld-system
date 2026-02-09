"""
执行custom_modules表的module_type迁移脚本
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import engine
from sqlalchemy import text


def run_migration():
    """执行迁移脚本"""
    migration_file = Path(__file__).parent / "migrations" / "add_module_type_to_custom_modules.sql"
    
    if not migration_file.exists():
        print(f"❌ 迁移文件不存在: {migration_file}")
        return False
    
    print("=" * 80)
    print("开始执行custom_modules表的module_type迁移")
    print("=" * 80)
    print()
    
    # 读取SQL文件
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    try:
        # 执行迁移
        with engine.connect() as connection:
            # 使用text()包装SQL语句
            connection.execute(text(sql_content))
            connection.commit()
        
        print()
        print("=" * 80)
        print("✓ 迁移成功完成！")
        print("=" * 80)
        print()
        print("现在custom_modules表支持以下module_type：")
        print("  - wps: WPS模块")
        print("  - pqr: PQR模块")
        print("  - ppqr: pPQR模块")
        print("  - common: 通用模块（可用于所有类型）")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ 迁移失败！")
        print("=" * 80)
        print(f"错误信息: {str(e)}")
        print()
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

