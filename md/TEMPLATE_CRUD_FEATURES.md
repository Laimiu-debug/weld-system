# WPS 模板卡片增删改查功能

## 功能概述

为 WPS 模板管理页面的表格卡片添加了完整的增删改查（CRUD）功能。

## 实现的功能

### 1. 查看（Read）✅
- **功能**：查看模板详情
- **按钮**：眼睛图标（EyeOutlined）
- **操作**：点击后打开模态框显示模板详情
- **适用范围**：所有模板（系统模板和用户模板）

### 2. 创建（Create）✅
- **功能**：创建新模板
- **按钮**：页面顶部的"使用模块创建模板"按钮
- **操作**：打开 TemplateBuilder 模态框，用户可以：
  - 填写模板名称、描述、焊接工艺、标准
  - 从模块库拖拽模块到画布
  - 保存模板
- **工作区支持**：自动检测当前工作区（个人/企业）

### 3. 编辑（Update）✅
- **功能**：编辑现有模板
- **按钮**：编辑图标（EditOutlined）
- **操作**：
  1. 点击编辑按钮
  2. 加载模板详情
  3. 打开 TemplateBuilder 模态框
  4. 修改模板信息和模块
  5. 保存更新
- **权限**：仅非系统模板可编辑
- **工作区支持**：保持原工作区类型

### 4. 删除（Delete）✅
- **功能**：删除模板
- **按钮**：删除图标（DeleteOutlined），红色
- **操作**：
  1. 点击删除按钮
  2. 确认删除对话框
  3. 确认后删除模板
- **权限**：仅非系统模板可删除
- **反馈**：删除成功后刷新列表

### 5. 复制（Copy）✅ - 额外功能
- **功能**：复制现有模板
- **按钮**：复制图标（CopyOutlined）
- **操作**：
  1. 点击复制按钮
  2. 加载原模板详情
  3. 打开 TemplateBuilder 模态框
  4. 模板名称自动添加"(副本)"后缀
  5. 用户可修改后保存为新模板
- **权限**：仅非系统模板可复制
- **用途**：快速创建相似模板

## 修改的文件

### 前端文件

#### 1. `frontend/src/components/WPS/TemplateBuilder.tsx`
**修改内容**：
- 添加 `editingTemplate` prop 支持编辑模式
- 添加 `useEffect` 钩子，当编辑模板时初始化表单和模块
- 修改 `handleSave` 函数，支持创建和更新两种模式
- 更新 Modal 标题，显示编辑或创建状态

**关键代码**：
```typescript
interface TemplateBuilderProps {
  visible: boolean
  onClose: () => void
  onSave: (template: any) => Promise<void>
  editingTemplate?: any  // 新增
}

// 初始化编辑模板
React.useEffect(() => {
  if (visible && editingTemplate) {
    form.setFieldsValue({...})
    setModules(editingTemplate.module_instances || [])
  }
}, [visible, editingTemplate, form])

// 保存时传递 templateId
const template = {
  ...values,
  templateId: editingTemplate?.id  // 编辑模式下传递
}
```

#### 2. `frontend/src/pages/WPS/TemplateManagement.tsx`
**修改内容**：
- 添加 `editingTemplate` 状态
- 添加 `handleEdit` 函数 - 编辑模板
- 添加 `handleCopy` 函数 - 复制模板
- 更新表格操作列，添加编辑和复制按钮
- 修改 `handleSaveTemplate` 函数，支持创建和更新
- 更新 TemplateBuilder 调用，传递编辑模板数据

**关键代码**：
```typescript
// 编辑模板
const handleEdit = async (template: WPSTemplateSummary) => {
  const response = await wpsTemplateService.getTemplate(template.id)
  setEditingTemplate(response.data)
  setBuilderVisible(true)
}

// 复制模板
const handleCopy = async (template: WPSTemplateSummary) => {
  const response = await wpsTemplateService.getTemplate(template.id)
  const copiedTemplate = {
    ...response.data,
    name: `${response.data.name} (副本)`,
    id: undefined
  }
  setEditingTemplate(copiedTemplate)
  setBuilderVisible(true)
}

// 保存时判断是编辑还是创建
const handleSaveTemplate = async (templateData: any) => {
  if (templateData.templateId) {
    // 编辑模式
    response = await wpsTemplateService.updateTemplate(templateId, updateData)
  } else {
    // 创建模式
    response = await wpsTemplateService.createTemplate(templateData)
  }
}
```

### 后端文件

**无需修改** - 后端已有完整的 CRUD 端点：
- `GET /wps-templates/` - 获取列表
- `GET /wps-templates/{id}` - 获取详情
- `POST /wps-templates/` - 创建
- `PUT /wps-templates/{id}` - 更新
- `DELETE /wps-templates/{id}` - 删除

## 用户界面

### 表格操作列
```
查看 | 编辑 | 复制 | 删除
```

- **查看**：所有模板可用
- **编辑**：非系统模板可用
- **复制**：非系统模板可用
- **删除**：非系统模板可用

### 模态框标题
- 创建模式：`创建模板 - 模块化拖拽`
- 编辑模式：`编辑模板 - {模板名称}`

## 工作流程

### 创建新模板
1. 点击"使用模块创建模板"按钮
2. 填写模板信息
3. 拖拽模块到画布
4. 点击保存
5. 模板创建成功，列表自动刷新

### 编辑现有模板
1. 在表格中找到要编辑的模板
2. 点击编辑按钮
3. 修改模板信息和模块
4. 点击保存
5. 模板更新成功，列表自动刷新

### 复制模板
1. 在表格中找到要复制的模板
2. 点击复制按钮
3. 模板名称自动添加"(副本)"
4. 可修改模板信息
5. 点击保存
6. 新模板创建成功

### 删除模板
1. 在表格中找到要删除的模板
2. 点击删除按钮
3. 确认删除
4. 模板删除成功，列表自动刷新

## 权限控制

- **系统模板**：仅可查看，不可编辑、复制、删除
- **用户模板**：可查看、编辑、复制、删除
- **企业模板**：可查看、编辑、复制、删除（如果是创建者）

## 工作区支持

- **个人工作区**：创建的模板为个人模板
- **企业工作区**：创建的模板为企业模板
- **编辑时**：保持原工作区类型

## 测试建议

1. ✅ 创建新模板
2. ✅ 编辑已创建的模板
3. ✅ 复制模板
4. ✅ 删除模板
5. ✅ 在不同工作区创建模板
6. ✅ 验证系统模板不可编辑/删除

