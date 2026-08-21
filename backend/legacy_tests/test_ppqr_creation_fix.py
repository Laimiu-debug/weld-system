"""
测试pPQR创建功能修复
"""
import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
# 请替换为有效的token
TOKEN = "test_token_21"

def test_ppqr_creation():
    """测试pPQR创建"""
    url = f"{BASE_URL}/api/v1/ppqr/"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "ppqr_number": f"TEST-PPQR-{requests.utils.quote(str(hash('test'))[:8])}",
        "title": "测试pPQR创建",
        "status": "draft",
        "template_id": "1",
        "revision": "A",
        "module_data": {}
    }
    
    print(f"发送请求到: {url}")
    print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        print(f"\n状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ pPQR创建成功!")
            result = response.json()
            print(f"创建的pPQR ID: {result.get('id')}")
            print(f"pPQR编号: {result.get('ppqr_number')}")
        else:
            print(f"\n❌ pPQR创建失败!")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"\n❌ 请求失败: {str(e)}")

if __name__ == "__main__":
    test_ppqr_creation()

