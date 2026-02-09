"""给用户 21 分配焊接工程师角色"""
import psycopg2
from app.core.config import settings

def assign_role():
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    
    # 更新用户 21 的角色为焊接工程师（ID: 11）
    cur.execute("""
        UPDATE company_employees
        SET company_role_id = 11, updated_at = NOW()
        WHERE user_id = 21 AND company_id = 4
    """)
    
    conn.commit()
    print("已将用户 21 的角色设置为焊接工程师（ID: 11）")
    
    # 验证更新
    cur.execute("""
        SELECT 
            ce.id,
            ce.user_id,
            u.username,
            ce.company_role_id,
            cr.name as role_name
        FROM company_employees ce
        LEFT JOIN users u ON ce.user_id = u.id
        LEFT JOIN company_roles cr ON ce.company_role_id = cr.id
        WHERE ce.user_id = 21 AND ce.company_id = 4
    """)
    
    row = cur.fetchone()
    if row:
        emp_id, user_id, username, role_id, role_name = row
        print(f"\n更新后的信息:")
        print(f"员工ID: {emp_id}")
        print(f"用户ID: {user_id}")
        print(f"用户名: {username}")
        print(f"角色ID: {role_id}")
        print(f"角色名称: {role_name}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    assign_role()

