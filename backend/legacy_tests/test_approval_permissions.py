"""测试审批权限"""
import psycopg2
from app.core.config import settings

def test_permissions():
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    
    # 查询用户 21 的企业角色和权限
    print("=" * 80)
    print("用户 21 的企业角色和权限:")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            ce.id as employee_id,
            ce.user_id,
            ce.company_id,
            ce.company_role_id,
            ce.status,
            cr.name as role_name,
            cr.permissions
        FROM company_employees ce
        LEFT JOIN company_roles cr ON ce.company_role_id = cr.id
        WHERE ce.user_id = 21
    """)
    
    rows = cur.fetchall()
    if rows:
        for row in rows:
            employee_id, user_id, company_id, role_id, status, role_name, permissions = row
            print(f"员工ID: {employee_id}")
            print(f"用户ID: {user_id}")
            print(f"企业ID: {company_id}")
            print(f"角色ID: {role_id}")
            print(f"角色名称: {role_name}")
            print(f"状态: {status}")
            print(f"权限: {permissions}")
            
            # 检查 WPS 审批权限
            if permissions and isinstance(permissions, dict):
                wps_perms = permissions.get('wps_management', {})
                print(f"\nWPS 管理权限:")
                print(f"  - 查看: {wps_perms.get('read', False)}")
                print(f"  - 创建: {wps_perms.get('create', False)}")
                print(f"  - 更新: {wps_perms.get('update', False)}")
                print(f"  - 删除: {wps_perms.get('delete', False)}")
                print(f"  - 审批: {wps_perms.get('approve', False)}")
    else:
        print("用户 21 没有企业角色")
    
    # 查询审批实例 18 的信息
    print("\n" + "=" * 80)
    print("审批实例 18 的信息:")
    print("-" * 80)
    
    cur.execute("""
        SELECT 
            id,
            workflow_id,
            document_type,
            document_id,
            status,
            current_step,
            current_step_name,
            submitter_id,
            company_id,
            factory_id
        FROM approval_instances
        WHERE id = 18
    """)
    
    row = cur.fetchone()
    if row:
        instance_id, workflow_id, doc_type, doc_id, status, current_step, step_name, submitter_id, company_id, factory_id = row
        print(f"实例ID: {instance_id}")
        print(f"工作流ID: {workflow_id}")
        print(f"文档类型: {doc_type}")
        print(f"文档ID: {doc_id}")
        print(f"状态: {status}")
        print(f"当前步骤: {current_step}")
        print(f"步骤名称: {step_name}")
        print(f"提交人ID: {submitter_id}")
        print(f"企业ID: {company_id}")
        print(f"工厂ID: {factory_id}")
    else:
        print("审批实例 18 不存在")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    test_permissions()

