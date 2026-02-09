"""检查PQR表中是否有modules_data列"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
conn = engine.connect()

result = conn.execute(text("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'pqr' AND column_name LIKE '%module%'
"""))

columns = result.fetchall()
print(f"找到 {len(columns)} 个包含'module'的列:")
for col in columns:
    print(f"  - {col[0]}: {col[1]}")

if len(columns) == 0:
    print("\n❌ PQR表中没有modules_data列！需要添加。")
else:
    print("\n✅ PQR表中有modules相关的列")

conn.close()

