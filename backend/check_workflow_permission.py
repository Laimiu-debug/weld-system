"""
检查用户创建工作流的权限
"""
from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import CompanyEmployee, Company
from app.core.data_access import WorkspaceContext, WorkspaceType

db = SessionLocal()

# 查找用户
user = db.query(User).filter(User.email == 'testuser176070001@example.com').first()

if user:
    print(f'用户信息:')
    print(f'  ID: {user.id}')
    print(f'  邮箱: {user.email}')
    print(f'  用户名: {user.username}')
    print(f'  会员类型: {user.membership_type}')
    print(f'  是否激活: {user.is_active}')
    
    # 查找企业员工记录
    employee = db.query(CompanyEmployee).filter(
        CompanyEmployee.user_id == user.id,
        CompanyEmployee.status == 'active'
    ).first()
    
    if employee:
        print(f'\n企业员工信息:')
        print(f'  企业ID: {employee.company_id}')
        print(f'  工厂ID: {employee.factory_id}')
        print(f'  公司角色ID: {employee.company_role_id}')
        print(f'  状态: {employee.status}')
        
        # 查找企业信息
        company = db.query(Company).filter(Company.id == employee.company_id).first()
        if company:
            print(f'\n企业信息:')
            print(f'  企业名称: {company.name}')
            print(f'  企业会员等级: {company.membership_tier}')
            print(f'  工作区ID: enterprise_{company.id}')
            
        # 检查工作区上下文
        workspace_context = WorkspaceContext(
            user_id=user.id,
            workspace_type=WorkspaceType.ENTERPRISE,
            company_id=employee.company_id,
            factory_id=employee.factory_id
        )
        print(f'\n工作区上下文:')
        print(f'  workspace_type: {workspace_context.workspace_type}')
        print(f'  company_id: {workspace_context.company_id}')
        print(f'  是否企业工作区: {workspace_context.is_enterprise()}')
        
        # 测试权限检查逻辑
        print(f'\n权限检查:')
        print(f'  workspace_context.workspace_type = "{workspace_context.workspace_type}"')
        print(f'  WorkspaceType.ENTERPRISE = "{WorkspaceType.ENTERPRISE}"')
        print(f'  比较结果: {workspace_context.workspace_type == WorkspaceType.ENTERPRISE}')
        print(f'  字符串比较: {workspace_context.workspace_type == "enterprise"}')
        
        # 检查现有工作流
        from app.models.approval import ApprovalWorkflowDefinition
        workflows = db.query(ApprovalWorkflowDefinition).filter(
            ApprovalWorkflowDefinition.company_id == employee.company_id
        ).all()
        print(f'\n现有工作流数量: {len(workflows)}')
        for wf in workflows:
            print(f'  - {wf.name} (code: {wf.code}, company_id: {wf.company_id})')
            
    else:
        print(f'\n未找到企业员工记录')
else:
    print('未找到用户')

db.close()

