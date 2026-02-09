"""
确保所有企业会员都有企业记录
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

def ensure_enterprise_records():
    """确保所有企业会员都有企业记录"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("确保所有企业会员都有企业记录")
        print("=" * 80)
        
        # 查找所有企业会员
        enterprise_users = db.query(User).filter(
            User.membership_type == "enterprise",
            User.is_active == True
        ).all()
        
        print(f"\n找到 {len(enterprise_users)} 个企业会员")
        
        enterprise_service = EnterpriseService(db)
        
        for user in enterprise_users:
            print(f"\n处理用户: {user.email}")
            print(f"  - User ID: {user.id}")
            print(f"  - Member Tier: {user.member_tier}")
            
            # 检查是否有企业记录
            company = enterprise_service.get_company_by_owner(user.id)
            
            if company:
                print(f"  - ✓ 企业记录已存在: {company.name} (ID: {company.id})")
                
                # 检查工厂
                factories = enterprise_service.get_factories_by_company(company.id)
                print(f"  - ✓ 工厂数量: {len(factories)}")
                
                # 检查员工
                from app.models.company import CompanyEmployee
                employees = db.query(CompanyEmployee).filter(
                    CompanyEmployee.company_id == company.id
                ).all()
                print(f"  - ✓ 员工数量: {len(employees)}")
                
            else:
                print(f"  - ✗ 企业记录不存在，正在创建...")
                
                # 创建企业
                company = enterprise_service.create_company(
                    owner_id=user.id,
                    name=f"{user.full_name or user.username or user.email.split('@')[0]}'s Company",
                    membership_tier=user.member_tier
                )
                print(f"  - ✓ 企业创建成功: {company.name} (ID: {company.id})")
                
                # 创建总部工厂
                factory = enterprise_service.create_factory(
                    company_id=company.id,
                    name="Headquarters",
                    code="HQ",
                    is_headquarters=True,
                    created_by=user.id
                )
                print(f"  - ✓ 工厂创建成功: {factory.name} (ID: {factory.id})")
                
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
                print(f"  - ✓ 员工记录创建成功: {employee.employee_number}")
        
        print("\n" + "=" * 80)
        print("检查完成！")
        print("=" * 80)
        
        print(f"\n企业会员列表:")
        for user in enterprise_users:
            company = enterprise_service.get_company_by_owner(user.id)
            if company:
                print(f"  ✓ {user.email} - {company.name}")
            else:
                print(f"  ✗ {user.email} - 无企业记录")
        
    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    ensure_enterprise_records()

