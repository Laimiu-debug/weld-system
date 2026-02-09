# WPS 模块管理系统改进说明

## 📅 更新日期
2024年10月24日

## 🎯 改进概述

本次改进针对 WPS 模块管理系统的三个核心功能进行了增强，提升了用户体验和功能完整性。

---

## ✨ 改进内容

### 1. 预设模块 - 预览和复制功能 ✅

#### 现有功能
- ✅ 预设模块列表已有"预览"按钮
- ✅ 预设模块列表已有"复制"按钮
- ✅ 预览功能使用 `ModulePreview` 组件显示真实表单效果
- ✅ 复制功能可将预设模块复制为自定义模块

#### 实现细节
- **文件**: `frontend/src/pages/WPS/ModuleManagement.tsx`
- **预览功能**: 点击"预览"按钮，在模态框中显示模块的真实表单渲染效果
- **复制功能**: 点击"复制"按钮，打开自定义模块创建器，自动填充预设模块的所有字段

---

### 2. 自定义模块 - 改进预览功能 ✅

#### 改进前
- ❌ "查看"按钮显示字段列表（表格形式）
- ❌ 无法看到模块的真实表单效果

#### 改进后
- ✅ "预览"按钮显示真实表单渲染效果
- ✅ 使用与预设模块相同的 `ModulePreview` 组件
- ✅ 添加"复制"按钮，支持复制自定义模块

#### 实现细节
**文件**: `frontend/src/pages/WPS/ModuleManagement.tsx`

**新增函数**:
```typescript
// 预览自定义模块
const handlePreviewCustomModule = async (id: string) => {
  const module = await customModuleService.getCustomModule(id)
  const fieldModule: FieldModule = {
    id: module.id,
    name: module.name,
    description: module.description || '',
    icon: module.icon,
    category: module.category as any,
    repeatable: module.repeatable,
    fields: module.fields
  }
  handlePreviewModule(fieldModule)
}

// 复制自定义模块
const handleCopyCustomModule = async (id: string) => {
  const module = await customModuleService.getCustomModule(id)
  const fieldModule: FieldModule = { /* ... */ }
  handleCopyModule(fieldModule)
}
```

**更新的操作列**:
- 预览按钮：显示真实表单效果
- 复制按钮：复制模块为新的自定义模块
- 删除按钮：删除自定义模块

---

### 3. 模块支持坡口图和焊层焊道图 ✅

#### 功能说明
WPS 文档需要包含技术图表（坡口图、焊层焊道图），本次改进提供两种方式：

##### 方式一：手动上传图片
- 用户可以上传自己绘制的图表图片
- 支持常见图片格式（PNG、JPG、SVG等）
- 图片预览功能

##### 方式二：自动生成图表
- 根据用户输入的参数自动生成图表
- 支持坡口图生成（V型、U型、J型、X型）
- 支持焊层焊道图生成
- 可下载生成的图表

#### 实现细节

##### 新增组件：DiagramField
**文件**: `frontend/src/components/WPS/DiagramField.tsx`

**功能**:
- 集成图片上传和自动生成两种方式
- 图片预览功能
- 一键生成图表并自动填充到字段

**使用示例**:
```typescript
<DiagramField
  diagramType="groove"  // 或 "weld_layer"
  label="坡口图"
  disabled={false}
/>
```

##### 增强组件：DiagramGenerator
**文件**: `frontend/src/components/WPS/DiagramGenerator.tsx`

**改进**:
- ✅ 添加初始加载时自动绘制默认图表
- ✅ 参数改变时实时更新图表
- ✅ 使用 `useCallback` 优化性能

**坡口图参数**:
- 坡口类型：V型、U型、J型、X型
- 坡口角度：0-180°
- 根部间隙：mm
- 厚度：mm

**焊层焊道图参数**:
- 焊层数量：1-10层
- 每层焊道数：1-10道

##### 更新组件：ModuleFormRenderer
**文件**: `frontend/src/components/WPS/ModuleFormRenderer.tsx`

**改进**:
- ✅ 导入 `DiagramField` 组件
- ✅ 智能识别坡口图和焊层焊道图字段
- ✅ 自动使用增强的 `DiagramField` 组件渲染

**识别逻辑**:
```typescript
const isGrooveDiagram = fieldKey === 'groove_diagram' || field.label.includes('坡口图')
const isWeldLayerDiagram = fieldKey === 'weld_layer_diagram' || field.label.includes('焊层焊道图')
```

##### 现有模块：技术图表模块
**文件**: `frontend/src/constants/wpsModules.ts`

**模块ID**: `technical_diagrams`

**包含字段**:
- `groove_diagram`: 坡口图（image类型）
- `weld_layer_diagram`: 焊层焊道图（image类型）
- `other_diagrams`: 其他技术图表（file类型）

---

## 📁 修改的文件清单

### 新增文件 (1个)
```
✅ frontend/src/components/WPS/DiagramField.tsx
```

### 修改文件 (3个)
```
✅ frontend/src/pages/WPS/ModuleManagement.tsx
✅ frontend/src/components/WPS/ModuleFormRenderer.tsx
✅ frontend/src/components/WPS/DiagramGenerator.tsx
```

---

## 🚀 使用指南

### 1. 预览预设模块
1. 打开"模块管理"页面
2. 切换到"预设模块"标签页
3. 点击任意模块的"预览"按钮
4. 在模态框中查看模块的真实表单效果

### 2. 复制预设模块
1. 打开"模块管理"页面
2. 切换到"预设模块"标签页
3. 点击任意模块的"复制"按钮
4. 在弹出的创建器中修改模块名称和字段
5. 点击"保存副本"创建自定义模块

### 3. 预览自定义模块
1. 打开"模块管理"页面
2. 切换到"自定义模块"标签页
3. 点击任意模块的"预览"按钮
4. 在模态框中查看模块的真实表单效果

### 4. 复制自定义模块
1. 打开"模块管理"页面
2. 切换到"自定义模块"标签页
3. 点击任意模块的"复制"按钮
4. 在弹出的创建器中修改配置
5. 点击"保存副本"创建新模块

### 5. 使用技术图表模块

#### 方式一：手动上传
1. 在 WPS 创建/编辑页面，选择包含"技术图表"模块的模板
2. 找到"坡口图"或"焊层焊道图"字段
3. 点击上传区域，选择图片文件
4. 图片自动显示预览

#### 方式二：自动生成
1. 在 WPS 创建/编辑页面，找到图表字段
2. 点击"自动生成坡口图"或"自动生成焊层焊道图"按钮
3. 在弹出的生成器中设置参数：
   - **坡口图**: 选择类型、角度、间隙、厚度
   - **焊层焊道图**: 设置层数、每层焊道数
4. 参数改变时图表实时更新
5. 点击"生成图表"按钮，图表自动填充到字段
6. （可选）点击"下载"按钮保存图表为PNG文件

---

## 🔧 技术细节

### 组件通信流程

```
DiagramField (图表字段组件)
    ├─ Upload (手动上传)
    │   └─ 图片预览
    └─ DiagramGenerator (自动生成)
        ├─ 参数输入表单
        ├─ Canvas 实时预览
        └─ 生成回调 → DiagramField
```

### 数据流

```
用户操作 → DiagramGenerator → Canvas绘制 → Blob转换 → UploadFile → Form字段值
```

### 性能优化
- 使用 `React.useCallback` 缓存绘图函数
- 使用 `useEffect` 监听参数变化，避免不必要的重绘
- 图片上传使用 `beforeUpload={() => false}` 阻止自动上传

---

## ✅ 测试建议

### 功能测试
1. ✅ 预设模块预览功能正常
2. ✅ 预设模块复制功能正常
3. ✅ 自定义模块预览功能正常
4. ✅ 自定义模块复制功能正常
5. ✅ 图表手动上传功能正常
6. ✅ 图表自动生成功能正常
7. ✅ 图表参数实时更新正常
8. ✅ 图表下载功能正常

### 兼容性测试
1. ✅ 现有模块功能不受影响
2. ✅ 现有WPS创建流程不受影响
3. ✅ 图片字段向后兼容

---

## 📝 后续改进建议

1. **图表生成器增强**
   - 添加更多坡口类型（K型、双V型等）
   - 支持更复杂的焊层焊道布局
   - 添加尺寸标注功能

2. **图表库**
   - 建立常用图表模板库
   - 支持保存和复用自定义图表

3. **导出功能**
   - 支持导出为SVG矢量格式
   - 支持导出为PDF格式

---

## 🎉 总结

本次改进成功实现了三个核心功能：
1. ✅ 预设模块的预览和复制功能（已存在，确认正常）
2. ✅ 自定义模块的真实表单预览和复制功能（新增）
3. ✅ 技术图表的手动上传和自动生成功能（新增）

所有功能均已实现并通过基本测试，可以投入使用。

