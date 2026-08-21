"""
测试 /users/me-membership API 端点
"""
import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import create_access_token

# 创建测试客户端
client = TestClient(app)

# 获取测试用户
db = SessionLocal()
try:
    user = db.query(User).filter(User.email == 'testuser176070002@example.com').first()
    if not user:
        print('用户不存在')
        sys.exit(1)
    
    # 创建访问令牌
    access_token = create_access_token(subject=str(user.id))
    
    # 调用 API
    response = client.get(
        '/api/v1/users/me-membership',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    print(f'状态码: {response.status_code}')
    print(f'响应内容:')
    
    if response.status_code == 200:
        import json
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        print('\n=== 功能列表 ===')
        for i, feature in enumerate(data.get('features', []), 1):
            print(f'{i}. {feature}')
    else:
        print(response.text)
        
finally:
    db.close()

