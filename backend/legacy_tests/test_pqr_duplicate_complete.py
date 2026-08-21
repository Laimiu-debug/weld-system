"""
完整测试 PQR 复制功能
"""
import requests
import json
from datetime import datetime

# API 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def login():
    """登录获取 token"""
    print("\n" + "=" * 80)
    print("步骤 1: 登录获取 token")
    print("=" * 80)
    
    login_url = f"{API_BASE}/auth/login"
    
    # 尝试不同的用户
    users = [
        {"username": "testuser", "password": "test123"},
    ]
    
    for user in users:
        try:
            print(f"\n尝试登录用户: {user['username']}")

            # 尝试使用 username
            response = requests.post(
                login_url,
                data={
                    "username": user["username"],
                    "password": user["password"]
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            # 如果失败，尝试使用 email
            if response.status_code != 200 and "@" not in user["username"]:
                print(f"  尝试使用 email 登录...")
                email = user.get("email", f"{user['username']}@example.com")
                response = requests.post(
                    login_url,
                    data={
                        "username": email,
                        "password": user["password"]
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                print(f"✅ 登录成功！")
                print(f"Token: {token[:50]}...")
                return token
            else:
                print(f"❌ 登录失败: {response.status_code}")
                print(f"响应: {response.text}")
        except Exception as e:
            print(f"❌ 登录异常: {e}")
    
    print("\n❌ 所有用户登录都失败了")
    return None

def get_pqr_list(token):
    """获取 PQR 列表"""
    print("\n" + "=" * 80)
    print("步骤 2: 获取 PQR 列表")
    print("=" * 80)
    
    url = f"{API_BASE}/pqr/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 尝试不同的工作区类型
    workspace_types = ["personal", "enterprise"]
    
    for workspace_type in workspace_types:
        try:
            print(f"\n尝试获取 {workspace_type} 工作区的 PQR 列表")
            params = {
                "workspace_type": workspace_type,
                "page": 1,
                "page_size": 10
            }
            
            if workspace_type == "enterprise":
                params["company_id"] = 1
            
            response = requests.get(url, headers=headers, params=params)
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                print(f"✅ 获取成功！找到 {len(items)} 个 PQR")
                
                if items:
                    for i, pqr in enumerate(items[:3], 1):
                        print(f"\nPQR {i}:")
                        print(f"  ID: {pqr.get('id')}")
                        print(f"  编号: {pqr.get('pqr_number')}")
                        print(f"  标题: {pqr.get('title')}")
                    
                    return items[0], workspace_type, params.get("company_id")
                else:
                    print("⚠️  列表为空，尝试下一个工作区类型")
            else:
                print(f"❌ 获取失败: {response.text}")
        except Exception as e:
            print(f"❌ 异常: {e}")
    
    print("\n❌ 无法获取 PQR 列表")
    return None, None, None

def duplicate_pqr(token, pqr_id, workspace_type, company_id):
    """复制 PQR"""
    print("\n" + "=" * 80)
    print(f"步骤 3: 复制 PQR (ID: {pqr_id})")
    print("=" * 80)
    
    url = f"{API_BASE}/pqr/{pqr_id}/duplicate"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "workspace_type": workspace_type
    }
    
    if company_id:
        params["company_id"] = company_id
    
    print(f"\n请求 URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        response = requests.post(url, headers=headers, params=params)
        
        print(f"\n状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 复制成功！")
            print(f"\n新 PQR 信息:")
            print(f"  ID: {data.get('id')}")
            print(f"  编号: {data.get('pqr_number')}")
            print(f"  标题: {data.get('title')}")
            print(f"  评定结果: {data.get('qualification_result')}")
            return True
        else:
            print(f"❌ 复制失败")
            print(f"响应: {response.text}")
            
            # 尝试解析错误信息
            try:
                error_data = response.json()
                print(f"\n错误详情:")
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                pass
            
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_duplicate(token, original_pqr, workspace_type, company_id):
    """验证复制结果"""
    print("\n" + "=" * 80)
    print("步骤 4: 验证复制结果")
    print("=" * 80)
    
    url = f"{API_BASE}/pqr/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "workspace_type": workspace_type,
        "page": 1,
        "page_size": 20
    }
    
    if company_id:
        params["company_id"] = company_id
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            
            # 查找副本（标题包含 "副本"）
            original_title = original_pqr.get("title")
            duplicates = [pqr for pqr in items if "副本" in pqr.get("title", "")]
            
            if duplicates:
                print(f"✅ 找到 {len(duplicates)} 个副本:")
                for dup in duplicates:
                    print(f"\n  副本:")
                    print(f"    ID: {dup.get('id')}")
                    print(f"    编号: {dup.get('pqr_number')}")
                    print(f"    标题: {dup.get('title')}")
                    print(f"    评定结果: {dup.get('qualification_result')}")
                return True
            else:
                print("⚠️  未找到副本")
                return False
        else:
            print(f"❌ 验证失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("PQR 复制功能完整测试")
    print("=" * 80)
    
    # 步骤 1: 登录
    token = login()
    if not token:
        print("\n❌ 测试失败：无法登录")
        return
    
    # 步骤 2: 获取 PQR 列表
    pqr, workspace_type, company_id = get_pqr_list(token)
    if not pqr:
        print("\n❌ 测试失败：无法获取 PQR 列表")
        return
    
    # 步骤 3: 复制 PQR
    success = duplicate_pqr(token, pqr.get("id"), workspace_type, company_id)
    if not success:
        print("\n❌ 测试失败：复制 PQR 失败")
        return
    
    # 步骤 4: 验证复制结果
    verified = verify_duplicate(token, pqr, workspace_type, company_id)
    
    # 最终结果
    print("\n" + "=" * 80)
    print("测试结果")
    print("=" * 80)
    
    if success and verified:
        print("\n✅ 测试成功！PQR 复制功能正常工作！")
    elif success:
        print("\n⚠️  复制成功，但验证未通过")
    else:
        print("\n❌ 测试失败")
    
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()

