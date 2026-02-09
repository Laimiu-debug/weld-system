# 共享库端到端测试指南

## 测试目标
验证共享库系统的完整上传-下载流程，确保数据完整性。

---

## 测试前提条件

1. 数据库表结构已修复（运行过 `fix_shared_library_tables_direct.py`）
2. 后端服务正在运行
3. 有至少一个测试用户账号
4. 用户已创建至少一个自定义模块和一个WPS模板

---

## 测试步骤

### 1. 准备测试数据

#### 创建测试模块
```http
POST /api/v1/custom-modules
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "测试共享模块",
  "description": "用于测试共享库功能的模块",
  "icon": "TestOutlined",
  "category": "basic",
  "repeatable": false,
  "fields": [
    {
      "id": "field1",
      "label": "测试字段1",
      "type": "text",
      "required": true
    },
    {
      "id": "field2",
      "label": "测试字段2",
      "type": "number",
      "required": false
    }
  ]
}
```

**记录返回的模块ID**: `{module_id}`

#### 创建测试模板
```http
POST /api/v1/wps-templates
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "测试共享模板",
  "description": "用于测试共享库功能的模板",
  "welding_process": "SMAW",
  "welding_process_name": "手工电弧焊",
  "standard": "AWS D1.1",
  "module_instances": [
    {
      "module_id": "{module_id}",
      "instance_id": "instance1",
      "data": {
        "field1": "测试值1",
        "field2": 123
      }
    }
  ]
}
```

**记录返回的模板ID**: `{template_id}`

---

### 2. 测试模块共享

#### 2.1 上传模块到共享库
```http
POST /api/v1/shared-library/modules/share
Authorization: Bearer {token}
Content-Type: application/json

{
  "original_module_id": "{module_id}",
  "name": "测试共享模块",
  "description": "用于测试共享库功能的模块",
  "icon": "TestOutlined",
  "category": "basic",
  "repeatable": false,
  "fields": [...],  // 从原始模块复制
  "changelog": "初始版本",
  "tags": ["测试", "示例"],
  "difficulty_level": "beginner"
}
```

**验证点：**
- ✓ 返回状态码 200
- ✓ 返回的 `status` 字段为 `"approved"`
- ✓ 返回的 `download_count` 为 0
- ✓ 返回的 `like_count` 为 0
- ✓ 返回的 `fields` 字段完整
- ✓ 记录返回的共享模块ID: `{shared_module_id}`

#### 2.2 查询共享模块列表
```http
GET /api/v1/shared-library/modules?page=1&page_size=10
Authorization: Bearer {token}
```

**验证点：**
- ✓ 能找到刚上传的模块
- ✓ 模块的 `status` 为 `"approved"`
- ✓ 模块的所有字段都存在

#### 2.3 查询共享模块详情
```http
GET /api/v1/shared-library/modules/{shared_module_id}
Authorization: Bearer {token}
```

**验证点：**
- ✓ 返回完整的模块信息
- ✓ `fields` 字段与原始模块一致
- ✓ `view_count` 增加了 1

#### 2.4 下载共享模块
```http
POST /api/v1/shared-library/modules/{shared_module_id}/download
Authorization: Bearer {token}
Content-Type: application/json

{
  "workspace_type": "personal"
}
```

**验证点：**
- ✓ 返回状态码 200
- ✓ 返回的模块信息完整
- ✓ `fields` 字段与共享模块一致
- ✓ 记录返回的新模块ID: `{downloaded_module_id}`

#### 2.5 验证下载的模块
```http
GET /api/v1/custom-modules/{downloaded_module_id}
Authorization: Bearer {token}
```

**验证点：**
- ✓ 模块存在
- ✓ 所有字段与原始模块一致
- ✓ `fields` 字段完整
- ✓ `workspace_type` 为 `"personal"`

---

### 3. 测试模板共享

#### 3.1 上传模板到共享库
```http
POST /api/v1/shared-library/templates/share
Authorization: Bearer {token}
Content-Type: application/json

{
  "original_template_id": "{template_id}",
  "name": "测试共享模板",
  "description": "用于测试共享库功能的模板",
  "welding_process": "SMAW",
  "welding_process_name": "手工电弧焊",
  "standard": "AWS D1.1",
  "module_instances": [...],  // 从原始模板复制
  "changelog": "初始版本",
  "tags": ["测试", "示例"],
  "difficulty_level": "beginner"
}
```

**验证点：**
- ✓ 返回状态码 200
- ✓ 返回的 `status` 字段为 `"approved"`
- ✓ 返回的 `download_count` 为 0
- ✓ 返回的 `module_instances` 字段完整
- ✓ 记录返回的共享模板ID: `{shared_template_id}`

#### 3.2 查询共享模板列表
```http
GET /api/v1/shared-library/templates?page=1&page_size=10
Authorization: Bearer {token}
```

**验证点：**
- ✓ 能找到刚上传的模板
- ✓ 模板的 `status` 为 `"approved"`
- ✓ 模板的所有字段都存在

#### 3.3 查询共享模板详情
```http
GET /api/v1/shared-library/templates/{shared_template_id}
Authorization: Bearer {token}
```

**验证点：**
- ✓ 返回完整的模板信息
- ✓ `module_instances` 字段与原始模板一致
- ✓ `view_count` 增加了 1

#### 3.4 下载共享模板
```http
POST /api/v1/shared-library/templates/{shared_template_id}/download
Authorization: Bearer {token}
Content-Type: application/json

{
  "workspace_type": "personal"
}
```

**验证点：**
- ✓ 返回状态码 200
- ✓ 返回的模板信息完整
- ✓ `module_instances` 字段与共享模板一致
- ✓ 记录返回的新模板ID: `{downloaded_template_id}`

#### 3.5 验证下载的模板
```http
GET /api/v1/wps-templates/{downloaded_template_id}
Authorization: Bearer {token}
```

**验证点：**
- ✓ 模板存在
- ✓ 所有字段与原始模板一致
- ✓ `module_instances` 字段完整
- ✓ `workspace_type` 为 `"personal"`

---

### 4. 测试统计功能

#### 4.1 验证下载次数
```http
GET /api/v1/shared-library/modules/{shared_module_id}
Authorization: Bearer {token}
```

**验证点：**
- ✓ `download_count` 为 1（因为下载了一次）

```http
GET /api/v1/shared-library/templates/{shared_template_id}
Authorization: Bearer {token}
```

**验证点：**
- ✓ `download_count` 为 1（因为下载了一次）

#### 4.2 测试评分功能
```http
POST /api/v1/shared-library/rate
Authorization: Bearer {token}
Content-Type: application/json

{
  "target_type": "module",
  "target_id": "{shared_module_id}",
  "rating_type": "like"
}
```

**验证点：**
- ✓ 返回状态码 200
- ✓ 共享模块的 `like_count` 增加了 1

---

## 数据完整性验证清单

### 模块数据完整性
- [ ] 原始模块的 `name` = 共享模块的 `name` = 下载模块的 `name`
- [ ] 原始模块的 `description` = 共享模块的 `description` = 下载模块的 `description`
- [ ] 原始模块的 `icon` = 共享模块的 `icon` = 下载模块的 `icon`
- [ ] 原始模块的 `category` = 共享模块的 `category` = 下载模块的 `category`
- [ ] 原始模块的 `repeatable` = 共享模块的 `repeatable` = 下载模块的 `repeatable`
- [ ] 原始模块的 `fields` = 共享模块的 `fields` = 下载模块的 `fields` （JSONB完整性）

### 模板数据完整性
- [ ] 原始模板的 `name` = 共享模板的 `name` = 下载模板的 `name`
- [ ] 原始模板的 `description` = 共享模板的 `description` = 下载模板的 `description`
- [ ] 原始模板的 `welding_process` = 共享模板的 `welding_process` = 下载模板的 `welding_process`
- [ ] 原始模板的 `welding_process_name` = 共享模板的 `welding_process_name` = 下载模板的 `welding_process_name`
- [ ] 原始模板的 `standard` = 共享模板的 `standard` = 下载模板的 `standard`
- [ ] 原始模板的 `module_instances` = 共享模板的 `module_instances` = 下载模板的 `module_instances` （JSONB完整性）

---

## 预期结果

### 成功标准
1. ✅ 所有API调用返回成功状态码
2. ✅ 上传的资源默认状态为 `"approved"`
3. ✅ 所有字段完整复制，无数据丢失
4. ✅ JSONB字段（`fields`, `module_instances`）完整保留
5. ✅ 统计功能正常工作（下载次数、评分）
6. ✅ 工作区隔离正常工作

### 失败情况处理
如果任何验证点失败：
1. 检查后端日志
2. 检查数据库表结构
3. 检查服务层代码
4. 参考 `SHARED_LIBRARY_FIX_SUMMARY.md`

---

## 自动化测试脚本（可选）

可以使用 Python + requests 编写自动化测试脚本：

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your_test_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 1. 创建模块
response = requests.post(f"{BASE_URL}/custom-modules", json={...}, headers=headers)
module_id = response.json()["id"]

# 2. 上传到共享库
response = requests.post(f"{BASE_URL}/shared-library/modules/share", json={...}, headers=headers)
shared_module_id = response.json()["id"]
assert response.json()["status"] == "approved"

# 3. 下载模块
response = requests.post(f"{BASE_URL}/shared-library/modules/{shared_module_id}/download", headers=headers)
downloaded_module_id = response.json()["module"]["id"]

# 4. 验证数据完整性
original = requests.get(f"{BASE_URL}/custom-modules/{module_id}", headers=headers).json()
downloaded = requests.get(f"{BASE_URL}/custom-modules/{downloaded_module_id}", headers=headers).json()

assert original["name"] == downloaded["name"]
assert original["fields"] == downloaded["fields"]
# ... 更多断言

print("✅ 所有测试通过！")
```

---

## 总结

完成以上测试后，您应该能够确认：
1. ✅ 共享库系统正常工作
2. ✅ 数据完整性得到保证
3. ✅ 审核流程按预期工作（自动通过）
4. ✅ 权限控制正确
5. ✅ 统计功能正常

