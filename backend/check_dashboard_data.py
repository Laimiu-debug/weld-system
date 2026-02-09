#!/usr/bin/env python3
"""
检查仪表盘数据的实际统计
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.wps import WPS
from app.models.pqr import PQR
from app.models.ppqr import PPQR
from app.models.welder import Welder
from app.core.data_access import WorkspaceType

def check_dashboard_data():
    """检查仪表盘数据的实际统计"""
    db = SessionLocal()
    try:
        print("=== 检查仪表盘数据统计 ===\n")

        # 检查用户
        users = db.query(User).all()
        print(f"总用户数: {len(users)}")

        for user in users:
            print(f"\n--- 用户: {user.username} (ID: {user.id}, 会员等级: {user.member_tier}) ---")

            # 检查WPS记录
            wps_all = db.query(WPS).filter(WPS.user_id == user.id).all()
            wps_personal = db.query(WPS).filter(
                WPS.user_id == user.id,
                WPS.workspace_type == WorkspaceType.PERSONAL
            ).all()
            wps_enterprise = db.query(WPS).filter(
                WPS.user_id == user.id,
                WPS.workspace_type == WorkspaceType.ENTERPRISE
            ).all()
            wps_null = db.query(WPS).filter(
                WPS.user_id == user.id,
                WPS.workspace_type.is_(None)
            ).all()

            print(f"WPS统计:")
            print(f"  总数: {len(wps_all)}")
            print(f"  个人工作区: {len(wps_personal)}")
            print(f"  企业工作区: {len(wps_enterprise)}")
            print(f"  workspace_type为空: {len(wps_null)}")
            if wps_all:
                print(f"  WPS记录详情:")
                for wps in wps_all[:3]:  # 只显示前3条
                    print(f"    - {wps.wps_number} (workspace_type: {wps.workspace_type})")

            # 检查PQR记录
            pqr_all = db.query(PQR).filter(PQR.user_id == user.id).all()
            pqr_personal = db.query(PQR).filter(
                PQR.user_id == user.id,
                PQR.workspace_type == WorkspaceType.PERSONAL
            ).all()
            pqr_enterprise = db.query(PQR).filter(
                PQR.user_id == user.id,
                PQR.workspace_type == WorkspaceType.ENTERPRISE
            ).all()
            pqr_null = db.query(PQR).filter(
                PQR.user_id == user.id,
                PQR.workspace_type.is_(None)
            ).all()

            print(f"PQR统计:")
            print(f"  总数: {len(pqr_all)}")
            print(f"  个人工作区: {len(pqr_personal)}")
            print(f"  企业工作区: {len(pqr_enterprise)}")
            print(f"  workspace_type为空: {len(pqr_null)}")
            if pqr_all:
                print(f"  PQR记录详情:")
                for pqr in pqr_all[:3]:  # 只显示前3条
                    print(f"    - {pqr.pqr_number} (workspace_type: {pqr.workspace_type})")

            # 检查PPQR记录
            ppqr_all = db.query(PPQR).filter(PPQR.user_id == user.id).all()
            ppqr_personal = db.query(PPQR).filter(
                PPQR.user_id == user.id,
                PPQR.workspace_type == WorkspaceType.PERSONAL
            ).all()
            ppqr_enterprise = db.query(PPQR).filter(
                PPQR.user_id == user.id,
                PPQR.workspace_type == WorkspaceType.ENTERPRISE
            ).all()
            ppqr_null = db.query(PPQR).filter(
                PPQR.user_id == user.id,
                PPQR.workspace_type.is_(None)
            ).all()

            print(f"PPQR统计:")
            print(f"  总数: {len(ppqr_all)}")
            print(f"  个人工作区: {len(ppqr_personal)}")
            print(f"  企业工作区: {len(ppqr_enterprise)}")
            print(f"  workspace_type为空: {len(ppqr_null)}")
            if ppqr_all:
                print(f"  PPQR记录详情:")
                for ppqr in ppqr_all[:3]:  # 只显示前3条
                    print(f"    - {ppqr.ppqr_number} (workspace_type: {ppqr.workspace_type})")

            # 检查焊工记录
            welder_all = db.query(Welder).filter(Welder.user_id == user.id).all()
            welder_personal = db.query(Welder).filter(
                Welder.user_id == user.id,
                Welder.workspace_type == WorkspaceType.PERSONAL
            ).all()
            welder_enterprise = db.query(Welder).filter(
                Welder.user_id == user.id,
                Welder.workspace_type == WorkspaceType.ENTERPRISE
            ).all()
            welder_null = db.query(Welder).filter(
                Welder.user_id == user.id,
                Welder.workspace_type.is_(None)
            ).all()

            print(f"焊工统计:")
            print(f"  总数: {len(welder_all)}")
            print(f"  个人工作区: {len(welder_personal)}")
            print(f"  企业工作区: {len(welder_enterprise)}")
            print(f"  workspace_type为空: {len(welder_null)}")
            if welder_all:
                print(f"  焊工记录详情:")
                for welder in welder_all[:3]:  # 只显示前3条
                    print(f"    - {welder.name} (workspace_type: {welder.workspace_type})")

            # 检查用户配额
            print(f"用户配额:")
            print(f"  WPS配额已用: {user.wps_quota_used}")
            print(f"  PQR配额已用: {user.pqr_quota_used}")
            print(f"  PPQR配额已用: {user.ppqr_quota_used}")
            print(f"  存储配额已用: {user.storage_quota_used}MB")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_dashboard_data()