"""
添加 module_type 字段到 wps_templates 表的迁移脚本
用于区分 WPS、PQR 和 pPQR 模板
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import SessionLocal


def migrate():
    """执行迁移"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("开始迁移 wps_templates 表...")
        print("=" * 80)
        
        # 1. 检查表是否存在
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'wps_templates'
            );
        """))
        table_exists = result.scalar()
        
        if not table_exists:
            print("❌ wps_templates 表不存在，请先运行应用创建表")
            return
        
        print("✅ wps_templates 表存在")
        
        # 2. 检查 module_type 字段是否已存在
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'wps_templates' AND column_name = 'module_type'
            );
        """))
        module_type_exists = result.scalar()
        
        if module_type_exists:
            print("✅ module_type 字段已存在，跳过迁移")
            return
        
        print("开始添加 module_type 字段...")
        
        # 3. 添加 module_type 字段
        db.execute(text("""
            ALTER TABLE wps_templates 
            ADD COLUMN module_type VARCHAR(20) DEFAULT 'wps';
        """))
        db.commit()
        print("✅ module_type 字段添加成功")
        
        # 4. 添加索引
        print("添加索引...")
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_wps_templates_module_type 
            ON wps_templates(module_type);
        """))
        db.commit()
        print("✅ 索引添加成功")
        
        # 5. 添加检查约束
        print("添加检查约束...")
        try:
            db.execute(text("""
                ALTER TABLE wps_templates 
                ADD CONSTRAINT check_module_type 
                CHECK (module_type IN ('wps', 'pqr', 'ppqr'));
            """))
            db.commit()
            print("✅ 检查约束添加成功")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("⚠️  检查约束已存在，跳过")
                db.rollback()
            else:
                raise
        
        # 6. 更新现有数据
        print("更新现有数据...")
        result = db.execute(text("""
            UPDATE wps_templates 
            SET module_type = 'wps' 
            WHERE module_type IS NULL;
        """))
        db.commit()
        updated_count = result.rowcount
        print(f"✅ 已更新 {updated_count} 条记录的 module_type")
        
        # 7. 将 module_type 设置为 NOT NULL
        print("设置 module_type 为 NOT NULL...")
        db.execute(text("""
            ALTER TABLE wps_templates 
            ALTER COLUMN module_type SET NOT NULL;
        """))
        db.commit()
        print("✅ module_type 设置为 NOT NULL 成功")
        
        # 8. 添加注释
        db.execute(text("""
            COMMENT ON COLUMN wps_templates.module_type IS '模块类型: wps/pqr/ppqr';
        """))
        db.commit()
        print("✅ 注释添加成功")
        
        print("\n" + "=" * 80)
        print("✅ 迁移完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()

