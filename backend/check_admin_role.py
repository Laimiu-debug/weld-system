"""检查企业管理员角色"""
import psycopg2
from app.core.config import settings

def check_admin():
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    
    # 查询企业 4 的所有角色，看是否有管理员角色
    print("=" * 80)
    print("企业 4 的所有角色:")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            id,
            name,
            description,
            permissions
        FROM company_roles
        WHERE company_id = 4
        ORDER BY id
    """)
    
    rows = cur.fetchall()
    admin_role_id = None
    
    for row in rows:
        role_id, name, description, permissions = row
        print(f"\n角色ID: {role_id}, 名称: {name}")
        
        # 检查是否是管理员角色
        if '管理员' in name or 'admin' in name.lower():
            admin_role_id = role_id
            print(f"  >>> 这是管理员角色!")
            
            if permissions:
                # 检查是否有 WPS 审批权限
                wps_perms = permissions.get('wps_management', {})
                has_approve = wps_perms.get('approve', False)
                print(f"  WPS 审批权限: {has_approve}")
    
    if not admin_role_id:
        print("\n⚠️ 企业 4 没有管理员角色！")
        print("需要创建企业管理员角色")
    
    # 查询用户 21 的信息
    print("\n" + "=" * 80)
    print("用户 21 的信息:")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            u.id,
            u.username,
            u.email,
            u.is_admin,
            u.is_superuser,
            ce.company_role_id,
            cr.name as role_name
        FROM users u
        LEFT JOIN company_employees ce ON u.id = ce.user_id AND ce.company_id = 4
        LEFT JOIN company_roles cr ON ce.company_role_id = cr.id
        WHERE u.id = 21
    """)
    
    row = cur.fetchone()
    if row:
        user_id, username, email, is_admin, is_superuser, role_id, role_name = row
        print(f"用户ID: {user_id}")
        print(f"用户名: {username}")
        print(f"邮箱: {email}")
        print(f"是否管理员: {is_admin}")
        print(f"是否超级用户: {is_superuser}")
        print(f"企业角色ID: {role_id}")
        print(f"企业角色名称: {role_name}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_admin()

