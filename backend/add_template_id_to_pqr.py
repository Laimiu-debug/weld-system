"""
为PQR表添加template_id列
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

def add_template_id_column():
    """为PQR表添加template_id列"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("=" * 80)
        print("为 PQR 表添加 template_id 列")
        print("=" * 80)
        
        # 1. 检查列是否已存在
        print("\n1. 检查 template_id 列是否存在...")
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'pqr' AND column_name = 'template_id';
        """))
        
        exists = result.fetchone()
        
        if exists:
            print("   ✅ template_id 列已存在，无需添加")
            return
        
        # 2. 添加列
        print("\n2. 添加 template_id 列...")
        try:
            conn.execute(text("""
                ALTER TABLE pqr 
                ADD COLUMN template_id VARCHAR(100);
            """))
            
            conn.commit()
            print("   ✅ template_id 列添加成功")
        except Exception as e:
            print(f"   ❌ 添加失败: {str(e)}")
            conn.rollback()
            raise
        
        # 3. 添加索引
        print("\n3. 添加索引...")
        try:
            conn.execute(text("""
                CREATE INDEX idx_pqr_template_id ON pqr(template_id);
            """))
            
            conn.commit()
            print("   ✅ 索引添加成功")
        except Exception as e:
            print(f"   ⚠️  添加索引失败: {str(e)}")
        
        # 4. 添加注释
        print("\n4. 添加列注释...")
        try:
            conn.execute(text("""
                COMMENT ON COLUMN pqr.template_id IS '使用的模板ID';
            """))
            
            conn.commit()
            print("   ✅ 列注释添加成功")
        except Exception as e:
            print(f"   ⚠️  添加注释失败: {str(e)}")
        
        # 5. 验证
        print("\n5. 验证...")
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'pqr' AND column_name = 'template_id';
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
        add_template_id_column()
    except Exception as e:
        print(f"\n❌ 操作失败: {str(e)}")
        import traceback
        traceback.print_exc()

