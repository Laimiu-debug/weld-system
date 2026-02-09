# WPS 模板数据不一致问题诊断报告

## 问题描述

用户使用模板创建的 WPS 与模板格式、数据不一致。卡片上显示的是虚假信息或空值，而不是用户在模板中填写的实际数据。

## 根本原因分析

### 1. 数据流程不匹配

**前端数据流（WPSCreate.tsx）：**
```
用户填写模板表单 
  ↓
提取所有模块数据 (module_instances)
  ↓
构建 modules_data 结构：
{
  "module_instance_id": {
    "moduleId": "...",
    "customName": "...",
    "data": { "field_key": value, ... }
  }
}
  ↓
发送到后端 API
  ↓
保存到 WPS.modules_data JSONB 字段
```

**后端返回数据流（WPS List API）：**
```
查询 WPS 表
  ↓
构建 WPSSummary 对象
  ↓
只返回旧的标准字段：
- id, title, wps_number, revision, status
- company, project_name, welding_process
- base_material_spec, filler_material_classification
- created_at, updated_at
  ↓
❌ 不返回 modules_data 字段！
```

### 2. 关键问题

| 问题 | 影响 | 严重性 |
|------|------|--------|
| WPSSummary schema 不包含 modules_data | 列表 API 无法返回模板数据 | 🔴 严重 |
| 卡片显示的是旧字段而非模板数据 | 用户看不到实际填写的数据 | 🔴 严重 |
| 没有从 modules_data 提取关键字段 | 无法显示模板中的重要信息 | 🔴 严重 |
| 前后端数据结构不对应 | 模板系统形同虚设 | 🔴 严重 |

## 解决方案

### 方案 1：扩展 WPSSummary（推荐）

**修改后端 schema：**
```python
class WPSSummary(BaseModel):
    """WPS summary for list views."""
    id: int
    title: str
    wps_number: str
    revision: str
    status: str
    company: Optional[str] = None
    project_name: Optional[str] = None
    welding_process: Optional[str] = None
    base_material_spec: Optional[str] = None
    filler_material_classification: Optional[str] = None
    
    # 新增：模板数据
    template_id: Optional[str] = None
    modules_data: Optional[Dict[str, Any]] = None  # ✅ 新增
    
    created_at: datetime
    updated_at: datetime
```

**修改后端 API：**
```python
# 在 read_wps_list 和 search_wps 中添加
wps_summaries.append(WPSSummary(
    ...
    template_id=wps.template_id,
    modules_data=wps.modules_data,  # ✅ 新增
    ...
))
```

### 方案 2：前端智能提取（辅助）

**修改前端卡片显示逻辑：**
```typescript
// 从 modules_data 中提取关键字段
const extractKeyFieldsFromModules = (modulesData: any) => {
  const extracted = {
    welding_process: '',
    base_material: '',
    filler_material: '',
    // ... 其他字段
  }
  
  // 遍历 modules_data，提取关键字段
  Object.values(modulesData).forEach((module: any) => {
    if (module.data) {
      // 根据字段名映射到卡片显示字段
      extracted.welding_process = module.data.welding_process || extracted.welding_process
      extracted.base_material = module.data.base_material_spec || extracted.base_material
      // ...
    }
  })
  
  return extracted
}
```

## 实施步骤

### 第一步：修改后端 Schema
- [ ] 更新 `backend/app/schemas/wps.py` 中的 `WPSSummary`
- [ ] 添加 `template_id` 和 `modules_data` 字段

### 第二步：修改后端 API
- [ ] 更新 `backend/app/api/v1/endpoints/wps.py` 中的 `read_wps_list`
- [ ] 更新 `backend/app/api/v1/endpoints/wps.py` 中的 `search_wps`
- [ ] 在构建 WPSSummary 时包含 modules_data

### 第三步：修改前端卡片显示
- [ ] 更新 `frontend/src/pages/WPS/WPSList.tsx`
- [ ] 添加从 modules_data 提取数据的逻辑
- [ ] 优先显示 modules_data 中的数据，其次显示旧字段

### 第四步：测试验证
- [ ] 使用模板创建 WPS
- [ ] 验证卡片显示的数据与模板中填写的数据一致
- [ ] 验证预览功能显示完整数据
- [ ] 验证编辑功能能正确加载数据

## 预期效果

✅ 用户使用模板创建的 WPS 数据完整保存
✅ 卡片上显示的是实际填写的数据，而非虚假信息
✅ 模板系统真正发挥作用
✅ 用户体验大幅提升

