"""
执行外键级联删除问题修复的数据库迁移

问题1：共享模块/模板删除级联问题
问题2：模板删除导致已创建的WPS/PQR/pPQR文档无法编辑

使用方法:
    python run_foreign_key_fix_migration.py
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.core.config import settings


def run_migration():
    """执行数据库迁移"""
    print("=" * 80)
    print("开始执行外键级联删除问题修复迁移")
    print("=" * 80)
    
    # 创建数据库连接
    engine = create_engine(settings.DATABASE_URL)
    
    # 读取 SQL 文件
    sql_file = Path(__file__).parent / "migrations" / "fix_foreign_key_cascade_issues.sql"
    
    if not sql_file.exists():
        print(f"错误: SQL 文件不存在: {sql_file}")
        return False
    
    print(f"\n读取 SQL 文件: {sql_file}")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 执行迁移
    try:
        with engine.begin() as conn:
            print("\n开始执行迁移...")
            
            # 分割 SQL 语句（按照 BEGIN/COMMIT 块）
            # 由于我们的 SQL 文件已经包含了 BEGIN/COMMIT，我们直接执行整个文件
            conn.execute(text(sql_content))
            
            print("\n✓ 迁移执行成功！")
            
            # 验证结果
            print("\n" + "=" * 80)
            print("验证外键约束...")
            print("=" * 80)
            
            verify_sql = """
            SELECT 
                tc.table_name, 
                tc.constraint_name, 
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            JOIN information_schema.referential_constraints AS rc
                ON rc.constraint_name = tc.constraint_name
                AND rc.constraint_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name IN ('shared_modules', 'shared_templates', 'wps', 'pqr', 'ppqr')
                AND kcu.column_name IN ('original_module_id', 'original_template_id', 'template_id')
            ORDER BY tc.table_name, kcu.column_name;
            """
            
            result = conn.execute(text(verify_sql))
            rows = result.fetchall()
            
            if rows:
                print("\n外键约束验证结果:")
                print("-" * 80)
                print(f"{'表名':<20} {'约束名':<40} {'列名':<20} {'删除规则':<15}")
                print("-" * 80)
                for row in rows:
                    table_name = row[0]
                    constraint_name = row[1]
                    column_name = row[2]
                    delete_rule = row[5]
                    print(f"{table_name:<20} {constraint_name:<40} {column_name:<20} {delete_rule:<15}")
                print("-" * 80)
                
                # 检查是否所有相关外键都是 SET NULL
                expected_constraints = {
                    'shared_modules': {'original_module_id': 'SET NULL'},
                    'shared_templates': {'original_template_id': 'SET NULL'},
                    'wps': {'template_id': 'SET NULL'},
                    'pqr': {'template_id': 'SET NULL'},
                    'ppqr': {'template_id': 'SET NULL'},
                }
                
                all_correct = True
                for row in rows:
                    table_name = row[0]
                    column_name = row[2]
                    delete_rule = row[5]
                    
                    if table_name in expected_constraints and column_name in expected_constraints[table_name]:
                        expected_rule = expected_constraints[table_name][column_name]
                        if delete_rule != expected_rule:
                            print(f"\n⚠ 警告: {table_name}.{column_name} 的删除规则是 {delete_rule}，期望是 {expected_rule}")
                            all_correct = False
                
                if all_correct:
                    print("\n✓ 所有外键约束都已正确设置为 SET NULL")
                else:
                    print("\n⚠ 部分外键约束未正确设置，请检查")
            else:
                print("\n⚠ 警告: 未找到相关的外键约束")
            
            return True
            
    except Exception as e:
        print(f"\n✗ 迁移执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n外键级联删除问题修复迁移工具")
    print("=" * 80)
    print("\n此迁移将修复以下问题:")
    print("1. 共享模块/模板删除级联问题")
    print("   - 用户删除工作区模块时，共享库副本不应被删除")
    print("2. 模板删除导致已创建文档无法编辑的问题")
    print("   - 模板删除后，已创建的 WPS/PQR/pPQR 文档应该仍然可以编辑")
    print("\n" + "=" * 80)
    
    # 确认执行
    response = input("\n是否继续执行迁移? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("迁移已取消")
        return
    
    # 执行迁移
    success = run_migration()
    
    if success:
        print("\n" + "=" * 80)
        print("迁移完成!")
        print("=" * 80)
        print("\n修改说明:")
        print("1. 共享库独立性:")
        print("   - 用户删除工作区模块/模板时，共享库副本不会被删除")
        print("   - original_module_id/original_template_id 会被设为 NULL")
        print("\n2. 文档编辑独立性:")
        print("   - 模板删除时，已创建的文档不会受影响")
        print("   - template_id 会被设为 NULL")
        print("   - 文档数据保存在 modules_data 中，仍可正常编辑")
        print("\n3. 前端需要处理:")
        print("   - 当 template_id 为 NULL 时，直接使用 modules_data 渲染表单")
        print("   - 不要依赖模板来编辑已创建的文档")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("迁移失败，请检查错误信息")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()

