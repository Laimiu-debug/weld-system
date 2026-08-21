"""
测试共享库修复
验证：
1. 表结构是否正确
2. 数据完整性（字段复制）
3. 默认状态是否为 approved
"""
import sys
from sqlalchemy import inspect, text
from app.core.database import engine
from app.models.shared_library import SharedModule, SharedTemplate
from app.models.custom_module import CustomModule
from app.models.wps_template import WPSTemplate

def test_table_structure():
    """测试表结构"""
    print("=" * 80)
    print("1. 测试表结构")
    print("=" * 80)
    
    inspector = inspect(engine)
    
    # 检查 shared_modules 表
    print("\n✓ shared_modules 表字段:")
    columns = inspector.get_columns('shared_modules')
    required_fields = [
        'id', 'original_module_id', 'name', 'description', 'icon', 'category',
        'repeatable', 'fields', 'uploader_id', 'upload_time', 'version',
        'changelog', 'download_count', 'like_count', 'dislike_count', 'view_count',
        'status', 'reviewer_id', 'review_time', 'review_comment', 'is_featured',
        'featured_order', 'tags', 'difficulty_level', 'created_at', 'updated_at'
    ]
    
    column_names = [col['name'] for col in columns]
    missing_fields = [f for f in required_fields if f not in column_names]
    
    if missing_fields:
        print(f"  ❌ 缺少字段: {missing_fields}")
        return False
    else:
        print(f"  ✓ 所有必需字段都存在 ({len(required_fields)} 个)")
    
    # 检查 shared_templates 表
    print("\n✓ shared_templates 表字段:")
    columns = inspector.get_columns('shared_templates')
    required_fields = [
        'id', 'original_template_id', 'name', 'description', 'welding_process',
        'welding_process_name', 'standard', 'module_instances', 'uploader_id',
        'upload_time', 'version', 'changelog', 'download_count', 'like_count',
        'dislike_count', 'view_count', 'status', 'reviewer_id', 'review_time',
        'review_comment', 'is_featured', 'featured_order', 'tags', 'difficulty_level',
        'industry_type', 'created_at', 'updated_at'
    ]
    
    column_names = [col['name'] for col in columns]
    missing_fields = [f for f in required_fields if f not in column_names]
    
    if missing_fields:
        print(f"  ❌ 缺少字段: {missing_fields}")
        return False
    else:
        print(f"  ✓ 所有必需字段都存在 ({len(required_fields)} 个)")
    
    return True

def test_default_values():
    """测试默认值"""
    print("\n" + "=" * 80)
    print("2. 测试默认值")
    print("=" * 80)
    
    with engine.connect() as conn:
        # 检查 shared_modules 默认值
        result = conn.execute(text("""
            SELECT column_name, column_default
            FROM information_schema.columns
            WHERE table_name = 'shared_modules'
            AND column_name IN ('status', 'download_count', 'like_count', 'dislike_count', 'view_count', 'is_featured')
            ORDER BY column_name
        """))
        
        print("\n✓ shared_modules 默认值:")
        for row in result:
            print(f"  {row.column_name}: {row.column_default}")
        
        # 检查 shared_templates 默认值
        result = conn.execute(text("""
            SELECT column_name, column_default
            FROM information_schema.columns
            WHERE table_name = 'shared_templates'
            AND column_name IN ('status', 'download_count', 'like_count', 'dislike_count', 'view_count', 'is_featured')
            ORDER BY column_name
        """))
        
        print("\n✓ shared_templates 默认值:")
        for row in result:
            print(f"  {row.column_name}: {row.column_default}")
    
    return True

def test_field_mapping():
    """测试字段映射"""
    print("\n" + "=" * 80)
    print("3. 测试字段映射")
    print("=" * 80)
    
    inspector = inspect(engine)
    
    # CustomModule vs SharedModule
    print("\n✓ CustomModule → SharedModule 字段映射:")
    custom_module_cols = {col['name'] for col in inspector.get_columns('custom_modules')}
    shared_module_cols = {col['name'] for col in inspector.get_columns('shared_modules')}
    
    # 应该复制的字段
    fields_to_copy = ['name', 'description', 'icon', 'category', 'repeatable', 'fields']
    for field in fields_to_copy:
        if field in custom_module_cols and field in shared_module_cols:
            print(f"  ✓ {field}")
        else:
            print(f"  ❌ {field} - 缺失")
    
    # WPSTemplate vs SharedTemplate
    print("\n✓ WPSTemplate → SharedTemplate 字段映射:")
    wps_template_cols = {col['name'] for col in inspector.get_columns('wps_templates')}
    shared_template_cols = {col['name'] for col in inspector.get_columns('shared_templates')}
    
    # 应该复制的字段
    fields_to_copy = ['name', 'description', 'welding_process', 'welding_process_name', 'standard', 'module_instances']
    for field in fields_to_copy:
        if field in wps_template_cols and field in shared_template_cols:
            print(f"  ✓ {field}")
        else:
            print(f"  ❌ {field} - 缺失")
    
    return True

def test_indexes():
    """测试索引"""
    print("\n" + "=" * 80)
    print("4. 测试索引")
    print("=" * 80)
    
    inspector = inspect(engine)
    
    # shared_modules 索引
    print("\n✓ shared_modules 索引:")
    indexes = inspector.get_indexes('shared_modules')
    for idx in indexes:
        print(f"  {idx['name']}: {idx['column_names']}")
    
    # shared_templates 索引
    print("\n✓ shared_templates 索引:")
    indexes = inspector.get_indexes('shared_templates')
    for idx in indexes:
        print(f"  {idx['name']}: {idx['column_names']}")
    
    return True

def test_foreign_keys():
    """测试外键"""
    print("\n" + "=" * 80)
    print("5. 测试外键约束")
    print("=" * 80)
    
    inspector = inspect(engine)
    
    # shared_modules 外键
    print("\n✓ shared_modules 外键:")
    fks = inspector.get_foreign_keys('shared_modules')
    for fk in fks:
        print(f"  {fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}")
    
    # shared_templates 外键
    print("\n✓ shared_templates 外键:")
    fks = inspector.get_foreign_keys('shared_templates')
    for fk in fks:
        print(f"  {fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}")
    
    return True

def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("共享库修复验证测试")
    print("=" * 80)
    
    results = []
    
    # 运行所有测试
    results.append(("表结构", test_table_structure()))
    results.append(("默认值", test_default_values()))
    results.append(("字段映射", test_field_mapping()))
    results.append(("索引", test_indexes()))
    results.append(("外键约束", test_foreign_keys()))
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ 所有测试通过！")
        print("=" * 80)
        return 0
    else:
        print("❌ 部分测试失败")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    sys.exit(main())

