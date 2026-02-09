"""
初始化默认审批工作流
运行此脚本将创建系统默认的审批工作流定义
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.approval import ApprovalWorkflowDefinition, DocumentType


def create_default_workflows():
    """创建默认审批工作流"""
    db = SessionLocal()
    
    try:
        # 检查是否已存在默认工作流
        existing = db.query(ApprovalWorkflowDefinition).filter(
            ApprovalWorkflowDefinition.company_id.is_(None),
            ApprovalWorkflowDefinition.is_default == True
        ).count()
        
        if existing > 0:
            print(f"已存在 {existing} 个默认工作流，跳过创建")
            return
        
        workflows = []
        
        # 1. WPS审批工作流
        wps_workflow = ApprovalWorkflowDefinition(
            name="WPS标准审批流程",
            code="WPS_STANDARD",
            description="焊接工艺规程(WPS)的标准审批流程",
            document_type="wps",
            company_id=None,  # 系统默认
            factory_id=None,
            steps=[
                {
                    "step_number": 1,
                    "step_name": "部门经理审批",
                    "approver_type": "role",
                    "approver_ids": [2],  # 部门经理角色ID
                    "approval_mode": "any",
                    "time_limit_hours": 48,
                    "description": "部门经理审核WPS技术内容"
                },
                {
                    "step_number": 2,
                    "step_name": "技术总监审批",
                    "approver_type": "role",
                    "approver_ids": [1],  # 企业管理员角色ID
                    "approval_mode": "any",
                    "time_limit_hours": 24,
                    "description": "技术总监最终审批"
                }
            ],
            is_active=True,
            is_default=True
        )
        workflows.append(wps_workflow)
        
        # 2. PQR审批工作流
        pqr_workflow = ApprovalWorkflowDefinition(
            name="PQR标准审批流程",
            code="PQR_STANDARD",
            description="焊接工艺评定记录(PQR)的标准审批流程",
            document_type="pqr",
            company_id=None,
            factory_id=None,
            steps=[
                {
                    "step_number": 1,
                    "step_name": "质量工程师审批",
                    "approver_type": "role",
                    "approver_ids": [2],
                    "approval_mode": "any",
                    "time_limit_hours": 48,
                    "description": "质量工程师审核PQR数据"
                },
                {
                    "step_number": 2,
                    "step_name": "技术总监审批",
                    "approver_type": "role",
                    "approver_ids": [1],
                    "approval_mode": "any",
                    "time_limit_hours": 24,
                    "description": "技术总监最终审批"
                }
            ],
            is_active=True,
            is_default=True
        )
        workflows.append(pqr_workflow)
        
        # 3. pPQR审批工作流
        ppqr_workflow = ApprovalWorkflowDefinition(
            name="pPQR标准审批流程",
            code="PPQR_STANDARD",
            description="预焊接工艺评定记录(pPQR)的标准审批流程",
            document_type="ppqr",
            company_id=None,
            factory_id=None,
            steps=[
                {
                    "step_number": 1,
                    "step_name": "部门经理审批",
                    "approver_type": "role",
                    "approver_ids": [2],
                    "approval_mode": "any",
                    "time_limit_hours": 48,
                    "description": "部门经理审核pPQR内容"
                },
                {
                    "step_number": 2,
                    "step_name": "技术总监审批",
                    "approver_type": "role",
                    "approver_ids": [1],
                    "approval_mode": "any",
                    "time_limit_hours": 24,
                    "description": "技术总监最终审批"
                }
            ],
            is_active=True,
            is_default=True
        )
        workflows.append(ppqr_workflow)
        
        # 4. 设备管理审批工作流
        equipment_workflow = ApprovalWorkflowDefinition(
            name="设备管理标准审批流程",
            code="EQUIPMENT_STANDARD",
            description="设备管理的标准审批流程",
            document_type="equipment",
            company_id=None,
            factory_id=None,
            steps=[
                {
                    "step_number": 1,
                    "step_name": "设备管理员审批",
                    "approver_type": "role",
                    "approver_ids": [2],
                    "approval_mode": "any",
                    "time_limit_hours": 24,
                    "description": "设备管理员审核设备信息"
                }
            ],
            is_active=True,
            is_default=True
        )
        workflows.append(equipment_workflow)
        
        # 5. 焊材管理审批工作流
        material_workflow = ApprovalWorkflowDefinition(
            name="焊材管理标准审批流程",
            code="MATERIAL_STANDARD",
            description="焊材管理的标准审批流程",
            document_type="material",
            company_id=None,
            factory_id=None,
            steps=[
                {
                    "step_number": 1,
                    "step_name": "材料管理员审批",
                    "approver_type": "role",
                    "approver_ids": [2],
                    "approval_mode": "any",
                    "time_limit_hours": 24,
                    "description": "材料管理员审核焊材信息"
                }
            ],
            is_active=True,
            is_default=True
        )
        workflows.append(material_workflow)
        
        # 6. 焊工管理审批工作流
        welder_workflow = ApprovalWorkflowDefinition(
            name="焊工管理标准审批流程",
            code="WELDER_STANDARD",
            description="焊工管理的标准审批流程",
            document_type="welder",
            company_id=None,
            factory_id=None,
            steps=[
                {
                    "step_number": 1,
                    "step_name": "人力资源审批",
                    "approver_type": "role",
                    "approver_ids": [2],
                    "approval_mode": "any",
                    "time_limit_hours": 24,
                    "description": "人力资源审核焊工资质"
                }
            ],
            is_active=True,
            is_default=True
        )
        workflows.append(welder_workflow)
        
        # 批量添加到数据库
        for workflow in workflows:
            db.add(workflow)
            print(f"创建工作流: {workflow.name} ({workflow.code})")
        
        db.commit()
        print(f"\n成功创建 {len(workflows)} 个默认审批工作流！")
        
    except Exception as e:
        print(f"创建工作流失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def list_workflows():
    """列出所有工作流"""
    db = SessionLocal()
    
    try:
        workflows = db.query(ApprovalWorkflowDefinition).all()
        
        print("\n当前系统中的审批工作流：")
        print("-" * 80)
        
        for wf in workflows:
            print(f"\nID: {wf.id}")
            print(f"名称: {wf.name}")
            print(f"代码: {wf.code}")
            print(f"文档类型: {wf.document_type}")
            print(f"企业ID: {wf.company_id or '系统默认'}")
            print(f"步骤数: {len(wf.steps)}")
            print(f"状态: {'启用' if wf.is_active else '禁用'}")
            print(f"默认: {'是' if wf.is_default else '否'}")
            
            if wf.steps:
                print("审批步骤:")
                for step in wf.steps:
                    print(f"  {step['step_number']}. {step['step_name']} "
                          f"({step['approver_type']}, 模式: {step['approval_mode']}, "
                          f"时限: {step.get('time_limit_hours', 'N/A')}小时)")
        
        print("-" * 80)
        print(f"\n总计: {len(workflows)} 个工作流")
        
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="审批工作流管理脚本")
    parser.add_argument(
        "action",
        choices=["create", "list"],
        help="操作类型: create-创建默认工作流, list-列出所有工作流"
    )
    
    args = parser.parse_args()
    
    if args.action == "create":
        create_default_workflows()
    elif args.action == "list":
        list_workflows()

