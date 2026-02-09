"""检查WPS表的列"""
from app.core.database import engine
import pandas as pd

# 查询WPS表的所有列
query = """
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'wps' 
ORDER BY ordinal_position
"""

result = pd.read_sql(query, engine)
print("WPS表的列：")
print(result.to_string())
print(f"\n总共 {len(result)} 列")

# 检查是否存在JSON字段
json_fields = ['header_info', 'summary_info', 'diagram_info', 'weld_layers', 'additional_info']
print("\n检查JSON字段：")
for field in json_fields:
    exists = field in result['column_name'].values
    print(f"  {field}: {'✓ 存在' if exists else '✗ 不存在'}")

