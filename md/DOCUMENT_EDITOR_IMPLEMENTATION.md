# WPS文档编辑器实现文档

## 📋 概述

本文档描述了WPS/PQR/pPQR系统的文档编辑和导出功能的实现。该功能允许用户使用类似Word的富文本编辑器编辑文档，并导出为Word或PDF格式。

## 🎯 功能特性

### 1. 双编辑模式
- **表单编辑模式**：结构化的表单编辑，基于模块化模板
- **文档编辑模式**：所见即所得的富文本编辑器，类似Word体验

### 2. 富文本编辑功能
- ✅ 文本格式化（粗体、斜体、下划线、删除线）
- ✅ 标题（H1、H2、H3）
- ✅ 文本对齐（左对齐、居中、右对齐、两端对齐）
- ✅ 列表（有序列表、无序列表）
- ✅ 表格（插入、删除行/列、合并单元格）
- ✅ 图片插入
- ✅ 文本颜色
- ✅ 撤销/重做

### 3. 导出功能
- ✅ 导出为Word文档（.docx）
- ✅ 导出为PDF文档
- ✅ 浏览器打印功能
- ✅ A4纸张格式，专业排版

## 🏗️ 技术架构

### 前端技术栈
- **TipTap**: 基于ProseMirror的富文本编辑器（完全免费开源）
- **React**: UI框架
- **Ant Design**: UI组件库

### 后端技术栈
- **python-docx**: Word文档生成
- **WeasyPrint**: PDF文档生成
- **BeautifulSoup4**: HTML解析
- **FastAPI**: Web框架

## 📦 安装步骤

### 1. 前端依赖安装

```bash
cd frontend
npm install @tiptap/react @tiptap/starter-kit @tiptap/extension-table @tiptap/extension-table-row @tiptap/extension-table-cell @tiptap/extension-table-header @tiptap/extension-image @tiptap/extension-text-align @tiptap/extension-underline @tiptap/extension-color @tiptap/extension-text-style @tiptap/pm
```

### 2. 后端依赖安装

```bash
cd backend
pip install python-docx weasyprint beautifulsoup4 lxml
```

或者运行安装脚本：

```bash
cd backend
python install_export_dependencies.py
```

### 3. 数据库迁移

```bash
cd backend
psql -U your_username -d your_database -f migrations/add_document_html_to_wps.sql
```

## 📁 文件结构

### 前端文件

```
frontend/src/
├── components/
│   └── DocumentEditor/
│       ├── WPSDocumentEditor.tsx      # 文档编辑器组件
│       └── DocumentEditor.css         # 编辑器样式
├── utils/
│   └── moduleToTipTapHTML.ts          # 模块数据转HTML工具
└── pages/
    └── WPS/
        └── WPSEdit.tsx                # WPS编辑页面（已修改）
```

### 后端文件

```
backend/
├── app/
│   ├── api/v1/endpoints/
│   │   └── wps_export.py              # 导出API端点
│   ├── services/
│   │   └── document_export_service.py # 导出服务
│   ├── models/
│   │   └── wps.py                     # WPS模型（已添加document_html字段）
│   └── schemas/
│       └── wps.py                     # WPS Schema（已添加document_html字段）
├── migrations/
│   └── add_document_html_to_wps.sql   # 数据库迁移脚本
└── requirements.txt                    # Python依赖（已更新）
```

## 🚀 使用方法

### 1. 编辑文档

1. 进入WPS编辑页面
2. 点击"文档编辑"标签切换到文档编辑模式
3. 使用工具栏进行文本编辑、格式化、插入表格等操作
4. 点击"保存"按钮保存文档

### 2. 导出文档

在文档编辑模式下：
- 点击"导出Word"按钮导出为.docx文件
- 点击"导出PDF"按钮导出为PDF文件
- 点击"打印"按钮使用浏览器打印功能

## 🔧 API接口

### 1. 导出Word

```
POST /api/v1/wps/{wps_id}/export/word
```

**响应**：Word文档文件流

### 2. 导出PDF

```
POST /api/v1/wps/{wps_id}/export/pdf
```

**响应**：PDF文档文件流

## 💾 数据存储

### WPS表新增字段

```sql
document_html TEXT  -- 存储富文本HTML内容
```

### 数据结构

- **modules_data** (JSONB): 结构化的模块数据（表单模式）
- **document_html** (TEXT): 富文本HTML内容（文档模式）

两种数据格式独立存储，互不影响。

## 🎨 样式说明

### A4纸张样式

- 宽度：21cm
- 高度：29.7cm
- 边距：2cm（上下左右）

### 打印样式

使用CSS `@media print` 媒体查询：
- 隐藏工具栏和编辑按钮
- 优化表格和图片的分页
- 保持专业的文档外观

## 🔄 模块数据转换

### 表单模式 → 文档模式

使用 `convertModulesToTipTapHTML()` 函数将模块化数据转换为HTML：

```typescript
const html = convertModulesToTipTapHTML(
  modules,
  modulesData,
  {
    title: wpsData.title,
    number: wpsData.wps_number,
    revision: wpsData.revision
  },
  'wps'
)
```

### 文档模式 → 表单模式

⚠️ **注意**：从文档模式切换回表单模式可能会丢失部分格式信息。建议以表单模式为主，文档模式为辅。

## 📝 开发说明

### 扩展到PQR和pPQR

要将此功能扩展到PQR和pPQR：

1. 为PQR和pPQR表添加`document_html`字段
2. 创建类似的导出API端点
3. 在PQREdit.tsx和PPQREdit.tsx中集成文档编辑器
4. 更新相应的Schema

### 自定义编辑器

TipTap编辑器高度可定制，可以添加更多扩展：

```typescript
import { Extension } from '@tiptap/core'

const editor = useEditor({
  extensions: [
    StarterKit,
    // 添加更多扩展...
  ],
})
```

## 🐛 故障排除

### 1. WeasyPrint安装失败

WeasyPrint依赖系统库，在Windows上可能需要额外配置。

**解决方案**：
- 安装GTK+ for Windows
- 或使用Docker容器运行后端

### 2. 中文字体问题

PDF导出时中文可能显示为方块。

**解决方案**：
在`document_export_service.py`中配置中文字体：

```python
font-family: 'SimSun', 'Microsoft YaHei', 'Arial', sans-serif;
```

### 3. 图片无法导出

确保图片路径正确，且后端可以访问。

## 📊 性能优化

### 1. 大文档处理

对于包含大量内容的文档：
- 使用分页加载
- 优化HTML结构
- 压缩图片

### 2. 导出速度

- 使用异步任务队列（Celery）处理导出
- 缓存常用模板
- 优化HTML到Word/PDF的转换逻辑

## 🔐 安全考虑

1. **XSS防护**：TipTap自动处理HTML清理
2. **文件大小限制**：限制上传图片大小
3. **权限检查**：确保用户只能导出自己有权限的文档

## 📚 参考资源

- [TipTap文档](https://tiptap.dev/)
- [python-docx文档](https://python-docx.readthedocs.io/)
- [WeasyPrint文档](https://weasyprint.org/)

## 🎉 总结

该实现提供了一个完整的文档编辑和导出解决方案，完全基于免费开源技术，无需任何付费许可证。用户可以在熟悉的Word式界面中编辑文档，并导出为专业的Word或PDF格式。

