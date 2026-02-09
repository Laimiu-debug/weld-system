"""
初始化企业角色表和默认角色
"""
import sys
sys.path.insert(0, 'backend')

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.company import Company, CompanyRole, CompanyEmployee
from app.models.user import User
import json

def init_company_roles():
    """初始化企业角色"""
    
    # 创建所有表
    print("创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")
    
    db: Session = SessionLocal()
    
    try:
        # 获取所有活跃企业
        companies = db.query(Company).filter(Company.is_active == True).all()
        
        print(f"\n找到 {len(companies)} 个活跃企业")
        
        for company in companies:
            print(f"\n处理企业: {company.name} (ID: {company.id})")
            
            # 检查是否已有角色
            existing_roles = db.query(CompanyRole).filter(
                CompanyRole.company_id == company.id
            ).count()
            
            if existing_roles > 0:
                print(f"  ⚠️  企业已有 {existing_roles} 个角色，跳过")
                continue
            
            # 创建默认角色
            default_roles = [
                {
                    'name': '企业管理员',
                    'code': 'ADMIN',
                    'description': '拥有所有权限的管理员角色',
                    'permissions': {
                        'wps_management': {'view': True, 'create': True, 'edit': True, 'delete': True},
                        'pqr_management': {'view': True, 'create': True, 'edit': True, 'delete': True},
                        'ppqr_management': {'view': True, 'create': True, 'edit': True, 'delete': True},
                        'equipment_management': {'view': True, 'create': True, 'edit': True, 'delete': True},
                        'materials_management': {'view': True, 'create': True, 'edit': True, 'delete': True},
                        'welders_management': {'view': True, 'create': True, 'edit': True, 'delete': True},
                        'employee_management': {'view': True, 'create': True, 'edit': True, 'delete': True},
                        'factory_management': {'view': True, 'create': True, 'edit': True, 'delete': True},
                        'department_management': {'view': True, 'create': True, 'edit': True, 'delete': True},
                        'role_management': {'view': True, 'create': True, 'edit': True, 'delete': True},
                        'reports_management': {'view': True, 'create': True, 'edit': True, 'delete': True},
                    },
                    'data_access_scope': 'company',
                    'is_system': True
                },
                {
                    'name': '部门经理',
                    'code': 'MANAGER',
                    'description': '部门经理，可以管理本部门的数据',
                    'permissions': {
                        'wps_management': {'view': True, 'create': True, 'edit': True, 'delete': False},
                        'pqr_management': {'view': True, 'create': True, 'edit': True, 'delete': False},
                        'ppqr_management': {'view': True, 'create': True, 'edit': True, 'delete': False},
                        'equipment_management': {'view': True, 'create': True, 'edit': True, 'delete': False},
                        'materials_management': {'view': True, 'create': True, 'edit': False, 'delete': False},
                        'welders_management': {'view': True, 'create': False, 'edit': False, 'delete': False},
                        'employee_management': {'view': True, 'create': False, 'edit': False, 'delete': False},
                        'factory_management': {'view': True, 'create': False, 'edit': False, 'delete': False},
                        'department_management': {'view': True, 'create': False, 'edit': False, 'delete': False},
                        'role_management': {'view': False, 'create': False, 'edit': False, 'delete': False},
                        'reports_management': {'view': True, 'create': True, 'edit': False, 'delete': False},
                    },
                    'data_access_scope': 'factory',
                    'is_system': True
                },
                {
                    'name': '普通员工',
                    'code': 'EMPLOYEE',
                    'description': '普通员工，只能查看和创建基本数据',
                    'permissions': {
                        'wps_management': {'view': True, 'create': True, 'edit': False, 'delete': False},
                        'pqr_management': {'view': True, 'create': True, 'edit': False, 'delete': False},
                        'ppqr_management': {'view': True, 'create': False, 'edit': False, 'delete': False},
                        'equipment_management': {'view': True, 'create': False, 'edit': False, 'delete': False},
                        'materials_management': {'view': True, 'create': False, 'edit': False, 'delete': False},
                        'welders_management': {'view': True, 'create': False, 'edit': False, 'delete': False},
                        'employee_management': {'view': False, 'create': False, 'edit': False, 'delete': False},
                        'factory_management': {'view': False, 'create': False, 'edit': False, 'delete': False},
                        'department_management': {'view': False, 'create': False, 'edit': False, 'delete': False},
                        'role_management': {'view': False, 'create': False, 'edit': False, 'delete': False},
                        'reports_management': {'view': True, 'create': False, 'edit': False, 'delete': False},
                    },
                    'data_access_scope': 'factory',
                    'is_system': True
                }
            ]
            
            admin_role_id = None
            
            for role_data in default_roles:
                # 创建角色
                new_role = CompanyRole(
                    company_id=company.id,
                    name=role_data['name'],
                    code=role_data['code'],
                    description=role_data['description'],
                    permissions=role_data['permissions'],
                    data_access_scope=role_data['data_access_scope'],
                    is_system=role_data['is_system'],
                    created_by=company.owner_id
                )
                
                db.add(new_role)
                db.flush()  # 获取ID
                
                print(f"  ✅ 创建角色: {role_data['name']} (ID: {new_role.id})")
                
                # 记录管理员角色ID
                if role_data['code'] == 'ADMIN':
                    admin_role_id = new_role.id
            
            # 将企业所有者分配到管理员角色
            if admin_role_id:
                admin_employee = db.query(CompanyEmployee).filter(
                    CompanyEmployee.company_id == company.id,
                    CompanyEmployee.user_id == company.owner_id,
                    CompanyEmployee.role == 'admin'
                ).first()
                
                if admin_employee:
                    admin_employee.company_role_id = admin_role_id
                    print(f"  ✅ 将企业所有者分配到管理员角色")
        
        db.commit()
        print("\n" + "="*80)
        print("✅ 所有企业角色初始化完成！")
        print("="*80)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    init_company_roles()

