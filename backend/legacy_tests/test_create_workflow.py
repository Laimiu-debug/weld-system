"""
测试创建工作流API
"""
import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

# 1. 先登录获取token
login_data = {
    "username": "testuser176070001@example.com",
    "password": "Test123456"
}

print("=== 步骤1: 登录 ===")
response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
print(f"状态码: {response.status_code}")
print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if response.status_code != 200:
    print("登录失败!")
    exit(1)

token = response.json()["access_token"]
print(f"Token: {token[:50]}...")

# 2. 获取工作区列表
print("\n=== 步骤2: 获取工作区列表 ===")
headers = {
    "Authorization": f"Bearer {token}"
}
response = requests.get(f"{BASE_URL}/workspace/workspaces", headers=headers)
print(f"状态码: {response.status_code}")
workspaces = response.json()
print(f"工作区数量: {len(workspaces)}")
for ws in workspaces:
    print(f"  - {ws['name']} (ID: {ws['id']}, Type: {ws['type']})")

# 找到企业工作区
enterprise_workspace = None
for ws in workspaces:
    if ws['type'] == 'enterprise':
        enterprise_workspace = ws
        break

if not enterprise_workspace:
    print("未找到企业工作区!")
    exit(1)

print(f"\n使用企业工作区: {enterprise_workspace['id']}")

# 3. 获取现有工作流
print("\n=== 步骤3: 获取现有工作流 ===")
headers["X-Workspace-ID"] = enterprise_workspace['id']
response = requests.get(f"{BASE_URL}/approvals/workflows", headers=headers)
print(f"状态码: {response.status_code}")
print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

# 4. 尝试创建新工作流
print("\n=== 步骤4: 创建新工作流 ===")
workflow_data = {
    "name": "测试工作流",
    "code": "TEST_WORKFLOW_001",
    "description": "这是一个测试工作流",
    "document_type": "wps",
    "steps": [
        {
            "step_name": "部门经理审批",
            "approver_type": "role",
            "approver_ids": [1],
            "approval_mode": "any",
            "time_limit_hours": 48
        }
    ],
    "is_active": True
}

response = requests.post(
    f"{BASE_URL}/approvals/workflows",
    headers=headers,
    json=workflow_data
)
print(f"状态码: {response.status_code}")
print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if response.status_code == 200:
    print("\n✅ 工作流创建成功!")
else:
    print(f"\n❌ 工作流创建失败!")
    print(f"错误详情: {response.json().get('detail', '未知错误')}")

