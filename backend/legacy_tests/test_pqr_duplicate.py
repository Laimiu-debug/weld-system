"""
测试PQR复制功能
"""
import sys
import os
import requests
import json

# 测试配置
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

# 测试用户凭证（需要先登录获取token）
TEST_EMAIL = "admin@example.com"
TEST_PASSWORD = "admin123"

def login():
    """登录获取token"""
    url = f"{API_URL}/auth/login"
    data = {
        "username": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            print(f"✅ 登录成功，获取token")
            return token
        else:
            print(f"❌ 登录失败: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ 登录错误: {e}")
        return None

def get_pqr_list(token):
    """获取PQR列表"""
    url = f"{API_URL}/pqr"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            pqrs = result.get("data", {}).get("items", [])
            print(f"✅ 获取到 {len(pqrs)} 个PQR")
            return pqrs
        else:
            print(f"❌ 获取PQR列表失败: {response.status_code}")
            print(response.text)
            return []
    except Exception as e:
        print(f"❌ 获取PQR列表错误: {e}")
        return []

def duplicate_pqr(token, pqr_id):
    """复制PQR"""
    url = f"{API_URL}/pqr/{pqr_id}/duplicate"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        print(f"\n正在复制PQR ID: {pqr_id}")
        print(f"请求URL: {url}")
        
        response = requests.post(url, headers=headers)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text[:500]}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 复制成功!")
            print(f"  新PQR ID: {result.get('id')}")
            print(f"  新PQR编号: {result.get('pqr_number')}")
            print(f"  新PQR标题: {result.get('title')}")
            return result
        else:
            print(f"❌ 复制失败: {response.status_code}")
            print(f"错误详情: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 复制错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数"""
    print("=" * 80)
    print("测试PQR复制功能")
    print("=" * 80)
    
    # 1. 登录
    print("\n1. 登录...")
    token = login()
    if not token:
        print("❌ 无法获取token，测试终止")
        return
    
    # 2. 获取PQR列表
    print("\n2. 获取PQR列表...")
    pqrs = get_pqr_list(token)
    if not pqrs:
        print("❌ 没有找到PQR，测试终止")
        return
    
    # 显示前5个PQR
    print("\n可用的PQR:")
    for i, pqr in enumerate(pqrs[:5]):
        print(f"  {i+1}. ID: {pqr.get('id')}, 编号: {pqr.get('pqr_number')}, 标题: {pqr.get('title')}")
    
    # 3. 复制第一个PQR
    print("\n3. 复制第一个PQR...")
    first_pqr = pqrs[0]
    result = duplicate_pqr(token, first_pqr.get('id'))
    
    if result:
        print("\n✅ 测试成功！")
    else:
        print("\n❌ 测试失败！")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

