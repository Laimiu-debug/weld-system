#!/usr/bin/env python3
"""
检查用户的数据访问权限设置
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import CompanyEmployee, CompanyRole
from app.core.data_access import WorkspaceContext, WorkspaceType

def check_user_permissions():
    """检查用户的数据访问权限"""
    db = SessionLocal()
    try:
        print("=== 检查用户 testuser176070001 的数据访问权限 ===\n")

        # 查找用户
        user = db.query(User).filter(User.username == "testuser176070001").first()
        if not user:
            print("用户不存在")
            return

        print(f"用户: {user.username} (ID: {user.id})")
        print(f"会员类型: {user.membership_type}")

        # 查找企业员工信息
        employee = db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == user.id,
            CompanyEmployee.status == "active"
        ).first()

        if not employee:
            print("❌ 未找到活跃的企业员工记录")
            return

        print(f"\n企业员工信息:")
        print(f"  员工ID: {employee.id}")
        print(f"  公司ID: {employee.company_id}")
        print(f"  工厂ID: {employee.factory_id}")
        print(f"  角色: {employee.role}")
        print(f"  数据访问范围: {employee.data_access_scope}")
        print(f"  部门: {employee.department}")
        print(f"  职位: {employee.position}")

        # 查找角色信息
        if employee.company_role_id:
            role = db.query(CompanyRole).filter(CompanyRole.id == employee.company_role_id).first()
            if role:
                print(f"\n角色信息:")
                print(f"  角色名称: {role.name}")
                print(f"  角色数据访问范围: {role.data_access_scope}")
                print(f"  权限: {role.permissions}")

        # 创建工作区上下文（使用仪表盘API的逻辑）
        print(f"\n=== 创建工作区上下文 ===")
        from app.core.data_access import WorkspaceContext, WorkspaceType

        # 根据用户的会员类型确定默认工作区
        if user.membership_type == "enterprise":
            # 企业用户，查找其企业
            if employee:
                workspace_context = WorkspaceContext(
                    user_id=user.id,
                    workspace_type=WorkspaceType.ENTERPRISE,
                    company_id=employee.company_id,
                    factory_id=employee.factory_id
                )
            else:
                workspace_context = WorkspaceContext(
                    user_id=user.id,
                    workspace_type=WorkspaceType.PERSONAL
                )
        else:
            # 默认使用个人工作区
            workspace_context = WorkspaceContext(
                user_id=user.id,
                workspace_type=WorkspaceType.PERSONAL
            )

        print(f"工作区上下文:")
        print(f"  用户ID: {workspace_context.user_id}")
        print(f"  工作区类型: {workspace_context.workspace_type}")
        print(f"  公司ID: {workspace_context.company_id}")
        print(f"  工厂ID: {workspace_context.factory_id}")
        print(f"  数据访问范围: {employee.data_access_scope}")

        # 测试数据访问权限
        print(f"\n=== 测试数据访问权限 ===")
        from app.core.data_access import check_data_access

        # 测试WPS访问权限
        wps_access = check_data_access(
            db=db,
            user=user,
            resource_type="wps",
            workspace_context=workspace_context
        )
        print(f"WPS访问权限: {wps_access}")

        # 测试PQR访问权限
        pqr_access = check_data_access(
            db=db,
            user=user,
            resource_type="pqr",
            workspace_context=workspace_context
        )
        print(f"PQR访问权限: {pqr_access}")

        # 测试焊工访问权限
        welder_access = check_data_access(
            db=db,
            user=user,
            resource_type="welder",
            workspace_context=workspace_context
        )
        print(f"焊工访问权限: {welder_access}")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_user_permissions()