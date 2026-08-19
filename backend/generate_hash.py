import os
import sys

from app.core.security import get_password_hash
from app.core.bootstrap_secrets import require_admin_initial_password

password = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("ADMIN_INITIAL_PASSWORD")
if not password:
    password = require_admin_initial_password()
hashed_password = get_password_hash(password)
print("哈希值已生成（明文密码不会打印）")
print(f"哈希值: {hashed_password}")
