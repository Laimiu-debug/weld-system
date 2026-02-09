"""
验证外键级联删除问题修复

此脚本仅验证数据库外键约束是否正确设置，不需要创建测试数据

使用方法:
    python verify_foreign_key_fix.py
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.core.config import settings


def verify_foreign_keys():
    """验证外键约束是否正确设置"""
    print("\n" + "=" * 80)
    print("验证外键级联删除问题修复")
    print("=" * 80)
    
    # 创建数据库连接
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.begin() as conn:
            # 查询所有相关的外键约束
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
            
            if not rows:
                print("\n⚠ 警告: 未找到相关的外键约束")
                return False
            
            print("\n外键约束验证结果:")
            print("-" * 80)
            print(f"{'表名':<20} {'约束名':<45} {'列名':<20} {'删除规则':<15}")
            print("-" * 80)
            
            # 期望的外键约束配置
            expected_constraints = {
                'shared_modules': {'original_module_id': 'SET NULL'},
                'shared_templates': {'original_template_id': 'SET NULL'},
                'wps': {'template_id': 'SET NULL'},
                'pqr': {'template_id': 'SET NULL'},
                'ppqr': {'template_id': 'SET NULL'},
            }
            
            found_constraints = {}
            all_correct = True
            
            for row in rows:
                table_name = row[0]
                constraint_name = row[1]
                column_name = row[2]
                delete_rule = row[5]
                
                print(f"{table_name:<20} {constraint_name:<45} {column_name:<20} {delete_rule:<15}")
                
                # 记录找到的约束
                if table_name not in found_constraints:
                    found_constraints[table_name] = {}
                found_constraints[table_name][column_name] = delete_rule
                
                # 检查是否符合期望
                if table_name in expected_constraints and column_name in expected_constraints[table_name]:
                    expected_rule = expected_constraints[table_name][column_name]
                    if delete_rule != expected_rule:
                        all_correct = False
            
            print("-" * 80)
            
            # 详细验证结果
            print("\n详细验证结果:")
            print("-" * 80)
            
            all_found = True
            for table_name, columns in expected_constraints.items():
                for column_name, expected_rule in columns.items():
                    if table_name in found_constraints and column_name in found_constraints[table_name]:
                        actual_rule = found_constraints[table_name][column_name]
                        if actual_rule == expected_rule:
                            print(f"✓ {table_name}.{column_name}: {actual_rule} (正确)")
                        else:
                            print(f"✗ {table_name}.{column_name}: {actual_rule} (期望: {expected_rule})")
                            all_correct = False
                    else:
                        print(f"✗ {table_name}.{column_name}: 未找到外键约束")
                        all_found = False
                        all_correct = False
            
            print("-" * 80)
            
            # 总结
            print("\n" + "=" * 80)
            print("验证总结")
            print("=" * 80)
            
            if all_found and all_correct:
                print("✓ 所有外键约束都已正确设置为 SET NULL")
                print("\n修复成功！")
                print("\n修复效果:")
                print("1. 用户删除工作区模块/模板时，共享库副本不会被删除")
                print("2. 模板删除时，已创建的 WPS/PQR/pPQR 文档不会受影响")
                print("3. 文档数据保存在 modules_data 中，仍可正常编辑")
                return True
            else:
                if not all_found:
                    print("✗ 部分外键约束未找到")
                if not all_correct:
                    print("✗ 部分外键约束的删除规则不正确")
                print("\n请检查迁移是否正确执行")
                return False
                
    except Exception as e:
        print(f"\n✗ 验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    success = verify_foreign_keys()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()

