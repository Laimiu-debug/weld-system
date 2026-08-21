#!/usr/bin/env python3
"""
测试仪表盘统计修复
验证修复后的仪表盘统计是否正确过滤了已删除的记录
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import CompanyEmployee
from app.models.wps import WPS
from app.models.pqr import PQR
from app.models.ppqr import PPQR
from app.models.welder import Welder
from app.services.dashboard_service import DashboardService
from app.core.data_access import WorkspaceContext, WorkspaceType
from sqlalchemy import func

def test_dashboard_stats_fix():
    """测试仪表盘统计修复"""
    db = SessionLocal()
    try:
        print("=== 测试仪表盘统计修复 ===\n")

        # 查找测试用户
        user = db.query(User).filter(User.username == "testuser176070001").first()
        if not user:
            print("❌ 测试失败：用户 testuser176070001 不存在")
            return False

        # 查找企业员工信息
        employee = db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == user.id,
            CompanyEmployee.status == "active"
        ).first()

        if not employee:
            print("❌ 测试失败：未找到活跃的企业员工记录")
            return False

        company_id = employee.company_id
        print(f"测试用户: {user.username} (ID: {user.id})")
        print(f"企业ID: {company_id}\n")

        # 手动统计活跃记录
        print("=== 手动统计活跃记录 ===")
        wps_active = db.query(func.count(WPS.id)).filter(
            WPS.company_id == company_id,
            WPS.workspace_type == WorkspaceType.ENTERPRISE,
            WPS.is_active == True
        ).scalar() or 0

        pqr_active = db.query(func.count(PQR.id)).filter(
            PQR.company_id == company_id,
            PQR.workspace_type == WorkspaceType.ENTERPRISE,
            PQR.is_active == True
        ).scalar() or 0

        ppqr_active = db.query(func.count(PPQR.id)).filter(
            PPQR.company_id == company_id,
            PPQR.workspace_type == WorkspaceType.ENTERPRISE,
            PPQR.is_active == True
        ).scalar() or 0

        welder_active = db.query(func.count(Welder.id)).filter(
            Welder.company_id == company_id,
            Welder.workspace_type == WorkspaceType.ENTERPRISE,
            Welder.is_active == True
        ).scalar() or 0

        print(f"WPS (活跃): {wps_active}")
        print(f"PQR (活跃): {pqr_active}")
        print(f"pPQR (活跃): {ppqr_active}")
        print(f"焊工 (活跃): {welder_active}")

        # 使用 DashboardService 获取统计
        print("\n=== DashboardService 统计结果 ===")
        workspace_context = WorkspaceContext(
            user_id=user.id,
            workspace_type="enterprise",
            company_id=company_id,
            factory_id=employee.factory_id
        )

        dashboard_service = DashboardService(db)
        stats = dashboard_service.get_overview_stats(user, workspace_context)

        print(f"WPS: {stats.get('wps_count', 0)}")
        print(f"PQR: {stats.get('pqr_count', 0)}")
        print(f"pPQR: {stats.get('ppqr_count', 0)}")
        print(f"焊工: {stats.get('welders_count', 0)}")

        # 验证结果
        print("\n=== 验证结果 ===")
        all_passed = True

        if stats.get('wps_count', 0) != wps_active:
            print(f"❌ WPS 统计不匹配: 预期 {wps_active}, 实际 {stats.get('wps_count', 0)}")
            all_passed = False
        else:
            print(f"✓ WPS 统计正确: {wps_active}")

        if stats.get('pqr_count', 0) != pqr_active:
            print(f"❌ PQR 统计不匹配: 预期 {pqr_active}, 实际 {stats.get('pqr_count', 0)}")
            all_passed = False
        else:
            print(f"✓ PQR 统计正确: {pqr_active}")

        if stats.get('ppqr_count', 0) != ppqr_active:
            print(f"❌ pPQR 统计不匹配: 预期 {ppqr_active}, 实际 {stats.get('ppqr_count', 0)}")
            all_passed = False
        else:
            print(f"✓ pPQR 统计正确: {ppqr_active}")

        if stats.get('welders_count', 0) != welder_active:
            print(f"❌ 焊工统计不匹配: 预期 {welder_active}, 实际 {stats.get('welders_count', 0)}")
            all_passed = False
        else:
            print(f"✓ 焊工统计正确: {welder_active}")

        # 测试个人工作区统计
        print("\n=== 测试个人工作区统计 ===")
        personal_workspace_context = WorkspaceContext(
            user_id=user.id,
            workspace_type="personal",
            company_id=None,
            factory_id=None
        )

        personal_stats = dashboard_service.get_overview_stats(user, personal_workspace_context)
        
        # 手动统计个人工作区活跃记录
        wps_personal_active = db.query(func.count(WPS.id)).filter(
            WPS.user_id == user.id,
            WPS.workspace_type == WorkspaceType.PERSONAL,
            WPS.is_active == True
        ).scalar() or 0

        if personal_stats.get('wps_count', 0) != wps_personal_active:
            print(f"❌ 个人工作区 WPS 统计不匹配: 预期 {wps_personal_active}, 实际 {personal_stats.get('wps_count', 0)}")
            all_passed = False
        else:
            print(f"✓ 个人工作区 WPS 统计正确: {wps_personal_active}")

        # 总结
        print("\n=== 测试总结 ===")
        if all_passed:
            print("✓ 所有测试通过！仪表盘统计修复成功")
            return True
        else:
            print("❌ 部分测试失败，请检查修复")
            return False

    except Exception as e:
        print(f"❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_dashboard_stats_fix()
    sys.exit(0 if success else 1)

