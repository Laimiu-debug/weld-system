"""
迁移脚本：为 PQR 表添加工作区上下文字段

这个脚本会：
1. 添加新的工作区字段（user_id, workspace_type, company_id, factory_id, is_shared, access_level）
2. 从现有的 owner_id 迁移数据到 user_id
3. 设置默认值
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import SessionLocal, engine

def migrate_pqr_table():
    """迁移 PQR 表，添加工作区上下文字段"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("开始迁移 PQR 表...")
        print("=" * 80)
        
        # 1. 检查表是否存在
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'pqr'
            );
        """))
        table_exists = result.scalar()
        
        if not table_exists:
            print("❌ PQR 表不存在，请先运行应用创建表")
            return
        
        print("✅ PQR 表存在")
        
        # 2. 检查 user_id 字段是否已存在
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'pqr' AND column_name = 'user_id'
            );
        """))
        user_id_exists = result.scalar()
        
        if user_id_exists:
            print("✅ user_id 字段已存在，跳过迁移")
            return
        
        print("开始添加新字段...")
        
        # 3. 添加新字段（允许 NULL，稍后更新）
        db.execute(text("""
            ALTER TABLE pqr 
            ADD COLUMN IF NOT EXISTS user_id INTEGER,
            ADD COLUMN IF NOT EXISTS workspace_type VARCHAR(20) DEFAULT 'personal',
            ADD COLUMN IF NOT EXISTS company_id INTEGER,
            ADD COLUMN IF NOT EXISTS factory_id INTEGER,
            ADD COLUMN IF NOT EXISTS is_shared BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS access_level VARCHAR(20) DEFAULT 'private';
        """))
        db.commit()
        print("✅ 新字段添加成功")
        
        # 4. 从 owner_id 迁移数据到 user_id
        print("开始迁移数据...")
        result = db.execute(text("""
            UPDATE pqr 
            SET user_id = owner_id 
            WHERE owner_id IS NOT NULL AND user_id IS NULL;
        """))
        db.commit()
        updated_count = result.rowcount
        print(f"✅ 已更新 {updated_count} 条记录的 user_id")
        
        # 5. 检查是否有 user_id 为 NULL 的记录
        result = db.execute(text("""
            SELECT COUNT(*) FROM pqr WHERE user_id IS NULL;
        """))
        null_count = result.scalar()
        
        if null_count > 0:
            print(f"⚠️  警告：有 {null_count} 条记录的 user_id 为 NULL")
            print("   这些记录可能需要手动处理")
        
        # 6. 设置 user_id 为 NOT NULL（如果没有 NULL 值）
        if null_count == 0:
            db.execute(text("""
                ALTER TABLE pqr 
                ALTER COLUMN user_id SET NOT NULL;
            """))
            db.commit()
            print("✅ user_id 字段设置为 NOT NULL")
        
        # 7. 添加外键约束（先检查是否存在）
        print("添加外键约束...")

        # 检查并添加 user_id 外键
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_pqr_user_id' AND table_name = 'pqr'
            );
        """))
        if not result.scalar():
            db.execute(text("""
                ALTER TABLE pqr
                ADD CONSTRAINT fk_pqr_user_id
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
            """))
            print("  ✅ user_id 外键约束添加成功")
        else:
            print("  ✅ user_id 外键约束已存在")

        # 检查并添加 company_id 外键
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_pqr_company_id' AND table_name = 'pqr'
            );
        """))
        if not result.scalar():
            db.execute(text("""
                ALTER TABLE pqr
                ADD CONSTRAINT fk_pqr_company_id
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE;
            """))
            print("  ✅ company_id 外键约束添加成功")
        else:
            print("  ✅ company_id 外键约束已存在")

        # 检查并添加 factory_id 外键
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_pqr_factory_id' AND table_name = 'pqr'
            );
        """))
        if not result.scalar():
            db.execute(text("""
                ALTER TABLE pqr
                ADD CONSTRAINT fk_pqr_factory_id
                FOREIGN KEY (factory_id) REFERENCES factories(id) ON DELETE SET NULL;
            """))
            print("  ✅ factory_id 外键约束添加成功")
        else:
            print("  ✅ factory_id 外键约束已存在")

        db.commit()
        print("✅ 所有外键约束处理完成")
        
        # 8. 添加索引
        print("添加索引...")
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_pqr_user_id ON pqr(user_id);
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_pqr_workspace_type ON pqr(workspace_type);
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_pqr_company_id ON pqr(company_id);
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_pqr_factory_id ON pqr(factory_id);
        """))
        db.commit()
        print("✅ 索引添加成功")
        
        # 9. 显示迁移后的统计信息
        print("\n" + "=" * 80)
        print("迁移完成！统计信息：")
        print("=" * 80)
        
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN workspace_type = 'personal' THEN 1 END) as personal,
                COUNT(CASE WHEN workspace_type = 'enterprise' THEN 1 END) as enterprise
            FROM pqr;
        """))
        stats = result.fetchone()
        
        print(f"总记录数: {stats[0]}")
        print(f"个人工作区: {stats[1]}")
        print(f"企业工作区: {stats[2]}")
        
        print("\n✅ PQR 表迁移成功完成！")
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_pqr_table()

