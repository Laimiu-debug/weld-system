"""
创建pPQR审批工作流
使用API方式创建
"""
import requests
import json

# 配置
API_BASE_URL = "http://localhost:8000/api/v1"
# 请替换为您的实际token
TOKEN = "your_token_here"  # 需要从浏览器localStorage中获取

# 请替换为您的实际公司ID（企业工作区的company_id）
COMPANY_ID = 1  # 默认为1，请根据实际情况修改

def create_ppqr_workflow():
    """创建pPQR审批工作流"""
    
    # 工作流配置
    workflow_data = {
        "name": "pPQR标准审批流程",
        "description": "pPQR文档的标准审批流程",
        "document_type": "ppqr",
        "company_id": COMPANY_ID,
        "steps": [
            {
                "step_name": "技术审核",
                "approver_type": "role",
                "approver_ids": [2],  # 角色ID 2 通常是技术审核员
                "approval_mode": "any",  # any表示任意一人审批即可
                "time_limit_hours": 48,
                "step_order": 1
            },
            {
                "step_name": "质量审批",
                "approver_type": "role",
                "approver_ids": [3],  # 角色ID 3 通常是质量审批员
                "approval_mode": "any",
                "time_limit_hours": 24,
                "step_order": 2
            }
        ]
    }
    
    # 发送请求
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/approvals/workflows",
            headers=headers,
            json=workflow_data
        )
        
        if response.status_code == 200:
            print("✅ pPQR审批工作流创建成功！")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"❌ 创建失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        print("\n请确保：")
        print("1. 后端服务器正在运行 (http://localhost:8000)")
        print("2. 已登录系统并获取了有效的token")
        print("3. 在企业工作区中操作")

def print_instructions():
    """打印使用说明"""
    print("=" * 70)
    print("创建pPQR审批工作流")
    print("=" * 70)
    print("\n使用方法：")
    print("\n方法1: 使用API（推荐）")
    print("-" * 70)
    print("1. 打开浏览器，登录系统")
    print("2. 按F12打开开发者工具")
    print("3. 在Console中输入: localStorage.getItem('token')")
    print("4. 复制token值，替换本文件中的 TOKEN 变量")
    print("5. 确认 COMPANY_ID 是否正确（通常为1）")
    print("6. 运行: python create_ppqr_workflow.py")
    print("\n方法2: 使用Swagger UI（更简单）")
    print("-" * 70)
    print("1. 访问: http://localhost:8000/api/v1/docs")
    print("2. 点击右上角 'Authorize' 按钮")
    print("3. 输入token（格式: Bearer your_token）")
    print("4. 找到 'POST /api/v1/approvals/workflows' 接口")
    print("5. 点击 'Try it out'")
    print("6. 粘贴以下JSON到请求体：")
    print("\n" + json.dumps({
        "name": "pPQR标准审批流程",
        "description": "pPQR文档的标准审批流程",
        "document_type": "ppqr",
        "steps": [
            {
                "step_name": "技术审核",
                "approver_type": "role",
                "approver_ids": [2],
                "approval_mode": "any",
                "time_limit_hours": 48
            },
            {
                "step_name": "质量审批",
                "approver_type": "role",
                "approver_ids": [3],
                "approval_mode": "any",
                "time_limit_hours": 24
            }
        ]
    }, indent=2, ensure_ascii=False))
    print("\n7. 点击 'Execute'")
    print("\n方法3: 使用SQL（直接插入数据库）")
    print("-" * 70)
    print("运行 setup_approval_workflows.sql 文件")
    print("（需要修改其中的company_id为您的实际公司ID）")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    print_instructions()
    
    # 如果已经配置了TOKEN，可以取消下面的注释来执行
    # if TOKEN != "your_token_here":
    #     create_ppqr_workflow()
    # else:
    #     print("\n⚠️  请先配置TOKEN后再运行")

