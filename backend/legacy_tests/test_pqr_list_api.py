"""
测试PQR列表API
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.services.pqr_service import pqr_service

def test_pqr_list():
    """测试PQR列表查询"""
    db: Session = SessionLocal()
    
    try:
        print("=" * 80)
        print("测试 PQR 列表查询")
        print("=" * 80)
        
        # 1. 获取测试用户
        print("\n1. 获取测试用户...")
        user = db.query(User).first()
        if not user:
            print("   ❌ 没有找到用户")
            return
        print(f"   ✅ 使用用户: {user.email} (ID: {user.id})")
        
        # 2. 查询总数
        print("\n2. 查询PQR总数...")
        total = pqr_service.count(db)
        print(f"   ✅ 总记录数: {total}")
        
        # 3. 查询列表（第1页）
        print("\n3. 查询PQR列表（第1页，每页20条）...")
        pqr_list = pqr_service.get_multi(db, skip=0, limit=20)
        print(f"   ✅ 返回记录数: {len(pqr_list)}")
        
        if pqr_list:
            print("\n   前3条记录:")
            for i, pqr in enumerate(pqr_list[:3], 1):
                print(f"   {i}. ID={pqr.id}, 编号={pqr.pqr_number}, 标题={pqr.title}")
        else:
            print("   ⚠️  没有找到PQR记录")
        
        # 4. 测试搜索
        print("\n4. 测试搜索功能...")
        search_count = pqr_service.count(db, search_term="PQR")
        print(f"   ✅ 包含'PQR'的记录数: {search_count}")
        
        # 5. 测试按用户过滤
        print("\n5. 测试按用户过滤...")
        user_count = pqr_service.count(db, owner_id=user.id)
        print(f"   ✅ 用户 {user.id} 的PQR数量: {user_count}")
        
        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)
        
    finally:
        db.close()

if __name__ == "__main__":
    test_pqr_list()

