"""
初始化管理员系统的脚本
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import Base
from app.models import *  # 导入所有模型


def init_database():
    """初始化数据库表"""
    print("正在初始化数据库...")

    # 创建数据库引擎
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        echo=True  # 显示SQL语句
    )

    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功")

        # 运行迁移脚本
        run_migration_script(engine)

        print("✅ 数据库初始化完成")

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise


def run_migration_script(engine):
    """运行迁移脚本"""
    print("正在运行迁移脚本...")

    # 读取迁移脚本
    migration_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 'migrations', 'add_admin_and_system_tables.sql')

    with open(migration_path, 'r', encoding='utf-8') as f:
        migration_sql = f.read()

    # 执行迁移脚本
    with engine.connect() as conn:
        # 分割SQL语句并逐个执行
        statements = migration_sql.split(';')

        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    conn.execute(text(statement))
                    conn.commit()
                except Exception as e:
                    print(f"执行SQL语句失败: {e}")
                    print(f"SQL语句: {statement[:100]}...")
                    # 继续执行其他语句

    print("✅ 迁移脚本执行完成")


def create_default_admin():
    """创建默认管理员用户"""
    print("正在创建默认管理员用户...")

    from sqlalchemy.orm import sessionmaker
    from app.core.security import get_password_hash

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()

    try:
        # 检查是否已存在管理员用户
        from app.models.user import User
        from app.models.admin import Admin

        existing_admin = db.query(User).filter(User.email == "Laimiu.new@gmail.com").first()

        if existing_admin:
            print("⚠️  默认管理员用户已存在，跳过创建")
            return

        # 创建默认管理员用户
        default_admin = User(
            email="Laimiu.new@gmail.com",
            username="Laimiu",
            hashed_password=get_password_hash("ghzzz123"),
            full_name="系统管理员",
            is_active=True,
            is_verified=True,
            is_superuser=True,
            is_admin=True,
            member_tier="enterprise_pro_max",
            membership_type="enterprise",
            subscription_status="active"
        )

        db.add(default_admin)
        db.commit()
        db.refresh(default_admin)

        # 创建管理员记录
        admin_record = Admin(
            user_id=default_admin.id,
            admin_level="super_admin",
            is_active=True,
            permissions={
                "user_management": True,
                "system_management": True,
                "membership_management": True,
                "announcement_management": True,
                "log_management": True,
                "config_management": True
            }
        )

        db.add(admin_record)
        db.commit()

        print("✅ 默认管理员用户创建成功")
        print("   邮箱: Laimiu.new@gmail.com")
        print("   密码: ghzzz123")
        print("   ⚠️  请在首次登录后立即修改密码！")

    except Exception as e:
        print(f"❌ 创建默认管理员失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """主函数"""
    print("🚀 开始初始化管理员系统...")

    try:
        # 初始化数据库
        init_database()

        # 创建默认管理员
        create_default_admin()

        print("🎉 管理员系统初始化完成！")
        print("\n📋 接下来的步骤:")
        print("1. 启动后端服务: 运行 start-backend.bat")
        print("2. 启动管理员门户: 运行 start-admin.bat")
        print("3. 访问管理员门户: http://localhost:3001")
        print("4. 使用管理员账号登录")
        print("   邮箱: Laimiu.new@gmail.com")
        print("   密码: ghzzz123")
        print("5. 修改默认密码（建议）")

    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()