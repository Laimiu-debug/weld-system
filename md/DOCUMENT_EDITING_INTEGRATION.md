# 文档编辑功能集成到 PQR 和 pPQR

## ✅ 完成的工作

已成功将文档编辑功能从 WPS 集成到 PQR 和 pPQR 模块中。

---

## 📋 修改的文件

### 1. **PQR 编辑页面**
- **文件**: `frontend/src/pages/PQR/PQREdit.tsx`

### 2. **pPQR 编辑页面**
- **文件**: `frontend/src/pages/pPQR/PPQREdit.tsx`

---

## 🎯 新增功能

### 1️⃣ **双模式编辑**

#### 表单编辑模式
- 结构化数据输入
- 字段验证
- 按照模板布局显示（支持多行多列）

#### 文档编辑模式
- 富文本编辑器（TipTap）
- 自动从表单数据生成HTML文档
- 支持自由编辑、格式化、插入图片等

### 2️⃣ **模式切换**

使用 Radio.Group 切换编辑模式：
- 🔘 **表单编辑** - 结构化表单
- 🔘 **文档编辑** - 富文本编辑器

### 3️⃣ **自动内容同步**

当从表单模式切换到文档模式时：
1. 获取当前表单数据
2. 构建 `modules_data` 结构
3. 调用 `convertModulesToTipTapHTML()` 生成HTML
4. 显示在文档编辑器中

### 4️⃣ **文档保存**

- 保存文档HTML到数据库的 `document_html` 字段
- 独立于表单数据保存
- 支持增量更新

### 5️⃣ **导出功能**（占位）

- 导出为 Word（开发中）
- 导出为 PDF（开发中）

---

## 🔧 技术实现

### 新增的 State

```typescript
const [editMode, setEditMode] = useState<'form' | 'document'>('form')
const [documentHTML, setDocumentHTML] = useState<string>('')
```

### 新增的导入

```typescript
import { Radio } from 'antd'
import { FormOutlined, FileWordOutlined } from '@ant-design/icons'
import WPSDocumentEditor from '@/components/DocumentEditor/WPSDocumentEditor'
import { convertModulesToTipTapHTML } from '@/utils/moduleToTipTapHTML'
```

### 新增的函数

#### 1. `handleEditModeChange(mode)`
- 处理编辑模式切换
- 自动生成文档HTML（如果需要）

#### 2. `handleSaveDocument(html)`
- 保存文档HTML到数据库
- 更新 `document_html` 字段

#### 3. `handleExportWord()`
- 导出为Word（占位）

#### 4. `handleExportPDF()`
- 导出为PDF（占位）

### 数据加载

在 `useEffect` 中添加：
```typescript
// 如果有 document_html，初始化文档内容
if (pqr.document_html) {
  setDocumentHTML(pqr.document_html)
}
```

---

## 📊 数据流

### 表单模式 → 文档模式

```
1. 用户点击"文档编辑"
   ↓
2. handleEditModeChange('document')
   ↓
3. 检查是否已有 documentHTML
   ↓
4. 如果没有，从表单数据生成：
   - form.getFieldsValues()
   - 构建 modulesData
   - convertModulesToTipTapHTML()
   ↓
5. setDocumentHTML(html)
   ↓
6. WPSDocumentEditor 显示内容
```

### 文档保存

```
1. 用户在编辑器中编辑
   ↓
2. 点击"保存"按钮
   ↓
3. handleSaveDocument(html)
   ↓
4. 调用 API: pqrService.update() / ppqrService.update()
   ↓
5. 更新 document_html 字段
   ↓
6. 显示成功消息
```

---

## 🎨 UI 变化

### 编辑模式切换器

```tsx
<Radio.Group
  value={editMode}
  onChange={e => handleEditModeChange(e.target.value)}
  buttonStyle="solid"
>
  <Radio.Button value="form">
    <FormOutlined /> 表单编辑
  </Radio.Button>
  <Radio.Button value="document">
    <FileWordOutlined /> 文档编辑
  </Radio.Button>
</Radio.Group>
```

### 条件渲染

```tsx
{editMode === 'form' ? (
  <Form>
    {/* 表单内容 */}
  </Form>
) : (
  <WPSDocumentEditor
    initialContent={documentHTML}
    onSave={handleSaveDocument}
    onExportWord={handleExportWord}
    onExportPDF={handleExportPDF}
  />
)}
```

---

## 🔄 与 WPS 的一致性

PQR 和 pPQR 的文档编辑功能与 WPS 完全一致：

| 功能 | WPS | PQR | pPQR |
|------|-----|-----|------|
| 双模式编辑 | ✅ | ✅ | ✅ |
| 自动生成HTML | ✅ | ✅ | ✅ |
| 多列布局支持 | ✅ | ✅ | ✅ |
| 文档保存 | ✅ | ✅ | ✅ |
| 导出Word | 🚧 | 🚧 | 🚧 |
| 导出PDF | 🚧 | 🚧 | 🚧 |

---

## 📝 使用方法

### 1. 创建/编辑 PQR 或 pPQR

1. 打开编辑页面
2. 默认显示**表单编辑模式**
3. 填写结构化数据

### 2. 切换到文档模式

1. 点击"文档编辑"按钮
2. 系统自动生成HTML文档
3. 显示完整的格式化文档

### 3. 编辑文档

1. 在富文本编辑器中自由编辑
2. 添加额外文字、调整格式
3. 插入图片、表格等

### 4. 保存文档

1. 点击编辑器中的"保存"按钮
2. 文档HTML保存到数据库
3. 下次打开时自动加载

### 5. 切换回表单模式

1. 点击"表单编辑"按钮
2. 返回结构化表单
3. 文档内容保持不变

---

## 🎯 关键特性

### ✅ 智能同步

- 首次切换到文档模式：自动生成HTML
- 已有文档内容：直接加载
- 表单数据变化：可重新生成

### ✅ 独立保存

- 表单数据和文档HTML分别保存
- 互不影响
- 灵活性高

### ✅ 布局保持

- 完全按照模板的行列布局
- 支持1-4列布局
- 不同行可以有不同列数

### ✅ 完整字段显示

- 显示所有字段（包括未填写的）
- 未填写字段显示为 "-"
- 符合真实文档格式

---

## 🚀 下一步

### 可选的增强功能

1. **导出功能**
   - 实现Word导出
   - 实现PDF导出

2. **版本控制**
   - 文档历史记录
   - 版本对比

3. **协作编辑**
   - 多人同时编辑
   - 实时同步

4. **模板定制**
   - 自定义文档样式
   - 公司Logo/水印

---

## ✅ 测试建议

1. **创建新的 PQR**
   - 使用多列模板
   - 填写部分字段
   - 切换到文档模式
   - 验证布局和内容

2. **编辑现有 PQR**
   - 打开已有文档
   - 修改表单数据
   - 切换到文档模式
   - 验证更新

3. **文档保存**
   - 在文档模式编辑
   - 保存文档
   - 刷新页面
   - 验证内容保持

4. **pPQR 同样测试**
   - 重复以上步骤
   - 验证功能一致性

---

**状态**: ✅ 已完成  
**功能**: ✅ PQR 和 pPQR 文档编辑功能  
**一致性**: ✅ 与 WPS 完全一致

现在 PQR 和 pPQR 都支持完整的文档编辑功能了！🎉

