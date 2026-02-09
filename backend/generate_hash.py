import hashlib
from app.core.security import get_password_hash

# 生成密码哈希
password = "ghzzz123"
hashed_password = get_password_hash(password)
print(f"密码: {password}")
print(f"哈希值: {hashed_password}")