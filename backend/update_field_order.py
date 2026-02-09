"""
更新焊层字段顺序脚本
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from app.core.database import engine

# 111模板的新字段顺序
fields_111 = {
    "welding_process": {"label": "焊接工艺", "type": "select", "options": ["111"], "default": "111"},
    "welding_method_type": {"label": "焊接方法类型", "type": "text"},
    "pass_number": {"label": "焊接道次", "type": "number"},
    "layer_id": {"label": "焊道id", "type": "text"},
    "groove_thickness": {"label": "熔覆金属坡口焊缝厚度", "type": "number", "unit": "mm"},
    
    "filler_metal_type": {"label": "填充金属型号", "type": "text"},
    "filler_metal_diameter": {"label": "填充金属直径", "type": "number", "unit": "mm"},
    "filler_metal_manufacturer": {"label": "填充金属制造商", "type": "text"},
    "filler_metal_brand": {"label": "填充金属商标名", "type": "text"},
    
    "electrode_redry_temp": {"label": "电极二次烘干温度", "type": "number", "unit": "°C"},
    "electrode_redry_time": {"label": "电极二次烘干时间", "type": "number", "unit": "h"},
    
    "backing_gas_name": {"label": "背部保护气名称", "type": "text"},
    "backing_gas_flow": {"label": "背部保护气流量", "type": "number", "unit": "L/min"},
    "backing_gas_pretime": {"label": "背部保护气预送气时间", "type": "number", "unit": "s"},
    "backing_gas_posttime": {"label": "背部保护气延迟送气时间", "type": "number", "unit": "s"},
    "backing_gas_brand": {"label": "背部保护气商标名", "type": "text"},
    "backing_gas_manufacturer": {"label": "背部保护气制造商", "type": "text"},
    
    "current_type": {"label": "电流种类与极性", "type": "select", "options": ["AC", "DCEP", "DCEN"]},
    "current": {"label": "电流", "type": "text"},
    "voltage": {"label": "焊接电压", "type": "text"},
    
    "travel_speed": {"label": "焊接速度", "type": "text"},
    "angle": {"label": "倾斜角度", "type": "number", "unit": "°"},
    
    "oscillation_width": {"label": "抖动宽度", "type": "number", "unit": "mm"},
    "oscillation_frequency": {"label": "抖动频率", "type": "number", "unit": "Hz"},
    "oscillation_dwell": {"label": "抖动停留时间", "type": "number", "unit": "s"},
    
    "equipment_manufacturer": {"label": "焊接设备制造商", "type": "text"},
    "equipment_name": {"label": "焊接设备名称", "type": "text"},
    
    "heat_input_calculated": {"label": "热输入（系统计算）", "type": "number", "unit": "kJ/mm", "readonly": True},
    "heat_input_manual": {"label": "热输入（用户输入）", "type": "number", "unit": "kJ/mm"}
}

# 114模板的新字段顺序
fields_114 = {
    "welding_process": {"label": "焊接工艺", "type": "select", "options": ["114"], "default": "114"},
    "welding_method_type": {"label": "焊接方法类型", "type": "text"},
    "pass_number": {"label": "焊接道次", "type": "number"},
    "layer_id": {"label": "焊道id", "type": "text"},
    "groove_thickness": {"label": "熔覆金属坡口焊缝厚度", "type": "number", "unit": "mm"},
    
    "filler_metal_type": {"label": "填充金属型号", "type": "text"},
    "filler_metal_diameter": {"label": "填充金属直径", "type": "number", "unit": "mm"},
    "filler_metal_manufacturer": {"label": "填充金属制造商", "type": "text"},
    "filler_metal_brand": {"label": "填充金属商标名", "type": "text"},
    
    "electrode_redry_temp": {"label": "电极二次烘干温度", "type": "number", "unit": "°C"},
    "electrode_redry_time": {"label": "电极二次烘干时间", "type": "number", "unit": "h"},
    
    "current_type": {"label": "电流种类与极性", "type": "select", "options": ["AC", "DCEP", "DCEN"]},
    "current_pulse": {"label": "电流脉冲", "type": "select", "options": ["none", "pulsed"]},
    "current": {"label": "电流", "type": "text"},
    "voltage": {"label": "焊接电压", "type": "text"},
    
    "transfer_mode": {"label": "材料过渡", "type": "select", "options": ["Short arc", "Spray arc", "Pulsed arc"]},
    "wire_feed_speed": {"label": "送丝速度", "type": "text"},
    "travel_speed": {"label": "焊接速度", "type": "text"},
    "angle": {"label": "倾斜角度", "type": "number", "unit": "°"},
    "contact_tip_distance": {"label": "焊嘴间距", "type": "number", "unit": "mm"},
    
    "oscillation_width": {"label": "抖动宽度", "type": "number", "unit": "mm"},
    "oscillation_frequency": {"label": "抖动频率", "type": "number", "unit": "Hz"},
    "oscillation_dwell": {"label": "抖动停留时间", "type": "number", "unit": "s"},
    
    "equipment_manufacturer": {"label": "焊接设备制造商", "type": "text"},
    "equipment_name": {"label": "焊接设备名称", "type": "text"},
    
    "heat_input_calculated": {"label": "热输入（系统计算）", "type": "number", "unit": "kJ/mm", "readonly": True},
    "heat_input_manual": {"label": "热输入（用户输入）", "type": "number", "unit": "kJ/mm"}
}

def update_template_fields():
    """更新模板字段顺序"""
    import json

    with engine.begin() as conn:
        # 更新111模板
        print("更新111模板...")
        new_fields_json = json.dumps(fields_111)
        result = conn.execute(text("""
            UPDATE wps_templates
            SET field_schema = jsonb_set(
                field_schema,
                '{tabs,3,fields}',
                CAST(:new_fields AS jsonb)
            )
            WHERE welding_process = '111' AND standard = 'EN ISO 15609-1'
            RETURNING id, name
        """), {"new_fields": new_fields_json})

        for row in result:
            print(f"  ✓ 已更新模板: {row[1]} (ID: {row[0]})")

        # 更新114模板
        print("\n更新114模板...")
        new_fields_json = json.dumps(fields_114)
        result = conn.execute(text("""
            UPDATE wps_templates
            SET field_schema = jsonb_set(
                field_schema,
                '{tabs,3,fields}',
                CAST(:new_fields AS jsonb)
            )
            WHERE welding_process = '114' AND standard = 'EN ISO 15609-1'
            RETURNING id, name
        """), {"new_fields": new_fields_json})

        for row in result:
            print(f"  ✓ 已更新模板: {row[1]} (ID: {row[0]})")
        
        # 验证更新
        print("\n验证更新结果...")
        result = conn.execute(text("""
            SELECT 
                id,
                name,
                welding_process,
                jsonb_object_keys(field_schema->'tabs'->3->'fields') as field_keys
            FROM wps_templates
            WHERE welding_process IN ('111', '114')
            ORDER BY welding_process, id
        """))
        
        current_template = None
        for row in result:
            if current_template != row[1]:
                current_template = row[1]
                print(f"\n{row[1]} ({row[2]}):")
            print(f"  - {row[3]}")

if __name__ == "__main__":
    print("=" * 60)
    print("更新焊层字段顺序")
    print("=" * 60)
    
    try:
        update_template_fields()
        print("\n✅ 字段顺序更新成功！")
    except Exception as e:
        print(f"\n❌ 更新失败: {e}")
        import traceback
        traceback.print_exc()

