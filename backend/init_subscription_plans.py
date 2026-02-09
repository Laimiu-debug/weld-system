"""
初始化订阅计划脚本
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.subscription import SubscriptionPlan
from app.core.config import settings


def init_subscription_plans():
    """初始化订阅计划数据"""
    db: Session = SessionLocal()
    
    try:
        # 检查是否已有订阅计划
        existing_plans = db.query(SubscriptionPlan).count()
        if existing_plans > 0:
            print(f"数据库中已有 {existing_plans} 个订阅计划，跳过初始化")
            return
        
        # 订阅计划数据
        plans_data = [
            {
                "id": "free",
                "name": "个人免费版",
                "description": "基础功能，适合个人用户试用",
                "monthly_price": 0,
                "quarterly_price": 0,
                "yearly_price": 0,
                "currency": "CNY",
                "max_wps_files": 10,
                "max_pqr_files": 10,
                "max_ppqr_files": 0,
                "max_materials": 0,
                "max_welders": 0,
                "max_equipment": 0,
                "max_factories": 0,
                "max_employees": 0,
                "features": "WPS管理模块（10个）,PQR管理模块（10个）",
                "sort_order": 1,
                "is_recommended": False,
                "is_active": True
            },
            {
                "id": "personal_pro",
                "name": "个人专业版",
                "description": "适合个人专业用户，包含基础管理功能",
                "monthly_price": 19,
                "quarterly_price": 51,
                "yearly_price": 183,
                "currency": "CNY",
                "max_wps_files": 30,
                "max_pqr_files": 30,
                "max_ppqr_files": 30,
                "max_materials": 50,
                "max_welders": 20,
                "max_equipment": 0,
                "max_factories": 0,
                "max_employees": 0,
                "features": "WPS管理模块（30个）,PQR管理模块（30个）,pPQR管理模块（30个）,焊材管理模块,焊工管理模块",
                "sort_order": 2,
                "is_recommended": True,
                "is_active": True
            },
            {
                "id": "personal_advanced",
                "name": "个人高级版",
                "description": "适合需要高级功能的个人用户",
                "monthly_price": 49,
                "quarterly_price": 132,
                "yearly_price": 470,
                "currency": "CNY",
                "max_wps_files": 50,
                "max_pqr_files": 50,
                "max_ppqr_files": 50,
                "max_materials": 100,
                "max_welders": 50,
                "max_equipment": 20,
                "max_factories": 0,
                "max_employees": 0,
                "features": "WPS管理模块（50个）,PQR管理模块（50个）,pPQR管理模块（50个）,焊材管理模块,焊工管理模块,生产管理模块,设备管理模块,质量管理模块",
                "sort_order": 3,
                "is_recommended": False,
                "is_active": True
            },
            {
                "id": "personal_flagship",
                "name": "个人旗舰版",
                "description": "个人用户最全功能版本",
                "monthly_price": 99,
                "quarterly_price": 267,
                "yearly_price": 950,
                "currency": "CNY",
                "max_wps_files": 100,
                "max_pqr_files": 100,
                "max_ppqr_files": 100,
                "max_materials": 200,
                "max_welders": 100,
                "max_equipment": 50,
                "max_factories": 0,
                "max_employees": 0,
                "features": "WPS管理模块（100个）,PQR管理模块（100个）,pPQR管理模块（100个）,焊材管理模块,焊工管理模块,生产管理模块,设备管理模块,质量管理模块,报表统计模块",
                "sort_order": 4,
                "is_recommended": False,
                "is_active": True
            },
            {
                "id": "enterprise",
                "name": "企业版",
                "description": "适合小型企业，包含员工管理功能",
                "monthly_price": 199,
                "quarterly_price": 537,
                "yearly_price": 1910,
                "currency": "CNY",
                "max_wps_files": 200,
                "max_pqr_files": 200,
                "max_ppqr_files": 200,
                "max_materials": 500,
                "max_welders": 200,
                "max_equipment": 100,
                "max_factories": 1,
                "max_employees": 10,
                "features": "WPS管理模块（200个）,PQR管理模块（200个）,pPQR管理模块（200个）,焊材管理模块,焊工管理模块,生产管理模块,设备管理模块,质量管理模块,报表统计模块,企业员工管理模块（10人）,多工厂数量：1个",
                "sort_order": 5,
                "is_recommended": False,
                "is_active": True
            },
            {
                "id": "enterprise_pro",
                "name": "企业版PRO",
                "description": "适合中型企业，更多员工和工厂",
                "monthly_price": 399,
                "quarterly_price": 1077,
                "yearly_price": 3830,
                "currency": "CNY",
                "max_wps_files": 400,
                "max_pqr_files": 400,
                "max_ppqr_files": 400,
                "max_materials": 1000,
                "max_welders": 500,
                "max_equipment": 200,
                "max_factories": 3,
                "max_employees": 20,
                "features": "WPS管理模块（400个）,PQR管理模块（400个）,pPQR管理模块（400个）,焊材管理模块,焊工管理模块,生产管理模块,设备管理模块,质量管理模块,报表统计模块,企业员工管理模块（20人）,多工厂数量：3个",
                "sort_order": 6,
                "is_recommended": False,
                "is_active": True
            },
            {
                "id": "enterprise_pro_max",
                "name": "企业版PRO MAX",
                "description": "适合大型企业，最全功能和最高配额",
                "monthly_price": 899,
                "quarterly_price": 2427,
                "yearly_price": 8630,
                "currency": "CNY",
                "max_wps_files": 500,
                "max_pqr_files": 500,
                "max_ppqr_files": 500,
                "max_materials": 2000,
                "max_welders": 1000,
                "max_equipment": 500,
                "max_factories": 5,
                "max_employees": 50,
                "features": "WPS管理模块（500个）,PQR管理模块（500个）,pPQR管理模块（500个）,焊材管理模块,焊工管理模块,生产管理模块,设备管理模块,质量管理模块,报表统计模块,企业员工管理模块（50人）,多工厂数量：5个",
                "sort_order": 7,
                "is_recommended": False,
                "is_active": True
            }
        ]
        
        # 创建订阅计划
        created_count = 0
        for plan_data in plans_data:
            plan = SubscriptionPlan(**plan_data)
            db.add(plan)
            created_count += 1
            
        db.commit()
        
        print(f"成功初始化 {created_count} 个订阅计划")
        
        # 显示创建的计划
        print("\n已创建的订阅计划:")
        plans = db.query(SubscriptionPlan).order_by(SubscriptionPlan.sort_order).all()
        for plan in plans:
            print(f"- {plan.name} ({plan.id}): ¥{plan.monthly_price}/月")
        
    except Exception as e:
        print(f"初始化订阅计划失败: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("开始初始化订阅计划...")
    init_subscription_plans()
    print("订阅计划初始化完成")