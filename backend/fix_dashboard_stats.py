#!/usr/bin/env python3
"""
修复仪表盘统计数据问题
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.user import User
from app.models.wps import WPS
from app.models.pqr import PQR
from app.models.ppqr import PPQR
from app.models.welder import Welder
from app.core.data_access import WorkspaceType

def fix_dashboard_stats():
    """修复仪表盘统计数据"""
    db = SessionLocal()
    try:
        print("=== 修复仪表盘统计数据 ===\n")

        # 检查用户
        users = db.query(User).all()
        print(f"总用户数: {len(users)}")

        for user in users:
            print(f"\n--- 修复用户: {user.username} (ID: {user.id}, 会员等级: {user.member_tier}) ---")

            # 修复配额数据 - 统计该用户的所有记录（不按工作区类型过滤）
            wps_count = db.query(func.count(WPS.id)).filter(WPS.user_id == user.id).scalar() or 0
            pqr_count = db.query(func.count(PQR.id)).filter(PQR.user_id == user.id).scalar() or 0
            ppqr_count = db.query(func.count(PPQR.id)).filter(PPQR.user_id == user.id).scalar() or 0
            welders_count = db.query(func.count(Welder.id)).filter(Welder.user_id == user.id).scalar() or 0

            print(f"实际统计: WPS={wps_count}, PQR={pqr_count}, PPQR={ppqr_count}, 焊工={welders_count}")
            print(f"当前配额: WPS={user.wps_quota_used}, PQR={user.pqr_quota_used}, PPQR={user.ppqr_quota_used}")

            # 更新用户的配额数据
            old_wps_quota = user.wps_quota_used or 0
            old_pqr_quota = user.pqr_quota_used or 0
            old_ppqr_quota = user.ppqr_quota_used or 0

            user.wps_quota_used = wps_count
            user.pqr_quota_used = pqr_count
            user.ppqr_quota_used = ppqr_count

            print(f"更新配额: WPS {old_wps_quota} -> {wps_count}, PQR {old_pqr_quota} -> {pqr_count}, PPQR {old_ppqr_quota} -> {ppqr_count}")

            # 修复workspace_type字段 - 为没有workspace_type的记录设置默认值
            if user.membership_type == "enterprise":
                # 企业用户，查找企业信息
                from app.models.company import CompanyEmployee
                employee = db.query(CompanyEmployee).filter(
                    CompanyEmployee.user_id == user.id,
                    CompanyEmployee.status == "active"
                ).first()

                if employee:
                    # 企业用户，设置为企业工作区
                    wps_null_workspace = db.query(WPS).filter(
                        WPS.user_id == user.id,
                        WPS.workspace_type.is_(None)
                    ).all()
                    pqr_null_workspace = db.query(PQR).filter(
                        PQR.user_id == user.id,
                        PQR.workspace_type.is_(None)
                    ).all()
                    ppqr_null_workspace = db.query(PPQR).filter(
                        PPQR.user_id == user.id,
                        PPQR.workspace_type.is_(None)
                    ).all()
                    welders_null_workspace = db.query(Welder).filter(
                        Welder.user_id == user.id,
                        Welder.workspace_type.is_(None)
                    ).all()

                    # 更新为企业工作区
                    for wps in wps_null_workspace:
                        wps.workspace_type = WorkspaceType.ENTERPRISE
                        wps.company_id = employee.company_id
                        wps.factory_id = employee.factory_id

                    for pqr in pqr_null_workspace:
                        pqr.workspace_type = WorkspaceType.ENTERPRISE
                        pqr.company_id = employee.company_id
                        pqr.factory_id = employee.factory_id

                    for ppqr in ppqr_null_workspace:
                        ppqr.workspace_type = WorkspaceType.ENTERPRISE
                        ppqr.company_id = employee.company_id
                        ppqr.factory_id = employee.factory_id

                    for welder in welders_null_workspace:
                        welder.workspace_type = WorkspaceType.ENTERPRISE
                        welder.company_id = employee.company_id
                        welder.factory_id = employee.factory_id

                    print(f"修复了 {len(wps_null_workspace)} WPS, {len(pqr_null_workspace)} PQR, {len(ppqr_null_workspace)} PPQR, {len(welders_null_workspace)} 焊工的工作区类型为企业")
                else:
                    # 找不到企业信息，设置为个人工作区
                    wps_null_workspace = db.query(WPS).filter(
                        WPS.user_id == user.id,
                        WPS.workspace_type.is_(None)
                    ).all()
                    pqr_null_workspace = db.query(PQR).filter(
                        PQR.user_id == user.id,
                        PQR.workspace_type.is_(None)
                    ).all()
                    ppqr_null_workspace = db.query(PPQR).filter(
                        PPQR.user_id == user.id,
                        PPQR.workspace_type.is_(None)
                    ).all()
                    welders_null_workspace = db.query(Welder).filter(
                        Welder.user_id == user.id,
                        Welder.workspace_type.is_(None)
                    ).all()

                    # 更新为个人工作区
                    for wps in wps_null_workspace:
                        wps.workspace_type = WorkspaceType.PERSONAL

                    for pqr in pqr_null_workspace:
                        pqr.workspace_type = WorkspaceType.PERSONAL

                    for ppqr in ppqr_null_workspace:
                        ppqr.workspace_type = WorkspaceType.PERSONAL

                    for welder in welders_null_workspace:
                        welder.workspace_type = WorkspaceType.PERSONAL

                    print(f"修复了 {len(wps_null_workspace)} WPS, {len(pqr_null_workspace)} PQR, {len(ppqr_null_workspace)} PPQR, {len(welders_null_workspace)} 焊工的工作区类型为个人")
            else:
                # 个人用户，设置为个人工作区
                wps_null_workspace = db.query(WPS).filter(
                    WPS.user_id == user.id,
                    WPS.workspace_type.is_(None)
                ).all()
                pqr_null_workspace = db.query(PQR).filter(
                    PQR.user_id == user.id,
                    PQR.workspace_type.is_(None)
                ).all()
                ppqr_null_workspace = db.query(PPQR).filter(
                    PPQR.user_id == user.id,
                    PPQR.workspace_type.is_(None)
                ).all()
                welders_null_workspace = db.query(Welder).filter(
                    Welder.user_id == user.id,
                    Welder.workspace_type.is_(None)
                ).all()

                # 更新为个人工作区
                for wps in wps_null_workspace:
                    wps.workspace_type = WorkspaceType.PERSONAL

                for pqr in pqr_null_workspace:
                    pqr.workspace_type = WorkspaceType.PERSONAL

                for ppqr in ppqr_null_workspace:
                    ppqr.workspace_type = WorkspaceType.PERSONAL

                for welder in welders_null_workspace:
                    welder.workspace_type = WorkspaceType.PERSONAL

                print(f"修复了 {len(wps_null_workspace)} WPS, {len(pqr_null_workspace)} PQR, {len(ppqr_null_workspace)} PPQR, {len(welders_null_workspace)} 焊工的工作区类型为个人")

        # 提交所有更改
        db.commit()
        print("\n=== 所有修复已完成并提交到数据库 ===")

    except Exception as e:
        print(f"错误: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fix_dashboard_stats()