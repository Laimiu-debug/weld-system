"""
批量重置所有账户密码
"""
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()

print("=" * 80)
print("批量重置所有账户密码")
print("=" * 80)

# 查询所有用户
all_users = db.query(User).all()

print(f"\n总共 {len(all_users)} 个账户\n")

print("选择重置密码:")
print("1. 重置所有账户密码为: password123")
print("2. 重置所有账户密码为: Welcome123!")
print("3. 自定义密码")
print("4. 取消")

choice = input("\n请选择 (1-4): ").strip()

if choice == '1':
    new_password = 'password123'
elif choice == '2':
    new_password = 'Welcome123!'
elif choice == '3':
    new_password = input("请输入新密码: ").strip()
    if not new_password:
        print("密码不能为空，已取消")
        db.close()
        exit(0)
elif choice == '4':
    print("已取消")
    db.close()
    exit(0)
else:
    print("无效选择，已取消")
    db.close()
    exit(0)

print(f"\n确认要将所有 {len(all_users)} 个账户的密码重置为: {new_password}")
confirm = input("输入 'yes' 确认: ").strip().lower()

if confirm != 'yes':
    print("已取消")
    db.close()
    exit(0)

print("\n" + "=" * 80)
print("开始重置...")
print("=" * 80)

# 生成新的密码哈希
new_hash = get_password_hash(new_password)

success_count = 0
for user in all_users:
    try:
        user.hashed_password = new_hash
        db.commit()
        print(f"✅ {user.email}")
        success_count += 1
    except Exception as e:
        print(f"❌ {user.email}: {str(e)}")
        db.rollback()

print("\n" + "=" * 80)
print(f"重置完成! 成功: {success_count}/{len(all_users)}")
print("=" * 80)

print(f"\n所有账户的新密码: {new_password}")
print("\n账户列表:")
for user in all_users:
    print(f"  - {user.email} (用户名: {user.username})")

db.close()

