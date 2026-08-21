"""
测试pPQR编辑功能的脚本
"""
import requests
import json

# 配置
BASE_URL = "http://localhost:8000/api/v1"
# 请替换为有效的认证token
AUTH_TOKEN = "YOUR_AUTH_TOKEN_HERE"

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

def test_get_ppqr_detail(ppqr_id: int):
    """测试获取pPQR详情"""
    print(f"\n{'='*60}")
    print(f"测试获取pPQR详情 (ID: {ppqr_id})")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/ppqr/{ppqr_id}"
    
    try:
        response = requests.get(url, headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 获取成功!")
            print(f"\n响应数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        else:
            print(f"❌ 获取失败!")
            print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return None


def test_update_ppqr(ppqr_id: int, update_data: dict):
    """测试更新pPQR"""
    print(f"\n{'='*60}")
    print(f"测试更新pPQR (ID: {ppqr_id})")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/ppqr/{ppqr_id}"
    
    print(f"\n更新数据:")
    print(json.dumps(update_data, indent=2, ensure_ascii=False))
    
    try:
        response = requests.put(url, headers=headers, json=update_data)
        print(f"\n状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 更新成功!")
            print(f"\n响应数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        else:
            print(f"❌ 更新失败!")
            print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return None


def test_ppqr_list():
    """测试获取pPQR列表"""
    print(f"\n{'='*60}")
    print(f"测试获取pPQR列表")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/ppqr/"
    
    try:
        response = requests.get(url, headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 获取成功!")
            
            if 'items' in data and len(data['items']) > 0:
                print(f"\n找到 {len(data['items'])} 条pPQR记录")
                print(f"\n第一条记录:")
                print(json.dumps(data['items'][0], indent=2, ensure_ascii=False))
                return data['items'][0]['id']
            else:
                print(f"⚠️  列表为空")
                return None
        else:
            print(f"❌ 获取失败!")
            print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return None


if __name__ == "__main__":
    print("="*60)
    print("pPQR编辑功能测试")
    print("="*60)
    
    # 检查token
    if AUTH_TOKEN == "YOUR_AUTH_TOKEN_HERE":
        print("\n⚠️  请先设置有效的认证token!")
        print("1. 登录系统获取token")
        print("2. 在脚本中替换 AUTH_TOKEN 的值")
        exit(1)
    
    # 1. 获取pPQR列表，找到第一个pPQR的ID
    ppqr_id = test_ppqr_list()
    
    if not ppqr_id:
        print("\n⚠️  没有找到pPQR记录，请先创建一个pPQR")
        exit(1)
    
    # 2. 获取pPQR详情
    ppqr_detail = test_get_ppqr_detail(ppqr_id)
    
    if not ppqr_detail:
        print("\n❌ 无法获取pPQR详情")
        exit(1)
    
    # 3. 更新pPQR
    update_data = {
        "title": f"{ppqr_detail.get('title', 'Test')} (已编辑)",
        "modules_data": ppqr_detail.get('modules_data', {})
    }
    
    updated_ppqr = test_update_ppqr(ppqr_id, update_data)
    
    if updated_ppqr:
        print("\n" + "="*60)
        print("✅ 所有测试通过!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ 测试失败!")
        print("="*60)

