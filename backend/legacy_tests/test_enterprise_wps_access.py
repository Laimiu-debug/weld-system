"""
测试企业会员访问WPS列表的权限
"""
import requests
import json
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import create_access_token

# 获取测试用户
db = SessionLocal()
user = db.query(User).filter(User.email == "testuser176070001@example.com").first()

if not user:
    print("❌ 用户不存在: testuser176070001@example.com")
    db.close()
    exit(1)

print(f"✅ 找到用户: {user.email}")
print(f"   会员类型: {user.membership_type}")
print(f"   会员等级: {user.member_tier}")

# 创建访问令牌
access_token = create_access_token(user.id)
print(f"\n✅ 生成访问令牌")

# 测试WPS列表API
print("\n" + "="*80)
print("测试WPS列表API")
print("="*80)

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# 测试获取WPS列表
print("\n1. 测试获取WPS列表...")
response = requests.get(
    "http://localhost:8000/api/v1/wps/",
    headers=headers
)

print(f"   状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ 成功获取WPS列表")
    print(f"   返回记录数: {len(data)}")
    if len(data) > 0:
        print(f"   第一条记录: {data[0].get('wps_number', 'N/A')} - {data[0].get('title', 'N/A')}")
else:
    print(f"   ❌ 请求失败")
    print(f"   响应: {response.text}")

# 测试WPS统计API
print("\n2. 测试获取WPS统计...")
response = requests.get(
    "http://localhost:8000/api/v1/wps/statistics/overview",
    headers=headers
)

print(f"   状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ 成功获取WPS统计")
    print(f"   统计数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
else:
    print(f"   ❌ 请求失败")
    print(f"   响应: {response.text}")

# 测试WPS模板API
print("\n3. 测试获取WPS模板列表...")
response = requests.get(
    "http://localhost:8000/api/v1/wps-templates/",
    headers=headers
)

print(f"   状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ 成功获取WPS模板列表")
    print(f"   总数: {data.get('total', 0)}")
    print(f"   返回记录数: {len(data.get('items', []))}")
    if len(data.get('items', [])) > 0:
        print(f"   第一个模板: {data['items'][0].get('name', 'N/A')}")
else:
    print(f"   ❌ 请求失败")
    print(f"   响应: {response.text}")

db.close()
print("\n" + "="*80)
print("测试完成")
print("="*80)

