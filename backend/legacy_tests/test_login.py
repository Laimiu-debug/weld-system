"""
测试登录流程
"""
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password
from app.core.config import settings

db = SessionLocal()

print("=" * 80)
print("测试登录流程")
print("=" * 80)

# 检查环境配置
print(f"\n环境配置:")
print(f"  DEVELOPMENT: {settings.DEVELOPMENT}")
print(f"  DEBUG: {settings.DEBUG}")

# 测试账户
test_accounts = [
    ("testuser176070004@example.com", "password123"),
    ("testuser176070004@example.com", "test123"),
    ("testuser176070004@example.com", "123456"),
    ("testuser176070002@example.com", "password123"),
    ("testuser176070001@example.com", "password123"),
]

print(f"\n" + "=" * 80)
print("测试登录")
print("=" * 80)

for email, password in test_accounts:
    print(f"\n测试: {email} / {password}")
    
    # 查找用户
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        print(f"  ❌ 用户不存在")
        continue
    
    print(f"  ✅ 用户存在")
    print(f"     用户名: {user.username}")
    print(f"     is_active: {user.is_active}")
    print(f"     is_verified: {user.is_verified}")
    
    # 检查是否激活
    if not user.is_active:
        print(f"  ❌ 登录失败: 用户账户已被禁用")
        continue
    
    # 验证密码
    try:
        is_valid = verify_password(password, user.hashed_password)
        if not is_valid:
            print(f"  ❌ 登录失败: 密码错误")
            continue
        print(f"  ✅ 密码正确")
    except Exception as e:
        print(f"  ❌ 密码验证失败: {str(e)}")
        continue
    
    # 检查邮箱验证
    if not settings.DEVELOPMENT and not user.is_verified:
        print(f"  ❌ 登录失败: 请先验证邮箱地址 (DEVELOPMENT={settings.DEVELOPMENT})")
        continue
    
    if not user.is_verified:
        print(f"  ⚠️  邮箱未验证，但开发环境跳过验证 (DEVELOPMENT={settings.DEVELOPMENT})")
    
    print(f"  ✅ 登录成功!")

db.close()

