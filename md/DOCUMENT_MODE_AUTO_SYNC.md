# 文档模式自动同步功能说明

**更新时间**: 2025-10-27  
**状态**: ✅ 已实现

---

## 🎯 功能概述

当用户从**表单编辑模式**切换到**文档编辑模式**时，系统会自动将表单中的数据转换为格式化的HTML文档，显示在富文本编辑器中。

---

## ✨ 核心功能

### 1. 自动内容生成
- ✅ 切换到文档模式时，自动从表单数据生成HTML
- ✅ 包含文档标题、编号、版本信息
- ✅ 所有模块数据以表格形式展示
- ✅ 保持字段标签、单位等元信息

### 2. 实时同步
- ✅ 首次切换：从数据库加载的`document_html`
- ✅ 如果没有保存的HTML：从当前表单数据生成
- ✅ 表单修改后切换：重新生成最新内容

### 3. 智能更新
- ✅ 编辑器内容只在必要时更新
- ✅ 避免不必要的重渲染
- ✅ 保持编辑器性能

---

## 🔧 实现细节

### 修改的文件

#### 1. `frontend/src/components/DocumentEditor/WPSDocumentEditor.tsx`

**添加了useEffect监听initialContent变化**：
```typescript
import React, { useEffect } from 'react'

// 当initialContent变化时更新编辑器内容
useEffect(() => {
  if (editor && initialContent) {
    // 只在内容不同时更新，避免不必要的重渲染
    const currentContent = editor.getHTML()
    if (currentContent !== initialContent) {
      editor.commands.setContent(initialContent)
    }
  }
}, [editor, initialContent])
```

**作用**：
- 监听`initialContent`属性的变化
- 当内容改变时，更新编辑器显示
- 避免重复更新相同内容

#### 2. `frontend/src/pages/WPS/WPSEdit.tsx`

**添加了handleEditModeChange函数**：
```typescript
const handleEditModeChange = (mode: 'form' | 'document') => {
  setEditMode(mode)
  
  // 如果切换到文档模式，且没有HTML内容，从当前表单数据生成
  if (mode === 'document' && !documentHTML && template && wpsData) {
    const formValues = form.getFieldsValue()
    
    // 重新构建modules_data从表单值
    const modulesData: Record<string, any> = {}
    
    template.module_instances.forEach(instance => {
      const moduleData: Record<string, any> = {
        moduleId: instance.moduleId,
        customName: instance.customName,
        data: {}
      }
      
      const module = getModuleById(instance.moduleId)
      if (module) {
        Object.keys(module.fields).forEach(fieldKey => {
          const formFieldName = `${instance.instanceId}_${fieldKey}`
          if (formValues[formFieldName] !== undefined) {
            let fieldValue = formValues[formFieldName]
            
            // 处理日期字段
            const fieldDef = module.fields[fieldKey]
            if (fieldDef?.type === 'date' && dayjs.isDayjs(fieldValue)) {
              fieldValue = fieldValue.format('YYYY-MM-DD')
            }
            
            moduleData.data[fieldKey] = fieldValue
          }
        })
      }
      
      modulesData[instance.instanceId] = moduleData
    })
    
    // 生成HTML
    const html = convertModulesToTipTapHTML(
      template.module_instances,
      modulesData,
      {
        title: wpsData.title || '',
        number: wpsData.wps_number || '',
        revision: wpsData.revision || 'A'
      },
      'wps'
    )
    
    setDocumentHTML(html)
  }
}
```

**作用**：
- 处理编辑模式切换
- 检查是否需要生成HTML
- 从表单数据构建模块数据
- 调用转换函数生成HTML
- 更新状态触发编辑器刷新

**更新UI绑定**：
```typescript
<Radio.Group
  value={editMode}
  onChange={e => handleEditModeChange(e.target.value)}
  buttonStyle="solid"
>
```

---

## 📊 数据流程

### 流程图
```
用户点击"文档编辑"
    ↓
handleEditModeChange('document')
    ↓
检查documentHTML是否为空
    ↓
如果为空：
    ↓
获取当前表单数据 (form.getFieldsValue())
    ↓
遍历所有模块实例
    ↓
构建modulesData对象
    ↓
调用convertModulesToTipTapHTML()
    ↓
生成HTML字符串
    ↓
setDocumentHTML(html)
    ↓
触发WPSDocumentEditor的useEffect
    ↓
editor.commands.setContent(initialContent)
    ↓
编辑器显示格式化的文档内容
```

---

## 🎨 生成的HTML格式

### 文档结构
```html
<h1>文档标题</h1>
<p style="text-align: center;">文档编号: WPS-001 | 版本: A</p>
<hr />

<h2>模块名称1</h2>
<table>
  <tbody>
    <tr>
      <td style="width: 30%; font-weight: bold;">字段标签 (单位)</td>
      <td style="width: 70%;">字段值</td>
    </tr>
    <!-- 更多字段行 -->
  </tbody>
</table>
<p></p>

<h2>模块名称2</h2>
<table>
  <!-- 模块2的字段 -->
</table>
<p></p>

<!-- 更多模块 -->
```

### 字段值格式化
- **文本**: 直接显示
- **数字**: 直接显示
- **日期**: YYYY-MM-DD格式
- **选择**: 显示选中的值
- **复选框**: 显示勾选的选项
- **表格**: 嵌套HTML表格
- **图片**: `<img>`标签
- **空值**: 显示"-"

---

## 🔄 使用场景

### 场景1: 新建WPS后首次编辑
1. 用户在表单模式填写数据
2. 点击"文档编辑"标签
3. 系统自动生成HTML文档
4. 用户可以在文档中调整格式

### 场景2: 编辑已保存的WPS
1. 打开已有WPS
2. 如果有保存的`document_html`，直接显示
3. 如果没有，从`modules_data`生成

### 场景3: 修改表单后查看文档
1. 在表单模式修改数据
2. 切换到文档模式
3. 如果之前没有HTML，生成新的
4. 如果有HTML，保持原有内容（用户可能已编辑）

---

## ⚠️ 注意事项

### 1. 数据优先级
- **已保存的document_html** > **从表单生成的HTML**
- 如果用户在文档模式编辑过，切换回表单再切回文档，会保留文档模式的编辑

### 2. 数据同步方向
- **表单 → 文档**: 自动（首次切换时）
- **文档 → 表单**: 不自动（避免丢失格式）

### 3. 保存机制
- 表单模式保存：更新`modules_data`
- 文档模式保存：更新`document_html`
- 两者独立存储

---

## 🎯 用户体验

### 优点
✅ 无需手动复制粘贴  
✅ 自动格式化，专业美观  
✅ 可以在文档模式自由编辑  
✅ 支持导出Word/PDF  

### 建议工作流程
1. **数据录入**: 使用表单模式（结构化、有验证）
2. **格式调整**: 切换到文档模式（自由排版）
3. **最终审核**: 在文档模式查看和微调
4. **导出分享**: 导出Word或PDF

---

## 🐛 故障排除

### 问题1: 切换到文档模式显示空白
**原因**: 
- 表单数据为空
- 模板未加载
- 转换函数出错

**解决**:
1. 检查表单是否有数据
2. 检查浏览器控制台错误
3. 确认模板已正确加载

### 问题2: 文档内容不更新
**原因**: 
- 已有保存的document_html
- useEffect未触发

**解决**:
1. 清空document_html重新生成
2. 刷新页面
3. 检查React DevTools

### 问题3: 日期格式错误
**原因**: dayjs对象未正确转换

**解决**: 已在代码中处理，自动转换为字符串

---

## 📚 相关文件

### 核心文件
- `frontend/src/components/DocumentEditor/WPSDocumentEditor.tsx` - 编辑器组件
- `frontend/src/pages/WPS/WPSEdit.tsx` - 编辑页面
- `frontend/src/utils/moduleToTipTapHTML.ts` - 转换工具

### 相关文档
- `DOCUMENT_EDITOR_IMPLEMENTATION.md` - 编辑器实现文档
- `TIPTAP_IMPORT_FIX.md` - TipTap导入修复
- `README_DOCUMENT_EDITOR.md` - 使用说明

---

## 🎊 总结

### 实现的功能
✅ 自动从表单数据生成文档  
✅ 实时同步到编辑器  
✅ 智能判断是否需要重新生成  
✅ 保持编辑器性能  

### 用户价值
✅ 节省手动输入时间  
✅ 保证数据一致性  
✅ 提供专业文档格式  
✅ 支持灵活编辑  

---

**功能状态**: ✅ 已完成并测试  
**最后更新**: 2025-10-27

现在切换到文档编辑模式时，会自动显示表单中的所有数据！🎉

