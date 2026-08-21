"""
测试质量检验的is_qualified字段
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.quality import QualityInspection

def test_is_qualified():
    """测试is_qualified属性"""
    db = SessionLocal()
    
    try:
        # 查询一些质量检验记录
        inspections = db.query(QualityInspection).limit(10).all()
        
        print(f"\n找到 {len(inspections)} 条质量检验记录\n")
        print("=" * 80)
        
        for inspection in inspections:
            print(f"检验编号: {inspection.inspection_number}")
            print(f"  inspection_result (数据库): {inspection.inspection_result}")
            print(f"  result (属性): {inspection.result}")
            print(f"  is_qualified (计算): {inspection.is_qualified}")
            print("-" * 80)
        
        # 测试设置is_qualified
        if inspections:
            test_inspection = inspections[0]
            print(f"\n测试设置 is_qualified:")
            print(f"  原始 inspection_result: {test_inspection.inspection_result}")
            print(f"  原始 is_qualified: {test_inspection.is_qualified}")
            
            # 设置为合格
            test_inspection.is_qualified = True
            print(f"  设置 is_qualified = True 后:")
            print(f"    inspection_result: {test_inspection.inspection_result}")
            print(f"    is_qualified: {test_inspection.is_qualified}")
            
            # 设置为不合格
            test_inspection.is_qualified = False
            print(f"  设置 is_qualified = False 后:")
            print(f"    inspection_result: {test_inspection.inspection_result}")
            print(f"    is_qualified: {test_inspection.is_qualified}")
        
        print("\n✅ 测试完成！")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_is_qualified()

