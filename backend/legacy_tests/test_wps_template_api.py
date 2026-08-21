"""
测试WPS模板API
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# 1. 测试登录获取token
def test_login():
    print("=" * 80)
    print("测试登录")
    print("=" * 80)
    
    login_data = {
        "username": "testuser176070001@example.com",
        "password": "password123"
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data=login_data
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"登录成功!")
        print(f"Token: {data.get('access_token', '')[:50]}...")
        return data.get('access_token')
    else:
        print(f"登录失败: {response.text}")
        return None

# 2. 测试获取模板列表
def test_get_templates(token):
    print("\n" + "=" * 80)
    print("测试获取模板列表")
    print("=" * 80)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Workspace-ID": "personal_21"
    }
    
    response = requests.get(
        f"{BASE_URL}/wps-templates/",
        headers=headers
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"获取成功! 共 {data.get('total', 0)} 个模板")
        if data.get('items'):
            print(f"第一个模板: {data['items'][0].get('name')}")
    else:
        print(f"获取失败: {response.text}")

# 3. 测试创建模板
def test_create_template(token):
    print("\n" + "=" * 80)
    print("测试创建模板")
    print("=" * 80)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Workspace-ID": "personal_21"
    }
    
    template_data = {
        "name": "测试模板 - API测试",
        "description": "这是一个API测试模板",
        "welding_process": "111",
        "standard": "GB/T 15169",
        "workspace_type": "personal",
        "module_instances": [
            {
                "instanceId": "test-instance-1",
                "moduleId": "basic_info",
                "order": 1,
                "rowIndex": 0,
                "columnIndex": 0
            }
        ]
    }
    
    print(f"请求数据: {json.dumps(template_data, indent=2, ensure_ascii=False)}")
    
    response = requests.post(
        f"{BASE_URL}/wps-templates/",
        headers=headers,
        json=template_data
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"创建成功!")
        print(f"模板ID: {data.get('id')}")
        print(f"模板名称: {data.get('name')}")
        return data.get('id')
    else:
        print(f"创建失败: {response.text}")
        return None

if __name__ == "__main__":
    # 测试流程
    token = test_login()
    
    if token:
        test_get_templates(token)
        template_id = test_create_template(token)
        
        if template_id:
            print(f"\n✅ 所有测试通过!")
        else:
            print(f"\n❌ 创建模板失败")
    else:
        print(f"\n❌ 登录失败，无法继续测试")

