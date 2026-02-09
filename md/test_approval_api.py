"""
测试审批API的脚本
用于诊断CORS和500错误问题
"""
import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

def test_cors():
    """测试CORS配置"""
    print("=" * 50)
    print("测试CORS配置")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_URL}/debug/cors-test")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        print("✓ CORS测试成功")
    except Exception as e:
        print(f"✗ CORS测试失败: {str(e)}")
    print()

def test_approval_submit():
    """测试提交审批API"""
    print("=" * 50)
    print("测试提交审批API")
    print("=" * 50)
    
    # 首先需要登录获取token
    # 这里假设您已经有了token，请替换为实际的token
    token = "YOUR_TOKEN_HERE"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Workspace-ID": "enterprise_1"  # 根据实际情况修改
    }
    
    data = {
        "document_type": "pqr",
        "document_ids": [1],
        "notes": "测试提交审批"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/approvals/submit",
            headers=headers,
            json=data
        )
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"响应: {response.json()}")
            print("✓ 提交审批成功")
        else:
            print(f"响应: {response.text}")
            print("✗ 提交审批失败")
    except Exception as e:
        print(f"✗ 请求失败: {str(e)}")
    print()

def check_server():
    """检查服务器是否运行"""
    print("=" * 50)
    print("检查服务器状态")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/docs")
        if response.status_code == 200:
            print("✓ 后端服务器正在运行")
            print(f"  API文档地址: {BASE_URL}/api/v1/docs")
        else:
            print(f"✗ 服务器响应异常: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到后端服务器")
        print("  请确保后端服务器正在运行在 http://localhost:8000")
    except Exception as e:
        print(f"✗ 检查失败: {str(e)}")
    print()

if __name__ == "__main__":
    print("\n审批API诊断工具\n")
    
    # 1. 检查服务器
    check_server()
    
    # 2. 测试CORS
    test_cors()
    
    # 3. 测试提交审批（需要token）
    # test_approval_submit()
    
    print("\n诊断完成")
    print("\n如果看到CORS错误，请检查:")
    print("1. 后端服务器是否正在运行")
    print("2. backend/app/core/config.py 中的 DEVELOPMENT 设置是否为 True")
    print("3. backend/app/main.py 中的 CORS 中间件配置")
    print("\n如果看到500错误，请检查:")
    print("1. 后端日志中的详细错误信息")
    print("2. 数据库连接是否正常")
    print("3. 审批工作流是否已配置")

