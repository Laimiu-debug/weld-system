"""
测试WPS模板和模块的数据隔离功能

运行方式：
cd backend
python test_template_module_isolation.py
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User
from app.models.company import CompanyEmployee
from app.services.wps_template_service import WPSTemplateService
from app.services.custom_module_service import CustomModuleService
from app.core.data_access import WorkspaceContext, WorkspaceType


def test_template_isolation():
    """测试WPS模板数据隔离"""
    print("\n" + "="*80)
    print("测试WPS模板数据隔离")
    print("="*80)
    
    # 创建数据库连接
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 查找测试用户
        test_user = db.query(User).filter(
            User.email == "testuser176070001@example.com"
        ).first()
        
        if not test_user:
            print("❌ 未找到测试用户: testuser176070001@example.com")
            return
        
        print(f"✅ 找到测试用户: {test_user.email}")
        print(f"   用户ID: {test_user.id}")
        print(f"   会员类型: {test_user.membership_type}")
        
        # 查找企业员工信息
        employee = db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == test_user.id,
            CompanyEmployee.status == "active"
        ).first()
        
        if employee:
            print(f"✅ 找到企业员工信息")
            print(f"   企业ID: {employee.company_id}")
            print(f"   工厂ID: {employee.factory_id}")
        
        # 创建Service实例
        template_service = WPSTemplateService(db)
        
        # 测试1: 个人工作区
        print("\n" + "-"*80)
        print("测试1: 个人工作区 - 获取模板列表")
        print("-"*80)
        
        personal_context = WorkspaceContext(
            user_id=test_user.id,
            workspace_type=WorkspaceType.PERSONAL
        )
        
        templates, total = template_service.get_available_templates(
            current_user=test_user,
            workspace_context=personal_context
        )
        
        print(f"✅ 个人工作区模板数量: {total}")
        for template in templates[:5]:  # 只显示前5个
            print(f"   - {template.name} (来源: {template.template_source}, 工作区: {template.workspace_type})")
        
        # 测试2: 企业工作区
        if employee:
            print("\n" + "-"*80)
            print("测试2: 企业工作区 - 获取模板列表")
            print("-"*80)
            
            enterprise_context = WorkspaceContext(
                user_id=test_user.id,
                workspace_type=WorkspaceType.ENTERPRISE,
                company_id=employee.company_id,
                factory_id=employee.factory_id
            )
            
            templates, total = template_service.get_available_templates(
                current_user=test_user,
                workspace_context=enterprise_context
            )
            
            print(f"✅ 企业工作区模板数量: {total}")
            for template in templates[:5]:  # 只显示前5个
                print(f"   - {template.name} (来源: {template.template_source}, 工作区: {template.workspace_type})")
        
        print("\n✅ WPS模板数据隔离测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_module_isolation():
    """测试自定义模块数据隔离"""
    print("\n" + "="*80)
    print("测试自定义模块数据隔离")
    print("="*80)
    
    # 创建数据库连接
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 查找测试用户
        test_user = db.query(User).filter(
            User.email == "testuser176070001@example.com"
        ).first()
        
        if not test_user:
            print("❌ 未找到测试用户: testuser176070001@example.com")
            return
        
        print(f"✅ 找到测试用户: {test_user.email}")
        
        # 查找企业员工信息
        employee = db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == test_user.id,
            CompanyEmployee.status == "active"
        ).first()
        
        # 创建Service实例
        module_service = CustomModuleService(db)
        
        # 测试1: 个人工作区
        print("\n" + "-"*80)
        print("测试1: 个人工作区 - 获取模块列表")
        print("-"*80)
        
        personal_context = WorkspaceContext(
            user_id=test_user.id,
            workspace_type=WorkspaceType.PERSONAL
        )
        
        modules = module_service.get_available_modules(
            current_user=test_user,
            workspace_context=personal_context
        )
        
        print(f"✅ 个人工作区模块数量: {len(modules)}")
        for module in modules[:5]:  # 只显示前5个
            print(f"   - {module.name} (工作区: {module.workspace_type})")
        
        # 测试2: 企业工作区
        if employee:
            print("\n" + "-"*80)
            print("测试2: 企业工作区 - 获取模块列表")
            print("-"*80)
            
            enterprise_context = WorkspaceContext(
                user_id=test_user.id,
                workspace_type=WorkspaceType.ENTERPRISE,
                company_id=employee.company_id,
                factory_id=employee.factory_id
            )
            
            modules = module_service.get_available_modules(
                current_user=test_user,
                workspace_context=enterprise_context
            )
            
            print(f"✅ 企业工作区模块数量: {len(modules)}")
            for module in modules[:5]:  # 只显示前5个
                print(f"   - {module.name} (工作区: {module.workspace_type})")
        
        print("\n✅ 自定义模块数据隔离测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("WPS模板和模块数据隔离测试")
    print("="*80)
    
    # 运行测试
    test_template_isolation()
    test_module_isolation()
    
    print("\n" + "="*80)
    print("所有测试完成！")
    print("="*80)

