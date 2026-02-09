"""
验证修复结果
"""
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password

db = SessionLocal()

print("=" * 80)
print("验证修复结果")
print("=" * 80)

# 查找修复后的账户
user = db.query(User).filter(User.email == 'testuser176070001@example.com').first()

if user:
    print(f"\n账户信息:")
    print(f"  Email: {user.email}")
    print(f"  Username: {user.username}")
    print(f"  是否激活: {user.is_active}")
    print(f"  是否验证: {user.is_verified}")
    print(f"  密码哈希前缀: {user.hashed_password[:10]}")
    print(f"  密码哈希长度: {len(user.hashed_password)}")
    
    # 验证密码
    print(f"\n密码验证:")
    test_password = 'password123'
    try:
        is_valid = verify_password(test_password, user.hashed_password)
        if is_valid:
            print(f"  ✅ 密码 '{test_password}' 验证成功!")
        else:
            print(f"  ❌ 密码 '{test_password}' 验证失败")
    except Exception as e:
        print(f"  ❌ 验证出错: {str(e)}")
    
    # 检查是否是bcrypt格式
    is_bcrypt = user.hashed_password.startswith('$2b$')
    print(f"\n密码格式检查:")
    print(f"  是否bcrypt格式: {'✅ 是' if is_bcrypt else '❌ 否'}")
    
else:
    print("\n❌ 账户不存在")

print("\n" + "=" * 80)
print("检查所有账户的密码格式")
print("=" * 80)

all_users = db.query(User).all()
bcrypt_count = 0
non_bcrypt_count = 0

for user in all_users:
    is_bcrypt = user.hashed_password.startswith('$2b$')
    if is_bcrypt:
        bcrypt_count += 1
    else:
        non_bcrypt_count += 1
        print(f"❌ 非bcrypt格式: {user.email}")

print(f"\n统计:")
print(f"  ✅ bcrypt格式: {bcrypt_count}")
print(f"  ❌ 非bcrypt格式: {non_bcrypt_count}")

if non_bcrypt_count == 0:
    print(f"\n🎉 所有账户密码都已修复为bcrypt格式!")
else:
    print(f"\n⚠️  还有 {non_bcrypt_count} 个账户需要修复")

db.close()

