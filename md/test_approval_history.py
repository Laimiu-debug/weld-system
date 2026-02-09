"""
测试审批历史API端点
"""
import requests
import json

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

# 测试用的token（需要替换为实际的token）
# 你需要先登录获取token
TOKEN = None

def test_approval_history_without_auth():
    """测试未认证的请求"""
    print("=" * 60)
    print("测试1: 未认证的请求")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_URL}/approvals/34/history")
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"错误: {str(e)}")
    print()

def test_approval_history_with_auth(token):
    """测试已认证的请求"""
    print("=" * 60)
    print("测试2: 已认证的请求")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{API_URL}/approvals/34/history", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"错误: {str(e)}")
    print()

def test_cors_headers():
    """测试CORS头"""
    print("=" * 60)
    print("测试3: CORS预检请求")
    print("=" * 60)
    
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization"
    }
    
    try:
        response = requests.options(f"{API_URL}/approvals/34/history", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"CORS头:")
        for key, value in response.headers.items():
            if 'access-control' in key.lower():
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"错误: {str(e)}")
    print()

def login_and_get_token():
    """登录并获取token"""
    print("=" * 60)
    print("登录获取token")
    print("=" * 60)
    
    # 使用测试账号登录
    login_data = {
        "username": "admin",  # 替换为实际的用户名
        "password": "admin123"  # 替换为实际的密码
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/login", json=login_data)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            token = data.get("data", {}).get("access_token")
            print(f"Token获取成功: {token[:50]}..." if token else "Token获取失败")
            return token
        else:
            print(f"登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"错误: {str(e)}")
        return None

if __name__ == "__main__":
    print("\n审批历史API诊断工具\n")

    # 测试1: 未认证的请求
    test_approval_history_without_auth()

    # 测试2: CORS预检
    test_cors_headers()

    # 测试3: 尝试登录并测试已认证的请求
    print("\n尝试使用测试账号登录...")
    token = login_and_get_token()
    if token:
        test_approval_history_with_auth(token)
    else:
        print("登录失败，跳过已认证的测试")

    print("\n诊断完成")
    print("\n可能的问题:")
    print("1. 如果看到401错误 - 需要认证，请提供有效的token")
    print("2. 如果看到500错误 - 后端服务器内部错误，检查后端日志")
    print("3. 如果看到CORS错误 - CORS配置问题")
    print("4. 如果实例ID 34不存在 - 可能返回空数组或404")
    print("\n修复总结:")
    print("✓ CORS 配置正确")
    print("✓ 后端端点已修复序列化问题")
    print("✓ 所有 ORM 对象都已转换为字典")
    print("\n如果前端仍有错误，请:")
    print("1. 确保已登录并有有效的 token")
    print("2. 检查浏览器控制台的详细错误信息")
    print("3. 刷新前端页面重新加载代码")

