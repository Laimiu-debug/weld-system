-- 更新焊层字段顺序，使其更符合焊接工艺逻辑
-- 新的顺序：基本信息 → 填充金属 → 电极烘干 → 保护气体 → 电流电压 → 速度角度 → 抖动 → 设备 → 热输入

-- 更新111模板（手工电弧焊）
UPDATE wps_templates
SET field_schema = jsonb_set(
    field_schema,
    '{tabs}',
    (
        SELECT jsonb_agg(
            CASE 
                WHEN tab->>'key' = 'weld_layers' THEN
                    jsonb_set(
                        tab,
                        '{fields}',
                        '{
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
                            
                            "heat_input_calculated": {"label": "热输入（系统计算）", "type": "number", "unit": "kJ/mm", "readonly": true},
                            "heat_input_manual": {"label": "热输入（用户输入）", "type": "number", "unit": "kJ/mm"}
                        }'::jsonb
                    )
                ELSE tab
            END
        )
        FROM jsonb_array_elements(field_schema->'tabs') AS tab
    )
)
WHERE welding_process = '111' AND standard = 'EN ISO 15609-1';

-- 更新114模板（TIG焊）
UPDATE wps_templates
SET field_schema = jsonb_set(
    field_schema,
    '{tabs}',
    (
        SELECT jsonb_agg(
            CASE 
                WHEN tab->>'key' = 'weld_layers' THEN
                    jsonb_set(
                        tab,
                        '{fields}',
                        '{
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
                            
                            "heat_input_calculated": {"label": "热输入（系统计算）", "type": "number", "unit": "kJ/mm", "readonly": true},
                            "heat_input_manual": {"label": "热输入（用户输入）", "type": "number", "unit": "kJ/mm"}
                        }'::jsonb
                    )
                ELSE tab
            END
        )
        FROM jsonb_array_elements(field_schema->'tabs') AS tab
    )
)
WHERE welding_process = '114' AND standard = 'EN ISO 15609-1';

-- 验证更新
SELECT 
    id,
    name,
    welding_process,
    standard,
    jsonb_pretty(field_schema->'tabs'->3->'fields') as weld_layer_fields
FROM wps_templates
WHERE welding_process IN ('111', '114')
ORDER BY welding_process;

