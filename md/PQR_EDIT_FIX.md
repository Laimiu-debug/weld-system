# PQR 编辑页面修复

## 🐛 问题描述

PQR 编辑页面存在以下问题：
1. 保存时无法正确检查响应状态
2. 缺少基本信息表单字段（PQR编号、标题、版本）

## 🔍 问题分析

### 1. Service 返回格式不一致

**问题位置**: `frontend/src/services/pqr.ts`

**PQREdit.tsx 期望的格式**:
```typescript
const response = await pqrService.update(parseInt(id!), updateData)
if (response.success) {  // 期望有 success 字段
  message.success('保存成功')
  navigate('/pqr')
}
```

**pqrService.update() 实际返回**:
```typescript
// 修复前
async update(id: number, data: PQRUpdate): Promise<PQRResponse> {
  const response = await api.put(`${this.baseURL}/${id}`, data)
  return response.data  // ❌ 只返回 data，没有 success 字段
}
```

**对比 WPS 实现**:
```typescript
// WPS Service (正确)
async updateWPS(id: number, data: WPSUpdate): Promise<any> {
  const response = await api.put(`/wps/${id}`, data)
  return response  // ✅ 返回完整的 response 对象
}
```

### 2. 缺少基本信息表单字段

**WPS 编辑页面有**:
- WPS编号输入框
- 标题输入框
- 版本输入框

**PQR 编辑页面缺少**:
- ❌ 没有 PQR编号输入框
- ❌ 没有标题输入框
- ❌ 没有版本输入框

这导致用户无法直接在编辑页面修改这些基本信息。

## ✅ 修复方案

### 1. 修改 pqrService.update() 方法

**文件**: `frontend/src/services/pqr.ts`

**修改前**:
```typescript
async update(id: number, data: PQRUpdate): Promise<PQRResponse> {
  const response = await api.put(`${this.baseURL}/${id}`, data)
  return response.data  // ❌
}
```

**修改后**:
```typescript
async update(id: number, data: PQRUpdate): Promise<any> {
  const response = await api.put(`${this.baseURL}/${id}`, data)
  return response  // ✅ 返回完整的 { success, data } 对象
}
```

### 2. 修改 pqrService.create() 方法

为了保持一致性，也修改 create 方法：

**修改前**:
```typescript
async create(data: PQRCreate): Promise<PQRResponse> {
  const response = await api.post(`${this.baseURL}`, data)
  return response.data  // ❌
}
```

**修改后**:
```typescript
async create(data: PQRCreate): Promise<any> {
  const response = await api.post(`${this.baseURL}`, data)
  return response  // ✅ 返回完整对象
}
```

### 3. 添加基本信息表单字段

**文件**: `frontend/src/pages/PQR/PQREdit.tsx`

**添加 Input 组件导入**:
```typescript
import { Card, Typography, Button, Space, Form, Spin, message, Alert, Input } from 'antd'
```

**添加表单字段**:
```typescript
<Form form={form} layout="vertical">
  {/* 基本信息 */}
  <Form.Item
    label="PQR编号"
    name="pqr_number"
    rules={[{ required: true, message: '请输入PQR编号' }]}
  >
    <Input />
  </Form.Item>

  <Form.Item
    label="标题"
    name="title"
    rules={[{ required: true, message: '请输入标题' }]}
  >
    <Input />
  </Form.Item>

  <Form.Item
    label="版本"
    name="revision"
  >
    <Input />
  </Form.Item>

  {/* 模块表单 */}
  <ModuleFormRenderer
    modules={template.module_instances || []}
    form={form}
    moduleType="pqr"
  />
</Form>
```

## 📊 修复前后对比

### Service 方法返回格式

| 方法 | 修复前 | 修复后 | 说明 |
|------|--------|--------|------|
| `get()` | `response.data` | `response` | ✅ 已修复 |
| `create()` | `response.data` | `response` | ✅ 已修复 |
| `update()` | `response.data` | `response` | ✅ 已修复 |
| `delete()` | `response` | `response` | ✅ 已正确 |
| `duplicate()` | `response.data` | `response.data` | ✅ 不需要修改 |

### 编辑页面功能

| 功能 | 修复前 | 修复后 |
|------|--------|--------|
| 加载数据 | ✅ 正常 | ✅ 正常 |
| 保存检查 | ❌ `response.success` 为 undefined | ✅ 正常检查 |
| 编辑 PQR编号 | ❌ 无法编辑 | ✅ 可以编辑 |
| 编辑标题 | ❌ 无法编辑 | ✅ 可以编辑 |
| 编辑版本 | ❌ 无法编辑 | ✅ 可以编辑 |
| 编辑模块数据 | ✅ 正常 | ✅ 正常 |

## 🎯 影响范围

### 受益功能

1. ✅ **PQR 编辑页面**
   - 可以正确检查保存结果
   - 可以编辑基本信息
   - 可以编辑模块数据

2. ✅ **PQR 创建页面**
   - 保持与 WPS 一致的返回格式

3. ✅ **PQR 详情页面**
   - 之前已修复

### 与 WPS 的一致性

现在 PQR 的实现与 WPS 完全一致：

| 功能 | WPS | PQR | 状态 |
|------|-----|-----|------|
| `get()` 返回格式 | `response` | `response` | ✅ 一致 |
| `create()` 返回格式 | `response` | `response` | ✅ 一致 |
| `update()` 返回格式 | `response` | `response` | ✅ 一致 |
| 编辑页面基本字段 | 有 | 有 | ✅ 一致 |
| 模块化表单 | 有 | 有 | ✅ 一致 |

## 📁 修改的文件

### 1. frontend/src/services/pqr.ts

**修改内容**:
- `get()` 方法返回完整 response
- `create()` 方法返回完整 response
- `update()` 方法返回完整 response

### 2. frontend/src/pages/PQR/PQREdit.tsx

**修改内容**:
- 导入 `Input` 组件
- 添加 PQR编号表单字段
- 添加标题表单字段
- 添加版本表单字段

## 🧪 测试验证

### 测试步骤

1. **测试编辑页面加载**
   - 进入 PQR 列表
   - 点击"编辑"按钮
   - 应该能看到编辑页面
   - 应该能看到 PQR编号、标题、版本输入框
   - 输入框应该已填充当前值

2. **测试保存功能**
   - 修改 PQR编号
   - 修改标题
   - 修改版本
   - 修改模块数据
   - 点击"保存"按钮
   - 应该显示"保存成功"消息
   - 应该跳转回 PQR 列表

3. **测试验证**
   - 在列表中查看修改后的 PQR
   - 确认修改已保存

### 预期结果

- ✅ 编辑页面正常加载
- ✅ 显示所有基本信息字段
- ✅ 可以修改所有字段
- ✅ 保存成功并正确提示
- ✅ 修改已持久化到数据库

## 🚀 使用说明

### 编辑 PQR

1. 在 PQR 列表中找到要编辑的记录
2. 点击"编辑"按钮
3. 在编辑页面可以修改：
   - **PQR编号** - 必填
   - **标题** - 必填
   - **版本** - 可选
   - **模块数据** - 根据模板动态显示
4. 点击"保存"按钮保存修改
5. 或点击"取消"按钮放弃修改

### 注意事项

- PQR编号和标题是必填字段
- 如果 PQR 不是使用模板创建的，将显示警告信息
- 保存时会验证所有必填字段

## 📝 总结

### 修复内容

1. ✅ 修改 `pqrService.get()` 返回完整 response
2. ✅ 修改 `pqrService.create()` 返回完整 response
3. ✅ 修改 `pqrService.update()` 返回完整 response
4. ✅ 添加 PQR 编辑页面基本信息字段

### 关键点

- **Service 层一致性**: 所有需要检查 `success` 的方法都返回完整 response
- **与 WPS 对齐**: PQR 的实现现在与 WPS 完全一致
- **用户体验**: 用户可以直接在编辑页面修改基本信息

### 最佳实践

**返回格式规则**:
- 如果页面需要检查 `success` → 返回 `response`
- 如果页面不需要检查 `success` → 可以返回 `response.data`
- 为了一致性，建议统一返回 `response`

## 🎉 完成

所有修复已完成！请刷新前端页面并测试：
1. ✅ 编辑 PQR
2. ✅ 修改基本信息
3. ✅ 修改模块数据
4. ✅ 保存修改

如果还有问题，请检查浏览器控制台的错误信息！

