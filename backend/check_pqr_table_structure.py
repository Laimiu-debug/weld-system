"""
检查PQR表结构和约束
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings

def check_pqr_table():
    """检查PQR表的结构和约束"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("=" * 80)
        print("检查 PQR 表结构")
        print("=" * 80)
        
        # 1. 检查表是否存在
        print("\n1. 检查表是否存在...")
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'pqr'
            );
        """))
        table_exists = result.scalar()
        print(f"   PQR表存在: {table_exists}")
        
        if not table_exists:
            print("   ❌ PQR表不存在！")
            return
        
        # 2. 检查列信息
        print("\n2. 检查列信息...")
        result = conn.execute(text("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = 'pqr'
            ORDER BY ordinal_position;
        """))
        
        columns = result.fetchall()
        print(f"   共有 {len(columns)} 列")
        print("\n   关键列信息:")
        key_columns = ['id', 'user_id', 'workspace_type', 'created_by', 'updated_by', 
                      'pqr_number', 'title', 'test_date', 'qualification_result']
        for col in columns:
            if col[0] in key_columns:
                nullable = "可空" if col[2] == 'YES' else "不可空"
                default = f", 默认值: {col[3]}" if col[3] else ""
                print(f"   - {col[0]}: {col[1]} ({nullable}{default})")
        
        # 3. 检查约束
        print("\n3. 检查约束...")
        result = conn.execute(text("""
            SELECT 
                constraint_name, 
                constraint_type
            FROM information_schema.table_constraints 
            WHERE table_name = 'pqr'
            ORDER BY constraint_type, constraint_name;
        """))
        
        constraints = result.fetchall()
        print(f"   共有 {len(constraints)} 个约束")
        for constraint in constraints:
            print(f"   - {constraint[0]}: {constraint[1]}")
        
        # 4. 检查外键
        print("\n4. 检查外键...")
        result = conn.execute(text("""
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule
            FROM information_schema.key_column_usage AS kcu
            JOIN information_schema.referential_constraints AS rc
                ON kcu.constraint_name = rc.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON rc.constraint_name = ccu.constraint_name
            WHERE kcu.table_name = 'pqr'
            ORDER BY kcu.column_name;
        """))
        
        foreign_keys = result.fetchall()
        print(f"   共有 {len(foreign_keys)} 个外键")
        for fk in foreign_keys:
            print(f"   - {fk[0]} -> {fk[1]}.{fk[2]} (删除规则: {fk[3]})")
        
        # 5. 检查索引
        print("\n5. 检查索引...")
        result = conn.execute(text("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE tablename = 'pqr'
            ORDER BY indexname;
        """))
        
        indexes = result.fetchall()
        print(f"   共有 {len(indexes)} 个索引")
        for idx in indexes:
            print(f"   - {idx[0]}")
        
        # 6. 检查数据
        print("\n6. 检查数据...")
        result = conn.execute(text("SELECT COUNT(*) FROM pqr;"))
        count = result.scalar()
        print(f"   共有 {count} 条PQR记录")
        
        if count > 0:
            # 检查是否有NULL值的必填字段
            print("\n   检查必填字段的NULL值:")
            for field in ['user_id', 'workspace_type', 'created_by', 'pqr_number', 'title']:
                result = conn.execute(text(f"SELECT COUNT(*) FROM pqr WHERE {field} IS NULL;"))
                null_count = result.scalar()
                if null_count > 0:
                    print(f"   ⚠️  {field}: {null_count} 条记录为NULL")
                else:
                    print(f"   ✅ {field}: 无NULL值")
        
        # 7. 检查是否有重复的created_by定义
        print("\n7. 检查模型定义...")
        from app.models.pqr import PQR
        import inspect as py_inspect
        
        # 获取PQR类的所有属性
        pqr_attrs = [attr for attr in dir(PQR) if not attr.startswith('_')]
        
        # 检查created_by和updated_by
        if 'created_by' in pqr_attrs:
            print("   ✅ created_by 字段存在于模型中")
        else:
            print("   ❌ created_by 字段不存在于模型中")
            
        if 'updated_by' in pqr_attrs:
            print("   ✅ updated_by 字段存在于模型中")
        else:
            print("   ❌ updated_by 字段不存在于模型中")
        
        print("\n" + "=" * 80)
        print("检查完成")
        print("=" * 80)

if __name__ == "__main__":
    try:
        check_pqr_table()
    except Exception as e:
        print(f"\n❌ 检查失败: {str(e)}")
        import traceback
        traceback.print_exc()

