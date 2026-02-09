# WPS 模块管理系统改进指南

## 📋 改进概述

本文档详细说明了对 WPS 模块管理系统的三大改进：

1. **预设模块功能增强** - 添加预览和复制功能
2. **自定义模块预览改进** - 从字段列表改为真实表单渲染
3. **图片/图表模块支持** - 支持图片上传和自动生成图表

---

## 1️⃣ 预设模块功能增强

### 功能说明

在模块管理页面的预设模块列表中，为每个预设模块添加了两个新按钮：

#### 1.1 预览按钮
- **位置**: 预设模块表格的"操作"列
- **功能**: 点击后在模态框中显示模块的真实表单渲染效果
- **显示内容**:
  - 模块名称和描述
  - 字段数量和可重复状态
  - 所有字段的实际输入控件（文本框、数字框、下拉选择等）
  - 字段的单位、占位符、验证规则等

#### 1.2 复制按钮
- **位置**: 预设模块表格的"操作"列
- **功能**: 将预设模块复制到自定义模块创建器
- **自动处理**:
  - 模块名称自动添加"(副本)"后缀
  - 所有字段配置完整复制
  - 用户可在此基础上修改后保存为自己的自定义模块

### 实现文件

- `frontend/src/pages/WPS/ModuleManagement.tsx` - 添加预览和复制按钮
- `frontend/src/components/WPS/ModulePreview.tsx` - 新建预览组件
- `frontend/src/components/WPS/CustomModuleCreator.tsx` - 支持从预设模块复制

### 使用流程

```
1. 打开模块管理页面
2. 切换到"预设模块"标签页
3. 找到要操作的模块
4. 点击"预览"按钮查看表单效果
5. 点击"复制"按钮复制到自定义模块创建器
6. 修改模块名称和配置
7. 点击"保存副本"完成创建
```

---

## 2️⃣ 自定义模块预览改进

### 功能说明

自定义模块创建器现在提供了两个标签页：

#### 2.1 编辑标签页
- 模块基本信息编辑（名称、描述、分类等）
- 字段定义编辑
- 字段预览（标签形式）

#### 2.2 预览标签页
- **新增功能**: 显示模块的真实表单渲染效果
- **实时更新**: 编辑字段后，预览会实时更新
- **完整体验**: 显示所有字段的实际输入控件
- **禁用条件**: 当没有字段时，预览标签页被禁用

### 实现文件

- `frontend/src/components/WPS/CustomModuleCreator.tsx` - 添加预览标签页
- `frontend/src/components/WPS/ModuleFormRenderer.tsx` - 支持自定义字段渲染

### 使用流程

```
1. 打开模块管理页面
2. 点击"创建自定义模块"按钮
3. 填写模块基本信息
4. 在"编辑"标签页添加字段
5. 切换到"预览"标签页查看表单效果
6. 如需修改，返回"编辑"标签页调整
7. 满意后点击"创建模块"保存
```

---

## 3️⃣ 图片/图表模块支持

### 功能说明

#### 3.1 图片字段类型
- **新字段类型**: `image`
- **特性**:
  - 支持图片上传（PNG、JPG、SVG 等格式）
  - 图片预览显示
  - 可配置接受的文件类型
  - 可配置最大文件大小

#### 3.2 技术图表模块
- **新预设模块**: "技术图表"
- **包含字段**:
  - 坡口图（image 类型）
  - 焊层焊道图（image 类型）
  - 其他技术图表（file 类型）

#### 3.3 图表生成器（可选）
- **新组件**: `DiagramGenerator.tsx`
- **功能**:
  - 根据参数自动生成坡口图
  - 根据参数自动生成焊层焊道图
  - 支持图表下载为 PNG 格式

### 实现文件

- `frontend/src/types/wpsModules.ts` - 添加 image 字段类型定义
- `frontend/src/components/WPS/ModuleFormRenderer.tsx` - 实现 image 字段渲染
- `frontend/src/components/WPS/CustomModuleCreator.tsx` - 支持 image 字段编辑
- `frontend/src/components/WPS/DiagramGenerator.tsx` - 图表生成器组件
- `frontend/src/constants/wpsModules.ts` - 添加技术图表预设模块

### 使用流程

#### 上传图片方式
```
1. 创建或编辑自定义模块
2. 添加字段，选择"图片"类型
3. 配置接受的文件类型和最大大小
4. 保存模块
5. 在 WPS 表单中上传图片
```

#### 自动生成图表方式（未来功能）
```
1. 在 WPS 表单中使用图表生成器
2. 输入坡口参数（类型、角度、根部间隙等）
3. 点击"生成图表"
4. 图表自动生成并显示
5. 点击"下载"保存为 PNG 文件
```

---

## 🔧 技术细节

### 新增类型定义

```typescript
// FieldDefinition 扩展
export interface FieldDefinition {
  // ... 现有字段 ...
  type: '...' | 'image'  // 新增 image 类型
  accept?: string  // 文件类型过滤
  maxSize?: number  // 最大文件大小（字节）
}
```

### 新增组件

#### ModulePreview.tsx
- 显示单个模块的预览
- 使用 ModuleFormRenderer 渲染表单

#### DiagramGenerator.tsx
- 生成坡口图和焊层焊道图
- 支持参数配置和图表下载

### 修改的组件

#### ModuleFormRenderer.tsx
- 添加 `customFields` 参数支持自定义字段预览
- 添加 `image` 字段类型的渲染逻辑

#### CustomModuleCreator.tsx
- 添加 `copyFromModule` 参数支持复制预设模块
- 添加预览标签页
- 添加 `image` 字段类型选项

#### ModuleManagement.tsx
- 预设模块表格添加"预览"和"复制"按钮
- 添加预览模态框

---

## 📝 测试清单

### 预设模块功能测试
- [ ] 预览按钮显示正确的表单
- [ ] 预览模态框可以关闭
- [ ] 复制按钮正确填充表单
- [ ] 复制的模块名称包含"(副本)"后缀
- [ ] 复制的字段配置完整

### 自定义模块预览测试
- [ ] 编辑标签页正常工作
- [ ] 预览标签页显示正确的表单
- [ ] 编辑字段后预览实时更新
- [ ] 没有字段时预览标签页被禁用
- [ ] 创建模块成功

### 图片字段功能测试
- [ ] 图片字段类型可以选择
- [ ] 图片字段可以配置接受类型
- [ ] 图片字段可以配置最大大小
- [ ] 图片上传正常工作
- [ ] 图片预览显示正确

### 技术图表模块测试
- [ ] 技术图表模块在预设模块列表中显示
- [ ] 技术图表模块可以预览
- [ ] 技术图表模块可以复制
- [ ] 图片字段在表单中正确渲染

---

## 🚀 后续改进建议

1. **图表生成器集成**
   - 在 WPS 表单中集成 DiagramGenerator 组件
   - 支持实时生成和预览图表

2. **图片编辑功能**
   - 添加图片裁剪功能
   - 添加图片标注功能

3. **模块模板库**
   - 创建更多预设模块
   - 支持模块分享和导入

4. **性能优化**
   - 图片压缩和优化
   - 大型表单的虚拟滚动

---

## 📞 常见问题

### Q: 如何修改已复制的模块名称？
A: 在自定义模块创建器中，模块名称字段是可编辑的，直接修改即可。

### Q: 图片字段支持哪些格式？
A: 默认支持所有图片格式（image/*），可通过 `accept` 参数自定义。

### Q: 如何删除已创建的自定义模块？
A: 在模块管理页面的"自定义模块"标签页中，点击"删除"按钮。

### Q: 预览和实际表单有区别吗？
A: 预览使用相同的渲染组件，应该完全一致。

---

## 📚 相关文件

- `frontend/src/pages/WPS/ModuleManagement.tsx`
- `frontend/src/components/WPS/ModulePreview.tsx`
- `frontend/src/components/WPS/CustomModuleCreator.tsx`
- `frontend/src/components/WPS/ModuleFormRenderer.tsx`
- `frontend/src/components/WPS/DiagramGenerator.tsx`
- `frontend/src/types/wpsModules.ts`
- `frontend/src/constants/wpsModules.ts`

