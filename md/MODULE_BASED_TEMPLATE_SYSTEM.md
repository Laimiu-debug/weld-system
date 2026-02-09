# 模块化拖拽模板系统设计与实现

## 🎯 核心理念

采用"模块化拖拽"的设计方案，让用户通过拖拽预设的字段模块来快速创建自定义WPS模板，同时支持用户创建自己的字段模块。

## 📋 系统架构

### 1. 三层模块体系

```
┌─────────────────────────────────────────┐
│          预设模块库（系统提供）            │
│  - 基本信息模块                           │
│  - 填充金属模块                           │
│  - 保护气体模块                           │
│  - 电流电压模块                           │
│  - 焊接速度模块                           │
│  - 抖动参数模块                           │
│  - 设备信息模块                           │
│  - 热输入模块                             │
│  - ... 等15+个预设模块                    │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│        用户自定义模块（用户创建）          │
│  - 用户可以创建自己的字段模块              │
│  - 定义字段名称、类型、单位等              │
│  - 可以设置模块是否可重复                  │
│  - 支持企业内共享                         │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│          模板（模块组合）                  │
│  - 用户通过拖拽选择需要的模块              │
│  - 可以调整模块顺序                       │
│  - 可以复制模块（用于多层多道焊）          │
│  - 保存为自定义模板                       │
└─────────────────────────────────────────┘
```

### 2. 数据结构

#### 字段模块 (FieldModule)
```typescript
interface FieldModule {
  id: string                    // 模块ID
  name: string                  // 模块名称
  description: string           // 模块描述
  icon: string                  // 图标
  category: string              // 分类（basic/material/gas/electrical/motion/equipment/calculation）
  repeatable: boolean           // 是否可重复（用于多层多道焊）
  fields: Record<string, FieldDefinition>  // 字段定义
}
```

#### 字段定义 (FieldDefinition)
```typescript
interface FieldDefinition {
  label: string                 // 字段标签
  type: string                  // 字段类型（text/number/select/date/textarea/file）
  unit?: string                 // 单位
  options?: string[]            // 选项（用于select类型）
  default?: any                 // 默认值
  required?: boolean            // 是否必填
  readonly?: boolean            // 是否只读
  placeholder?: string          // 占位符
  min?: number                  // 最小值
  max?: number                  // 最大值
  multiple?: boolean            // 是否多选
}
```

#### 模块实例 (ModuleInstance)
```typescript
interface ModuleInstance {
  instanceId: string            // 实例唯一ID
  moduleId: string              // 模块定义ID
  order: number                 // 排序
  customName?: string           // 自定义名称（如"第1层"、"第2层"）
}
```

## ✅ 已完成的工作

### 后端实现

1. **数据库设计** ✅
   - 创建 `custom_modules` 表
   - 支持用户自定义模块
   - 支持数据隔离（个人/企业/系统）
   - 支持访问控制（private/shared/public）

2. **数据模型** ✅
   - `CustomModule` 模型
   - 完整的字段定义（JSONB存储）
   - 时间戳和统计信息

3. **Pydantic Schemas** ✅
   - `CustomModuleCreate` - 创建模块
   - `CustomModuleUpdate` - 更新模块
   - `CustomModuleResponse` - 完整响应
   - `CustomModuleSummary` - 列表摘要

4. **业务逻辑服务** ✅
   - `CustomModuleService`
   - 获取可用模块（系统+用户+企业）
   - CRUD操作
   - 权限检查
   - 使用次数统计

5. **API端点** ✅
   - `GET /api/v1/custom-modules/` - 获取模块列表
   - `GET /api/v1/custom-modules/{id}` - 获取模块详情
   - `POST /api/v1/custom-modules/` - 创建模块
   - `PUT /api/v1/custom-modules/{id}` - 更新模块
   - `DELETE /api/v1/custom-modules/{id}` - 删除模块
   - `POST /api/v1/custom-modules/{id}/increment-usage` - 增加使用次数

### 前端实现

1. **类型定义** ✅
   - `frontend/src/types/wpsModules.ts`
   - 完整的TypeScript类型定义

2. **预设模块库** ✅
   - `frontend/src/constants/wpsModules.ts`
   - 15+个预设模块
   - 涵盖所有常用焊接参数
   - 按分类组织

3. **API服务** ✅
   - `frontend/src/services/customModules.ts`
   - 完整的CRUD操作封装

## 📝 预设模块列表

### 基本信息类 (basic)
1. **基本信息模块** - 焊接工艺、道次、焊道ID等
2. **预热参数模块** (示例) - 预热温度、层间温度等

### 材料信息类 (material)
3. **填充金属模块** - 型号、直径、制造商、商标名
4. **电极处理模块** - 烘干温度、烘干时间
5. **钨电极模块** - 型号、直径、制造商（用于TIG焊）

### 气体信息类 (gas)
6. **保护气体模块** - 名称、流量、预送气时间、延迟送气时间
7. **背部保护气模块** - 背部保护气参数
8. **等离子气模块** - 等离子气参数（用于等离子焊）

### 电气参数类 (electrical)
9. **电流电压模块** - 电流类型、电流、电压
10. **电流脉冲模块** - 脉冲参数（用于TIG焊等）

### 运动参数类 (motion)
11. **焊接速度模块** - 焊接速度、倾斜角度
12. **送丝速度模块** - 送丝速度、材料过渡、焊嘴间距
13. **抖动参数模块** - 抖动宽度、频率、停留时间

### 设备信息类 (equipment)
14. **喷嘴参数模块** - 喷嘴尺寸
15. **焊接设备模块** - 制造商、名称

### 计算结果类 (calculation)
16. **热输入模块** - 系统计算值、用户输入值

## 🚀 下一步工作

### 1. 前端拖拽界面 (进行中)

需要创建以下组件：

#### ModuleLibrary (模块库)
- 显示所有可用模块
- 按分类分组
- 支持搜索和过滤
- 可拖拽到画布

#### TemplateCanvas (模板画布)
- 接收拖拽的模块
- 显示已选择的模块列表
- 支持模块排序
- 支持模块复制
- 支持模块删除

#### ModuleCard (模块卡片)
- 显示模块信息
- 显示字段数量
- 可拖拽
- 可复制

#### TemplatePreview (模板预览)
- 实时预览生成的表单
- 显示所有字段
- 按模块分组显示

### 2. 自定义模块创建器

#### CustomModuleCreator
- 可视化字段编辑器
- 添加/删除字段
- 设置字段类型和属性
- 预览模块效果

### 3. 集成到模板管理

- 在模板管理页面添加"使用模块创建"按钮
- 打开拖拽创建器
- 保存模板时记录模块列表
- 编辑模板时加载模块配置

## 💡 核心优势

### 1. 降低学习成本
- ✅ 用户不需要理解复杂的字段定义
- ✅ 通过拖拽即可创建模板
- ✅ 预设模块保证规范性

### 2. 提高创建效率
- ✅ 快速组合模块
- ✅ 一键复制模块（多层多道焊）
- ✅ 模板可重用

### 3. 灵活性强
- ✅ 支持自定义模块
- ✅ 支持模块组合
- ✅ 支持企业共享

### 4. 可扩展性好
- ✅ 轻松添加新模块
- ✅ 模块化设计
- ✅ 易于维护

## 🎨 用户体验流程

### 创建模板流程

```
1. 用户点击"创建模板"
   ↓
2. 选择创建方式：
   - 使用模块创建（推荐）
   - 从零开始创建
   ↓
3. 进入拖拽创建器
   ↓
4. 从左侧模块库拖拽模块到右侧画布
   ↓
5. 调整模块顺序
   ↓
6. 复制模块（如需要多层多道焊）
   ↓
7. 预览生成的表单
   ↓
8. 填写模板基本信息（名称、描述等）
   ↓
9. 保存模板
```

### 创建自定义模块流程

```
1. 用户点击"创建自定义模块"
   ↓
2. 填写模块基本信息
   - 模块名称
   - 模块描述
   - 模块分类
   - 是否可重复
   ↓
3. 添加字段
   - 字段名称
   - 字段类型
   - 单位
   - 是否必填
   - 其他属性
   ↓
4. 预览模块效果
   ↓
5. 保存模块
   ↓
6. 模块出现在模块库中，可用于创建模板
```

## 📊 技术实现细节

### 拖拽库选择
- **@dnd-kit/core** - 核心拖拽功能
- **@dnd-kit/sortable** - 可排序列表
- **@dnd-kit/utilities** - 工具函数

### 状态管理
- 使用React Hooks (useState, useReducer)
- 模块列表状态
- 画布状态
- 拖拽状态

### 数据持久化
- 后端存储模块定义
- 模板存储模块实例列表
- 渲染时根据模块ID加载定义

## 🔄 与现有系统的集成

### WPS创建流程
1. 用户选择模板
2. 系统加载模板的模块列表
3. 根据模块定义动态渲染表单
4. 用户填写数据
5. 数据按模块结构保存到JSONB字段

### 数据存储
```json
{
  "template_id": "custom_user_123_abc",
  "modules": [
    {
      "instanceId": "inst_1",
      "moduleId": "basic_info",
      "order": 1,
      "customName": "第1层"
    },
    {
      "instanceId": "inst_2",
      "moduleId": "filler_metal",
      "order": 2
    },
    {
      "instanceId": "inst_3",
      "moduleId": "current_voltage",
      "order": 3
    }
  ]
}
```

## 📝 待办事项

- [ ] 安装拖拽库 (@dnd-kit)
- [ ] 创建ModuleLibrary组件
- [ ] 创建TemplateCanvas组件
- [ ] 创建ModuleCard组件
- [ ] 创建TemplatePreview组件
- [ ] 创建CustomModuleCreator组件
- [ ] 集成到模板管理页面
- [ ] 测试拖拽功能
- [ ] 测试模块复制功能
- [ ] 测试模板保存和加载

---

**更新时间**: 2025-10-22  
**状态**: 后端完成，前端进行中

