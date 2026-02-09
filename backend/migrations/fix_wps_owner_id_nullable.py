"""
修复 WPS owner_id 字段的 NOT NULL 约束

owner_id 字段已废弃，应该允许为 NULL
"""

from sqlalchemy import create_engine, text
from app.core.config import settings

def main():
    print("=" * 60)
    print("修复 WPS owner_id 字段")
    print("=" * 60)
    
    engine = create_engine(str(settings.DATABASE_URL))
    
    with engine.connect() as conn:
        # 检查 owner_id 字段的约束
        print("\n检查 owner_id 字段约束...")
        
        result = conn.execute(text("""
            SELECT 
                column_name, 
                is_nullable, 
                column_default
            FROM information_schema.columns
            WHERE table_name = 'wps' 
              AND column_name = 'owner_id'
        """))
        
        row = result.fetchone()
        if row:
            print(f"字段: {row[0]}")
            print(f"可为空: {row[1]}")
            print(f"默认值: {row[2]}")
            
            if row[1] == 'NO':
                print("\n修改 owner_id 字段为可空...")
                conn.execute(text("ALTER TABLE wps ALTER COLUMN owner_id DROP NOT NULL"))
                conn.commit()
                print("✓ owner_id 字段已修改为可空")
            else:
                print("\n✓ owner_id 字段已经是可空的")
        else:
            print("✗ 未找到 owner_id 字段")
    
    print("\n" + "=" * 60)
    print("修复完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()

