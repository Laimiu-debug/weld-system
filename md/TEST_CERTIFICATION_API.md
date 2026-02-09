# 证书管理 API 测试指南

## 🔧 修复内容总结

### 1. 数据库模型更新
- ✅ 添加 `qualified_items` 字段（TEXT，JSON格式）
- ✅ 添加 `qualified_range` 字段（TEXT，JSON格式）
- ✅ 添加 `renewal_result` 字段（VARCHAR(50)）
- ✅ 添加 `renewal_notes` 字段（TEXT）

### 2. 服务层更新
- ✅ `add_certification()` - 使用新的 JSON 字段
- ✅ `update_certification()` - 使用新的 JSON 字段
- ✅ 移除了旧的独立字段（qualified_process, qualified_material_group 等）

### 3. Schema 定义
- ✅ `WelderCertificationBase` - 已更新为使用 JSON 格式

---

## 📝 测试步骤

### 1. 启动后端服务

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 测试创建证书

**请求示例：**

```bash
POST http://localhost:8000/api/v1/welders/6/certifications?workspace_type=enterprise&company_id=4&factory_id=5
Content-Type: application/json
Authorization: Bearer <your_token>

{
  "certification_number": "TEST-2024-001",
  "certification_type": "焊工等级证书",
  "certification_level": "高级",
  "certification_system": "国标",
  "certification_standard": "GB/T 3323-2005",
  "issuing_authority": "中国机械工程学会",
  "issuing_country": "中国",
  "issue_date": "2024-01-01",
  "expiry_date": "2027-01-01",
  
  "qualified_items": "[{\"item\":\"GTAW-FeIV-6G-3/159-FefS-02/10/12\",\"description\":\"氩弧焊-碳钢-全位置\",\"notes\":\"\"}]",
  
  "qualified_range": "[{\"name\":\"母材\",\"value\":\"Q345R\",\"notes\":\"\"},{\"name\":\"焊接位置\",\"value\":\"1G,2G,3G,4G,5G,6G\",\"notes\":\"\"},{\"name\":\"厚度范围\",\"value\":\"3-12mm\",\"notes\":\"\"}]",
  
  "exam_date": "2023-12-15",
  "exam_location": "北京焊接技术培训中心",
  "exam_score": 95.5,
  "practical_test_result": "合格",
  "theory_test_result": "优秀",
  
  "renewal_count": 0,
  "renewal_result": "",
  "renewal_notes": "",
  
  "status": "valid",
  "is_primary": false,
  "attachments": "[]",
  "notes": "测试证书"
}
```

**预期响应：**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "welder_id": 6,
    "certification_number": "TEST-2024-001",
    "certification_type": "焊工等级证书",
    "certification_level": "高级",
    "issue_date": "2024-01-01",
    "expiry_date": "2027-01-01",
    "status": "valid",
    "created_at": "2024-01-20T10:00:00"
  },
  "message": "证书添加成功"
}
```

### 3. 测试获取证书列表

```bash
GET http://localhost:8000/api/v1/welders/6/certifications?workspace_type=enterprise&company_id=4&factory_id=5
Authorization: Bearer <your_token>
```

**预期响应：**

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "certification_number": "TEST-2024-001",
      "certification_type": "焊工等级证书",
      "certification_level": "高级",
      "certification_system": "国标",
      "qualified_items": "[{\"item\":\"GTAW-FeIV-6G-3/159-FefS-02/10/12\",\"description\":\"氩弧焊-碳钢-全位置\",\"notes\":\"\"}]",
      "qualified_range": "[{\"name\":\"母材\",\"value\":\"Q345R\",\"notes\":\"\"},{\"name\":\"焊接位置\",\"value\":\"1G,2G,3G,4G,5G,6G\",\"notes\":\"\"},{\"name\":\"厚度范围\",\"value\":\"3-12mm\",\"notes\":\"\"}]",
      "status": "valid",
      "issue_date": "2024-01-01",
      "expiry_date": "2027-01-01"
    }
  ],
  "message": "获取证书列表成功"
}
```

### 4. 测试更新证书

```bash
PUT http://localhost:8000/api/v1/welders/6/certifications/1?workspace_type=enterprise&company_id=4&factory_id=5
Content-Type: application/json
Authorization: Bearer <your_token>

{
  "qualified_items": "[{\"item\":\"GTAW-FeIV-6G-3/159-FefS-02/10/12\",\"description\":\"氩弧焊-碳钢-全位置\",\"notes\":\"已更新\"},{\"item\":\"SMAW-FeII-3G-6/100-FefS-01\",\"description\":\"手工电弧焊-碳钢\",\"notes\":\"新增项目\"}]",
  "notes": "已更新证书信息"
}
```

---

## 🐛 常见错误及解决方案

### 错误 1: 500 Internal Server Error

**原因：** 服务层代码使用了旧的字段名

**解决方案：** ✅ 已修复
- 更新了 `add_certification()` 方法
- 更新了 `update_certification()` 方法
- 使用 `qualified_items` 和 `qualified_range` 替代旧字段

### 错误 2: Column not found

**原因：** 数据库中缺少新字段

**解决方案：** ✅ 已修复
- 运行了数据库迁移脚本
- 添加了 `qualified_items`, `qualified_range`, `renewal_result`, `renewal_notes` 字段

### 错误 3: JSON parse error

**原因：** 前端发送的 JSON 字符串格式不正确

**解决方案：** 
- 确保前端使用 `JSON.stringify()` 序列化数据
- 检查 JSON 字符串是否有效

---

## ✅ 验证清单

- [ ] 后端服务启动成功
- [ ] 创建证书 API 返回 200
- [ ] 证书数据正确保存到数据库
- [ ] `qualified_items` 字段包含 JSON 数据
- [ ] `qualified_range` 字段包含 JSON 数据
- [ ] 获取证书列表返回正确数据
- [ ] 更新证书功能正常
- [ ] 删除证书功能正常

---

## 📊 数据库验证

### 查询证书数据

```sql
SELECT 
    id,
    certification_number,
    certification_type,
    qualified_items,
    qualified_range,
    renewal_result,
    renewal_notes,
    created_at
FROM welder_certifications
WHERE welder_id = 6
ORDER BY created_at DESC;
```

### 验证 JSON 数据格式

```sql
-- PostgreSQL
SELECT 
    id,
    certification_number,
    qualified_items::json,
    qualified_range::json
FROM welder_certifications
WHERE id = 1;
```

---

## 🎯 下一步

1. **重启后端服务**（如果正在运行）
2. **刷新前端页面**
3. **测试创建证书功能**
4. **验证数据是否正确保存**

如果遇到任何问题，请检查：
- 后端日志输出
- 数据库连接状态
- 前端控制台错误信息

