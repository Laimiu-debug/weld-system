"""
更新企业配额限制脚本

根据 MEMBERSHIP_TIERS_CORRECTION.md 文档更新企业配额：
- 企业版：10人员工，1个工厂
- 企业版PRO：20人员工，3个工厂
- 企业版PRO MAX：50人员工，5个工厂
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.company import Company


def get_tier_limits(tier: str) -> dict:
    """根据会员等级获取配额限制"""
    limits = {
        "enterprise": {
            "max_factories": 1,
            "max_employees": 10,
            "max_wps_records": 200,
            "max_pqr_records": 200
        },
        "enterprise_pro": {
            "max_factories": 3,
            "max_employees": 20,
            "max_wps_records": 400,
            "max_pqr_records": 400
        },
        "enterprise_pro_max": {
            "max_factories": 5,
            "max_employees": 50,
            "max_wps_records": 500,
            "max_pqr_records": 500
        }
    }
    return limits.get(tier, limits["enterprise"])


def update_enterprise_quotas(db: Session):
    """更新所有企业的配额限制"""
    print("开始更新企业配额限制...")
    
    # 获取所有企业
    companies = db.query(Company).all()
    
    updated_count = 0
    for company in companies:
        tier = company.membership_tier or "enterprise"
        limits = get_tier_limits(tier)
        
        # 检查是否需要更新
        needs_update = False
        
        if company.max_employees != limits["max_employees"]:
            print(f"企业 {company.name} (ID: {company.id}): 更新员工配额 {company.max_employees} -> {limits['max_employees']}")
            company.max_employees = limits["max_employees"]
            needs_update = True
        
        if company.max_factories != limits["max_factories"]:
            print(f"企业 {company.name} (ID: {company.id}): 更新工厂配额 {company.max_factories} -> {limits['max_factories']}")
            company.max_factories = limits["max_factories"]
            needs_update = True
        
        if company.max_wps_records != limits["max_wps_records"]:
            print(f"企业 {company.name} (ID: {company.id}): 更新WPS配额 {company.max_wps_records} -> {limits['max_wps_records']}")
            company.max_wps_records = limits["max_wps_records"]
            needs_update = True
        
        if company.max_pqr_records != limits["max_pqr_records"]:
            print(f"企业 {company.name} (ID: {company.id}): 更新PQR配额 {company.max_pqr_records} -> {limits['max_pqr_records']}")
            company.max_pqr_records = limits["max_pqr_records"]
            needs_update = True
        
        if needs_update:
            updated_count += 1
    
    # 提交更改
    db.commit()
    
    print(f"\n更新完成！共更新 {updated_count} 个企业的配额限制。")
    print(f"总企业数: {len(companies)}")


def main():
    """主函数"""
    db = SessionLocal()
    try:
        update_enterprise_quotas(db)
    except Exception as e:
        print(f"错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

