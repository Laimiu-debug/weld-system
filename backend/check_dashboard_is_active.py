#!/usr/bin/env python3
"""
检查仪表盘统计中 is_active 字段的影响
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

def check_is_active_impact():
    """检查 is_active 字段对统计的影响"""
    db = SessionLocal()
    try:
        print("=== 检查用户 testuser176070001 的仪表盘统计数据 ===\n")

        # 查找用户
        user = db.query(User).filter(User.username == "testuser176070001").first()
        if not user:
            print("用户 testuser176070001 不存在")
            return

        print(f"用户: {user.username} (ID: {user.id})")

        # 查找企业员工信息
        employee = db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == user.id,
            CompanyEmployee.status == "active"
        ).first()

        if not employee:
            print("❌ 未找到活跃的企业员工记录")
            return

        print(f"企业ID: {employee.company_id}\n")

        # 统计企业工作区数据（不过滤 is_active）
        print("=== 不过滤 is_active 的统计（当前仪表盘的统计方式） ===")
        wps_all = db.query(func.count(WPS.id)).filter(
            WPS.company_id == employee.company_id,
            WPS.workspace_type == WorkspaceType.ENTERPRISE
        ).scalar() or 0

        pqr_all = db.query(func.count(PQR.id)).filter(
            PQR.company_id == employee.company_id,
            PQR.workspace_type == WorkspaceType.ENTERPRISE
        ).scalar() or 0

        ppqr_all = db.query(func.count(PPQR.id)).filter(
            PPQR.company_id == employee.company_id,
            PPQR.workspace_type == WorkspaceType.ENTERPRISE
        ).scalar() or 0

        welder_all = db.query(func.count(Welder.id)).filter(
            Welder.company_id == employee.company_id,
            Welder.workspace_type == WorkspaceType.ENTERPRISE
        ).scalar() or 0

        print(f"WPS: {wps_all}")
        print(f"PQR: {pqr_all}")
        print(f"pPQR: {ppqr_all}")
        print(f"焊工: {welder_all}")

        # 统计企业工作区数据（过滤 is_active=True）
        print("\n=== 过滤 is_active=True 的统计（应该显示的数据） ===")
        wps_active = db.query(func.count(WPS.id)).filter(
            WPS.company_id == employee.company_id,
            WPS.workspace_type == WorkspaceType.ENTERPRISE,
            WPS.is_active == True
        ).scalar() or 0

        pqr_active = db.query(func.count(PQR.id)).filter(
            PQR.company_id == employee.company_id,
            PQR.workspace_type == WorkspaceType.ENTERPRISE,
            PQR.is_active == True
        ).scalar() or 0

        ppqr_active = db.query(func.count(PPQR.id)).filter(
            PPQR.company_id == employee.company_id,
            PPQR.workspace_type == WorkspaceType.ENTERPRISE,
            PPQR.is_active == True
        ).scalar() or 0

        welder_active = db.query(func.count(Welder.id)).filter(
            Welder.company_id == employee.company_id,
            Welder.workspace_type == WorkspaceType.ENTERPRISE,
            Welder.is_active == True
        ).scalar() or 0

        print(f"WPS: {wps_active}")
        print(f"PQR: {pqr_active}")
        print(f"pPQR: {ppqr_active}")
        print(f"焊工: {welder_active}")

        # 显示差异
        print("\n=== 差异（已删除但仍被统计的记录） ===")
        wps_diff = wps_all - wps_active
        pqr_diff = pqr_all - pqr_active
        ppqr_diff = ppqr_all - ppqr_active
        welder_diff = welder_all - welder_active

        print(f"WPS: {wps_diff} 条已删除记录")
        print(f"PQR: {pqr_diff} 条已删除记录")
        print(f"pPQR: {ppqr_diff} 条已删除记录")
        print(f"焊工: {welder_diff} 条已删除记录")

        # 显示已删除的记录详情
        if wps_diff > 0:
            print("\n=== 已删除的 WPS 记录详情 ===")
            deleted_wps = db.query(WPS).filter(
                WPS.company_id == employee.company_id,
                WPS.workspace_type == WorkspaceType.ENTERPRISE,
                WPS.is_active == False
            ).all()
            for wps in deleted_wps:
                print(f"  - {wps.wps_number} (ID: {wps.id}, 用户ID: {wps.user_id})")

        if pqr_diff > 0:
            print("\n=== 已删除的 PQR 记录详情 ===")
            deleted_pqr = db.query(PQR).filter(
                PQR.company_id == employee.company_id,
                PQR.workspace_type == WorkspaceType.ENTERPRISE,
                PQR.is_active == False
            ).all()
            for pqr in deleted_pqr:
                print(f"  - {pqr.pqr_number} (ID: {pqr.id}, 用户ID: {pqr.user_id})")

        if ppqr_diff > 0:
            print("\n=== 已删除的 pPQR 记录详情 ===")
            deleted_ppqr = db.query(PPQR).filter(
                PPQR.company_id == employee.company_id,
                PPQR.workspace_type == WorkspaceType.ENTERPRISE,
                PPQR.is_active == False
            ).all()
            for ppqr in deleted_ppqr:
                print(f"  - {ppqr.ppqr_number} (ID: {ppqr.id}, 用户ID: {ppqr.user_id})")

        if welder_diff > 0:
            print("\n=== 已删除的焊工记录详情 ===")
            deleted_welders = db.query(Welder).filter(
                Welder.company_id == employee.company_id,
                Welder.workspace_type == WorkspaceType.ENTERPRISE,
                Welder.is_active == False
            ).all()
            for welder in deleted_welders:
                print(f"  - {welder.welder_code} {welder.full_name} (ID: {welder.id}, 用户ID: {welder.user_id})")

        # 总结
        print("\n=== 问题总结 ===")
        if wps_diff > 0 or pqr_diff > 0 or ppqr_diff > 0 or welder_diff > 0:
            print("✗ 发现问题：仪表盘统计包含了已删除的记录")
            print("  原因：dashboard_service.py 中的统计查询没有过滤 is_active=False 的记录")
            print("  解决方案：在所有统计查询中添加 is_active=True 过滤条件")
        else:
            print("✓ 未发现已删除记录被统计的问题")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_is_active_impact()

