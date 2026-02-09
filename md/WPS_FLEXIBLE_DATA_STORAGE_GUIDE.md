# WPS 灵活数据存储架构改进指南

## 📋 概述

本文档描述了 WPS 系统从**固定字段映射**到**完全灵活的 JSONB 存储**的架构改进。

### 🎯 核心目标

✅ **完全灵活** - 支持无限自定义模块  
✅ **完整保留** - 所有用户数据和模块定义都被完整保存  
✅ **向后兼容** - 旧的 WPS 记录仍然可以正常工作  
✅ **无代码限制** - 不需要修改后端代码来支持新模块  

---

## 🏗️ 架构改进

### 旧架构（问题）

```
用户创建模块 → 前端硬编码映射 → 固定的 JSONB 字段
  ❌ 需要修改前端代码
  ❌ 只支持预定义的模块类型
  ❌ 新模块数据可能丢失
```

### 新架构（解决方案）

```
用户创建模块 → 直接保存到 modules_data → 完全灵活
  ✅ 无需修改代码
  ✅ 支持无限自定义
  ✅ 所有数据完整保留
```

---

## 📊 数据结构

### modules_data 字段结构

```json
{
  "module_instance_id_1": {
    "moduleId": "header_data",
    "customName": "表头信息",
    "data": {
      "title": "WPS-001",
      "revision": "A",
      "wps_number": "WPS-001"
    }
  },
  "module_instance_id_2": {
    "moduleId": "summary_info",
    "customName": "概要信息",
    "data": {
      "base_material_1": "钢材",
      "welding_process": "111"
    }
  },
  "custom_module_1": {
    "moduleId": "custom_module",
    "customName": "自定义模块",
    "data": {
      "custom_field_1": "值1",
      "custom_field_2": "值2"
    }
  }
}
```

### 关键特性

| 特性 | 说明 |
|------|------|
| **instanceId** | 模块实例的唯一标识符 |
| **moduleId** | 模块类型ID（可以是任意值） |
| **customName** | 模块的自定义名称 |
| **data** | 模块的实际数据（任意结构） |

---

## 🔄 数据流

### 前端流程

```typescript
// 1. 收集所有模块数据
const modulesData = {}
template.module_instances.forEach(instance => {
  const moduleData = {}
  // 收集该模块的所有字段值
  modulesData[instance.instanceId] = {
    moduleId: instance.moduleId,
    customName: instance.customName,
    data: moduleData
  }
})

// 2. 直接提交到后端
submitData.modules_data = modulesData
```

### 后端流程

```python
# 1. 接收 modules_data
modules_data = obj_in.modules_data

# 2. 直接保存到数据库
db_obj = WPS(
    modules_data=modules_data,
    # ... 其他字段
)
```

---

## 📝 实现细节

### 修改的文件

1. **backend/app/models/wps.py**
   - 添加 `modules_data` JSONB 字段
   - 保留旧字段用于向后兼容

2. **backend/app/schemas/wps.py**
   - 添加 `modules_data` 字段到 Pydantic schema

3. **backend/app/services/wps_service.py**
   - 简化创建逻辑，直接保存 `modules_data`
   - 保留对旧字段的支持

4. **frontend/src/pages/WPS/WPSCreate.tsx**
   - 简化提交逻辑
   - 直接收集所有模块数据到 `modules_data`

5. **backend/migrations/add_modules_data_field.sql**
   - 数据库迁移脚本

---

## ✅ 优势

### 1. 完全灵活
- 用户可以创建任意自定义模块
- 不需要修改代码
- 支持无限扩展

### 2. 数据完整
- 所有用户填写的数据都被保留
- 所有模块定义都被保留
- 没有数据丢失

### 3. 向后兼容
- 旧的 WPS 记录仍然可以读取
- 旧的 JSONB 字段仍然存在
- 可以逐步迁移

### 4. 简化代码
- 前端不需要硬编码映射
- 后端不需要字段白名单
- 更少的维护成本

---

## 🚀 使用示例

### 创建 WPS 时

```typescript
// 用户选择模板，填写数据
const submitData = {
  template_id: 'preset_smaw_standard',
  title: 'WPS-001',
  wps_number: 'WPS-001',
  modules_data: {
    'header_data_1': {
      moduleId: 'header_data',
      customName: '表头',
      data: { title: 'WPS-001', revision: 'A' }
    },
    'custom_module_1': {
      moduleId: 'custom_module',
      customName: '自定义模块',
      data: { field1: 'value1', field2: 'value2' }
    }
  }
}

// 提交到后端
await wpsService.createWPS(submitData)
```

### 查询 WPS 时

```python
# 后端直接返回 modules_data
wps = db.query(WPS).filter(WPS.id == wps_id).first()

# 前端可以直接使用
const modulesData = wps.modules_data
// {
//   'header_data_1': { moduleId: '...', customName: '...', data: {...} },
//   'custom_module_1': { moduleId: '...', customName: '...', data: {...} }
// }
```

---

## 📚 测试

运行测试脚本验证新结构：

```bash
cd backend
python test_new_modules_data.py
```

---

## 🔮 未来改进

1. **数据迁移** - 将旧的 JSONB 字段数据迁移到 `modules_data`
2. **查询优化** - 为 `modules_data` 添加更多索引
3. **版本控制** - 记录模块数据的版本历史
4. **导出功能** - 支持导出 `modules_data` 为各种格式

---

## 📞 支持

如有问题，请参考：
- 前端实现：`frontend/src/pages/WPS/WPSCreate.tsx`
- 后端实现：`backend/app/services/wps_service.py`
- 数据库迁移：`backend/migrations/add_modules_data_field.sql`

