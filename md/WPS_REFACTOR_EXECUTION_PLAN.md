# WPS 模板系统重构执行计划

## 📅 项目时间表

### 第一阶段：前端模块扩展（1-2天）

#### 任务1：添加5个新模块到预设库
- **文件**：`frontend/src/constants/wpsModules.ts`
- **工作**：
  - 添加 header_data 模块
  - 添加 summary_info 模块
  - 添加 diagram_info 模块
  - 添加 weld_layer 模块
  - 添加 additional_info 模块
- **验证**：
  - 模块在 ModuleLibrary 中显示
  - 可以拖拽到 TemplateCanvas
  - 字段正确显示

#### 任务2：创建3个预设模板
- **文件**：`frontend/src/constants/wpsModules.ts` 或新文件
- **工作**：
  - 创建 SMAW 预设模板
  - 创建 GMAW 预设模板
  - 创建 GTAW 预设模板
- **验证**：
  - 模板可以在 TemplateSelector 中选择
  - 模板包含正确的模块组合

---

### 第二阶段：后端模块支持（1天）

#### 任务3：后端模块库更新
- **文件**：`backend/app/models/custom_module.py`
- **工作**：
  - 确保支持所有新模块类型
  - 验证字段定义完整
- **验证**：
  - API 可以返回新模块信息

#### 任务4：创建预设模板数据
- **文件**：新建迁移脚本
- **工作**：
  - 创建 SMAW 预设模板记录
  - 创建 GMAW 预设模板记录
  - 创建 GTAW 预设模板记录
- **验证**：
  - 数据库中有3个预设模板
  - 模板包含正确的 module_instances

---

### 第三阶段：删除标准模板系统（1-2天）

#### 任务5：删除数据库数据
- **工作**：
  - 删除 wps_templates 表中所有 is_system=true 的记录
  - 验证没有其他数据依赖
- **验证**：
  - 数据库中没有旧系统模板
  - 现有 WPS 记录仍然完整

#### 任务6：删除迁移脚本
- **文件**：
  - `backend/migrations/insert_system_templates.sql`
  - `backend/migrations/insert_remaining_templates.sql`
- **工作**：
  - 删除这两个文件
  - 更新 `create_wps_templates_table.sql`（移除示例数据）

#### 任务7：更新后端模型和 Schema
- **文件**：
  - `backend/app/models/wps_template.py`
  - `backend/app/schemas/wps_template.py`
- **工作**：
  - 移除 field_schema 字段
  - 移除 ui_layout 字段
  - 移除 validation_rules 字段
  - 移除 default_values 字段
  - 更新相关 Schema
- **验证**：
  - 后端编译无错误
  - API 测试通过

#### 任务8：更新后端服务
- **文件**：`backend/app/services/wps_template_service.py`
- **工作**：
  - 移除处理 field_schema 的逻辑
  - 移除处理 ui_layout 的逻辑
  - 简化模板创建/更新逻辑
- **验证**：
  - 服务测试通过
  - 模板 CRUD 操作正常

#### 任务9：删除前端组件
- **文件**：
  - `frontend/src/components/WPS/DynamicFormRenderer.tsx`
- **工作**：
  - 删除该文件
  - 更新所有导入该组件的文件
- **验证**：
  - 前端编译无错误

#### 任务10：更新前端类型定义
- **文件**：`frontend/src/services/wpsTemplates.ts`
- **工作**：
  - 移除 FieldSchema 接口
  - 移除 UILayout 接口
  - 更新 WPSTemplate 接口
- **验证**：
  - TypeScript 编译无错误

#### 任务11：更新 WPS 创建流程
- **文件**：`frontend/src/pages/WPS/WPSCreate.tsx`
- **工作**：
  - 移除 DynamicFormRenderer 导入
  - 改为使用模块化模板渲染
  - 更新表单提交逻辑
- **验证**：
  - WPS 创建流程正常
  - 数据保存正确

---

### 第四阶段：测试和验证（1-2天）

#### 任务12：功能测试
- **测试项**：
  - [ ] 模块库显示所有20个模块
  - [ ] 可以拖拽模块到画布
  - [ ] 可以创建自定义模板
  - [ ] 可以选择预设模板
  - [ ] 可以创建 WPS 记录
  - [ ] WPS 数据保存正确
  - [ ] 现有 WPS 记录仍可查看

#### 任务13：数据迁移验证
- **验证项**：
  - [ ] 现有 WPS 数据完整
  - [ ] 现有 WPS 可以正常显示
  - [ ] 没有数据丢失

#### 任务14：性能测试
- **测试项**：
  - [ ] 模块库加载速度
  - [ ] 模板选择响应速度
  - [ ] WPS 创建性能

#### 任务15：文档更新
- **文件**：
  - `frontend/WPS_TEMPLATE_SYSTEM_README.md`
  - 其他相关文档
- **工作**：
  - 更新使用指南
  - 删除过时内容
  - 添加新模块说明

---

## 🎯 关键检查点

### 检查点1：模块扩展完成
- [ ] 5个新模块已添加
- [ ] 模块在 UI 中显示正确
- [ ] 模块字段完整

### 检查点2：预设模板创建完成
- [ ] 3个预设模板已创建
- [ ] 模板包含正确的模块
- [ ] 模板可以选择使用

### 检查点3：标准模板删除完成
- [ ] 数据库数据已删除
- [ ] 代码已删除
- [ ] 没有编译错误

### 检查点4：功能验证完成
- [ ] 所有测试通过
- [ ] 现有数据完整
- [ ] 新流程正常工作

---

## ⚠️ 风险和缓解措施

### 风险1：现有 WPS 数据丢失
- **缓解**：
  - 备份数据库
  - 验证数据迁移
  - 保留查询现有数据的能力

### 风险2：用户习惯改变
- **缓解**：
  - 提供清晰的迁移指南
  - 预设模板与旧模板功能相同
  - 提供用户培训

### 风险3：性能下降
- **缓解**：
  - 进行性能测试
  - 优化模块加载
  - 缓存预设模板

---

## 📊 成功标准

✅ 所有 5 个新模块已添加并正常工作
✅ 3 个预设模板已创建并可使用
✅ 所有标准模板代码已删除
✅ 所有测试通过
✅ 现有 WPS 数据完整
✅ 新 WPS 创建流程正常
✅ 文档已更新

