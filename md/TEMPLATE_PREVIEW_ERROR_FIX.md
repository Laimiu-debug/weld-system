# TemplatePreview 组件错误修复总结

## 问题描述

用户在使用模板管理功能时遇到以下错误：

```
Uncaught TypeError: Cannot read properties of undefined (reading 'module_instances')
    at TemplatePreview (TemplatePreview.tsx:21:28)
```

同时还有 Ant Design 的弃用警告：

```
Warning: [rc-collapse] `children` will be removed in next major version. Please use `items` instead.
```

## 根本原因

### 问题 1：Null 检查缺失

在 `TemplatePreview.tsx` 第 21 行，代码直接访问 `template.module_instances`，但没有检查 `template` 是否为 `undefined`：

```typescript
// 错误的做法
const modules = template.module_instances || []
```

当 `template` 为 `undefined` 时，会抛出错误。

### 问题 2：Collapse 组件使用过时 API

在 `TemplateBuilder.tsx` 第 494-498 行，使用了旧的 Collapse API（使用 `Panel` 和 `children`）：

```typescript
// 过时的做法
<Collapse defaultActiveKey={['preview']} ghost>
  <Panel header="预览生成的表单" key="preview">
    <TemplatePreview modules={modules} />
  </Panel>
</Collapse>
```

Ant Design v5+ 已弃用这种用法，应该使用 `items` 属性。

## 解决方案

### 修复 1：添加 Null 检查

**文件**: `frontend/src/components/WPS/TemplatePreview.tsx`

```typescript
const TemplatePreview: React.FC<TemplatePreviewProps> = ({ template, form }) => {
  // 添加 null 检查
  if (!template) {
    return (
      <Card
        title={
          <Space>
            <EyeOutlined />
            <span>模板预览</span>
          </Space>
        }
        size="small"
      >
        <Empty description="未选择模板" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </Card>
    )
  }

  const modules = template.module_instances || []
  // ... 其他代码
}
```

**改进**：
- 在访问 `template.module_instances` 之前检查 `template` 是否存在
- 如果 `template` 为 `undefined`，显示友好的空状态提示

### 修复 2：更新 Collapse 组件 API

**文件**: `frontend/src/components/WPS/TemplateBuilder.tsx`

```typescript
// 新的做法
{modules.length > 0 && (
  <Collapse
    defaultActiveKey={['preview']}
    ghost
    items={[
      {
        key: 'preview',
        label: '预览生成的表单',
        children: <TemplatePreview template={{ module_instances: modules } as any} />
      }
    ]}
  />
)}
```

**改进**：
- 使用 `items` 属性替代 `Panel` 子组件
- 每个 item 包含 `key`、`label` 和 `children` 属性
- 移除了不再使用的 `Panel` 导入

### 修复 3：清理导入

**文件**: `frontend/src/components/WPS/TemplateBuilder.tsx`

```typescript
// 移除不再使用的 Panel 导入
// const { Panel } = Collapse  // ❌ 删除
```

**文件**: `frontend/src/components/WPS/TemplatePreview.tsx`

```typescript
// 移除不再使用的导入
import { Card, Descriptions, Tag, Empty, Space, Typography, Row, Col, Table, FormInstance } from 'antd'
// 不再导入 Collapse
```

## 修改的文件

1. **frontend/src/components/WPS/TemplatePreview.tsx**
   - 添加 `template` 的 null 检查
   - 移除不再使用的 `Collapse` 和 `Panel` 导入

2. **frontend/src/components/WPS/TemplateBuilder.tsx**
   - 更新 Collapse 组件使用新的 `items` API
   - 移除不再使用的 `Panel` 导入

## 测试步骤

1. **访问模板管理页面**
   - 导航到 `/wps/templates`
   - 应该能正常加载，不再出现错误

2. **创建新模板**
   - 点击"创建模板"按钮
   - 添加模块到模板
   - 验证预览区域能正常显示
   - 不应该看到 Collapse 警告

3. **验证错误处理**
   - 如果 `template` 为 `undefined`，应该显示"未选择模板"的空状态

## 预期效果

✅ 不再出现 `Cannot read properties of undefined` 错误
✅ 不再出现 Collapse 弃用警告
✅ 模板预览功能正常工作
✅ 代码符合 Ant Design v5+ 最新 API

## 技术细节

### Ant Design Collapse API 变更

**v4 及之前**（已弃用）：
```typescript
<Collapse>
  <Panel header="标题" key="key1">
    内容
  </Panel>
</Collapse>
```

**v5+（推荐）**：
```typescript
<Collapse
  items={[
    {
      key: 'key1',
      label: '标题',
      children: '内容'
    }
  ]}
/>
```

### 为什么需要 Null 检查

在 React 中，组件可能在以下情况下接收 `undefined` 的 props：
- 异步加载数据时，初始值为 `undefined`
- 条件渲染时，某些分支可能不传递该 prop
- 错误处理时，API 调用失败导致数据为 `undefined`

因此，在访问对象属性之前进行 null/undefined 检查是最佳实践。

## 相关文件

- `frontend/src/components/WPS/TemplatePreview.tsx` - 模板预览组件
- `frontend/src/components/WPS/TemplateBuilder.tsx` - 模板构建器组件
- `frontend/src/pages/WPS/TemplateManagement.tsx` - 模板管理页面

