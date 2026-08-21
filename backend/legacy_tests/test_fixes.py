"""
测试修复：PQR复制和质量检验is_qualified
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.quality import QualityInspection
from app.schemas.quality import QualityInspectionResponse

def test_quality_is_qualified():
    """测试质量检验的is_qualified字段"""
    print("\n" + "=" * 80)
    print("测试1: 质量检验 is_qualified 字段")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # 查询质量检验记录
        inspections = db.query(QualityInspection).limit(5).all()
        
        if not inspections:
            print("⚠️  没有找到质量检验记录")
            return
        
        print(f"\n找到 {len(inspections)} 条质量检验记录\n")
        
        for inspection in inspections:
            print(f"检验编号: {inspection.inspection_number}")
            print(f"  inspection_result: {inspection.inspection_result}")
            print(f"  is_qualified (属性): {inspection.is_qualified}")

            # 测试序列化为响应Schema
            try:
                response = QualityInspectionResponse.model_validate(inspection)
                print(f"  响应Schema中的result: {response.result}")
                print(f"  响应Schema中的is_qualified: {response.is_qualified}")
                print(f"  ✅ Schema序列化成功")
            except Exception as e:
                print(f"  ❌ Schema序列化失败: {e}")

            print("-" * 80)
        
        # 测试设置不同的值
        print("\n测试设置不同的 inspection_result 值:")
        test_inspection = inspections[0]
        
        test_cases = [
            ("pass", True),
            ("fail", False),
            ("conditional", False),
            ("pending", False),
            (None, False),
        ]
        
        for result_value, expected_qualified in test_cases:
            test_inspection.inspection_result = result_value
            actual_qualified = test_inspection.is_qualified
            status = "✅" if actual_qualified == expected_qualified else "❌"
            print(f"  {status} inspection_result='{result_value}' → is_qualified={actual_qualified} (期望: {expected_qualified})")
        
        print("\n✅ 质量检验 is_qualified 测试完成！")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def test_pqr_service_import():
    """测试PQR服务导入"""
    print("\n" + "=" * 80)
    print("测试2: PQR 服务导入")
    print("=" * 80)
    
    try:
        from app.services.pqr_service import PQRService
        print("✅ PQRService 导入成功")
        
        db = SessionLocal()
        try:
            pqr_service = PQRService(db)
            print("✅ PQRService 实例化成功")
            
            # 测试获取PQR列表
            from app.models.pqr import PQR
            pqrs = db.query(PQR).limit(3).all()
            print(f"✅ 找到 {len(pqrs)} 个PQR记录")
            
            if pqrs:
                for pqr in pqrs:
                    print(f"  - PQR ID: {pqr.id}, 编号: {pqr.pqr_number}, 标题: {pqr.title}")
        finally:
            db.close()
        
        print("\n✅ PQR 服务测试完成！")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("修复验证测试")
    print("=" * 80)
    
    test_quality_is_qualified()
    test_pqr_service_import()
    
    print("\n" + "=" * 80)
    print("所有测试完成！")
    print("=" * 80)
    print("\n下一步:")
    print("1. 重启后端服务以加载新代码")
    print("2. 刷新前端页面")
    print("3. 测试 PQR 复制功能")
    print("4. 测试质量检验列表显示")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()

