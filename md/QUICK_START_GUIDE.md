# 🚀 WPS文档编辑器快速启动指南

## 📋 前置条件

- Node.js 16+ 和 npm
- Python 3.8+
- PostgreSQL数据库
- 已有的WPS系统运行环境

## ⚡ 快速启动（5分钟）

### 步骤1：安装前端依赖（2分钟）

```bash
cd frontend
npm install
```

前端依赖已经在package.json中配置好，npm install会自动安装TipTap相关包。

### 步骤2：安装后端依赖（2分钟）

```bash
cd backend

# 方法1：使用pip直接安装
pip install python-docx weasyprint beautifulsoup4 lxml

# 方法2：使用安装脚本
python install_export_dependencies.py

# 方法3：从requirements.txt安装
pip install -r requirements.txt
```

### 步骤3：运行数据库迁移（1分钟）

```bash
cd backend

# 连接到PostgreSQL并执行迁移
psql -U postgres -d your_database_name -f migrations/add_document_html_to_wps.sql
```

或者在PostgreSQL客户端中执行：

```sql
ALTER TABLE wps ADD COLUMN IF NOT EXISTS document_html TEXT;
COMMENT ON COLUMN wps.document_html IS '文档HTML内容（用于文档编辑模式）';
```

### 步骤4：启动应用

#### 启动后端

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 启动前端

```bash
cd frontend
npm run dev
```

## ✅ 验证安装

### 1. 检查前端

访问 `http://localhost:5173/wps` （或您的前端地址）

1. 进入任意WPS编辑页面
2. 应该能看到"表单编辑"和"文档编辑"两个标签
3. 点击"文档编辑"标签
4. 应该能看到富文本编辑器和工具栏

### 2. 检查后端API

访问 `http://localhost:8000/docs`

应该能看到以下新增的API端点：
- `POST /api/v1/wps/{wps_id}/export/word`
- `POST /api/v1/wps/{wps_id}/export/pdf`

### 3. 测试导出功能

1. 在文档编辑器中输入一些内容
2. 点击"保存"按钮
3. 点击"导出Word"按钮，应该下载一个.docx文件
4. 点击"导出PDF"按钮，应该下载一个.pdf文件

## 🐛 常见问题

### Q1: WeasyPrint安装失败

**Windows用户**：WeasyPrint在Windows上需要额外的系统库。

**解决方案A**：使用预编译的wheel文件
```bash
pip install --upgrade pip
pip install weasyprint
```

**解决方案B**：如果仍然失败，可以暂时跳过PDF导出功能
```bash
# 只安装Word导出依赖
pip install python-docx beautifulsoup4 lxml
```

然后在 `backend/app/services/document_export_service.py` 中，PDF导出会自动禁用。

### Q2: 前端编译错误

如果遇到TipTap相关的编译错误：

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Q3: 数据库迁移失败

如果表已经存在document_html字段：

```sql
-- 检查字段是否存在
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'wps' AND column_name = 'document_html';
```

如果已存在，可以跳过迁移步骤。

### Q4: 导出的PDF中文显示为方块

确保系统安装了中文字体。在Linux上：

```bash
sudo apt-get install fonts-wqy-microhei fonts-wqy-zenhei
```

## 📖 使用教程

### 基本编辑

1. **切换到文档编辑模式**
   - 在WPS编辑页面，点击"文档编辑"标签

2. **使用工具栏**
   - 保存：保存当前文档
   - 导出Word：导出为.docx文件
   - 导出PDF：导出为PDF文件
   - 打印：使用浏览器打印功能
   - 粗体/斜体/下划线：文本格式化
   - 标题：H1、H2、H3标题
   - 对齐：左对齐、居中、右对齐、两端对齐
   - 列表：有序列表、无序列表
   - 表格：插入表格、添加/删除行列
   - 图片：插入图片
   - 颜色：设置文本颜色

3. **插入表格**
   - 点击"插入表格"按钮
   - 使用"添加行"、"添加列"按钮扩展表格
   - 使用"删除行"、"删除列"按钮缩减表格

4. **保存文档**
   - 点击工具栏的"保存"按钮
   - 文档内容会保存到数据库的`document_html`字段

### 导出文档

1. **导出Word**
   - 点击"导出Word"按钮
   - 浏览器会自动下载.docx文件
   - 文件名格式：`WPS_{编号}_{日期}.docx`

2. **导出PDF**
   - 点击"导出PDF"按钮
   - 浏览器会自动下载.pdf文件
   - 文件名格式：`WPS_{编号}_{日期}.pdf`

3. **打印**
   - 点击"打印"按钮
   - 使用浏览器的打印对话框
   - 可以选择打印机或另存为PDF

## 🎯 下一步

### 扩展到PQR和pPQR

1. 为PQR和pPQR表添加`document_html`字段
2. 创建PQR和pPQR的导出API端点
3. 在PQREdit.tsx和PPQREdit.tsx中集成文档编辑器

### 高级功能

1. **协作编辑**：使用TipTap的Collaboration扩展
2. **版本历史**：保存文档的历史版本
3. **自定义模板**：创建预设的文档模板
4. **批量导出**：一次导出多个文档

## 📚 更多资源

- [完整实现文档](./DOCUMENT_EDITOR_IMPLEMENTATION.md)
- [TipTap官方文档](https://tiptap.dev/)
- [python-docx文档](https://python-docx.readthedocs.io/)
- [WeasyPrint文档](https://weasyprint.org/)

## 💡 提示

- 建议以**表单模式为主**，文档模式为辅
- 从表单模式切换到文档模式是无损的
- 从文档模式切换回表单模式可能丢失格式
- 定期保存文档，避免数据丢失
- 导出前先保存文档

## 🎉 完成！

现在您已经成功安装并配置了WPS文档编辑器功能。开始享受类似Word的编辑体验吧！

如有问题，请查看[完整实现文档](./DOCUMENT_EDITOR_IMPLEMENTATION.md)或提交Issue。

