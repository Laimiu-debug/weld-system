"""
测试PQR详情API
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.services.pqr_service import pqr_service
from app.schemas.pqr import PQRResponse
import json

def test_pqr_detail_api():
    """测试PQR详情API"""
    db: Session = SessionLocal()
    
    try:
        print("=" * 80)
        print("测试 PQR 详情 API")
        print("=" * 80)
        
        # 1. 获取测试用户
        print("\n1. 获取测试用户...")
        user = db.query(User).first()
        if not user:
            print("   ❌ 没有找到用户")
            return
        print(f"   ✅ 使用用户: {user.email} (ID: {user.id})")
        
        # 2. 查询PQR列表
        print("\n2. 查询PQR列表...")
        pqr_list = pqr_service.get_multi(db, skip=0, limit=10)
        print(f"   ✅ 找到 {len(pqr_list)} 条PQR记录")
        
        if not pqr_list:
            print("   ⚠️  没有PQR记录")
            return
        
        test_pqr = pqr_list[0]
        print(f"   使用测试PQR: {test_pqr.pqr_number} (ID: {test_pqr.id})")
        
        # 3. 测试获取单个PQR详情
        print("\n3. 测试获取单个PQR详情...")
        pqr = pqr_service.get(db, id=test_pqr.id)
        if not pqr:
            print("   ❌ 获取PQR失败")
            return
        
        print(f"   ✅ 成功获取PQR")
        print(f"      - ID: {pqr.id}")
        print(f"      - 编号: {pqr.pqr_number}")
        print(f"      - 标题: {pqr.title}")
        print(f"      - 状态: {pqr.status}")
        print(f"      - 评定结果: {pqr.qualification_result}")
        print(f"      - 模板ID: {pqr.template_id}")
        print(f"      - 模块数据: {'有' if pqr.modules_data else '无'}")
        
        # 4. 测试转换为 PQRResponse schema
        print("\n4. 测试转换为 PQRResponse schema...")
        try:
            pqr_response = PQRResponse.model_validate(pqr)
            print("   ✅ 成功转换为 PQRResponse")
            
            # 转换为字典
            pqr_dict = pqr_response.model_dump()
            
            # 检查关键字段
            required_fields = ['id', 'title', 'pqr_number', 'status', 'template_id', 'modules_data', 'created_at', 'updated_at']
            missing_fields = [f for f in required_fields if f not in pqr_dict]
            
            if missing_fields:
                print(f"   ⚠️  缺少字段: {missing_fields}")
            else:
                print("   ✅ 所有关键字段都存在")
            
            # 显示部分字段
            print("\n   关键字段值:")
            for field in required_fields:
                value = pqr_dict.get(field)
                if isinstance(value, dict):
                    print(f"      - {field}: {json.dumps(value, ensure_ascii=False)[:100]}...")
                else:
                    print(f"      - {field}: {value}")
            
        except Exception as e:
            print(f"   ❌ 转换失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)
        print("✅ PQR 详情 API 测试完成")
        print("=" * 80)
        
    finally:
        db.close()

if __name__ == "__main__":
    test_pqr_detail_api()

