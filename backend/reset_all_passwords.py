"""
批量重置所有账户密码
"""
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from getpass import getpass

db = SessionLocal()

print("=" * 80)
print("批量重置所有账户密码")
print("=" * 80)

# 查询所有用户
all_users = db.query(User).all()

print(f"\n总共 {len(all_users)} 个账户\n")

new_password = getpass("请输入所有账户的新密码: ").strip()
if len(new_password) < 12:
    print("密码至少需要 12 个字符，已取消")
    db.close()
    exit(0)

print(f"\n确认要重置所有 {len(all_users)} 个账户的密码")
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

print("\n账户列表:")
for user in all_users:
    print(f"  - {user.email} (用户名: {user.username})")

db.close()

