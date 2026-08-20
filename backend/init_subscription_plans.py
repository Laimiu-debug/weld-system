"""
初始化订阅计划脚本
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.services.subscription_plan_seed import ensure_subscription_plans


def init_subscription_plans():
    """初始化订阅计划数据"""
    db = SessionLocal()
    try:
        created = ensure_subscription_plans(db)
        if created == 0:
            from app.models.subscription import SubscriptionPlan

            existing = db.query(SubscriptionPlan).count()
            print(f"数据库中已有 {existing} 个订阅计划，跳过初始化")
            return

        print(f"成功初始化 {created} 个订阅计划")
        from app.models.subscription import SubscriptionPlan

        plans = db.query(SubscriptionPlan).order_by(SubscriptionPlan.sort_order).all()
        print("\n已创建的订阅计划:")
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
