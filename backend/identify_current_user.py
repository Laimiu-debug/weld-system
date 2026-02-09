"""
帮助确定当前用户身份和设备访问权限
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.equipment import Equipment
from app.models.user import User
from app.models.company import CompanyEmployee, Company

def show_all_companies_and_users():
    """显示所有公司和用户的详细信息"""
    print("=== 所有公司和用户信息 ===")

    try:
        db = SessionLocal()

        # 显示所有公司
        companies = db.query(Company).all()
        print(f"\n系统中的所有公司:")
        for company in companies:
            print(f"  公司ID: {company.id}, 名称: {company.name}, 所有者: {company.owner_id}")

        # 显示所有公司员工关系
        employees = db.query(CompanyEmployee).filter(CompanyEmployee.status == "active").all()
        print(f"\n活跃的企业员工:")
        for emp in employees:
            user = db.query(User).filter(User.id == emp.user_id).first()
            company = db.query(Company).filter(Company.id == emp.company_id).first()
            if user and company:
                print(f"  用户: {user.username} (ID: {emp.user_id}) -> 公司: {company.name} (ID: {emp.company_id})")

        # 显示设备
        equipment_list = db.query(Equipment).all()
        print(f"\n所有设备:")
        for eq in equipment_list:
            company = db.query(Company).filter(Company.id == eq.company_id).first()
            company_name = company.name if company else "未知公司"
            print(f"  设备: {eq.equipment_code} -> 公司: {company_name} (ID: {eq.company_id})")

        print(f"\n=== 推荐登录用户 ===")
        print(f"如果您想查看公司ID=1的设备，请使用以下任一用户登录:")

        company1_users = [emp for emp in employees if emp.company_id == 1]
        for emp in company1_users:
            user = db.query(User).filter(User.id == emp.user_id).first()
            if user:
                print(f"  - 用户名: {user.username}, 邮箱: {user.email}")

        db.close()

    except Exception as e:
        print(f"查询失败: {e}")

if __name__ == "__main__":
    show_all_companies_and_users()