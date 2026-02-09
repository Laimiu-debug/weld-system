"""
修复旧账户的密码哈希 - 将非bcrypt格式的密码重置为bcrypt格式
"""
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()

print("=" * 80)
print("修复旧账户密码哈希")
print("=" * 80)

# 查询所有用户
all_users = db.query(User).all()

non_bcrypt_users = []
bcrypt_users = []

for user in all_users:
    is_bcrypt = user.hashed_password.startswith('$2b$')
    if is_bcrypt:
        bcrypt_users.append(user)
    else:
        non_bcrypt_users.append(user)

print(f"\n统计:")
print(f"  bcrypt格式账户: {len(bcrypt_users)}")
print(f"  非bcrypt格式账户: {len(non_bcrypt_users)}")

if len(non_bcrypt_users) == 0:
    print("\n✅ 所有账户密码都是bcrypt格式，无需修复")
    db.close()
    exit(0)

print(f"\n需要修复的账户:")
for user in non_bcrypt_users:
    print(f"  - {user.email} (用户名: {user.username})")

print("\n" + "=" * 80)
print("修复选项:")
print("=" * 80)
print("1. 为所有非bcrypt账户设置默认密码: 'password123'")
print("2. 为所有非bcrypt账户设置默认密码: 'Welcome123!'")
print("3. 为每个账户设置自定义密码")
print("4. 取消")

choice = input("\n请选择 (1-4): ").strip()

if choice == '1':
    default_password = 'password123'
elif choice == '2':
    default_password = 'Welcome123!'
elif choice == '3':
    default_password = None
elif choice == '4':
    print("已取消")
    db.close()
    exit(0)
else:
    print("无效选择，已取消")
    db.close()
    exit(0)

print("\n" + "=" * 80)
print("开始修复...")
print("=" * 80)

fixed_count = 0
for user in non_bcrypt_users:
    try:
        if default_password:
            new_password = default_password
        else:
            new_password = input(f"\n为 {user.email} 设置新密码: ").strip()
            if not new_password:
                print(f"  跳过 {user.email}")
                continue
        
        # 生成新的bcrypt哈希
        new_hash = get_password_hash(new_password)
        
        # 更新数据库
        user.hashed_password = new_hash
        db.commit()
        
        print(f"✅ 已修复: {user.email} (新密码: {new_password})")
        fixed_count += 1
        
    except Exception as e:
        print(f"❌ 修复失败 {user.email}: {str(e)}")
        db.rollback()

print("\n" + "=" * 80)
print(f"修复完成! 共修复 {fixed_count} 个账户")
print("=" * 80)

if fixed_count > 0:
    print("\n修复后的账户列表:")
    for user in non_bcrypt_users[:fixed_count]:
        print(f"  - {user.email}")
        print(f"    用户名: {user.username}")
        if default_password:
            print(f"    新密码: {default_password}")
        print()

db.close()

