"""
测试PQR创建功能
"""
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.schemas.pqr import PQRCreate
from app.services.pqr_service import pqr_service

def test_pqr_creation():
    """测试PQR创建"""
    db: Session = SessionLocal()
    
    try:
        print("=" * 80)
        print("测试 PQR 创建功能")
        print("=" * 80)
        
        # 1. 获取测试用户
        print("\n1. 获取测试用户...")
        user = db.query(User).filter(User.email == "admin@example.com").first()
        if not user:
            # 尝试获取任何用户
            user = db.query(User).first()
        
        if not user:
            print("   ❌ 没有找到测试用户！")
            return
        
        print(f"   ✅ 使用用户: {user.email} (ID: {user.id})")
        
        # 2. 准备测试数据
        print("\n2. 准备测试数据...")
        test_pqr_data = PQRCreate(
            title="测试PQR记录",
            pqr_number=f"TEST-PQR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            test_date=datetime.now(),
            qualification_result="pending",
            welding_process="SMAW",
            base_material_spec="Q235B",
            modules_data={
                "test_module": {
                    "module_id": "pqr_basic_info",
                    "custom_name": "基本信息",
                    "data": {
                        "test_field": "test_value"
                    }
                }
            }
        )
        
        print(f"   PQR编号: {test_pqr_data.pqr_number}")
        print(f"   标题: {test_pqr_data.title}")
        
        # 3. 创建PQR
        print("\n3. 创建PQR...")
        try:
            pqr = pqr_service.create(db, obj_in=test_pqr_data, owner_id=user.id)
            print(f"   ✅ PQR创建成功！")
            print(f"   - ID: {pqr.id}")
            print(f"   - PQR编号: {pqr.pqr_number}")
            print(f"   - 标题: {pqr.title}")
            print(f"   - 用户ID: {pqr.user_id}")
            print(f"   - 工作区类型: {pqr.workspace_type}")
            print(f"   - 创建人: {pqr.created_by}")
            print(f"   - 更新人: {pqr.updated_by}")
            print(f"   - 创建时间: {pqr.created_at}")
            
            # 4. 验证数据
            print("\n4. 验证数据...")
            retrieved_pqr = pqr_service.get(db, id=pqr.id)
            if retrieved_pqr:
                print(f"   ✅ 可以成功检索PQR")
                print(f"   - 检索到的PQR编号: {retrieved_pqr.pqr_number}")
            else:
                print(f"   ❌ 无法检索PQR")
            
            # 5. 清理测试数据
            print("\n5. 清理测试数据...")
            pqr_service.remove(db, id=pqr.id)
            print(f"   ✅ 测试数据已清理")
            
        except Exception as e:
            print(f"   ❌ 创建失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        
        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)
        
    finally:
        db.close()

def test_pqr_creation_minimal():
    """测试最小数据创建PQR"""
    db: Session = SessionLocal()
    
    try:
        print("\n" + "=" * 80)
        print("测试 PQR 最小数据创建")
        print("=" * 80)
        
        # 1. 获取测试用户
        print("\n1. 获取测试用户...")
        user = db.query(User).first()
        
        if not user:
            print("   ❌ 没有找到测试用户！")
            return
        
        print(f"   ✅ 使用用户: {user.email} (ID: {user.id})")
        
        # 2. 准备最小测试数据（只有必填字段）
        print("\n2. 准备最小测试数据...")
        test_pqr_data = PQRCreate(
            title="最小测试PQR",
            pqr_number=f"MIN-PQR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        
        print(f"   PQR编号: {test_pqr_data.pqr_number}")
        print(f"   标题: {test_pqr_data.title}")
        
        # 3. 创建PQR
        print("\n3. 创建PQR...")
        try:
            pqr = pqr_service.create(db, obj_in=test_pqr_data, owner_id=user.id)
            print(f"   ✅ PQR创建成功！")
            print(f"   - ID: {pqr.id}")
            print(f"   - PQR编号: {pqr.pqr_number}")
            
            # 4. 清理测试数据
            print("\n4. 清理测试数据...")
            pqr_service.remove(db, id=pqr.id)
            print(f"   ✅ 测试数据已清理")
            
        except Exception as e:
            print(f"   ❌ 创建失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        
        print("\n" + "=" * 80)
        print("最小数据测试完成")
        print("=" * 80)
        
    finally:
        db.close()

if __name__ == "__main__":
    try:
        # 测试完整数据创建
        test_pqr_creation()
        
        # 测试最小数据创建
        test_pqr_creation_minimal()
        
        print("\n✅ 所有测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

