# WPS 模板系统架构重构分析报告

## 📊 现状分析

### 1. 当前系统架构

#### 两种模板定义方式并存：

**方式一：传统的固定结构模板（Standard Templates）**
- 使用 `field_schema` + `ui_layout` 定义
- 固定的标签页结构（表头数据、概要、示意图、焊层、附加信息）
- 7个系统内置模板（111, 114, 121, 135, 141, 15, 311）
- 每个模板都是完整的、独立的定义

**方式二：新的模块化模板（Module-based Templates）**
- 使用 `module_instances` 定义
- 基于拖拽式模块组合
- 15个预设模块库
- 支持自定义模块

#### 数据库表结构：
- `wps_templates` - 模板定义表
- `custom_modules` - 自定义模块表
- `wps` - WPS记录表（存储 JSONB 数据）

### 2. 现有的标准模板（需要删除）

#### 后端系统模板数据：
```
系统模板ID列表：
- system_111_smaw (手工电弧焊)
- system_114_fcaw (无保护气的药芯焊)
- system_121_saw (埋弧焊)
- system_135_gmaw (活性气体保护焊)
- system_141_gtaw (TIG焊)
- system_15_paw (等离子弧焊)
- system_311_oaw (氧乙炔焊)
```

#### 相关代码文件：
1. **后端迁移脚本**：
   - `backend/migrations/insert_system_templates.sql` - 插入7个系统模板
   - `backend/migrations/insert_remaining_templates.sql` - 补充模板数据
   - `backend/migrations/create_wps_templates_table.sql` - 创建模板表

2. **后端模型和服务**：
   - `backend/app/models/wps_template.py` - 模板模型（包含 field_schema, ui_layout）
   - `backend/app/schemas/wps_template.py` - 模板 Schema
   - `backend/app/services/wps_template_service.py` - 模板服务

3. **前端组件**：
   - `frontend/src/components/WPS/TemplateSelector.tsx` - 模板选择器
   - `frontend/src/components/WPS/DynamicFormRenderer.tsx` - 动态表单渲染
   - `frontend/src/pages/WPS/WPSCreate.tsx` - WPS创建页面

### 3. 现有的拖拽式模块系统

#### 预设模块库（15个）：
```
基本信息类：
- basic_info (基本信息)

材料信息类：
- filler_metal (填充金属)
- electrode_treatment (电极处理)
- tungsten_electrode (钨电极)

气体信息类：
- shielding_gas (保护气体)
- backing_gas (背部保护气)
- plasma_gas (等离子气体)

电气参数类：
- current_voltage (电流电压)
- current_pulse (电流脉冲)

运动参数类：
- welding_speed (焊接速度)
- wire_feed (送丝参数)
- oscillation (抖动参数)

设备信息类：
- equipment_info (设备信息)

计算结果类：
- calculation_results (计算结果)
```

#### 相关代码文件：
1. **前端**：
   - `frontend/src/constants/wpsModules.ts` - 预设模块库定义
   - `frontend/src/types/wpsModules.ts` - 模块类型定义
   - `frontend/src/components/WPS/ModuleLibrary.tsx` - 模块库组件
   - `frontend/src/components/WPS/TemplateBuilder.tsx` - 模板构建器
   - `frontend/src/components/WPS/TemplateCanvas.tsx` - 模板画布
   - `frontend/src/components/WPS/ModuleCard.tsx` - 模块卡片

2. **后端**：
   - `backend/app/models/custom_module.py` - 自定义模块模型
   - `backend/app/schemas/custom_module.py` - 自定义模块 Schema
   - `backend/app/services/custom_module_service.py` - 自定义模块服务
   - `backend/app/api/v1/endpoints/custom_modules.py` - 自定义模块 API
   - `backend/migrations/create_custom_modules_table.sql` - 自定义模块表

---

## 🎯 问题分析

### 1. 架构问题
- ❌ 两种模板定义方式并存，造成混乱
- ❌ 标准模板固定结构，不够灵活
- ❌ 用户界面不统一（有些用户看到标准模板，有些看到模块化模板）
- ❌ 维护成本高（需要维护两套系统）

### 2. 用户体验问题
- ❌ 标准模板的标签页结构不适合所有焊接工艺
- ❌ 无法自定义表单结构
- ❌ 模块化系统虽然灵活，但需要用户手动组合

### 3. 数据一致性问题
- ❌ WPS 数据存储格式不统一（有些用 field_schema，有些用 module_instances）
- ❌ 查询和统计困难

---

## ✅ 改进方案

### 1. 删除标准模板系统

**删除的数据库数据**：
- 删除 `wps_templates` 表中所有 `is_system=true` 的记录（7个系统模板）

**删除的代码**：
- `backend/migrations/insert_system_templates.sql`
- `backend/migrations/insert_remaining_templates.sql`
- `backend/migrations/create_wps_templates_table.sql` 中的示例数据

**保留但修改的代码**：
- `backend/app/models/wps_template.py` - 移除 `field_schema`, `ui_layout` 字段
- `backend/app/schemas/wps_template.py` - 移除相关 Schema
- `backend/app/services/wps_template_service.py` - 简化逻辑

**删除的前端组件**：
- `frontend/src/components/WPS/DynamicFormRenderer.tsx` - 动态表单渲染器

### 2. 保留并增强拖拽式模块系统

**保留的代码**：
- 所有模块库相关代码
- 所有拖拽组件

**需要扩展的模块**：
- ✅ 表头数据模块（Header Data Module）
- ✅ 概要模块（Summary Module）
- ✅ 示意图模块（Diagram Module）
- ✅ 焊层模块（Weld Layer Module）
- ✅ 附加信息模块（Additional Info Module）

### 3. 构建基于模块的预设模板

基于拖拽式模块系统，构建几个预设模板：

**模板1：手工电弧焊（SMAW）标准模板**
- 表头数据模块
- 概要模块
- 示意图模块
- 焊层模块（可重复）
- 附加信息模块

**模板2：MAG焊（GMAW）标准模板**
- 表头数据模块
- 概要模块
- 示意图模块
- 焊层模块（可重复）
- 附加信息模块

**模板3：TIG焊（GTAW）标准模板**
- 表头数据模块
- 概要模块
- 示意图模块
- 焊层模块（可重复）
- 附加信息模块

---

## 📋 执行步骤

### 第一阶段：扩展模块库
1. 创建表头数据模块
2. 创建概要模块
3. 创建示意图模块
4. 创建焊层模块
5. 创建附加信息模块

### 第二阶段：创建预设模板
1. 基于模块组合创建 SMAW 模板
2. 基于模块组合创建 GMAW 模板
3. 基于模块组合创建 GTAW 模板

### 第三阶段：删除标准模板系统
1. 删除数据库中的系统模板数据
2. 删除相关迁移脚本
3. 删除相关代码文件
4. 更新 API 和服务

### 第四阶段：测试和验证
1. 测试模块化模板创建
2. 测试 WPS 创建流程
3. 测试数据保存和查询

---

## 📝 需要确认的事项

1. ✓ 是否同意删除所有系统模板？
2. ✓ 是否同意完全迁移到模块化系统？
3. ✓ 新的预设模块是否满足需求？
4. ✓ 是否需要保留任何标准模板的功能？

