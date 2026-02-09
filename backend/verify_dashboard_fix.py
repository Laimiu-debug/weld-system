#!/usr/bin/env python3
"""
验证仪表盘统计修复
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import CompanyEmployee
from app.services.dashboard_service import DashboardService
from app.core.data_access import WorkspaceContext

def verify_dashboard_fix():
    """验证仪表盘统计修复"""
    db = SessionLocal()
    try:
        print("=== 验证仪表盘统计修复 ===\n")

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

        # 创建工作区上下文
        workspace_context = WorkspaceContext(
            user_id=user.id,
            workspace_type="enterprise",
            company_id=employee.company_id,
            factory_id=employee.factory_id
        )

        # 使用 DashboardService 获取统计数据
        dashboard_service = DashboardService(db)
        stats = dashboard_service.get_overview_stats(user, workspace_context)

        print("=== 仪表盘统计结果（修复后） ===")
        print(f"WPS: {stats.get('wps_count', 0)}")
        print(f"PQR: {stats.get('pqr_count', 0)}")
        print(f"pPQR: {stats.get('ppqr_count', 0)}")
        print(f"焊工: {stats.get('welders_count', 0)}")
        print(f"焊材: {stats.get('materials_count', 0)}")
        print(f"设备: {stats.get('equipment_count', 0)}")
        print(f"生产任务: {stats.get('production_count', 0)}")
        print(f"质量检验: {stats.get('quality_count', 0)}")

        print("\n=== 预期结果 ===")
        print("WPS: 4")
        print("PQR: 3")
        print("pPQR: 2")
        print("焊工: 1")

        print("\n=== 验证结果 ===")
        if (stats.get('wps_count', 0) == 4 and 
            stats.get('pqr_count', 0) == 3 and 
            stats.get('ppqr_count', 0) == 2 and 
            stats.get('welders_count', 0) == 1):
            print("✓ 修复成功！仪表盘统计数据正确")
        else:
            print("✗ 修复失败！仪表盘统计数据仍然不正确")
            print(f"  实际: WPS={stats.get('wps_count', 0)}, PQR={stats.get('pqr_count', 0)}, pPQR={stats.get('ppqr_count', 0)}, 焊工={stats.get('welders_count', 0)}")
            print(f"  预期: WPS=4, PQR=3, pPQR=2, 焊工=1")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_dashboard_fix()

