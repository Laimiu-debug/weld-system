"""测试会员信息获取"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.services.membership_service import MembershipService
from app.models.user import User
import json

db = SessionLocal()
try:
    print('=' * 80)
    print('测试会员信息获取')
    print('=' * 80)
    
    # 查询 testuser176070001@example.com 用户
    user = db.query(User).filter(User.email == 'testuser176070001@example.com').first()
    
    if user:
        print(f'\n用户: {user.email}')
        print(f'会员等级: {user.member_tier}')
        print(f'会员类型: {user.membership_type}')
        
        # 获取会员信息
        membership_service = MembershipService(db)
        membership_info = membership_service.get_user_membership_info(user.id)
        
        if membership_info:
            print(f'\n会员信息:')
            print(json.dumps(membership_info, indent=2, ensure_ascii=False, default=str))
        else:
            print('\n❌ 未获取到会员信息')
    else:
        print('未找到该用户')
    
finally:
    db.close()

