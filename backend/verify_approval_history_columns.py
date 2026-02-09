"""验证 approval_history 表的列结构"""
import psycopg2
from app.core.config import settings

def verify_columns():
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns 
        WHERE table_name = 'approval_history' 
        ORDER BY ordinal_position
    """)
    
    print("Columns in approval_history table:")
    print("-" * 60)
    for row in cur.fetchall():
        col_name, data_type, max_length = row
        if max_length:
            print(f"  {col_name}: {data_type}({max_length})")
        else:
            print(f"  {col_name}: {data_type}")
    
    # 检查 step_name 是否存在
    cur.execute("""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'approval_history' 
            AND column_name = 'step_name'
        )
    """)
    
    step_name_exists = cur.fetchone()[0]
    print("-" * 60)
    if step_name_exists:
        print("✓ step_name 字段存在")
    else:
        print("✗ step_name 字段不存在")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    verify_columns()

