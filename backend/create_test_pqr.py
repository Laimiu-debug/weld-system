"""
创建测试 PQR
"""
import requests
import json
from datetime import datetime

# API 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def login():
    """登录"""
    login_url = f"{API_BASE}/auth/login"
    response = requests.post(
        login_url,
        data={
            "username": "testuser@example.com",
            "password": "test123"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    else:
        print(f"登录失败: {response.text}")
        return None

def create_pqr(token):
    """创建 PQR"""
    url = f"{API_BASE}/pqr/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    pqr_data = {
        "pqr_number": f"TEST-PQR-{int(datetime.now().timestamp())}",
        "title": "测试PQR用于复制功能",
        "test_date": datetime.now().strftime("%Y-%m-%d"),
        "qualification_result": "qualified",
        "wps_number": "WPS-001",
        "company": "测试公司",
        "project_name": "测试项目",
        "test_location": "测试地点",
        "welding_operator": "测试焊工",
        "welding_process": "SMAW",
        "base_material_spec": "Q235",
        "filler_material_spec": "E4303",
        "shielding_gas": "None",
        "modules_data": {}
    }
    
    response = requests.post(url, headers=headers, json=pqr_data)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ PQR 创建成功！")
        print(f"  ID: {data.get('id')}")
        print(f"  编号: {data.get('pqr_number')}")
        print(f"  标题: {data.get('title')}")
        return data
    else:
        print(f"❌ PQR 创建失败: {response.status_code}")
        print(f"响应: {response.text}")
        return None

def main():
    print("创建测试 PQR...")
    
    # 登录
    token = login()
    if not token:
        print("❌ 登录失败")
        return
    
    print("✅ 登录成功")
    
    # 创建 PQR
    pqr = create_pqr(token)
    if pqr:
        print("\n✅ 测试 PQR 创建完成！")
    else:
        print("\n❌ 测试 PQR 创建失败")

if __name__ == "__main__":
    main()

