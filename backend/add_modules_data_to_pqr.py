"""
为PQR表添加modules_data列
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

def add_modules_data_column():
    """为PQR表添加modules_data列"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("=" * 80)
        print("为 PQR 表添加 modules_data 列")
        print("=" * 80)
        
        # 1. 检查列是否已存在
        print("\n1. 检查 modules_data 列是否存在...")
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'pqr' AND column_name = 'modules_data';
        """))
        
        exists = result.fetchone()
        
        if exists:
            print("   ✅ modules_data 列已存在，无需添加")
            return
        
        # 2. 添加列
        print("\n2. 添加 modules_data 列...")
        try:
            conn.execute(text("""
                ALTER TABLE pqr 
                ADD COLUMN modules_data JSONB;
            """))
            
            conn.commit()
            print("   ✅ modules_data 列添加成功")
        except Exception as e:
            print(f"   ❌ 添加失败: {str(e)}")
            conn.rollback()
            raise
        
        # 3. 添加注释
        print("\n3. 添加列注释...")
        try:
            conn.execute(text("""
                COMMENT ON COLUMN pqr.modules_data IS '模块化数据（JSONB格式）';
            """))
            
            conn.commit()
            print("   ✅ 列注释添加成功")
        except Exception as e:
            print(f"   ⚠️  添加注释失败: {str(e)}")
        
        # 4. 验证
        print("\n4. 验证...")
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'pqr' AND column_name = 'modules_data';
        """))
        
        col_info = result.fetchone()
        if col_info:
            print(f"   ✅ 验证成功: {col_info[0]} ({col_info[1]})")
        else:
            print("   ❌ 验证失败: 列不存在")
        
        print("\n" + "=" * 80)
        print("添加完成")
        print("=" * 80)

if __name__ == "__main__":
    try:
        add_modules_data_column()
    except Exception as e:
        print(f"\n❌ 操作失败: {str(e)}")
        import traceback
        traceback.print_exc()

