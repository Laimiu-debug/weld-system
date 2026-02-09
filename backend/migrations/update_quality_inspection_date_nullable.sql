-- 修改 quality_inspections 表的 inspection_date 字段为可空
-- 这样用户可以只填写检验编号，其他字段都是可选的

ALTER TABLE quality_inspections 
ALTER COLUMN inspection_date DROP NOT NULL;

