-- 修改 wps_templates 表，将 welding_process 字段改为可空
-- 原因：用户可能不想使用预设的焊接工艺选项

-- 修改 welding_process 字段为可空
ALTER TABLE wps_templates 
ALTER COLUMN welding_process DROP NOT NULL;

-- 添加注释说明
COMMENT ON COLUMN wps_templates.welding_process IS '焊接工艺代码: 111, 114, 121, 135, 141, 15, 311 (可选)';

