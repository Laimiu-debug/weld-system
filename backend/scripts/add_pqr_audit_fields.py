"""
为 PQR 表添加审计字段（created_by, updated_by）
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import SessionLocal

def add_audit_fields():
    """为 PQR 表添加审计字段"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("为 PQR 表添加审计字段...")
        print("=" * 80)
        
        # 1. 检查 created_by 字段是否存在
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'pqr' AND column_name = 'created_by'
            );
        """))
        created_by_exists = result.scalar()
        
        if not created_by_exists:
            print("\n添加 created_by 字段...")
            
            # 添加字段（允许 NULL）
            db.execute(text("""
                ALTER TABLE pqr 
                ADD COLUMN created_by INTEGER;
            """))
            db.commit()
            print("  ✅ created_by 字段添加成功")
            
            # 从 user_id 迁移数据
            print("  从 user_id 迁移数据到 created_by...")
            result = db.execute(text("""
                UPDATE pqr 
                SET created_by = user_id 
                WHERE user_id IS NOT NULL AND created_by IS NULL;
            """))
            db.commit()
            print(f"  ✅ 已更新 {result.rowcount} 条记录")
            
            # 检查是否有 NULL 值
            result = db.execute(text("""
                SELECT COUNT(*) FROM pqr WHERE created_by IS NULL;
            """))
            null_count = result.scalar()
            
            if null_count == 0:
                # 设置为 NOT NULL
                db.execute(text("""
                    ALTER TABLE pqr 
                    ALTER COLUMN created_by SET NOT NULL;
                """))
                db.commit()
                print("  ✅ created_by 设置为 NOT NULL")
            else:
                print(f"  ⚠️  警告：有 {null_count} 条记录的 created_by 为 NULL")
            
            # 添加外键约束
            result = db.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'fk_pqr_created_by' AND table_name = 'pqr'
                );
            """))
            if not result.scalar():
                db.execute(text("""
                    ALTER TABLE pqr 
                    ADD CONSTRAINT fk_pqr_created_by 
                    FOREIGN KEY (created_by) REFERENCES users(id);
                """))
                db.commit()
                print("  ✅ created_by 外键约束添加成功")
        else:
            print("✅ created_by 字段已存在")
        
        # 2. 检查 updated_by 字段是否存在
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'pqr' AND column_name = 'updated_by'
            );
        """))
        updated_by_exists = result.scalar()
        
        if not updated_by_exists:
            print("\n添加 updated_by 字段...")
            
            # 添加字段（允许 NULL）
            db.execute(text("""
                ALTER TABLE pqr 
                ADD COLUMN updated_by INTEGER;
            """))
            db.commit()
            print("  ✅ updated_by 字段添加成功")
            
            # 添加外键约束
            result = db.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'fk_pqr_updated_by' AND table_name = 'pqr'
                );
            """))
            if not result.scalar():
                db.execute(text("""
                    ALTER TABLE pqr 
                    ADD CONSTRAINT fk_pqr_updated_by 
                    FOREIGN KEY (updated_by) REFERENCES users(id);
                """))
                db.commit()
                print("  ✅ updated_by 外键约束添加成功")
        else:
            print("✅ updated_by 字段已存在")
        
        # 3. 显示最终状态
        print("\n" + "=" * 80)
        print("PQR 表字段检查：")
        print("=" * 80)
        
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'pqr' 
            AND column_name IN ('user_id', 'created_by', 'updated_by', 'created_at', 'updated_at')
            ORDER BY column_name;
        """))
        
        for row in result.fetchall():
            print(f"  {row[0]}: {row[1]} (nullable: {row[2]})")
        
        print("\n✅ 审计字段添加完成！")
        
    except Exception as e:
        print(f"\n❌ 操作失败: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    add_audit_fields()

