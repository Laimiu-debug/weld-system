"""
WPS 编号唯一性约束修复脚本

目的：实现正确的数据隔离，允许不同工作区使用相同的 WPS 编号

问题：
1. wps_number 字段有全局唯一约束 (unique=True)
2. 这导致个人工作区和企业工作区不能使用相同的 WPS 编号
3. 不同企业也不能使用相同的 WPS 编号

解决方案：
1. 删除全局唯一约束
2. 创建部分唯一索引（partial unique index）
   - 个人工作区：workspace_type + user_id + wps_number 唯一
   - 企业工作区：workspace_type + company_id + wps_number 唯一
"""

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings

def main():
    print("=" * 60)
    print("WPS 编号唯一性约束修复")
    print("=" * 60)
    
    # 创建数据库引擎
    engine = create_engine(str(settings.DATABASE_URL))
    
    with engine.connect() as conn:
        # 步骤 1: 查找并删除现有的唯一约束
        print("\n步骤 1: 查找 wps_number 的唯一约束...")
        
        result = conn.execute(text("""
            SELECT conname
            FROM pg_constraint
            WHERE conrelid = 'wps'::regclass
              AND contype = 'u'
              AND conkey = ARRAY[(
                  SELECT attnum 
                  FROM pg_attribute 
                  WHERE attrelid = 'wps'::regclass 
                    AND attname = 'wps_number'
              )]
        """))
        
        constraint_name = result.scalar()
        
        if constraint_name:
            print(f"找到唯一约束: {constraint_name}")
            print(f"删除约束: {constraint_name}...")
            conn.execute(text(f'ALTER TABLE wps DROP CONSTRAINT "{constraint_name}"'))
            conn.commit()
            print(f"✓ 已删除唯一约束: {constraint_name}")
        else:
            print("未找到 wps_number 的唯一约束")
        
        # 步骤 2: 删除现有的唯一索引（如果存在）
        print("\n步骤 2: 删除现有的唯一索引...")
        
        for index_name in ['wps_wps_number_key', 'ix_wps_wps_number']:
            try:
                conn.execute(text(f'DROP INDEX IF EXISTS {index_name}'))
                conn.commit()
                print(f"✓ 已删除索引: {index_name}")
            except Exception as e:
                print(f"索引 {index_name} 不存在或已删除")
        
        # 步骤 3: 创建新的普通索引（用于查询性能）
        print("\n步骤 3: 创建普通索引...")
        
        conn.execute(text('CREATE INDEX IF NOT EXISTS idx_wps_number ON wps(wps_number)'))
        conn.commit()
        print("✓ 已创建索引: idx_wps_number")
        
        # 步骤 4: 创建部分唯一索引 - 个人工作区
        print("\n步骤 4: 创建个人工作区唯一索引...")
        
        try:
            conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS uq_wps_number_personal
                ON wps (workspace_type, user_id, wps_number)
                WHERE workspace_type = 'personal'
            """))
            conn.commit()
            print("✓ 已创建索引: uq_wps_number_personal")
        except Exception as e:
            print(f"✗ 创建索引失败: {e}")
        
        # 步骤 5: 创建部分唯一索引 - 企业工作区
        print("\n步骤 5: 创建企业工作区唯一索引...")
        
        try:
            conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS uq_wps_number_enterprise
                ON wps (workspace_type, company_id, wps_number)
                WHERE workspace_type = 'enterprise'
            """))
            conn.commit()
            print("✓ 已创建索引: uq_wps_number_enterprise")
        except Exception as e:
            print(f"✗ 创建索引失败: {e}")
        
        # 步骤 6: 创建复合索引以提高查询性能
        print("\n步骤 6: 创建复合索引...")
        
        conn.execute(text('CREATE INDEX IF NOT EXISTS idx_wps_workspace_user ON wps (workspace_type, user_id)'))
        conn.commit()
        print("✓ 已创建索引: idx_wps_workspace_user")
        
        conn.execute(text('CREATE INDEX IF NOT EXISTS idx_wps_workspace_company ON wps (workspace_type, company_id)'))
        conn.commit()
        print("✓ 已创建索引: idx_wps_workspace_company")
        
        # 步骤 7: 验证索引创建成功
        print("\n步骤 7: 验证索引...")
        
        result = conn.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'wps' 
              AND indexname IN ('uq_wps_number_personal', 'uq_wps_number_enterprise')
        """))
        
        indexes = [row[0] for row in result]
        
        if 'uq_wps_number_personal' in indexes:
            print("✓ 个人工作区唯一索引创建成功")
        else:
            print("✗ 个人工作区唯一索引创建失败")
        
        if 'uq_wps_number_enterprise' in indexes:
            print("✓ 企业工作区唯一索引创建成功")
        else:
            print("✗ 企业工作区唯一索引创建失败")
    
    print("\n" + "=" * 60)
    print("数据库迁移完成！")
    print("=" * 60)
    print("\n数据隔离规则：")
    print("1. 个人工作区：同一用户的 WPS 编号必须唯一")
    print("2. 企业工作区：同一企业的 WPS 编号必须唯一")
    print("3. 不同用户/企业可以使用相同的 WPS 编号")
    print("4. 个人工作区和企业工作区可以使用相同的 WPS 编号")
    print("=" * 60)

if __name__ == "__main__":
    main()

