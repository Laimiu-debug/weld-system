"""
诊断pPQR审批问题的脚本
"""
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import SessionLocal
from app.models.approval import ApprovalWorkflowDefinition
from app.models.company import Company
from sqlalchemy import and_, or_

def diagnose():
    db = SessionLocal()
    try:
        print("=" * 80)
        print("pPQR 审批问题诊断工具")
        print("=" * 80)
        
        # 1. 检查所有pPQR工作流
        print("\n【步骤1】检查数据库中的pPQR工作流配置")
        print("-" * 80)
        
        ppqr_workflows = db.query(ApprovalWorkflowDefinition).filter(
            ApprovalWorkflowDefinition.document_type == 'ppqr'
        ).all()
        
        if not ppqr_workflows:
            print("❌ 错误：数据库中没有找到任何pPQR工作流！")
            print("\n解决方案：需要创建pPQR工作流")
            print("请运行: python create_ppqr_workflow.py")
            return
        
        print(f"✅ 找到 {len(ppqr_workflows)} 个pPQR工作流:\n")
        
        for i, wf in enumerate(ppqr_workflows, 1):
            print(f"工作流 #{i}:")
            print(f"  ID: {wf.id}")
            print(f"  名称: {wf.name}")
            print(f"  代码: {wf.code}")
            print(f"  企业ID: {wf.company_id or '系统默认(NULL)'}")
            print(f"  是否激活: {'✅ 是' if wf.is_active else '❌ 否'}")
            print(f"  是否默认: {'✅ 是' if wf.is_default else '❌ 否'}")
            print(f"  创建时间: {wf.created_at}")
            
            # 检查问题
            issues = []
            if not wf.is_active:
                issues.append("⚠️  工作流未激活 (is_active=False)")
            if wf.company_id is None and not wf.is_default:
                issues.append("⚠️  系统级工作流但未设置为默认 (is_default=False)")
            if not wf.steps or len(wf.steps) == 0:
                issues.append("⚠️  工作流没有配置审批步骤")
            
            if issues:
                print(f"  问题:")
                for issue in issues:
                    print(f"    {issue}")
            else:
                print(f"  状态: ✅ 配置正常")
            
            print()
        
        # 2. 检查企业信息
        print("\n【步骤2】检查企业信息")
        print("-" * 80)
        
        companies = db.query(Company).all()
        if companies:
            print(f"找到 {len(companies)} 个企业:\n")
            for company in companies:
                print(f"  企业ID: {company.id}")
                print(f"  企业名称: {company.name}")
                print(f"  所有者ID: {company.owner_id}")
                print()
        else:
            print("⚠️  数据库中没有企业信息")
            print("如果你在企业工作区，这可能是问题所在")
            print()
        
        # 3. 给出诊断结果和建议
        print("\n【步骤3】诊断结果和建议")
        print("-" * 80)
        
        # 检查是否有可用的工作流
        active_workflows = [wf for wf in ppqr_workflows if wf.is_active]
        
        if not active_workflows:
            print("❌ 问题：所有pPQR工作流都未激活")
            print("\n解决方案：")
            print("运行以下SQL激活工作流：")
            print(f"UPDATE approval_workflow_definitions SET is_active = true WHERE document_type = 'ppqr';")
            return
        
        # 检查企业工作流
        company_workflows = [wf for wf in active_workflows if wf.company_id is not None]
        system_workflows = [wf for wf in active_workflows if wf.company_id is None]
        
        print("✅ 有激活的工作流")
        print(f"   - 企业工作流: {len(company_workflows)} 个")
        print(f"   - 系统工作流: {len(system_workflows)} 个")
        print()
        
        if company_workflows:
            print("企业工作流配置:")
            for wf in company_workflows:
                print(f"  - {wf.name} (企业ID: {wf.company_id})")
            print()
            print("💡 提示：如果你在企业工作区，请确保：")
            print("   1. 你当前所在的企业ID与工作流的company_id匹配")
            print("   2. 检查浏览器控制台，查看当前工作区信息")
            print()
        
        if system_workflows:
            print("系统工作流配置:")
            for wf in system_workflows:
                status = "✅ 可用" if wf.is_default else "❌ 未设为默认"
                print(f"  - {wf.name} ({status})")
            print()
            
            non_default_system = [wf for wf in system_workflows if not wf.is_default]
            if non_default_system:
                print("⚠️  警告：以下系统工作流未设置为默认，可能无法使用：")
                for wf in non_default_system:
                    print(f"   - {wf.name} (ID: {wf.id})")
                print("\n解决方案：")
                print("运行以下SQL设置为默认：")
                for wf in non_default_system:
                    print(f"UPDATE approval_workflow_definitions SET is_default = true WHERE id = {wf.id};")
                print()
        
        # 4. 最终建议
        print("\n【步骤4】最终检查清单")
        print("-" * 80)
        print("请确认以下事项：")
        print()
        print("□ 1. 你在企业工作区（不是个人工作区）")
        print("     - 个人工作区不支持审批流程")
        print("     - 检查方法：查看页面左上角工作区切换器")
        print()
        print("□ 2. 工作流的company_id与你的企业ID匹配")
        print("     - 或者使用系统默认工作流(company_id=NULL, is_default=true)")
        print()
        print("□ 3. 工作流已激活 (is_active=true)")
        print()
        print("□ 4. 刷新页面 (Ctrl+F5 强制刷新)")
        print()
        print("□ 5. 检查浏览器控制台是否有错误")
        print()
        
        print("=" * 80)
        print("诊断完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 诊断过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    diagnose()

