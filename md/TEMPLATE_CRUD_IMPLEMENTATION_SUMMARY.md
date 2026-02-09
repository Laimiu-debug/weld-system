# WPS 模板卡片 CRUD 功能实现总结

## 📋 概述

为 WPS 模板管理页面的表格卡片添加了完整的增删改查（CRUD）功能，包括：
- ✅ 查看（Read）
- ✅ 创建（Create）
- ✅ 编辑（Update）
- ✅ 删除（Delete）
- ✅ 复制（Copy）- 额外功能

## 🔧 修改的文件

### 1. frontend/src/components/WPS/TemplateBuilder.tsx

**修改内容**：
- 添加 `editingTemplate` prop 支持编辑模式
- 添加 `useEffect` 钩子初始化编辑模板
- 修改 `handleSave` 函数支持创建和更新
- 更新 Modal 标题显示编辑/创建状态

**关键变化**：
```typescript
// 新增 prop
editingTemplate?: any

// 新增 useEffect
React.useEffect(() => {
  if (visible && editingTemplate) {
    form.setFieldsValue({...})
    setModules(editingTemplate.module_instances || [])
  }
}, [visible, editingTemplate, form])

// 修改 handleSave
const template = {
  ...values,
  templateId: editingTemplate?.id  // 编辑模式标识
}

// 修改 Modal 标题
title={editingTemplate ? `编辑模板 - ${editingTemplate.name}` : "创建模板 - 模块化拖拽"}
```

### 2. frontend/src/pages/WPS/TemplateManagement.tsx

**修改内容**：
- 添加 `editingTemplate` 状态
- 添加 `handleEdit` 函数 - 编辑模板
- 添加 `handleCopy` 函数 - 复制模板
- 更新表格操作列添加编辑和复制按钮
- 修改 `handleSaveTemplate` 支持创建和更新
- 更新 TemplateBuilder 调用传递编辑数据

**关键变化**：
```typescript
// 新增状态
const [editingTemplate, setEditingTemplate] = useState<WPSTemplate | null>(null)

// 新增编辑函数
const handleEdit = async (template: WPSTemplateSummary) => {
  const response = await wpsTemplateService.getTemplate(template.id)
  setEditingTemplate(response.data)
  setBuilderVisible(true)
}

// 新增复制函数
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

// 修改保存函数
const handleSaveTemplate = async (templateData: any) => {
  if (templateData.templateId) {
    // 编辑模式
    response = await wpsTemplateService.updateTemplate(templateId, updateData)
  } else {
    // 创建模式
    response = await wpsTemplateService.createTemplate(templateData)
  }
}

// 更新表格操作列
<Button icon={<EditOutlined />} onClick={() => handleEdit(record)} />
<Button icon={<CopyOutlined />} onClick={() => handleCopy(record)} />

// 更新 TemplateBuilder 调用
<TemplateBuilder
  editingTemplate={editingTemplate}
  onClose={() => {
    setBuilderVisible(false)
    setEditingTemplate(null)
  }}
/>
```

## 🎯 功能说明

### 查看（Read）
- 点击眼睛图标查看模板详情
- 显示模板名称、工艺、标准、使用次数等信息
- 适用于所有模板

### 创建（Create）
- 点击"使用模块创建模板"按钮
- 填写模板信息并拖拽模块
- 自动检测工作区类型（个人/企业）
- 保存后刷新列表

### 编辑（Update）
- 点击编辑图标编辑模板
- 修改模板信息和模块
- 保持原模板 ID 和工作区类型
- 保存后刷新列表

### 删除（Delete）
- 点击删除图标删除模板
- 确认后删除模板
- 仅非系统模板可删除
- 删除后刷新列表

### 复制（Copy）
- 点击复制图标复制模板
- 模板名称自动添加"(副本)"
- 可修改后保存为新模板
- 不影响原模板

## 🔐 权限控制

| 操作 | 系统模板 | 用户模板 | 企业模板 |
|------|---------|---------|---------|
| 查看 | ✅ | ✅ | ✅ |
| 编辑 | ❌ | ✅ | ✅ |
| 复制 | ❌ | ✅ | ✅ |
| 删除 | ❌ | ✅ | ✅ |

## 🌍 工作区支持

- **个人工作区**：创建的模板为个人模板（`template_source: 'user'`）
- **企业工作区**：创建的模板为企业模板（`template_source: 'enterprise'`）
- **自动检测**：系统根据 localStorage 中的 `current_workspace` 自动设置

## 📊 后端支持

后端已有完整的 CRUD 端点，无需修改：
- `POST /wps-templates/` - 创建模板
- `GET /wps-templates/{id}` - 获取模板详情
- `PUT /wps-templates/{id}` - 更新模板
- `DELETE /wps-templates/{id}` - 删除模板

## 🧪 测试建议

1. **创建模板**
   - 在个人工作区创建模板
   - 在企业工作区创建模板
   - 验证 `workspace_type` 正确

2. **编辑模板**
   - 编辑已创建的模板
   - 修改模板信息
   - 验证模板 ID 不变

3. **复制模板**
   - 复制模板
   - 验证名称添加"(副本)"
   - 修改后保存为新模板

4. **删除模板**
   - 删除用户模板
   - 验证系统模板不可删除
   - 验证删除后列表刷新

5. **权限控制**
   - 验证系统模板不可编辑
   - 验证系统模板不可删除
   - 验证系统模板不可复制

## 📝 代码质量

- ✅ 无 TypeScript 错误
- ✅ 无 ESLint 警告
- ✅ 遵循现有代码风格
- ✅ 完整的错误处理
- ✅ 用户友好的提示信息

## 🚀 下一步建议

1. 添加模板版本控制
2. 添加模板导出/导入功能
3. 添加模板分享功能
4. 添加模板搜索和过滤
5. 添加模板预览功能
6. 添加批量操作功能

## 📞 使用说明

详见：
- `TEMPLATE_CRUD_QUICK_GUIDE.md` - 快速使用指南
- `TEMPLATE_CRUD_FEATURES.md` - 详细功能说明

