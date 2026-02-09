#!/usr/bin/env python3
"""
检查用户 testuser176070001 的企业工作区数据
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import CompanyEmployee, Company
from app.models.wps import WPS
from app.models.pqr import PQR
from app.models.ppqr import PPQR
from app.models.welder import Welder
from app.core.data_access import WorkspaceType

def check_enterprise_workspace():
    """检查企业工作区数据"""
    db = SessionLocal()
    try:
        print("=== 检查用户 testuser176070001 的企业工作区数据 ===\n")

        # 查找用户
        user = db.query(User).filter(User.username == "testuser176070001").first()
        if not user:
            print("用户 testuser176070001 不存在")
            return

        print(f"用户: {user.username} (ID: {user.id})")
        print(f"会员类型: {user.membership_type}")
        print(f"会员等级: {user.member_tier}")

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
        print(f"  状态: {employee.status}")

        # 查找公司信息
        company = db.query(Company).filter(Company.id == employee.company_id).first()
        if company:
            print(f"\n公司信息:")
            print(f"  公司名称: {company.name}")
            print(f"  公司ID: {company.id}")

        # 统计企业工作区数据（按 company_id 过滤）
        print(f"\n=== 企业工作区数据统计（按公司ID: {employee.company_id}） ===")

        wps_enterprise = db.query(func.count(WPS.id)).filter(
            WPS.company_id == employee.company_id,
            WPS.workspace_type == WorkspaceType.ENTERPRISE
        ).scalar() or 0

        pqr_enterprise = db.query(func.count(PQR.id)).filter(
            PQR.company_id == employee.company_id,
            PQR.workspace_type == WorkspaceType.ENTERPRISE
        ).scalar() or 0

        ppqr_enterprise = db.query(func.count(PPQR.id)).filter(
            PPQR.company_id == employee.company_id,
            PPQR.workspace_type == WorkspaceType.ENTERPRISE
        ).scalar() or 0

        welders_enterprise = db.query(func.count(Welder.id)).filter(
            Welder.company_id == employee.company_id,
            Welder.workspace_type == WorkspaceType.ENTERPRISE
        ).scalar() or 0

        print(f"企业工作区总计:")
        print(f"  WPS: {wps_enterprise}")
        print(f"  PQR: {pqr_enterprise}")
        print(f"  PPQR: {ppqr_enterprise}")
        print(f"  焊工: {welders_enterprise}")

        # 统计该用户在企业工作区的数据
        print(f"\n=== 用户在企业工作区的数据（用户ID: {user.id}） ===")

        wps_user_enterprise = db.query(func.count(WPS.id)).filter(
            WPS.user_id == user.id,
            WPS.company_id == employee.company_id,
            WPS.workspace_type == WorkspaceType.ENTERPRISE
        ).scalar() or 0

        pqr_user_enterprise = db.query(func.count(PQR.id)).filter(
            PQR.user_id == user.id,
            PQR.company_id == employee.company_id,
            PQR.workspace_type == WorkspaceType.ENTERPRISE
        ).scalar() or 0

        ppqr_user_enterprise = db.query(func.count(PPQR.id)).filter(
            PPQR.user_id == user.id,
            PPQR.company_id == employee.company_id,
            PPQR.workspace_type == WorkspaceType.ENTERPRISE
        ).scalar() or 0

        welders_user_enterprise = db.query(func.count(Welder.id)).filter(
            Welder.user_id == user.id,
            Welder.company_id == employee.company_id,
            Welder.workspace_type == WorkspaceType.ENTERPRISE
        ).scalar() or 0

        print(f"用户企业数据:")
        print(f"  WPS: {wps_user_enterprise}")
        print(f"  PQR: {pqr_user_enterprise}")
        print(f"  PPQR: {ppqr_user_enterprise}")
        print(f"  焊工: {welders_user_enterprise}")

        # 统计个人工作区数据
        print(f"\n=== 个人工作区数据（用户ID: {user.id}） ===")

        wps_personal = db.query(func.count(WPS.id)).filter(
            WPS.user_id == user.id,
            WPS.workspace_type == WorkspaceType.PERSONAL
        ).scalar() or 0

        pqr_personal = db.query(func.count(PQR.id)).filter(
            PQR.user_id == user.id,
            PQR.workspace_type == WorkspaceType.PERSONAL
        ).scalar() or 0

        ppqr_personal = db.query(func.count(PPQR.id)).filter(
            PPQR.user_id == user.id,
            PPQR.workspace_type == WorkspaceType.PERSONAL
        ).scalar() or 0

        welders_personal = db.query(func.count(Welder.id)).filter(
            Welder.user_id == user.id,
            Welder.workspace_type == WorkspaceType.PERSONAL
        ).scalar() or 0

        print(f"个人数据:")
        print(f"  WPS: {wps_personal}")
        print(f"  PQR: {pqr_personal}")
        print(f"  PPQR: {ppqr_personal}")
        print(f"  焊工: {welders_personal}")

        # 显示详细的记录信息
        print(f"\n=== 详细的企业工作区记录 ===")

        # WPS记录详情
        wps_records = db.query(WPS).filter(
            WPS.company_id == employee.company_id,
            WPS.workspace_type == WorkspaceType.ENTERPRISE
        ).limit(10).all()

        print(f"\nWPS记录（前10条）:")
        for wps in wps_records:
            print(f"  - {wps.wps_number} (用户ID: {wps.user_id}, 创建者: {wps.created_by})")

        # PQR记录详情
        pqr_records = db.query(PQR).filter(
            PQR.company_id == employee.company_id,
            PQR.workspace_type == WorkspaceType.ENTERPRISE
        ).limit(10).all()

        print(f"\nPQR记录（前10条）:")
        for pqr in pqr_records:
            print(f"  - {pqr.pqr_number} (用户ID: {pqr.user_id}, 创建者: {pqr.created_by})")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_enterprise_workspace()