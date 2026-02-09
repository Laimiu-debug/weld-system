"""
检查用户凭据
"""
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password

db = SessionLocal()

# 查找用户
user = db.query(User).filter(User.email == 'testuser176070001@example.com').first()

if user:
    print(f"用户信息:")
    print(f"  ID: {user.id}")
    print(f"  Email: {user.email}")
    print(f"  Username: {user.username}")
    print(f"  是否激活: {user.is_active}")
    print(f"  会员类型: {user.membership_type}")
    
    # 测试密码
    test_passwords = ['password123', 'testpassword', 'password', '123456']
    
    print(f"\n测试密码:")
    for pwd in test_passwords:
        is_valid = verify_password(pwd, user.hashed_password)
        print(f"  {pwd}: {'✅ 正确' if is_valid else '❌ 错误'}")
else:
    print("用户不存在")

db.close()

