"""
测试用户权限和会员等级
"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from app.models.user import User
import json

db = SessionLocal()
try:
    # 获取测试用户
    user = db.query(User).filter(User.email == 'testuser176070002@example.com').first()
    if not user:
        print('用户不存在')
        sys.exit(1)
    
    print('=' * 80)
    print(f'用户信息: {user.email}')
    print('=' * 80)
    print(f'ID: {user.id}')
    print(f'member_tier: {user.member_tier}')
    print(f'membership_type: {user.membership_type}')
    print(f'subscription_status: {user.subscription_status}')
    print()
    
    # 检查权限
    from app.services.permission_service import PermissionService
    permission_service = PermissionService(db)
    
    permissions_to_check = [
        'wps.read',
        'wps.create',
        'pqr.read',
        'pqr.create',
        'ppqr.read',
        'ppqr.create',
        'materials.read',
        'materials.create',
        'welders.read',
        'welders.create',
        'equipment.read',
        'equipment.create',
    ]
    
    print('权限检查结果:')
    print('-' * 80)
    for perm in permissions_to_check:
        has_perm = permission_service.has_permission(user.id, perm)
        status = '✅' if has_perm else '❌'
        print(f'{status} {perm}: {has_perm}')
    
    print()
    print('=' * 80)
    print('前端权限映射 (personal_pro):')
    print('=' * 80)
    
    # 模拟前端的权限检查逻辑
    frontend_permissions = [
        'wps.read', 'wps.create', 'wps.update', 'wps.delete',
        'pqr.read', 'pqr.create', 'pqr.update', 'pqr.delete',
        'ppqr.read', 'ppqr.create', 'ppqr.update', 'ppqr.delete',
        'materials.read', 'materials.create', 'materials.update', 'materials.delete',
        'welders.read', 'welders.create', 'welders.update', 'welders.delete',
    ]
    
    print('personal_pro 应该拥有的权限:')
    for perm in frontend_permissions:
        print(f'  - {perm}')
    
finally:
    db.close()

