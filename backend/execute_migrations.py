#!/usr/bin/env python
"""
执行 WPS 模板系统重构的数据库迁移脚本
"""
import os
import sys
from pathlib import Path
from sqlalchemy import text, create_engine
from app.core.config import settings

def execute_migration_file(engine, file_path: str, description: str):
    """执行迁移脚本文件"""
    print(f"\n{'='*60}")
    print(f"📝 {description}")
    print(f"{'='*60}")
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print(f"📄 读取文件: {file_path}")
        print(f"📊 SQL 语句行数: {len(sql_content.splitlines())}")
        
        # 分割 SQL 语句（按 ; 分割）
        statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        
        with engine.begin() as conn:
            for i, statement in enumerate(statements, 1):
                if statement.strip():
                    print(f"  执行语句 {i}/{len(statements)}...", end=" ")
                    try:
                        conn.execute(text(statement))
                        print("✅")
                    except Exception as e:
                        print(f"⚠️ {str(e)[:50]}")
        
        print(f"✅ {description} 完成！")
        return True
        
    except Exception as e:
        print(f"❌ 执行失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 WPS 模板系统重构 - 数据库迁移执行")
    print("="*60)
    
    # 创建数据库引擎
    try:
        database_url = str(settings.DATABASE_URL)
        print(f"\n📌 数据库连接: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
        engine = create_engine(database_url, echo=False)
        
        # 测试连接
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False
    
    # 获取迁移脚本路径
    migrations_dir = Path(__file__).parent / "migrations"
    
    # 执行迁移脚本
    migrations = [
        (
            str(migrations_dir / "insert_preset_templates.sql"),
            "第1步：插入预设模板"
        ),
        (
            str(migrations_dir / "cleanup_old_system_templates.sql"),
            "第2步：清理旧系统模板数据"
        ),
        (
            str(migrations_dir / "remove_old_template_fields.sql"),
            "第3步：移除旧字段"
        ),
    ]
    
    results = []
    for file_path, description in migrations:
        success = execute_migration_file(engine, file_path, description)
        results.append((description, success))
    
    # 打印总结
    print(f"\n{'='*60}")
    print("📊 迁移执行总结")
    print(f"{'='*60}")
    
    all_success = True
    for description, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {description}")
        if not success:
            all_success = False
    
    # 验证结果
    print(f"\n{'='*60}")
    print("🔍 验证迁移结果")
    print(f"{'='*60}")
    
    try:
        with engine.connect() as conn:
            # 检查预设模板
            result = conn.execute(text(
                "SELECT COUNT(*) as count FROM wps_templates WHERE id LIKE 'preset_%'"
            ))
            preset_count = result.scalar()
            print(f"✅ 预设模板数量: {preset_count} 个")
            
            # 检查系统模板
            result = conn.execute(text(
                "SELECT COUNT(*) as count FROM wps_templates WHERE is_system = true"
            ))
            system_count = result.scalar()
            print(f"✅ 系统模板数量: {system_count} 个")
            
            # 检查字段
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'wps_templates' AND column_name IN ('field_schema', 'ui_layout', 'validation_rules', 'default_values')"
            ))
            old_fields = result.fetchall()
            if old_fields:
                print(f"⚠️ 旧字段仍存在: {[row[0] for row in old_fields]}")
            else:
                print(f"✅ 旧字段已移除")
    
    except Exception as e:
        print(f"⚠️ 验证失败: {str(e)}")
    
    # 最终结果
    print(f"\n{'='*60}")
    if all_success:
        print("🎉 所有迁移脚本执行成功！")
        print("\n📝 后续步骤:")
        print("1. 重启后端服务")
        print("2. 访问 http://localhost:3002/wps/create 测试新功能")
        print("3. 选择预设模板验证功能")
        print(f"{'='*60}\n")
        return True
    else:
        print("❌ 部分迁移脚本执行失败，请检查错误信息")
        print(f"{'='*60}\n")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

