"""
确保所有企业会员都有员工记录（包括所有者自己）
"""
import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine, text
from app.core.config import settings

def ensure_owners_as_employees():
    """确保所有企业所有者都在员工表中"""
    engine = create_engine(str(settings.DATABASE_URL).replace('\\', '/'))
    
    with engine.connect() as conn:
        # 开始事务
        trans = conn.begin()
        
        try:
            # 查询所有企业及其所有者
            query = text("""
                SELECT 
                    c.id as company_id,
                    c.name as company_name,
                    c.owner_id,
                    u.email as owner_email,
                    u.full_name,
                    u.username,
                    (SELECT f.id FROM factories f 
                     WHERE f.company_id = c.id AND f.is_headquarters = true 
                     LIMIT 1) as headquarters_id,
                    (SELECT COUNT(*) FROM company_employees ce 
                     WHERE ce.company_id = c.id AND ce.user_id = c.owner_id) as owner_in_employees
                FROM companies c
                JOIN users u ON c.owner_id = u.id
                WHERE c.is_active = true
            """)
            
            result = conn.execute(query)
            rows = result.fetchall()
            
            print("\n" + "="*80)
            print("确保企业所有者都在员工表中")
            print("="*80 + "\n")
            
            added_count = 0
            
            for row in rows:
                company_id, company_name, owner_id, owner_email, full_name, username, headquarters_id, owner_in_employees = row
                
                if owner_in_employees > 0:
                    print(f"✅ {company_name} - 所有者 {owner_email} 已在员工表中")
                else:
                    print(f"❌ {company_name} - 所有者 {owner_email} 不在员工表中")
                    
                    if not headquarters_id:
                        print(f"   ⚠️  没有总部工厂，跳过")
                        continue
                    
                    # 生成员工编号
                    emp_number_query = text("""
                        SELECT COALESCE(MAX(CAST(SUBSTRING(employee_number FROM 4) AS INTEGER)), 0) + 1
                        FROM company_employees
                        WHERE company_id = :company_id
                    """)
                    emp_number_result = conn.execute(emp_number_query, {"company_id": company_id})
                    next_number = emp_number_result.scalar()
                    employee_number = f"EMP{next_number:08d}"
                    
                    # 插入员工记录
                    insert_query = text("""
                        INSERT INTO company_employees (
                            company_id, user_id, employee_number, role, status,
                            position, department, factory_id, data_access_scope,
                            permissions, joined_at, created_at, updated_at,
                            total_wps_created, total_tasks_completed
                        ) VALUES (
                            :company_id, :user_id, :employee_number, 'admin', 'active',
                            '企业所有者', '管理层', :factory_id, 'company',
                            '{"wps_management": true, "pqr_management": true, "ppqr_management": true, "factory_management": true, "welders_management": true, "employee_management": true, "equipment_management": true, "materials_management": true}',
                            NOW(), NOW(), NOW(), 0, 0
                        )
                    """)
                    
                    conn.execute(insert_query, {
                        "company_id": company_id,
                        "user_id": owner_id,
                        "employee_number": employee_number,
                        "factory_id": headquarters_id
                    })
                    
                    print(f"   ✅ 已添加所有者为员工 (员工编号: {employee_number})")
                    added_count += 1
            
            # 提交事务
            trans.commit()
            
            print("\n" + "="*80)
            print(f"完成！共添加 {added_count} 个所有者为员工")
            print("="*80 + "\n")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    ensure_owners_as_employees()

