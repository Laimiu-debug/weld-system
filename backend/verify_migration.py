"""
验证数据库迁移结果
"""
import os
import sys
import psycopg2

def load_env_file():
    """加载.env文件"""
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

def verify_migration():
    """验证迁移结果"""
    load_env_file()
    
    db_config = {
        'host': os.getenv('DATABASE_HOST', 'localhost'),
        'port': os.getenv('DATABASE_PORT', '5432'),
        'database': os.getenv('DATABASE_NAME', 'weld_db'),
        'user': os.getenv('DATABASE_USER', 'weld_user'),
        'password': os.getenv('DATABASE_PASSWORD', 'weld_password')
    }
    
    print("=" * 60)
    print("验证数据库迁移结果")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # 检查document_html字段
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = 'wps' AND column_name = 'document_html'
        """)
        
        result = cursor.fetchone()
        
        if result:
            print("\n✓ document_html字段已成功添加到wps表")
            print(f"  字段名: {result[0]}")
            print(f"  数据类型: {result[1]}")
            print(f"  允许NULL: {result[2]}")
            print(f"  默认值: {result[3] or '无'}")
        else:
            print("\n✗ 未找到document_html字段")
            return False
        
        # 检查wps表的所有字段
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'wps'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print(f"\n✓ wps表共有 {len(columns)} 个字段")
        print("  最后5个字段:")
        for col in columns[-5:]:
            print(f"    - {col[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ 验证完成！迁移成功！")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ 验证失败: {e}")
        return False

if __name__ == "__main__":
    success = verify_migration()
    sys.exit(0 if success else 1)

