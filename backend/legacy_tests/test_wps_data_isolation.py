"""
测试WPS数据隔离和权限管理
Test WPS Data Isolation and Permission Management

运行方式：
cd backend
python test_wps_data_isolation.py
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import Company, CompanyEmployee
from app.models.wps import WPS
from app.services.wps_service import WPSService
from app.core.data_access import WorkspaceContext, WorkspaceType


def test_wps_data_isolation():
    """测试WPS数据隔离功能"""
    db: Session = SessionLocal()
    
    try:
        print("=" * 80)
        print("WPS数据隔离和权限管理测试")
        print("=" * 80)
        
        # 1. 查找测试用户
        print("\n1. 查找测试用户...")
        test_user = db.query(User).filter(
            User.email == "testuser176070001@example.com"
        ).first()
        
        if not test_user:
            print("❌ 测试用户不存在: testuser176070001@example.com")
            print("   请先创建该测试用户")
            return
        
        print(f"✅ 找到测试用户: {test_user.email}")
        print(f"   - ID: {test_user.id}")
        print(f"   - 会员类型: {test_user.membership_type}")
        print(f"   - 会员等级: {test_user.member_tier}")
        
        # 2. 检查企业会员身份
        print("\n2. 检查企业会员身份...")
        employee = db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == test_user.id,
            CompanyEmployee.status == "active"
        ).first()
        
        if not employee:
            print("❌ 用户不是任何企业的成员")
            print("   请先将用户添加到企业")
            return
        
        company = db.query(Company).filter(
            Company.id == employee.company_id
        ).first()
        
        print(f"✅ 用户是企业成员")
        print(f"   - 企业ID: {company.id}")
        print(f"   - 企业名称: {company.name}")
        print(f"   - 角色: {employee.role}")
        print(f"   - 工厂ID: {employee.factory_id}")
        
        # 3. 创建工作区上下文
        print("\n3. 创建工作区上下文...")
        
        # 个人工作区上下文
        personal_context = WorkspaceContext(
            user_id=test_user.id,
            workspace_type=WorkspaceType.PERSONAL
        )
        print(f"✅ 个人工作区上下文创建成功")
        print(f"   - 类型: {personal_context.workspace_type}")
        print(f"   - 用户ID: {personal_context.user_id}")
        
        # 企业工作区上下文
        enterprise_context = WorkspaceContext(
            user_id=test_user.id,
            workspace_type=WorkspaceType.ENTERPRISE,
            company_id=employee.company_id,
            factory_id=employee.factory_id
        )
        print(f"✅ 企业工作区上下文创建成功")
        print(f"   - 类型: {enterprise_context.workspace_type}")
        print(f"   - 用户ID: {enterprise_context.user_id}")
        print(f"   - 企业ID: {enterprise_context.company_id}")
        print(f"   - 工厂ID: {enterprise_context.factory_id}")
        
        # 4. 测试WPS列表查询（个人工作区）
        print("\n4. 测试WPS列表查询（个人工作区）...")
        wps_service = WPSService(db)
        
        personal_wps_list = wps_service.get_multi(
            db,
            skip=0,
            limit=100,
            current_user=test_user,
            workspace_context=personal_context
        )
        
        print(f"✅ 个人工作区WPS查询成功")
        print(f"   - 找到 {len(personal_wps_list)} 个WPS")
        
        # 显示个人WPS详情
        if personal_wps_list:
            print(f"\n   个人WPS列表:")
            for wps in personal_wps_list[:5]:  # 只显示前5个
                print(f"   - [{wps.id}] {wps.wps_number} - {wps.title}")
                print(f"     工作区类型: {wps.workspace_type}, 用户ID: {wps.user_id}")
        
        # 5. 测试WPS列表查询（企业工作区）
        print("\n5. 测试WPS列表查询（企业工作区）...")
        
        enterprise_wps_list = wps_service.get_multi(
            db,
            skip=0,
            limit=100,
            current_user=test_user,
            workspace_context=enterprise_context
        )
        
        print(f"✅ 企业工作区WPS查询成功")
        print(f"   - 找到 {len(enterprise_wps_list)} 个WPS")
        
        # 显示企业WPS详情
        if enterprise_wps_list:
            print(f"\n   企业WPS列表:")
            for wps in enterprise_wps_list[:5]:  # 只显示前5个
                print(f"   - [{wps.id}] {wps.wps_number} - {wps.title}")
                print(f"     工作区类型: {wps.workspace_type}, 企业ID: {wps.company_id}")
        
        # 6. 验证数据隔离
        print("\n6. 验证数据隔离...")
        
        # 检查个人WPS是否都属于个人工作区
        personal_wps_valid = all(
            wps.workspace_type == WorkspaceType.PERSONAL and wps.user_id == test_user.id
            for wps in personal_wps_list
        )
        
        if personal_wps_valid:
            print(f"✅ 个人工作区数据隔离正确")
            print(f"   - 所有WPS都属于个人工作区且用户ID匹配")
        else:
            print(f"❌ 个人工作区数据隔离失败")
            print(f"   - 存在不属于当前用户的WPS")
        
        # 检查企业WPS是否都属于企业工作区
        enterprise_wps_valid = all(
            wps.workspace_type == WorkspaceType.ENTERPRISE and wps.company_id == employee.company_id
            for wps in enterprise_wps_list
        )
        
        if enterprise_wps_valid:
            print(f"✅ 企业工作区数据隔离正确")
            print(f"   - 所有WPS都属于企业工作区且企业ID匹配")
        else:
            print(f"❌ 企业工作区数据隔离失败")
            print(f"   - 存在不属于当前企业的WPS")
        
        # 7. 统计所有WPS（不带过滤）
        print("\n7. 数据库中所有WPS统计...")
        
        all_wps = db.query(WPS).filter(WPS.is_active == True).all()
        personal_count = sum(1 for wps in all_wps if wps.workspace_type == WorkspaceType.PERSONAL)
        enterprise_count = sum(1 for wps in all_wps if wps.workspace_type == WorkspaceType.ENTERPRISE)
        
        print(f"   - 总WPS数量: {len(all_wps)}")
        print(f"   - 个人工作区WPS: {personal_count}")
        print(f"   - 企业工作区WPS: {enterprise_count}")
        print(f"   - 当前用户可见个人WPS: {len(personal_wps_list)}")
        print(f"   - 当前用户可见企业WPS: {len(enterprise_wps_list)}")
        
        # 8. 总结
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)
        
        if personal_wps_valid and enterprise_wps_valid:
            print("✅ 所有测试通过！")
            print("   - WPS数据隔离功能正常工作")
            print("   - 个人工作区和企业工作区数据完全隔离")
            print("   - 用户只能看到自己工作区内的数据")
        else:
            print("❌ 测试失败！")
            print("   - 数据隔离存在问题，请检查代码")
        
        print("\n提示:")
        print("   - 企业会员可以访问WPS列表")
        print("   - 数据按工作区上下文严格隔离")
        print("   - 个人工作区只显示个人数据")
        print("   - 企业工作区只显示企业数据")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    test_wps_data_isolation()

