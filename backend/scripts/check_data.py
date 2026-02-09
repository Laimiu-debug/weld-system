"""检查企业和用户数据"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.company import Company
from sqlalchemy import text

db = SessionLocal()
try:
    # 查询企业ID 1和4的信息
    companies = db.query(Company).filter(Company.id.in_([1, 4])).all()
    
    print('=' * 80)
    print('企业配额信息检查')
    print('=' * 80)
    
    for company in companies:
        print(f'\n企业ID: {company.id}')
        print(f'企业名称: {company.name}')
        print(f'会员等级: {company.membership_tier}')
        print(f'最大员工数: {company.max_employees}')
        print(f'最大工厂数: {company.max_factories}')
        print(f'订阅状态: {company.subscription_status}')
        print(f'订阅开始日期: {company.subscription_start_date}')
        print(f'订阅结束日期: {company.subscription_end_date}')
        print(f'自动续费: {company.auto_renewal}')
        print('-' * 80)
    
    # 查询testuser176070001@example.com用户信息
    print('\n' + '=' * 80)
    print('用户信息检查: testuser176070001@example.com')
    print('=' * 80)

    result = db.execute(text("""
        SELECT
            id, email, username, member_tier, membership_type,
            subscription_status, subscription_start_date, subscription_end_date, auto_renewal,
            company
        FROM users
        WHERE email = 'testuser176070001@example.com'
    """))

    user = result.fetchone()
    if user:
        print(f'用户ID: {user.id}')
        print(f'邮箱: {user.email}')
        print(f'用户名: {user.username}')
        print(f'会员等级: {user.member_tier}')
        print(f'会员类型: {user.membership_type}')
        print(f'订阅状态: {user.subscription_status}')
        print(f'订阅开始日期: {user.subscription_start_date}')
        print(f'订阅结束日期: {user.subscription_end_date}')
        print(f'自动续费: {user.auto_renewal}')
        print(f'公司字段: {user.company}')
    else:
        print('未找到该用户')
    
finally:
    db.close()

