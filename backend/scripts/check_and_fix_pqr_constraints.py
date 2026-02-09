"""
检查并修复 PQR 表的约束和索引
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import SessionLocal

def check_and_fix_constraints():
    """检查并修复 PQR 表的约束和索引"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("检查 PQR 表的约束和索引...")
        print("=" * 80)
        
        # 1. 检查外键约束
        print("\n检查外键约束...")
        result = db.execute(text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'pqr' AND constraint_type = 'FOREIGN KEY';
        """))
        existing_fks = [row[0] for row in result.fetchall()]
        print(f"现有外键约束: {existing_fks}")
        
        # 添加 user_id 外键
        if 'fk_pqr_user_id' not in existing_fks:
            print("添加 user_id 外键约束...")
            db.execute(text("""
                ALTER TABLE pqr 
                ADD CONSTRAINT fk_pqr_user_id 
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
            """))
            db.commit()
            print("  ✅ user_id 外键约束添加成功")
        else:
            print("  ✅ user_id 外键约束已存在")
        
        # 添加 company_id 外键
        if 'fk_pqr_company_id' not in existing_fks:
            print("添加 company_id 外键约束...")
            db.execute(text("""
                ALTER TABLE pqr 
                ADD CONSTRAINT fk_pqr_company_id 
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE;
            """))
            db.commit()
            print("  ✅ company_id 外键约束添加成功")
        else:
            print("  ✅ company_id 外键约束已存在")
        
        # 添加 factory_id 外键
        if 'fk_pqr_factory_id' not in existing_fks:
            print("添加 factory_id 外键约束...")
            db.execute(text("""
                ALTER TABLE pqr 
                ADD CONSTRAINT fk_pqr_factory_id 
                FOREIGN KEY (factory_id) REFERENCES factories(id) ON DELETE SET NULL;
            """))
            db.commit()
            print("  ✅ factory_id 外键约束添加成功")
        else:
            print("  ✅ factory_id 外键约束已存在")
        
        # 2. 检查索引
        print("\n检查索引...")
        result = db.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'pqr';
        """))
        existing_indexes = [row[0] for row in result.fetchall()]
        print(f"现有索引: {existing_indexes}")
        
        # 添加索引
        indexes_to_create = [
            ('ix_pqr_user_id', 'user_id'),
            ('ix_pqr_workspace_type', 'workspace_type'),
            ('ix_pqr_company_id', 'company_id'),
            ('ix_pqr_factory_id', 'factory_id'),
        ]
        
        for index_name, column_name in indexes_to_create:
            if index_name not in existing_indexes:
                print(f"创建索引 {index_name}...")
                db.execute(text(f"""
                    CREATE INDEX {index_name} ON pqr({column_name});
                """))
                db.commit()
                print(f"  ✅ {index_name} 创建成功")
            else:
                print(f"  ✅ {index_name} 已存在")
        
        # 3. 检查数据完整性
        print("\n检查数据完整性...")
        result = db.execute(text("""
            SELECT COUNT(*) FROM pqr WHERE user_id IS NULL;
        """))
        null_user_id_count = result.scalar()
        
        if null_user_id_count > 0:
            print(f"⚠️  警告：有 {null_user_id_count} 条记录的 user_id 为 NULL")
            print("   尝试从 owner_id 迁移数据...")
            
            result = db.execute(text("""
                UPDATE pqr 
                SET user_id = owner_id 
                WHERE owner_id IS NOT NULL AND user_id IS NULL;
            """))
            db.commit()
            updated_count = result.rowcount
            print(f"  ✅ 已更新 {updated_count} 条记录")
            
            # 再次检查
            result = db.execute(text("""
                SELECT COUNT(*) FROM pqr WHERE user_id IS NULL;
            """))
            null_user_id_count = result.scalar()
            
            if null_user_id_count > 0:
                print(f"  ⚠️  仍有 {null_user_id_count} 条记录的 user_id 为 NULL，需要手动处理")
        else:
            print("  ✅ 所有记录的 user_id 都不为 NULL")
        
        # 4. 显示统计信息
        print("\n" + "=" * 80)
        print("PQR 表统计信息：")
        print("=" * 80)
        
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN workspace_type = 'personal' THEN 1 END) as personal,
                COUNT(CASE WHEN workspace_type = 'enterprise' THEN 1 END) as enterprise,
                COUNT(CASE WHEN user_id IS NOT NULL THEN 1 END) as has_user_id,
                COUNT(CASE WHEN company_id IS NOT NULL THEN 1 END) as has_company_id
            FROM pqr;
        """))
        stats = result.fetchone()
        
        print(f"总记录数: {stats[0]}")
        print(f"个人工作区: {stats[1]}")
        print(f"企业工作区: {stats[2]}")
        print(f"有 user_id: {stats[3]}")
        print(f"有 company_id: {stats[4]}")
        
        print("\n✅ 检查和修复完成！")
        
    except Exception as e:
        print(f"\n❌ 操作失败: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_and_fix_constraints()

