#!/usr/bin/env python
"""
Test script to verify the new modules_data JSONB field structure.
"""
import json
from app.core.database import SessionLocal
from app.models.wps import WPS

def test_modules_data_structure():
    """Test the new modules_data structure."""
    db = SessionLocal()
    
    print("=" * 70)
    print("🧪 测试新的 modules_data 结构")
    print("=" * 70)
    
    # Get the latest WPS records
    wps_list = db.query(WPS).order_by(WPS.created_at.desc()).limit(3).all()
    
    if not wps_list:
        print("❌ 没有找到 WPS 记录")
        return False
    
    for wps in wps_list:
        print(f"\n📋 WPS ID: {wps.id}")
        print(f"   标题: {wps.title}")
        print(f"   WPS编号: {wps.wps_number}")
        
        # Check modules_data
        if wps.modules_data:
            print(f"\n   ✅ modules_data 字段存在:")
            print(f"   {json.dumps(wps.modules_data, indent=6, ensure_ascii=False)}")
        else:
            print(f"\n   ⚠️  modules_data 字段为空")
        
        # Check old fields (for backward compatibility)
        if wps.header_info:
            print(f"\n   📌 header_info (旧字段):")
            print(f"   {json.dumps(wps.header_info, indent=6, ensure_ascii=False)}")
        
        if wps.summary_info:
            print(f"\n   📌 summary_info (旧字段):")
            print(f"   {json.dumps(wps.summary_info, indent=6, ensure_ascii=False)}")
        
        print("\n" + "-" * 70)
    
    print("\n✅ 测试完成！")
    print("=" * 70)
    return True

if __name__ == "__main__":
    test_modules_data_structure()

