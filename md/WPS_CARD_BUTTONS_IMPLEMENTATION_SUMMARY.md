# WPS 卡片按钮功能实现总结

## 用户需求

1. ✅ **查看详情页面** - 直接跳转到真实信息的页面，而不是虚假信息页面
2. ✅ **编辑按钮** - 直接跳转到使用模板创建 WPS 的页面，已填写的数据自动保存
3. ✅ **预览页面** - 显示完整的真实数据
4. ✅ **复制按钮** - 直接复制一份 WPS

## 实现内容

### 1. WPSDetail 页面 - 查看详情 ✅

**文件**: `frontend/src/pages/WPS/WPSDetail.tsx`

**功能**:
- 从后端加载完整的 WPS 数据
- 显示基本信息（WPS编号、标题、状态、版本等）
- 显示所有模块数据（从 modules_data 中提取）
- 支持编辑、复制、下载 PDF 等操作
- 使用 Tabs 组件展示多个模块的数据

**关键特性**:
- 自动从 modules_data 中提取所有字段
- 显示完整的模块数据结构
- 支持复制功能（直接在详情页复制）
- 支持编辑功能（跳转到编辑页面）

### 2. WPSEdit 页面 - 编辑 WPS ✅

**文件**: `frontend/src/pages/WPS/WPSEdit.tsx`

**功能**:
- 加载已创建的 WPS 数据
- 获取关联的模板
- 使用模板编辑页面的形式进行编辑
- 自动恢复所有已填写的数据到表单中
- 保存时重新构建 modules_data 结构

**关键特性**:
- 从 modules_data 中恢复表单值
- 支持模板编辑器（ModuleFormRenderer）
- 保存时自动重建 modules_data 结构
- 如果 WPS 不是使用模板创建的，显示警告信息

### 3. 预览模态框 - 完整真实数据 ✅

**文件**: `frontend/src/pages/WPS/WPSList.tsx`

**改进**:
- 扩展预览模态框，显示更多信息
- 添加模块数据详情部分
- 使用 Tabs 组件展示多个模块
- 显示每个模块中的所有字段
- 增加模态框高度和滚动支持

**显示内容**:
- 基本信息（WPS编号、标题、状态等）
- 焊接方法、母材、填充金属等关键字段
- 创建时间和更新时间
- 所有模块数据及其字段

### 4. 复制功能 - 复制 WPS ✅

**文件**: `frontend/src/pages/WPS/WPSList.tsx`

**功能**:
- 获取完整的 WPS 数据（包括 modules_data）
- 创建新的 WPS 副本
- 自动修改 WPS 编号和标题（添加 -COPY 后缀）
- 设置状态为 draft
- 刷新列表显示新创建的 WPS

**实现逻辑**:
```typescript
1. 点击复制按钮
2. 获取完整 WPS 数据
3. 创建副本数据（修改编号、标题、状态）
4. 调用 createWPS API
5. 刷新列表
```

### 5. 前端接口更新 ✅

**文件**: `frontend/src/services/wps.ts`

**更新**:
- 添加 `template_id` 字段到 WPSSummary
- 添加 `modules_data` 字段到 WPSSummary
- 添加 `filler_material_classification` 字段到 WPSSummary
- 修复 API 响应格式处理

## 数据流程

### 查看详情流程
```
卡片"查看"按钮
  ↓
导航到 /wps/{id}
  ↓
WPSDetail 页面加载
  ↓
调用 getWPS API 获取完整数据
  ↓
显示所有真实信息（包括 modules_data）
```

### 编辑流程
```
卡片"编辑"按钮
  ↓
导航到 /wps/{id}/edit
  ↓
WPSEdit 页面加载
  ↓
获取 WPS 数据和关联模板
  ↓
从 modules_data 恢复表单值
  ↓
使用模板编辑器显示表单
  ↓
用户修改数据
  ↓
保存时重建 modules_data
  ↓
调用 updateWPS API
```

### 预览流程
```
卡片"预览"按钮
  ↓
打开预览模态框
  ↓
显示基本信息
  ↓
显示所有模块数据
  ↓
用户可点击"编辑"进入编辑页面
```

### 复制流程
```
卡片"复制"按钮
  ↓
获取完整 WPS 数据
  ↓
创建副本（修改编号、标题、状态）
  ↓
调用 createWPS API
  ↓
刷新列表显示新 WPS
```

## 技术细节

### 数据提取
```typescript
// 从 modules_data 中提取所有字段
const extractAllFieldsFromModules = (modulesData: any) => {
  const extracted: Record<string, any> = {}
  
  if (!modulesData) return extracted
  
  Object.values(modulesData).forEach((module: any) => {
    if (module && module.data) {
      Object.assign(extracted, module.data)
    }
  })
  
  return extracted
}
```

### 表单恢复
```typescript
// 从 modules_data 恢复表单值
if (wps.modules_data) {
  Object.entries(wps.modules_data).forEach(([moduleId, moduleContent]: [string, any]) => {
    if (moduleContent && moduleContent.data) {
      Object.entries(moduleContent.data).forEach(([fieldKey, fieldValue]: [string, any]) => {
        const formFieldName = `${moduleId}_${fieldKey}`
        formValues[formFieldName] = fieldValue
      })
    }
  })
}
```

## 测试清单

- [ ] 点击"查看"按钮，验证详情页显示所有真实数据
- [ ] 点击"编辑"按钮，验证编辑页加载所有数据
- [ ] 在编辑页修改数据并保存，验证数据正确保存
- [ ] 点击"预览"按钮，验证预览模态框显示完整数据
- [ ] 点击"复制"按钮，验证成功复制 WPS
- [ ] 验证复制的 WPS 包含所有原始数据
- [ ] 验证复制的 WPS 编号和标题已修改
- [ ] 验证复制的 WPS 状态为 draft

## 相关文件

- `frontend/src/pages/WPS/WPSDetail.tsx` - 详情页面
- `frontend/src/pages/WPS/WPSEdit.tsx` - 编辑页面
- `frontend/src/pages/WPS/WPSList.tsx` - 列表页面（预览和复制）
- `frontend/src/services/wps.ts` - WPS 服务

## 后续改进建议

1. **性能优化**: 考虑缓存 WPS 数据，避免重复加载
2. **批量操作**: 支持批量复制、批量编辑等操作
3. **版本管理**: 在编辑时自动创建版本记录
4. **权限控制**: 根据用户权限限制编辑、复制等操作
5. **数据验证**: 在保存前进行更严格的数据验证

