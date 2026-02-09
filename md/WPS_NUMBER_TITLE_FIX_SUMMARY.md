# WPS 编号和标题虚假信息修复总结

## 问题描述

用户反馈：卡片上显示的 WPS 编号是虚假信息，如 `WPS-1761154258426`，而不是用户在模板中填写的真实编号。

## 根本原因

在 `WPSCreate.tsx` 和 `WPSEdit.tsx` 中，`wps_number` 和 `title` 是从表单的顶级字段获取的：

```typescript
// 错误的做法
const submitData: any = {
  title: values.title || `WPS-${Date.now()}`,
  wps_number: values.wps_number || `WPS-${Date.now()}`,
  // ...
}
```

但实际上，这些字段是在 `header_data` 模块中定义的，所以表单中没有顶级的 `title` 和 `wps_number` 字段，导致系统使用了默认的时间戳生成的编号。

## 解决方案

### 修改 WPSCreate.tsx

**改进**：从 `header_data` 模块中提取 `wps_number`、`title` 和 `revision` 字段

```typescript
// 正确的做法
let wpsNumber = ''
let wpsTitle = ''
let wpsRevision = 'A'

if (selectedTemplate?.module_instances) {
  selectedTemplate.module_instances.forEach(instance => {
    const moduleData: Record<string, any> = {}
    const module = getModuleById(instance.moduleId)

    if (module) {
      Object.keys(module.fields).forEach(fieldKey => {
        const formFieldName = `${instance.instanceId}_${fieldKey}`
        if (values[formFieldName] !== undefined && values[formFieldName] !== null && values[formFieldName] !== '') {
          moduleData[fieldKey] = values[formFieldName]

          // 从 header_data 模块中提取关键字段
          if (instance.moduleId === 'header_data') {
            if (fieldKey === 'wps_number') {
              wpsNumber = values[formFieldName]
            } else if (fieldKey === 'title') {
              wpsTitle = values[formFieldName]
            } else if (fieldKey === 'revision') {
              wpsRevision = values[formFieldName]
            }
          }
        }
      })
    }
    // ...
  })
}

// 使用提取的值
const submitData: any = {
  title: wpsTitle || `WPS-${Date.now()}`,
  wps_number: wpsNumber || `WPS-${Date.now()}`,
  revision: wpsRevision || 'A',
  // ...
}
```

### 修改 WPSEdit.tsx

**改进**：同样从 `header_data` 模块中提取关键字段，确保编辑时也能正确保存

### 修复 Modal 警告

**改进**：将 `bodyStyle` 改为 `styles={{ body: { ... } }}`，符合最新的 Ant Design API

```typescript
// 旧的做法（已弃用）
<Modal bodyStyle={{ maxHeight: '70vh', overflowY: 'auto' }} />

// 新的做法
<Modal styles={{ body: { maxHeight: '70vh', overflowY: 'auto' } }} />
```

## 数据流程改进

### 创建 WPS 流程

```
用户填写模板表单
  ↓
表单中的字段名格式：{instanceId}_{fieldKey}
  例如：header_data_1_wps_number, header_data_1_title
  ↓
遍历所有模块实例
  ↓
检测到 header_data 模块
  ↓
从表单值中提取 wps_number, title, revision
  ↓
使用提取的值作为 WPS 的顶级字段
  ↓
同时保存到 modules_data 中
  ↓
WPS 编号和标题现在是真实的用户输入 ✅
```

### 编辑 WPS 流程

```
加载已创建的 WPS
  ↓
从 modules_data 中恢复表单值
  ↓
用户修改数据
  ↓
保存时重新从 header_data 模块中提取关键字段
  ↓
更新 WPS 的顶级字段
  ↓
同时更新 modules_data
  ↓
数据保持一致 ✅
```

## 修改的文件

1. **frontend/src/pages/WPS/WPSCreate.tsx**
   - 修改 `handleSubmit` 函数
   - 从 `header_data` 模块中提取 `wps_number`、`title`、`revision`

2. **frontend/src/pages/WPS/WPSEdit.tsx**
   - 修改 `handleSave` 函数
   - 从 `header_data` 模块中提取关键字段

3. **frontend/src/pages/WPS/WPSList.tsx**
   - 修复 Modal 的 `bodyStyle` 警告

## 测试步骤

1. **创建 WPS**
   - 访问 `/wps/create`
   - 选择模板
   - 在 "表头数据" 模块中填写：
     - WPS编号：`WPS-001`
     - 标题：`测试焊接工艺规程`
     - 版本：`A`
   - 提交保存

2. **验证卡片显示**
   - 访问 `/wps` 列表页面
   - 检查卡片上显示的编号是否为 `WPS-001`（而不是 `WPS-1761154258426`）
   - 检查标题是否为 `测试焊接工艺规程`

3. **验证详情页**
   - 点击"查看"按钮
   - 验证详情页显示的编号和标题是否正确

4. **验证编辑**
   - 点击"编辑"按钮
   - 验证编辑页加载的数据是否正确
   - 修改编号为 `WPS-002`
   - 保存并验证卡片上的编号已更新

## 预期效果

✅ 卡片上显示的 WPS 编号是用户在模板中填写的真实编号
✅ 卡片上显示的标题是用户在模板中填写的真实标题
✅ 不再显示虚假的时间戳生成的编号
✅ 编辑时能正确保存和显示用户输入的数据
✅ 没有 Modal 警告信息

## 技术细节

### 表单字段命名规则

模板中的表单字段名遵循以下规则：
```
{instanceId}_{fieldKey}

例如：
- header_data_1_wps_number
- header_data_1_title
- header_data_1_revision
- summary_info_1_base_material_spec
- weld_layer_1_pass_number
```

### 模块实例结构

```typescript
interface ModuleInstance {
  instanceId: string      // 模块实例ID，用于表单字段名前缀
  moduleId: string        // 模块ID，用于查找模块定义
  customName?: string     // 自定义模块名称
  order?: number          // 显示顺序
}
```

### 数据保存结构

```typescript
// modules_data 结构
{
  "header_data_1": {
    "moduleId": "header_data",
    "customName": "表头数据",
    "data": {
      "wps_number": "WPS-001",
      "title": "测试焊接工艺规程",
      "revision": "A",
      // ... 其他字段
    }
  },
  "summary_info_1": {
    // ...
  }
}
```

## 后续改进建议

1. **自动编号生成**：考虑添加自动编号生成功能（如：WPS-2024-001）
2. **编号验证**：添加编号唯一性验证
3. **编号格式**：支持自定义编号格式
4. **批量操作**：支持批量修改编号前缀

