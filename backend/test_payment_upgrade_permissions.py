"""
测试支付升级后的权限更新
"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from app.models.user import User
from app.services.membership_tier_service import MembershipTierService
import json

db = SessionLocal()
try:
    # 获取测试用户
    user = db.query(User).filter(User.email == 'testuser176070002@example.com').first()
    if not user:
        print('用户不存在')
        sys.exit(1)
    
    print('=' * 80)
    print('测试支付升级后的权限更新')
    print('=' * 80)
    print()
    
    # 显示当前状态
    print('升级前:')
    print(f'  member_tier: {user.member_tier}')
    print(f'  membership_type: {user.membership_type}')
    
    if user.permissions:
        perms = json.loads(user.permissions) if isinstance(user.permissions, str) else user.permissions
        print(f'  permissions:')
        for key, value in perms.items():
            status = '✅' if value else '❌'
            print(f'    {status} {key}: {value}')
    else:
        print(f'  permissions: None')
    
    print()
    print('-' * 80)
    print('执行会员等级更新...')
    print('-' * 80)
    
    # 使用MembershipTierService更新会员等级
    tier_service = MembershipTierService(db)
    result = tier_service.update_user_tier(user.id)
    
    print(f'✅ 更新完成')
    print(f'  old_tier: {result["old_tier"]}')
    print(f'  new_tier: {result["new_tier"]}')
    print(f'  changed: {result["changed"]}')
    print()
    
    # 刷新用户数据
    db.expire_all()
    user = db.query(User).filter(User.email == 'testuser176070002@example.com').first()
    
    print('-' * 80)
    print('升级后:')
    print(f'  member_tier: {user.member_tier}')
    print(f'  membership_type: {user.membership_type}')
    
    if user.permissions:
        perms = json.loads(user.permissions) if isinstance(user.permissions, str) else user.permissions
        print(f'  permissions:')
        for key, value in perms.items():
            status = '✅' if value else '❌'
            print(f'    {status} {key}: {value}')
    else:
        print(f'  permissions: None')
    
    print()
    print('=' * 80)
    print('验证 personal_pro 应该拥有的权限:')
    print('=' * 80)
    
    expected_permissions = {
        'wps_management': True,
        'pqr_management': True,
        'ppqr_management': True,  # ✅ 应该是 True
        'materials_management': True,  # ✅ 应该是 True
        'welders_management': True,  # ✅ 应该是 True
        'equipment_management': False,
        'production_management': False,
        'quality_management': False,
        'employee_management': False,
        'multi_factory_management': False,
        'reports_management': False,
        'api_access': False
    }
    
    if user.permissions:
        perms = json.loads(user.permissions) if isinstance(user.permissions, str) else user.permissions
        all_correct = True
        for key, expected_value in expected_permissions.items():
            actual_value = perms.get(key, False)
            if actual_value == expected_value:
                print(f'✅ {key}: {actual_value} (正确)')
            else:
                print(f'❌ {key}: {actual_value} (期望: {expected_value})')
                all_correct = False
        
        if all_correct:
            print()
            print('🎉 所有权限都正确!')
        else:
            print()
            print('⚠️  部分权限不正确')
    else:
        print('❌ permissions 字段为空!')
    
finally:
    db.close()

