"""
修复PQR表的test_date字段约束
将test_date从NOT NULL改为可空
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

def fix_test_date_constraint():
    """修复test_date字段约束"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("=" * 80)
        print("修复 PQR 表的 test_date 字段约束")
        print("=" * 80)
        
        # 1. 检查当前约束
        print("\n1. 检查当前 test_date 字段约束...")
        result = conn.execute(text("""
            SELECT 
                column_name, 
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = 'pqr' AND column_name = 'test_date';
        """))
        
        col_info = result.fetchone()
        if col_info:
            print(f"   当前状态: is_nullable={col_info[1]}, default={col_info[2]}")
        else:
            print("   ❌ test_date 字段不存在！")
            return
        
        # 2. 删除NOT NULL约束
        if col_info[1] == 'NO':
            print("\n2. 删除 test_date 的 NOT NULL 约束...")
            try:
                # 先删除约束
                conn.execute(text("""
                    ALTER TABLE pqr 
                    DROP CONSTRAINT IF EXISTS pqr_test_date_not_null;
                """))
                
                # 修改列为可空
                conn.execute(text("""
                    ALTER TABLE pqr 
                    ALTER COLUMN test_date DROP NOT NULL;
                """))
                
                conn.commit()
                print("   ✅ test_date 字段已改为可空")
            except Exception as e:
                print(f"   ❌ 修改失败: {str(e)}")
                conn.rollback()
                raise
        else:
            print("\n2. test_date 字段已经是可空的，无需修改")
        
        # 3. 验证修改
        print("\n3. 验证修改...")
        result = conn.execute(text("""
            SELECT is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'pqr' AND column_name = 'test_date';
        """))
        
        is_nullable = result.scalar()
        if is_nullable == 'YES':
            print("   ✅ 验证成功: test_date 字段现在是可空的")
        else:
            print("   ❌ 验证失败: test_date 字段仍然是NOT NULL")
        
        print("\n" + "=" * 80)
        print("修复完成")
        print("=" * 80)

if __name__ == "__main__":
    try:
        fix_test_date_constraint()
    except Exception as e:
        print(f"\n❌ 修复失败: {str(e)}")
        import traceback
        traceback.print_exc()

