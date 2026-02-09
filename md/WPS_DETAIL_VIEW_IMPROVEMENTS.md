# WPS 详情页面改进

## 📋 改进概述

完善了 WPS 详情查看页面，提供更丰富、更直观的数据展示体验，支持多种字段类型的正确渲染。

---

## ✨ 改进内容

### 1. **增强的页面头部**

#### 改进前
- 简单的标题和返回按钮
- 状态信息不明显

#### 改进后
- ✅ **大标题显示**：WPS 标题作为主标题
- ✅ **关键信息展示**：WPS 编号和版本号在副标题中
- ✅ **状态徽章**：右上角显示醒目的状态标签（带图标）
  - 草稿：默认色 + 编辑图标
  - 审核中：处理中色 + 旋转图标
  - 已批准：成功色 + 勾选图标
  - 已拒绝：错误色 + 叉号图标

### 2. **改进的基本信息卡片**

- ✅ **卡片标题**：带图标的标题
- ✅ **状态徽章**：使用 Badge 组件显示状态
- ✅ **版本标签**：使用 Tag 组件突出显示版本
- ✅ **强调 WPS 编号**：使用粗体文本

### 3. **完善的模块数据展示**

这是最重要的改进！

#### 改进前的问题
- ❌ 只显示字段键（如 `welding_process`），不显示字段标签（如 "焊接工艺"）
- ❌ 所有值都显示为纯文本或 JSON 字符串
- ❌ 无法正确显示图片、文件、表格等特殊字段
- ❌ 没有模块分类信息
- ❌ 自定义模块无法正确显示

#### 改进后的功能
- ✅ **显示字段标签**：从模块定义中获取字段的 label
- ✅ **显示字段单位**：如果字段有单位，显示在标签后面
- ✅ **必填标识**：必填字段显示红色星号
- ✅ **模块分类图标**：每个模块标签页显示分类图标和名称
- ✅ **支持自定义模块**：自动加载自定义模块定义
- ✅ **多种字段类型渲染**：
  - 文本/数字：普通文本
  - 布尔值：是/否标签
  - 文件：可点击的文件链接
  - 图片：可预览的图片（支持图片组）
  - 表格：完整的表格展示
  - 对象：格式化的 JSON 代码块
  - 空值：显示 "-"

### 4. **智能字段值渲染**

新增 `renderFieldValue` 函数，根据字段类型智能渲染：

```typescript
// 文件字段
if (fieldDef?.type === 'file') {
  return <a href={file.url}>文件名</a>
}

// 图片字段
if (fieldDef?.type === 'image') {
  return <Image.PreviewGroup>...</Image.PreviewGroup>
}

// 表格字段
if (fieldDef?.type === 'table') {
  return <Table columns={...} dataSource={...} />
}

// 布尔值
if (typeof value === 'boolean') {
  return <Tag color="success">是</Tag>
}
```

### 5. **自定义模块支持**

- ✅ **自动检测**：检测 modules_data 中的自定义模块
- ✅ **动态加载**：从后端加载自定义模块定义
- ✅ **缓存机制**：使用 `customModulesCache` 缓存已加载的模块
- ✅ **降级处理**：如果加载失败，仍然显示字段键

### 6. **优化的布局**

- ✅ **响应式网格**：使用 Row/Col 布局，自适应不同屏幕
  - xs: 24 (手机：1列)
  - sm: 12 (平板：2列)
  - md: 8 (桌面：3列)
- ✅ **卡片嵌套**：每个模块标签页内使用小卡片
- ✅ **间距优化**：合理的 gutter 和 margin
- ✅ **空状态**：如果模块无数据，显示友好的空状态

---

## 🎨 视觉改进

### 状态配置

| 状态 | 颜色 | 图标 | 文本 |
|------|------|------|------|
| draft | default | EditOutlined | 草稿 |
| review | processing | SyncOutlined (旋转) | 审核中 |
| approved | success | CheckCircleOutlined | 已批准 |
| rejected | error | CloseCircleOutlined | 已拒绝 |

### 模块分类图标

| 分类 | 图标 | 颜色 |
|------|------|------|
| 基本信息 | FileTextOutlined | 蓝色 |
| 材料信息 | ToolOutlined | 绿色 |
| 气体信息 | ExperimentOutlined | 橙色 |
| 电气参数 | ThunderboltOutlined | 红色 |
| 运动参数 | DashboardOutlined | 紫色 |
| 设备信息 | SettingOutlined | 青色 |
| 计算结果 | CalculatorOutlined | 品红 |

---

## 🔧 技术实现

### 修改的文件

**`frontend/src/pages/WPS/WPSDetail.tsx`**

### 新增功能

1. **getCategoryIcon(category)** - 获取分类图标
2. **getCategoryName(category)** - 获取分类名称
3. **getStatusConfig(status)** - 获取状态配置（颜色、图标、文本）
4. **renderFieldValue(fieldKey, value, fieldDef)** - 智能渲染字段值
5. **customModulesCache** - 自定义模块缓存

### 核心代码片段

#### 自定义模块加载
```typescript
// 获取自定义模块定义
if (response.data.modules_data) {
  const customModuleIds = new Set<string>()
  Object.values(response.data.modules_data).forEach((module: any) => {
    if (module.moduleId && !getModuleById(module.moduleId)) {
      customModuleIds.add(module.moduleId)
    }
  })
  
  // 加载自定义模块定义
  const customModules: Record<string, any> = {}
  for (const moduleId of customModuleIds) {
    try {
      const moduleData = await customModuleService.getCustomModule(moduleId)
      customModules[moduleId] = moduleData
    } catch (error) {
      console.error(`加载自定义模块 ${moduleId} 失败:`, error)
    }
  }
  setCustomModulesCache(customModules)
}
```

#### 字段标签获取
```typescript
// 获取模块定义
const presetModule = getModuleById(moduleId)
const customModule = customModulesCache[moduleId]
const module = presetModule || customModule

// 获取字段定义
const fieldDef = module?.fields?.[fieldKey]
const fieldLabel = fieldDef?.label || fieldKey
```

#### 图片字段渲染
```typescript
if (fieldDef?.type === 'image' && Array.isArray(value)) {
  return (
    <Image.PreviewGroup>
      <Space wrap>
        {value.map((img: any, index: number) => (
          <Image
            key={index}
            width={100}
            src={img.url || img.thumbUrl}
            alt={img.name || `图片${index + 1}`}
          />
        ))}
      </Space>
    </Image.PreviewGroup>
  )
}
```

#### 表格字段渲染
```typescript
if (fieldDef?.type === 'table' && Array.isArray(value)) {
  const columns = fieldDef.tableDefinition?.columns || []
  const tableColumns = columns.map((col: any) => ({
    title: col.label,
    dataIndex: col.key,
    key: col.key,
  }))
  return (
    <Table
      size="small"
      columns={tableColumns}
      dataSource={value}
      pagination={false}
      bordered
    />
  )
}
```

---

## 📊 改进对比

| 功能 | 改进前 | 改进后 |
|------|--------|--------|
| 页面标题 | 简单文本 | WPS 标题 + 编号 + 版本 ✨ |
| 状态显示 | 简单标签 | 徽章 + 图标 + 动画 ✨ |
| 字段标签 | 显示字段键 ❌ | 显示字段标签 ✅ |
| 字段单位 | 不显示 ❌ | 显示在标签后 ✅ |
| 必填标识 | 不显示 ❌ | 红色星号 ✅ |
| 模块分类 | 不显示 ❌ | 图标 + 名称 ✅ |
| 自定义模块 | 可能失败 ❌ | 完全支持 ✅ |
| 图片字段 | JSON 字符串 ❌ | 可预览图片 ✅ |
| 文件字段 | JSON 字符串 ❌ | 可点击链接 ✅ |
| 表格字段 | JSON 字符串 ❌ | 完整表格 ✅ |
| 布尔值 | true/false ❌ | 是/否标签 ✅ |
| 空值 | 空白 ❌ | 显示 "-" ✅ |
| 响应式布局 | 无 ❌ | 自适应 ✅ |

---

## ✅ 功能验证

### 测试场景

1. **基本信息展示**
   - ✅ WPS 标题、编号、版本正确显示
   - ✅ 状态徽章正确显示（颜色、图标、文本）
   - ✅ 基本信息卡片完整展示

2. **预设模块数据**
   - ✅ 模块标签页显示分类图标和名称
   - ✅ 字段显示正确的标签（而不是字段键）
   - ✅ 字段单位正确显示
   - ✅ 必填字段显示红色星号

3. **自定义模块数据**
   - ✅ 自动加载自定义模块定义
   - ✅ 字段标签正确显示
   - ✅ 如果加载失败，降级显示字段键

4. **特殊字段类型**
   - ✅ 图片字段：显示可预览的图片
   - ✅ 文件字段：显示可点击的文件链接
   - ✅ 表格字段：显示完整的表格
   - ✅ 布尔值：显示是/否标签
   - ✅ 空值：显示 "-"

5. **响应式布局**
   - ✅ 手机端：1列布局
   - ✅ 平板端：2列布局
   - ✅ 桌面端：3列布局

---

## 🎯 用户体验提升

### 改进前的问题
1. ❌ 字段键难以理解（如 `welding_process`）
2. ❌ 图片、文件等特殊字段无法正常查看
3. ❌ 表格数据显示为 JSON 字符串
4. ❌ 自定义模块可能无法正确显示
5. ❌ 缺少模块分类信息
6. ❌ 状态信息不够醒目

### 改进后的优势
1. ✅ 字段标签清晰易懂（如 "焊接工艺"）
2. ✅ 图片可以直接预览
3. ✅ 文件可以直接下载
4. ✅ 表格数据结构化展示
5. ✅ 自定义模块完美支持
6. ✅ 模块分类一目了然
7. ✅ 状态信息醒目直观

---

## 📝 使用说明

### 查看 WPS 详情
1. 在 WPS 列表页面点击某个 WPS 的"查看"按钮
2. 进入 WPS 详情页面
3. 查看基本信息卡片
4. 切换模块标签页查看各模块数据
5. 点击图片可以预览
6. 点击文件链接可以下载

### 字段信息说明
- **粗体标签**：字段名称
- **红色星号**：必填字段
- **括号内容**：字段单位
- **"-"**：空值或未填写

---

## 🚀 下一步建议

1. **PDF 导出**：实现"下载 PDF"功能
2. **打印优化**：优化打印样式
3. **历史版本**：显示 WPS 的历史版本
4. **审批流程**：显示审批记录和流程
5. **关联数据**：显示关联的 PQR、焊工等信息
6. **数据对比**：支持对比不同版本的 WPS

---

## 📅 更新日期

2025-10-24

---

## 👨‍💻 技术栈

- React 18
- TypeScript
- Ant Design 5
- @ant-design/icons
- dayjs

