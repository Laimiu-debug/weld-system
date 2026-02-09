#!/usr/bin/env python3
"""
检查所有用户的统计数据
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

def check_all_users_stats():
    """检查所有用户的统计数据"""
    db = SessionLocal()
    try:
        print("=== 检查所有用户的统计数据 ===\n")

        # 检查用户
        users = db.query(User).all()
        print(f"总用户数: {len(users)}")

        total_wps = 0
        total_pqr = 0
        total_ppqr = 0
        total_welders = 0

        for user in users:
            # 统计各类型数据（不分工作区类型）
            wps_count = db.query(func.count(WPS.id)).filter(WPS.user_id == user.id).scalar() or 0
            pqr_count = db.query(func.count(PQR.id)).filter(PQR.user_id == user.id).scalar() or 0
            ppqr_count = db.query(func.count(PPQR.id)).filter(PPQR.user_id == user.id).scalar() or 0
            welders_count = db.query(func.count(Welder.id)).filter(Welder.user_id == user.id).scalar() or 0

            total_wps += wps_count
            total_pqr += pqr_count
            total_ppqr += ppqr_count
            total_welders += welders_count

            if wps_count > 0 or pqr_count > 0 or ppqr_count > 0 or welders_count > 0:
                print(f"用户: {user.username} (ID: {user.id}, 会员等级: {user.member_tier})")
                print(f"  WPS: {wps_count}, PQR: {pqr_count}, PPQR: {ppqr_count}, 焊工: {welders_count}")
                print(f"  配额 - WPS已用: {user.wps_quota_used}, PQR已用: {user.pqr_quota_used}, PPQR已用: {user.ppqr_quota_used}")
                print()

        print(f"\n=== 总计统计 ===")
        print(f"WPS总计: {total_wps}")
        print(f"PQR总计: {total_pqr}")
        print(f"PPQR总计: {total_ppqr}")
        print(f"焊工总计: {total_welders}")

        print(f"\n=== 按工作区类型统计 ===")

        # 统计所有WPS按工作区类型
        all_wps_personal = db.query(func.count(WPS.id)).filter(WPS.workspace_type == WorkspaceType.PERSONAL).scalar() or 0
        all_wps_enterprise = db.query(func.count(WPS.id)).filter(WPS.workspace_type == WorkspaceType.ENTERPRISE).scalar() or 0
        all_wps_null = db.query(func.count(WPS.id)).filter(WPS.workspace_type.is_(None)).scalar() or 0

        print(f"WPS - 个人工作区: {all_wps_personal}, 企业工作区: {all_wps_enterprise}, workspace_type为空: {all_wps_null}")

        # 统计所有PQR按工作区类型
        all_pqr_personal = db.query(func.count(PQR.id)).filter(PQR.workspace_type == WorkspaceType.PERSONAL).scalar() or 0
        all_pqr_enterprise = db.query(func.count(PQR.id)).filter(PQR.workspace_type == WorkspaceType.ENTERPRISE).scalar() or 0
        all_pqr_null = db.query(func.count(PQR.id)).filter(PQR.workspace_type.is_(None)).scalar() or 0

        print(f"PQR - 个人工作区: {all_pqr_personal}, 企业工作区: {all_pqr_enterprise}, workspace_type为空: {all_pqr_null}")

        # 统计所有焊工按工作区类型
        all_welders_personal = db.query(func.count(Welder.id)).filter(Welder.workspace_type == WorkspaceType.PERSONAL).scalar() or 0
        all_welders_enterprise = db.query(func.count(Welder.id)).filter(Welder.workspace_type == WorkspaceType.ENTERPRISE).scalar() or 0
        all_welders_null = db.query(func.count(Welder.id)).filter(Welder.workspace_type.is_(None)).scalar() or 0

        print(f"焊工 - 个人工作区: {all_welders_personal}, 企业工作区: {all_welders_enterprise}, workspace_type为空: {all_welders_null}")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_all_users_stats()