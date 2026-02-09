"""
Equipment表结构更新迁移脚本
将现有的简化equipment表更新为完整的设备管理表结构
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backup_existing_data():
    """备份现有数据"""
    logger.info("备份现有equipment表数据...")

    # 创建备份表
    backup_sql = """
    CREATE TABLE equipment_backup AS SELECT * FROM equipment;
    """

    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text(backup_sql))
            conn.commit()
        logger.info("✅ 数据备份完成")
        return True
    except Exception as e:
        logger.error(f"❌ 数据备份失败: {e}")
        return False


def drop_existing_table():
    """删除现有表"""
    logger.info("删除现有equipment表...")

    drop_sql = """
    DROP TABLE IF EXISTS equipment CASCADE;
    """

    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text(drop_sql))
            conn.commit()
        logger.info("✅ 现有表删除完成")
        return True
    except Exception as e:
        logger.error(f"❌ 删除表失败: {e}")
        return False


def create_new_equipment_table():
    """创建新的equipment表结构"""
    logger.info("创建新的equipment表结构...")

    create_sql = """
    CREATE TABLE equipment (
        -- 主键
        id SERIAL PRIMARY KEY,

        -- 数据隔离核心字段
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        workspace_type VARCHAR(20) NOT NULL DEFAULT 'personal',
        company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
        factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,

        -- 数据访问控制
        is_shared BOOLEAN DEFAULT FALSE,
        access_level VARCHAR(20) DEFAULT 'private',

        -- 基本信息
        equipment_code VARCHAR(100) NOT NULL,
        equipment_name VARCHAR(255) NOT NULL,
        equipment_type VARCHAR(50) NOT NULL,
        category VARCHAR(100),

        -- 制造商信息
        manufacturer VARCHAR(255),
        brand VARCHAR(100),
        model VARCHAR(100),
        serial_number VARCHAR(100),

        -- 技术参数
        specifications TEXT,
        rated_power FLOAT,
        rated_voltage FLOAT,
        rated_current FLOAT,
        max_capacity FLOAT,
        working_range VARCHAR(255),

        -- 采购信息
        purchase_date DATE,
        purchase_price DECIMAL(12, 2),
        currency VARCHAR(3) DEFAULT 'CNY',
        supplier VARCHAR(255),
        warranty_period INTEGER,
        warranty_expiry_date DATE,

        -- 位置信息
        location VARCHAR(255),
        workshop VARCHAR(100),
        area VARCHAR(100),

        -- 状态信息
        status VARCHAR(20) DEFAULT 'operational',
        is_active BOOLEAN DEFAULT TRUE,
        is_critical BOOLEAN DEFAULT FALSE,
        installation_date DATE,
        commissioning_date DATE,

        -- 运行数据
        total_operating_hours FLOAT DEFAULT 0.0,
        total_maintenance_hours FLOAT DEFAULT 0.0,
        last_used_date TIMESTAMP,
        usage_count INTEGER DEFAULT 0,

        -- 维护信息
        last_maintenance_date DATE,
        next_maintenance_date DATE,
        maintenance_interval_days INTEGER,
        maintenance_count INTEGER DEFAULT 0,

        -- 检验信息
        last_inspection_date DATE,
        next_inspection_date DATE,
        inspection_interval_days INTEGER,

        -- 校准信息
        calibration_date DATE,
        calibration_due_date DATE,

        -- 人员信息
        responsible_person_id INTEGER,
        operator_ids INTEGER[],

        -- 性能指标
        availability_rate FLOAT DEFAULT 0.0,
        utilization_rate FLOAT DEFAULT 0.0,
        failure_rate FLOAT DEFAULT 0.0,
        mtbf FLOAT,
        mttr FLOAT,

        -- 附加信息
        description TEXT,
        notes TEXT,
        manual_url VARCHAR(500),
        images JSONB,
        documents JSONB,
        tags VARCHAR(500),

        -- 审计字段
        created_by INTEGER REFERENCES users(id),
        updated_by INTEGER REFERENCES users(id),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- 创建索引
    CREATE INDEX idx_equipment_user_id ON equipment(user_id);
    CREATE INDEX idx_equipment_company_id ON equipment(company_id);
    CREATE INDEX idx_equipment_factory_id ON equipment(factory_id);
    CREATE INDEX idx_equipment_equipment_code ON equipment(equipment_code);
    CREATE INDEX idx_equipment_status ON equipment(status);
    CREATE INDEX idx_equipment_type ON equipment(equipment_type);
    CREATE INDEX idx_equipment_workspace_type ON equipment(workspace_type);
    CREATE INDEX idx_equipment_created_at ON equipment(created_at);

    -- 创建触发器以自动更新 updated_at 字段
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS '
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    ' LANGUAGE plpgsql;

    CREATE TRIGGER update_equipment_updated_at
        BEFORE UPDATE ON equipment
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """

    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            # 分步执行SQL语句
            statements = create_sql.split(';')
            for statement in statements:
                if statement.strip():
                    conn.execute(text(statement))
            conn.commit()
        logger.info("✅ 新表创建完成")
        return True
    except Exception as e:
        logger.error(f"❌ 创建新表失败: {e}")
        return False


def restore_backup_data():
    """从备份恢复数据"""
    logger.info("从备份恢复数据...")

    restore_sql = """
    INSERT INTO equipment (
        name, equipment_number, equipment_type, manufacturer, model,
        purchase_date, last_maintenance, next_maintenance, status,
        owner_id, company_id, factory_id, created_at, updated_at
    )
    SELECT
        name, equipment_number, equipment_type, manufacturer, model,
        purchase_date, last_maintenance, next_maintenance, status,
        owner_id, company_id, factory_id, created_at, updated_at
    FROM equipment_backup;
    """

    # 更新字段映射
    update_sql = """
    UPDATE equipment SET
        equipment_code = equipment_number,
        equipment_name = name,
        user_id = owner_id;
    """

    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text(restore_sql))
            conn.execute(text(update_sql))
            conn.commit()
        logger.info("✅ 数据恢复完成")
        return True
    except Exception as e:
        logger.error(f"❌ 数据恢复失败: {e}")
        return False


def create_sequences():
    """创建序列"""
    logger.info("创建序列...")

    sequence_sql = """
    -- 创建设备ID序列（如果不存在）
    CREATE SEQUENCE IF NOT EXISTS equipment_id_seq START 1;

    -- 设置序列所有权
    ALTER TABLE equipment ALTER COLUMN id SET DEFAULT nextval('equipment_id_seq');
    ALTER SEQUENCE equipment_id_seq OWNED BY equipment.id;
    """

    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text(sequence_sql))
            conn.commit()
        logger.info("✅ 序列创建完成")
        return True
    except Exception as e:
        logger.error(f"❌ 序列创建失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("开始Equipment表结构更新迁移...")

    steps = [
        ("备份数据", backup_existing_data),
        ("删除现有表", drop_existing_table),
        ("创建新表", create_new_equipment_table),
        ("恢复数据", restore_backup_data),
        ("创建序列", create_sequences),
    ]

    for step_name, step_func in steps:
        logger.info(f"执行步骤: {step_name}")
        if not step_func():
            logger.error(f"❌ 迁移失败于步骤: {step_name}")
            return False

    logger.info("🎉 Equipment表结构更新迁移完成！")
    return True


if __name__ == "__main__":
    success = main()
    if success:
        logger.info("迁移成功完成")
        sys.exit(0)
    else:
        logger.error("迁移失败")
        sys.exit(1)