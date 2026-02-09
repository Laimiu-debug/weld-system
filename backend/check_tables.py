from app.core.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)

# 检查WPS表结构
print("=" * 60)
print("WPS表的字段:")
print("=" * 60)
columns = inspector.get_columns('wps')
for c in columns:
    print(f"  - {c['name']}: {c['type']}")

print("\n" + "=" * 60)
print("PQR表的字段:")
print("=" * 60)
columns = inspector.get_columns('pqr')
for c in columns:
    print(f"  - {c['name']}: {c['type']}")

print("\n" + "=" * 60)
print("pPQR表的字段:")
print("=" * 60)
columns = inspector.get_columns('ppqr')
for c in columns:
    print(f"  - {c['name']}: {c['type']}")

