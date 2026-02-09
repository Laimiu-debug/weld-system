"""检查企业角色"""
import psycopg2
from app.core.config import settings

def check_roles():
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    
    # 查询企业 4 的所有角色
    print("=" * 80)
    print("企业 4 的角色:")
    print("-" * 80)
    
    cur.execute("""
        SELECT
            id,
            name,
            description,
            permissions,
            created_at
        FROM company_roles
        WHERE company_id = 4
        ORDER BY created_at
    """)
    
    rows = cur.fetchall()
    if rows:
        for row in rows:
            role_id, name, description, permissions, created_at = row
            print(f"\n角色ID: {role_id}")
            print(f"名称: {name}")
            print(f"描述: {description}")
            print(f"创建时间: {created_at}")
            
            if permissions:
                print(f"权限:")
                for module, perms in permissions.items():
                    print(f"  {module}:")
                    for perm, value in perms.items():
                        print(f"    - {perm}: {value}")
    else:
        print("企业 4 没有角色")
    
    # 查询企业 4 的所有员工
    print("\n" + "=" * 80)
    print("企业 4 的员工:")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            ce.id,
            ce.user_id,
            u.username,
            u.email,
            ce.company_role_id,
            cr.name as role_name,
            ce.status
        FROM company_employees ce
        LEFT JOIN users u ON ce.user_id = u.id
        LEFT JOIN company_roles cr ON ce.company_role_id = cr.id
        WHERE ce.company_id = 4
        ORDER BY ce.created_at
    """)
    
    rows = cur.fetchall()
    if rows:
        print(f"{'员工ID':<10} {'用户ID':<10} {'用户名':<20} {'邮箱':<30} {'角色ID':<10} {'角色名称':<20} {'状态':<10}")
        print("-" * 120)
        for row in rows:
            emp_id, user_id, username, email, role_id, role_name, status = row
            print(f"{emp_id:<10} {user_id:<10} {username or '':<20} {email or '':<30} {str(role_id) if role_id else 'None':<10} {role_name or 'None':<20} {status:<10}")
    else:
        print("企业 4 没有员工")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_roles()

