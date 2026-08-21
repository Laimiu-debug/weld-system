"""
测试分享模板端点
"""
import requests
import json

# 测试数据
test_data = {
    "original_template_id": "test_template_id",
    "name": "测试模板",
    "description": "测试描述",
    "welding_process": "111",
    "welding_process_name": "手工电弧焊",
    "standard": "AWS",
    "module_instances": [],
    "tags": ["WPS", "焊接工艺"],
    "difficulty_level": "beginner",
    "changelog": "初始分享版本"
}

# 测试token（需要替换为真实的token）
token = "your_token_here"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

try:
    print("正在测试分享模板端点...")
    print(f"URL: http://localhost:8000/api/v1/shared-library/templates/share")
    print(f"数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    response = requests.post(
        "http://localhost:8000/api/v1/shared-library/templates/share",
        json=test_data,
        headers=headers,
        timeout=10
    )
    
    print(f"\n状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应内容: {response.text}")
    
except Exception as e:
    print(f"\n错误: {e}")

