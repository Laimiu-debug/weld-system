"""
检查pPQR审批工作流配置
"""
import sys
import os

# 添加backend目录到Python路径
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from app.db.session import SessionLocal
from app.models.approval import ApprovalWorkflowDefinition

def check_workflows():
    db = SessionLocal()
    try:
        # 查询pPQR工作流
        ppqr_workflows = db.query(ApprovalWorkflowDefinition).filter(
            ApprovalWorkflowDefinition.document_type == 'ppqr'
        ).all()
        
        print("=" * 60)
        print("pPQR 审批工作流检查")
        print("=" * 60)
        
        if ppqr_workflows:
            print(f"\n✅ 找到 {len(ppqr_workflows)} 个pPQR审批工作流:\n")
            for wf in ppqr_workflows:
                print(f"  工作流ID: {wf.id}")
                print(f"  名称: {wf.name}")
                print(f"  公司ID: {wf.company_id}")
                print(f"  状态: {'激活' if wf.is_active else '未激活'}")
                print(f"  创建时间: {wf.created_at}")
                print("-" * 60)
        else:
            print("\n❌ 没有找到pPQR的审批工作流！")
            print("\n这就是为什么pPQR无法提交审批的原因。")
            print("\n解决方案：需要创建pPQR的审批工作流。")
        
        # 显示所有工作流
        print("\n" + "=" * 60)
        print("所有审批工作流:")
        print("=" * 60)
        all_workflows = db.query(ApprovalWorkflowDefinition).all()
        if all_workflows:
            for wf in all_workflows:
                print(f"  类型: {wf.document_type:10s} | 名称: {wf.name:20s} | 公司ID: {wf.company_id}")
        else:
            print("  没有任何审批工作流")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_workflows()

