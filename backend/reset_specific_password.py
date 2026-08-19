"""
重置特定账户的密码
"""
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from getpass import getpass

db = SessionLocal()

print("=" * 80)
print("重置特定账户密码")
print("=" * 80)

# 输入邮箱
email = input("\n请输入要重置密码的账户邮箱: ").strip()

if not email:
    print("邮箱不能为空")
    db.close()
    exit(0)

# 查找用户
user = db.query(User).filter(User.email == email).first()

if not user:
    print(f"❌ 账户不存在: {email}")
    db.close()
    exit(0)

print(f"\n找到账户:")
print(f"  邮箱: {user.email}")
print(f"  用户名: {user.username}")
print(f"  是否激活: {user.is_active}")
print(f"  是否验证: {user.is_verified}")

# 输入新密码
new_password = getpass("\n请输入新密码: ").strip()
if len(new_password) < 12:
    print("密码至少需要 12 个字符")
    db.close()
    exit(0)

# 确认
print(f"\n确认要重置账户 {email} 的密码")
confirm = input("输入 'yes' 确认: ").strip().lower()

if confirm != 'yes':
    print("已取消")
    db.close()
    exit(0)

# 重置密码
try:
    new_hash = get_password_hash(new_password)
    user.hashed_password = new_hash
    db.commit()
    
    print("\n" + "=" * 80)
    print("✅ 密码重置成功!")
    print("=" * 80)
    print(f"\n账户: {user.email}")
    
except Exception as e:
    print(f"\n❌ 密码重置失败: {str(e)}")
    db.rollback()

db.close()

