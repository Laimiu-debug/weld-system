"""
将指定用户升级为企业会员
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.services.enterprise_service import EnterpriseService

DATABASE_URL = "postgresql://weld_user:weld_password@localhost:5432/weld_db"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def upgrade_user_to_enterprise(email: str, tier: str = "enterprise_pro_max"):
    """将用户升级为企业会员"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print(f"Upgrading User to Enterprise: {email}")
        print("=" * 80)
        
        # 查找用户
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"\n✗ 用户不存在: {email}")
            print("\n可用的用户:")
            users = db.query(User).limit(10).all()
            for u in users:
                print(f"  - {u.email}")
            return
        
        print(f"\n找到用户: {user.email}")
        print(f"  - 当前 Membership Type: {user.membership_type}")
        print(f"  - 当前 Member Tier: {user.member_tier}")
        
        # 更新用户为企业会员
        print(f"\n升级用户到企业会员...")
        user.membership_type = "enterprise"
        user.member_tier = tier
        user.is_active = True
        
        db.commit()
        db.refresh(user)
        
        print(f"✓ 用户已升级:")
        print(f"  - Membership Type: {user.membership_type}")
        print(f"  - Member Tier: {user.member_tier}")
        print(f"  - Is Active: {user.is_active}")
        
        # 检查是否已有企业记录
        enterprise_service = EnterpriseService(db)
        company = enterprise_service.get_company_by_owner(user.id)
        
        if company:
            print(f"\n✓ 企业记录已存在: {company.name}")
        else:
            print(f"\n创建企业记录...")
            
            # 创建企业
            company = enterprise_service.create_company(
                owner_id=user.id,
                name=f"{user.full_name or user.username or user.email.split('@')[0]}'s Company",
                membership_tier=user.member_tier
            )
            print(f"✓ 企业创建成功: {company.name}")
            
            # 创建总部工厂
            factory = enterprise_service.create_factory(
                company_id=company.id,
                name="Headquarters",
                code="HQ",
                is_headquarters=True,
                created_by=user.id
            )
            print(f"✓ 工厂创建成功: {factory.name}")
            
            # 添加用户为管理员员工
            employee = enterprise_service.create_employee(
                company_id=company.id,
                user_id=user.id,
                role="admin",
                position="Company Owner",
                department="Management",
                factory_id=factory.id,
                data_access_scope="company"
            )
            print(f"✓ 员工记录创建成功: {employee.employee_number}")
        
        print("\n" + "=" * 80)
        print("升级完成！")
        print("=" * 80)
        print(f"\n现在可以使用以下账号登录:")
        print(f"  - Email: {user.email}")
        print(f"  - 会员类型: {user.membership_type}")
        print(f"  - 会员等级: {user.member_tier}")
        print(f"\n登录后可以访问企业管理功能。")
        
    except Exception as e:
        print(f"\n✗ 升级失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        email = sys.argv[1]
        tier = sys.argv[2] if len(sys.argv) > 2 else "enterprise_pro_max"
        upgrade_user_to_enterprise(email, tier)
    else:
        print("使用方法: python upgrade_user_to_enterprise.py <email> [tier]")
        print("\n示例:")
        print("  python upgrade_user_to_enterprise.py test@example.com")
        print("  python upgrade_user_to_enterprise.py test@example.com enterprise_pro")
        print("\n可用的企业等级:")
        print("  - enterprise")
        print("  - enterprise_pro")
        print("  - enterprise_pro_max")
        
        # 显示可用用户
        db = SessionLocal()
        try:
            print("\n可用的用户:")
            users = db.query(User).limit(10).all()
            for u in users:
                print(f"  - {u.email} (当前: {u.membership_type}/{u.member_tier})")
        finally:
            db.close()

