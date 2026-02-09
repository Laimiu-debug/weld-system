"""
添加 status 字段到 PQR 表
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

def add_status_column():
    """添加 status 列到 pqr 表"""
    engine = create_engine(str(settings.DATABASE_URL))
    
    with engine.connect() as conn:
        print("=" * 80)
        print("添加 status 字段到 PQR 表")
        print("=" * 80)
        
        # 1. 检查列是否已存在
        print("\n1. 检查 status 列是否存在...")
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'pqr' AND column_name = 'status'
        """))
        
        if result.fetchone():
            print("   ✅ status 列已存在，无需添加")
            return
        
        print("   ⚠️  status 列不存在，开始添加...")
        
        # 2. 添加 status 列
        print("\n2. 添加 status 列...")
        conn.execute(text("""
            ALTER TABLE pqr 
            ADD COLUMN status VARCHAR(20) DEFAULT 'draft'
        """))
        conn.commit()
        print("   ✅ status 列添加成功")
        
        # 3. 创建索引
        print("\n3. 创建索引...")
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_pqr_status ON pqr(status)
        """))
        conn.commit()
        print("   ✅ 索引创建成功")
        
        # 4. 更新现有记录
        print("\n4. 更新现有记录的 status...")
        result = conn.execute(text("""
            UPDATE pqr 
            SET status = CASE 
                WHEN qualification_result = 'qualified' THEN 'approved'
                WHEN qualification_result = 'failed' THEN 'rejected'
                ELSE 'draft'
            END
            WHERE status IS NULL OR status = ''
        """))
        conn.commit()
        print(f"   ✅ 更新了 {result.rowcount} 条记录")
        
        # 5. 验证
        print("\n5. 验证...")
        result = conn.execute(text("""
            SELECT status, COUNT(*) as count
            FROM pqr
            GROUP BY status
        """))
        
        print("   状态分布:")
        for row in result:
            print(f"   - {row[0]}: {row[1]} 条")
        
        print("\n" + "=" * 80)
        print("✅ status 字段添加完成")
        print("=" * 80)

if __name__ == "__main__":
    add_status_column()

