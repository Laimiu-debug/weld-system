"""
检查密码问题 - 对比旧账户和新账户的密码哈希
"""
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password, get_password_hash

db = SessionLocal()

print("=" * 80)
print("检查密码哈希问题")
print("=" * 80)

# 查找新注册的可以登录的账户
new_user = db.query(User).filter(User.email == 'testuser176070099@example.com').first()

# 查找旧的不能登录的账户
old_user = db.query(User).filter(User.email == 'testuser176070001@example.com').first()

if new_user:
    print(f"\n✅ 新账户 (可以登录):")
    print(f"  Email: {new_user.email}")
    print(f"  Username: {new_user.username}")
    print(f"  是否激活: {new_user.is_active}")
    print(f"  是否验证: {new_user.is_verified}")
    print(f"  密码哈希: {new_user.hashed_password[:60]}...")
    print(f"  密码哈希长度: {len(new_user.hashed_password)}")
    print(f"  密码哈希前缀: {new_user.hashed_password[:7]}")
    
    # 测试常见密码
    test_passwords = ['password123', 'testpassword', 'password', '123456', 'test123']
    print(f"\n  测试密码验证:")
    for pwd in test_passwords:
        is_valid = verify_password(pwd, new_user.hashed_password)
        if is_valid:
            print(f"    {pwd}: ✅ 正确")
else:
    print("\n❌ 新账户不存在")

print("\n" + "-" * 80)

if old_user:
    print(f"\n❌ 旧账户 (不能登录):")
    print(f"  Email: {old_user.email}")
    print(f"  Username: {old_user.username}")
    print(f"  是否激活: {old_user.is_active}")
    print(f"  是否验证: {old_user.is_verified}")
    print(f"  密码哈希: {old_user.hashed_password[:60]}...")
    print(f"  密码哈希长度: {len(old_user.hashed_password)}")
    print(f"  密码哈希前缀: {old_user.hashed_password[:7]}")
    
    # 测试常见密码
    test_passwords = ['password123', 'testpassword', 'password', '123456', 'test123']
    print(f"\n  测试密码验证:")
    for pwd in test_passwords:
        is_valid = verify_password(pwd, old_user.hashed_password)
        if is_valid:
            print(f"    {pwd}: ✅ 正确")
else:
    print("\n❌ 旧账户不存在")

print("\n" + "=" * 80)
print("分析:")
print("=" * 80)

if new_user and old_user:
    # 检查密码哈希格式
    new_is_bcrypt = new_user.hashed_password.startswith('$2b$')
    old_is_bcrypt = old_user.hashed_password.startswith('$2b$')
    
    print(f"\n新账户密码是bcrypt格式: {new_is_bcrypt}")
    print(f"旧账户密码是bcrypt格式: {old_is_bcrypt}")
    
    if not old_is_bcrypt:
        print("\n⚠️  问题发现: 旧账户的密码哈希不是bcrypt格式!")
        print("   可能原因:")
        print("   1. 密码是明文存储的")
        print("   2. 使用了其他哈希算法")
        print("   3. 数据库迁移时密码字段被损坏")
        
        # 检查是否是明文
        test_passwords = ['password123', 'testpassword', 'password', '123456', 'test123']
        for pwd in test_passwords:
            if old_user.hashed_password == pwd:
                print(f"\n   ⚠️  密码是明文存储: {pwd}")
                break
    
    # 检查其他字段差异
    print(f"\n字段对比:")
    print(f"  is_active: 新={new_user.is_active}, 旧={old_user.is_active}")
    print(f"  is_verified: 新={new_user.is_verified}, 旧={old_user.is_verified}")
    print(f"  member_tier: 新={new_user.member_tier}, 旧={old_user.member_tier}")

print("\n" + "=" * 80)
print("查询所有用户的密码哈希格式")
print("=" * 80)

all_users = db.query(User).limit(10).all()
bcrypt_count = 0
non_bcrypt_count = 0

for user in all_users:
    is_bcrypt = user.hashed_password.startswith('$2b$')
    if is_bcrypt:
        bcrypt_count += 1
        status = "✅ bcrypt"
    else:
        non_bcrypt_count += 1
        status = "❌ 非bcrypt"
    
    print(f"{user.email:40} {status:15} 前缀: {user.hashed_password[:20]}")

print(f"\n统计:")
print(f"  bcrypt格式: {bcrypt_count}")
print(f"  非bcrypt格式: {non_bcrypt_count}")

if non_bcrypt_count > 0:
    print(f"\n⚠️  发现 {non_bcrypt_count} 个账户的密码不是bcrypt格式!")
    print("   建议: 需要重置这些账户的密码")

db.close()

