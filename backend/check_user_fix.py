#!/usr/bin/env python3
"""
检查修复后的用户数据
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

def check_user_fix():
    """检查修复后的用户数据"""
    db = SessionLocal()
    try:
        print("=== 检查修复后的用户数据 ===\n")

        # 检查用户 testuser176070002 (ID: 41)
        user = db.query(User).filter(User.username == "testuser176070002").first()
        if user:
            print(f"用户: {user.username} (ID: {user.id}, 会员等级: {user.member_tier})")

            # 统计各类型数据
            wps_count = db.query(func.count(WPS.id)).filter(WPS.user_id == user.id).scalar() or 0
            pqr_count = db.query(func.count(PQR.id)).filter(PQR.user_id == user.id).scalar() or 0
            ppqr_count = db.query(func.count(PPQR.id)).filter(PPQR.user_id == user.id).scalar() or 0
            welders_count = db.query(func.count(Welder.id)).filter(Welder.user_id == user.id).scalar() or 0

            print(f"实际统计: WPS={wps_count}, PQR={pqr_count}, PPQR={ppqr_count}, 焊工={welders_count}")
            print(f"配额数据: WPS={user.wps_quota_used}, PQR={user.pqr_quota_used}, PPQR={user.ppqr_quota_used}")

            # 按工作区类型统计
            wps_personal = db.query(func.count(WPS.id)).filter(
                WPS.user_id == user.id,
                WPS.workspace_type == WorkspaceType.PERSONAL
            ).scalar() or 0
            wps_enterprise = db.query(func.count(WPS.id)).filter(
                WPS.user_id == user.id,
                WPS.workspace_type == WorkspaceType.ENTERPRISE
            ).scalar() or 0

            pqr_personal = db.query(func.count(PQR.id)).filter(
                PQR.user_id == user.id,
                PQR.workspace_type == WorkspaceType.PERSONAL
            ).scalar() or 0
            pqr_enterprise = db.query(func.count(PQR.id)).filter(
                PQR.user_id == user.id,
                PQR.workspace_type == WorkspaceType.ENTERPRISE
            ).scalar() or 0

            print(f"工作区统计:")
            print(f"  WPS - 个人: {wps_personal}, 企业: {wps_enterprise}")
            print(f"  PQR - 个人: {pqr_personal}, 企业: {pqr_enterprise}")

        # 检查用户 testuser176070001 (ID: 21)
        user2 = db.query(User).filter(User.username == "testuser176070001").first()
        if user2:
            print(f"\n用户: {user2.username} (ID: {user2.id}, 会员等级: {user2.member_tier})")

            # 统计各类型数据
            wps_count = db.query(func.count(WPS.id)).filter(WPS.user_id == user2.id).scalar() or 0
            pqr_count = db.query(func.count(PQR.id)).filter(PQR.user_id == user2.id).scalar() or 0
            ppqr_count = db.query(func.count(PPQR.id)).filter(PPQR.user_id == user2.id).scalar() or 0
            welders_count = db.query(func.count(Welder.id)).filter(Welder.user_id == user2.id).scalar() or 0

            print(f"实际统计: WPS={wps_count}, PQR={pqr_count}, PPQR={ppqr_count}, 焊工={welders_count}")
            print(f"配额数据: WPS={user2.wps_quota_used}, PQR={user2.pqr_quota_used}, PPQR={user2.ppqr_quota_used}")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_user_fix()