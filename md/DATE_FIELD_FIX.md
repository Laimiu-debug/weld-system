# 日期字段错误修复

## 🐛 问题描述

在 PQR 和 WPS 编辑页面中，当表单包含日期字段时，出现以下错误：

```
Uncaught TypeError: date4.isValid is not a function
    at Object.isValidate (dayjs.js:181:17)
    at Object.current (useInvalidate.js:15:21)
```

## 🔍 问题分析

### 根本原因

**Ant Design 的 DatePicker 组件要求值必须是 dayjs 对象**，但从后端获取的日期数据是字符串格式。

### 数据流程

1. **后端返回数据**:
   ```json
   {
     "modules_data": {
       "instance_1": {
         "moduleId": "pqr_basic_info",
         "data": {
           "test_date": "2024-10-25"  // ❌ 字符串格式
         }
       }
     }
   }
   ```

2. **前端设置表单值**:
   ```typescript
   // ❌ 错误：直接设置字符串
   formValues[formFieldName] = fieldValue  // "2024-10-25"
   form.setFieldsValue(formValues)
   ```

3. **DatePicker 渲染**:
   ```typescript
   <DatePicker />  // ❌ 期望 dayjs 对象，但收到字符串
   ```

4. **错误发生**:
   - DatePicker 尝试调用 `date.isValid()` 方法
   - 但字符串没有 `isValid()` 方法
   - 抛出 `TypeError: date4.isValid is not a function`

### 影响范围

- ✅ **PQR 编辑页面** - 包含日期字段时崩溃
- ✅ **WPS 编辑页面** - 包含日期字段时崩溃
- ❌ **创建页面** - 不受影响（新建时没有初始值）
- ❌ **详情页面** - 不受影响（只显示，不使用 DatePicker）

## ✅ 修复方案

### 1. 加载数据时：字符串 → dayjs 对象

**修改位置**: 
- `frontend/src/pages/PQR/PQREdit.tsx`
- `frontend/src/pages/WPS/WPSEdit.tsx`

**修复前**:
```typescript
// 从 modules_data 中恢复表单值
if (pqr.modules_data) {
  Object.entries(pqr.modules_data).forEach(([moduleId, moduleContent]: [string, any]) => {
    if (moduleContent && moduleContent.data) {
      Object.entries(moduleContent.data).forEach(([fieldKey, fieldValue]: [string, any]) => {
        const formFieldName = `${moduleId}_${fieldKey}`
        formValues[formFieldName] = fieldValue  // ❌ 直接赋值
      })
    }
  })
}
```

**修复后**:
```typescript
// 从 modules_data 中恢复表单值
if (pqr.modules_data) {
  Object.entries(pqr.modules_data).forEach(([moduleId, moduleContent]: [string, any]) => {
    if (moduleContent && moduleContent.data) {
      Object.entries(moduleContent.data).forEach(([fieldKey, fieldValue]: [string, any]) => {
        const formFieldName = `${moduleId}_${fieldKey}`
        
        // 获取字段定义以检查字段类型
        const module = getPQRModuleById(moduleContent.moduleId)
        const fieldDef = module?.fields?.[fieldKey]
        
        // ✅ 如果是日期字段且值是字符串，转换为 dayjs 对象
        if (fieldDef?.type === 'date' && fieldValue && typeof fieldValue === 'string') {
          formValues[formFieldName] = dayjs(fieldValue)
        } else {
          formValues[formFieldName] = fieldValue
        }
      })
    }
  })
}
```

### 2. 保存数据时：dayjs 对象 → 字符串

**修改位置**: 
- `frontend/src/pages/PQR/PQREdit.tsx`
- `frontend/src/pages/WPS/WPSEdit.tsx`

**修复前**:
```typescript
Object.keys(module.fields).forEach(fieldKey => {
  const formFieldName = `${instance.instanceId}_${fieldKey}`
  if (values[formFieldName] !== undefined && values[formFieldName] !== null && values[formFieldName] !== '') {
    moduleData[fieldKey] = values[formFieldName]  // ❌ 直接保存 dayjs 对象
  }
})
```

**修复后**:
```typescript
Object.keys(module.fields).forEach(fieldKey => {
  const formFieldName = `${instance.instanceId}_${fieldKey}`
  if (values[formFieldName] !== undefined && values[formFieldName] !== null && values[formFieldName] !== '') {
    const fieldDef = module.fields[fieldKey]
    let fieldValue = values[formFieldName]
    
    // ✅ 如果是日期字段且值是 dayjs 对象，转换为字符串
    if (fieldDef?.type === 'date' && dayjs.isDayjs(fieldValue)) {
      fieldValue = fieldValue.format('YYYY-MM-DD')
    }
    
    moduleData[fieldKey] = fieldValue
  }
})
```

### 3. 添加 dayjs 导入

**修改位置**: 
- `frontend/src/pages/PQR/PQREdit.tsx`
- `frontend/src/pages/WPS/WPSEdit.tsx`

```typescript
import dayjs from 'dayjs'
```

## 📊 修复前后对比

### 数据转换流程

| 阶段 | 修复前 | 修复后 |
|------|--------|--------|
| **后端返回** | `"2024-10-25"` (字符串) | `"2024-10-25"` (字符串) |
| **设置表单值** | `"2024-10-25"` ❌ | `dayjs("2024-10-25")` ✅ |
| **DatePicker 显示** | 崩溃 ❌ | 正常显示 ✅ |
| **用户编辑** | - | dayjs 对象 |
| **表单提交** | - | `dayjs("2024-10-26")` |
| **保存到后端** | - | `"2024-10-26"` (字符串) ✅ |

### 类型检查

```typescript
// 加载时
if (fieldDef?.type === 'date' && fieldValue && typeof fieldValue === 'string') {
  // 字符串 → dayjs 对象
  formValues[formFieldName] = dayjs(fieldValue)
}

// 保存时
if (fieldDef?.type === 'date' && dayjs.isDayjs(fieldValue)) {
  // dayjs 对象 → 字符串
  fieldValue = fieldValue.format('YYYY-MM-DD')
}
```

## 🎯 技术细节

### dayjs API

```typescript
// 创建 dayjs 对象
const date = dayjs('2024-10-25')

// 检查是否是 dayjs 对象
dayjs.isDayjs(date)  // true
dayjs.isDayjs('2024-10-25')  // false

// 格式化为字符串
date.format('YYYY-MM-DD')  // "2024-10-25"
date.format('YYYY-MM-DD HH:mm:ss')  // "2024-10-25 00:00:00"
```

### Ant Design DatePicker

```typescript
// ✅ 正确用法
<DatePicker value={dayjs('2024-10-25')} />

// ❌ 错误用法
<DatePicker value="2024-10-25" />  // 会导致 isValid 错误
```

### 字段类型定义

```typescript
// 在 pqrModules.ts 或 wpsModules.ts 中
{
  test_date: {
    type: 'date',  // 标识这是日期字段
    label: '试验日期',
    required: true
  }
}
```

## 📁 修改的文件

### 1. frontend/src/pages/PQR/PQREdit.tsx

**修改内容**:
1. 导入 `dayjs`
2. 加载数据时转换日期字符串为 dayjs 对象
3. 保存数据时转换 dayjs 对象为字符串

**关键代码**:
- 第 10 行: `import dayjs from 'dayjs'`
- 第 71-93 行: 加载时的日期转换
- 第 124-150 行: 保存时的日期转换

### 2. frontend/src/pages/WPS/WPSEdit.tsx

**修改内容**:
1. 导入 `dayjs`
2. 加载数据时转换日期字符串为 dayjs 对象
3. 保存数据时转换 dayjs 对象为字符串

**关键代码**:
- 第 10 行: `import dayjs from 'dayjs'`
- 第 71-93 行: 加载时的日期转换
- 第 124-150 行: 保存时的日期转换

## 🧪 测试验证

### 测试步骤

1. **测试 PQR 编辑页面**
   - 创建一个包含日期字段的 PQR
   - 点击"编辑"按钮
   - ✅ 页面应该正常加载，不崩溃
   - ✅ 日期字段应该显示正确的日期
   - 修改日期
   - 点击"保存"
   - ✅ 应该保存成功

2. **测试 WPS 编辑页面**
   - 创建一个包含日期字段的 WPS
   - 点击"编辑"按钮
   - ✅ 页面应该正常加载，不崩溃
   - ✅ 日期字段应该显示正确的日期
   - 修改日期
   - 点击"保存"
   - ✅ 应该保存成功

3. **验证数据持久化**
   - 刷新页面
   - 再次编辑
   - ✅ 日期应该是修改后的值

### 预期结果

- ✅ 不再出现 `date4.isValid is not a function` 错误
- ✅ 日期字段正常显示
- ✅ 可以正常编辑日期
- ✅ 保存后数据正确持久化

## 🚀 最佳实践

### 1. 日期字段处理原则

**前端显示**: 始终使用 dayjs 对象
```typescript
<DatePicker value={dayjs(dateString)} />
```

**后端存储**: 始终使用字符串格式
```typescript
const dateString = dayjsObject.format('YYYY-MM-DD')
```

### 2. 类型安全检查

```typescript
// 检查字段类型
if (fieldDef?.type === 'date') {
  // 日期字段特殊处理
}

// 检查值类型
if (typeof value === 'string') {
  // 字符串 → dayjs
  return dayjs(value)
}

if (dayjs.isDayjs(value)) {
  // dayjs → 字符串
  return value.format('YYYY-MM-DD')
}
```

### 3. 通用转换函数（可选优化）

```typescript
// 可以创建通用的转换函数
const convertDatesForForm = (data: any, module: any) => {
  const result: any = {}
  Object.entries(data).forEach(([key, value]) => {
    const fieldDef = module.fields?.[key]
    if (fieldDef?.type === 'date' && typeof value === 'string') {
      result[key] = dayjs(value)
    } else {
      result[key] = value
    }
  })
  return result
}

const convertDatesForAPI = (data: any, module: any) => {
  const result: any = {}
  Object.entries(data).forEach(([key, value]) => {
    const fieldDef = module.fields?.[key]
    if (fieldDef?.type === 'date' && dayjs.isDayjs(value)) {
      result[key] = value.format('YYYY-MM-DD')
    } else {
      result[key] = value
    }
  })
  return result
}
```

## 📝 总结

### 修复内容

1. ✅ 在 PQREdit.tsx 中添加日期转换逻辑
2. ✅ 在 WPSEdit.tsx 中添加日期转换逻辑
3. ✅ 加载时：字符串 → dayjs 对象
4. ✅ 保存时：dayjs 对象 → 字符串

### 关键点

- **DatePicker 要求**: 值必须是 dayjs 对象
- **后端存储**: 日期以字符串格式存储
- **双向转换**: 加载和保存时都需要转换
- **类型检查**: 使用字段定义判断是否是日期字段

### 影响范围

- ✅ PQR 编辑页面 - 已修复
- ✅ WPS 编辑页面 - 已修复
- ✅ 所有包含日期字段的模块 - 已修复

## 🎉 完成

所有日期字段错误已修复！现在可以：
1. ✅ 正常编辑包含日期字段的 PQR
2. ✅ 正常编辑包含日期字段的 WPS
3. ✅ 日期数据正确保存和加载

请刷新页面并测试编辑功能！

