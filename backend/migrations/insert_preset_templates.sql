-- ============================================================
-- 插入预设模板（基于模块组合）
-- 包含3个标准焊接工艺的预设模板
-- ============================================================

-- ==================== SMAW 手工电弧焊标准模板 ====================
INSERT INTO wps_templates (
    id, name, description, welding_process, welding_process_name, standard,
    module_instances, workspace_type, template_source, is_system, is_active, version
) VALUES (
    'preset_smaw_standard',
    'SMAW 手工电弧焊标准模板',
    '手工电弧焊（SMAW）的标准WPS模板，包含所有必要的信息模块',
    '111',
    '手工电弧焊',
    'EN ISO 15609-1',
    '[
        {
            "instanceId": "header_data_1",
            "moduleId": "header_data",
            "order": 1,
            "customName": "表头数据"
        },
        {
            "instanceId": "summary_info_1",
            "moduleId": "summary_info",
            "order": 2,
            "customName": "概要信息"
        },
        {
            "instanceId": "diagram_info_1",
            "moduleId": "diagram_info",
            "order": 3,
            "customName": "示意图"
        },
        {
            "instanceId": "weld_layer_1",
            "moduleId": "weld_layer",
            "order": 4,
            "customName": "焊层信息"
        },
        {
            "instanceId": "additional_info_1",
            "moduleId": "additional_info",
            "order": 5,
            "customName": "附加信息"
        }
    ]'::jsonb,
    'system',
    'system',
    true,
    true,
    '1.0'
) ON CONFLICT (id) DO NOTHING;

-- ==================== GMAW MAG焊标准模板 ====================
INSERT INTO wps_templates (
    id, name, description, welding_process, welding_process_name, standard,
    module_instances, workspace_type, template_source, is_system, is_active, version
) VALUES (
    'preset_gmaw_standard',
    'GMAW MAG焊标准模板',
    'MAG焊（熔化极活性气体保护焊）的标准WPS模板',
    '135',
    'MAG焊（熔化极活性气体保护焊）',
    'EN ISO 15609-1',
    '[
        {
            "instanceId": "header_data_2",
            "moduleId": "header_data",
            "order": 1,
            "customName": "表头数据"
        },
        {
            "instanceId": "summary_info_2",
            "moduleId": "summary_info",
            "order": 2,
            "customName": "概要信息"
        },
        {
            "instanceId": "diagram_info_2",
            "moduleId": "diagram_info",
            "order": 3,
            "customName": "示意图"
        },
        {
            "instanceId": "weld_layer_2",
            "moduleId": "weld_layer",
            "order": 4,
            "customName": "焊层信息"
        },
        {
            "instanceId": "additional_info_2",
            "moduleId": "additional_info",
            "order": 5,
            "customName": "附加信息"
        }
    ]'::jsonb,
    'system',
    'system',
    true,
    true,
    '1.0'
) ON CONFLICT (id) DO NOTHING;

-- ==================== GTAW TIG焊标准模板 ====================
INSERT INTO wps_templates (
    id, name, description, welding_process, welding_process_name, standard,
    module_instances, workspace_type, template_source, is_system, is_active, version
) VALUES (
    'preset_gtaw_standard',
    'GTAW TIG焊标准模板',
    'TIG焊（钨极惰性气体保护焊）的标准WPS模板',
    '141',
    'TIG焊（钨极惰性气体保护焊）',
    'EN ISO 15609-1',
    '[
        {
            "instanceId": "header_data_3",
            "moduleId": "header_data",
            "order": 1,
            "customName": "表头数据"
        },
        {
            "instanceId": "summary_info_3",
            "moduleId": "summary_info",
            "order": 2,
            "customName": "概要信息"
        },
        {
            "instanceId": "diagram_info_3",
            "moduleId": "diagram_info",
            "order": 3,
            "customName": "示意图"
        },
        {
            "instanceId": "weld_layer_3",
            "moduleId": "weld_layer",
            "order": 4,
            "customName": "焊层信息"
        },
        {
            "instanceId": "additional_info_3",
            "moduleId": "additional_info",
            "order": 5,
            "customName": "附加信息"
        }
    ]'::jsonb,
    'system',
    'system',
    true,
    true,
    '1.0'
) ON CONFLICT (id) DO NOTHING;

-- 验证插入结果
SELECT id, name, welding_process, welding_process_name FROM wps_templates 
WHERE id LIKE 'preset_%' 
ORDER BY welding_process;

