# PQR与pPQR模块快速参考

## 📌 文档导航

**主设计文档**: `PQR_PPQR_MODULE_DESIGN_DOCUMENT.md` (1886行，完整设计)

本文档提供快速参考和关键要点总结。

---

## 🎯 核心概念

### 三个模块的关系

```
pPQR (预备评定)  →  PQR (正式评定)  →  WPS (工艺规程)
   试验探索          完整测试           生产指导
```

### 模块定位

| 模块 | 全称 | 用途 | 开发优先级 |
|------|------|------|-----------|
| **WPS** | Welding Procedure Specification | 焊接工艺规程，指导生产 | ✅ 已完成 |
| **PQR** | Procedure Qualification Record | 工艺评定记录，验证WPS | 🔴 第一阶段 |
| **pPQR** | Preliminary PQR | 预备评定，工艺探索 | 🟡 第二阶段 |

---

## 📊 功能对比

### WPS vs PQR vs pPQR

| 特性 | WPS | PQR | pPQR |
|------|-----|-----|------|
| **目的** | 生产指导文件 | 工艺验证记录 | 工艺探索试验 |
| **数据来源** | 基于PQR制定 | 实际试验数据 | 试验探索数据 |
| **测试要求** | 无需测试 | 完整力学测试+NDT | 简易测试 |
| **会员要求** | 所有会员 | 所有会员 | 专业版及以上 |
| **免费版配额** | 10个 | 10个 | 0个（不可用） |
| **模块化模板** | ✅ 支持 | ✅ 支持 | ✅ 支持 |

---

## 🏗️ 架构设计

### 模块化模板系统（三层架构）

```
第一层：预设模块库
  ├── WPS专用模块（15+个）
  ├── PQR专用模块（10+个）
  └── pPQR专用模块（8+个）

第二层：用户自定义模块
  ├── 个人私有模块
  ├── 企业共享模块
  └── 公开模块

第三层：模板（模块组合）
  ├── 系统模板
  └── 用户自定义模板
```

### 数据隔离机制

```sql
-- 所有模块共享的数据隔离字段
user_id          -- 创建用户
workspace_type   -- personal/enterprise
company_id       -- 企业ID
factory_id       -- 工厂ID
```

---

## 💾 数据模型

### PQR核心字段

```sql
-- 基本信息
pqr_number, title, test_date, status, standard

-- 焊接参数（实际测量值）
welding_process, base_material_*, filler_material_*
current_*, voltage_*, heat_input_*
preheat_temp_*, interpass_temp_*

-- 测试结果（JSONB）
tensile_test_results      -- 拉伸试验
bend_test_results         -- 弯曲试验
impact_test_results       -- 冲击试验
hardness_test_results     -- 硬度试验
ndt_results              -- 无损检测

-- 合格判定
qualification_result, qualification_date, qualified_by
```

### pPQR核心字段

```sql
-- 基本信息
ppqr_number, title, test_date, status, purpose, test_plan

-- 参数（JSONB）
planned_parameters        -- 计划参数
actual_parameters        -- 实际参数
parameter_adjustments    -- 参数调整记录

-- 试验结果（JSONB）
visual_inspection        -- 外观检查
dimension_measurements   -- 尺寸测量
simple_tests            -- 简易测试
defects_found           -- 缺陷记录

-- 评价
is_successful, evaluation_notes, improvement_suggestions

-- 转换信息
converted_to_pqr_id, converted_at, converted_by
```

---

## 🔑 关键功能

### PQR关键功能

1. **基础管理**: 创建、编辑、删除、查看、搜索
2. **焊接参数记录**: 实际电流、电压、温度、速度
3. **力学性能测试**: 拉伸、弯曲、冲击、硬度（高级版）
4. **无损检测**: RT、UT、MT、PT（高级版）
5. **合格判定**: 自动判定、不合格处理
6. **关联管理**: 关联WPS、焊工、设备
7. **导出功能**: PDF、Excel（专业版）

### pPQR关键功能

1. **基础管理**: 创建、编辑、删除、查看、搜索
2. **试验方案**: 目的、方案、步骤
3. **参数记录**: 计划参数、实际参数、调整记录
4. **试验结果**: 外观、尺寸、简易测试
5. **参数对比**: 多组试验对比分析（高级版）
6. **转换为PQR**: 成功试验转为正式PQR（高级版）
7. **协作功能**: 团队共享、评论（企业版）

---

## 👥 会员权限

### PQR权限矩阵

| 会员等级 | 数量限制 | 基础功能 | 测试管理 | 导出 | 高级特性 |
|---------|---------|---------|---------|------|---------|
| 游客 | 0（示例） | 只读 | ❌ | ❌ | ❌ |
| 免费版 | 10 | ✅ | ❌ | ❌ | ❌ |
| 专业版 | 30 | ✅ | ❌ | ✅ | ❌ |
| 高级版 | 50 | ✅ | ✅ | ✅ | ✅ |
| 旗舰版 | 100 | ✅ | ✅ | ✅ | ✅ |
| 企业版 | 200+ | ✅ | ✅ | ✅ | ✅ |

### pPQR权限矩阵

| 会员等级 | 数量限制 | 基础功能 | 参数对比 | 转换PQR | 协作 |
|---------|---------|---------|---------|---------|------|
| 游客 | 0 | ❌ | ❌ | ❌ | ❌ |
| 免费版 | 0 | ❌ | ❌ | ❌ | ❌ |
| 专业版 | 30 | ✅ | ❌ | ❌ | ❌ |
| 高级版 | 50 | ✅ | ✅ | ✅ | ❌ |
| 旗舰版 | 100 | ✅ | ✅ | ✅ | ❌ |
| 企业版 | 200+ | ✅ | ✅ | ✅ | ✅ |

---

## 🚀 实施计划

### 阶段一：PQR模块（2-3周）

**后端**:
- ✅ 数据模型（已有基础）
- ⬜ 模块化模板系统
- ⬜ 业务逻辑服务
- ⬜ API端点
- ⬜ 测试

**前端**:
- ⬜ 列表页面
- ⬜ 创建/编辑页面（模块化表单）
- ⬜ 详情页面
- ⬜ 测试结果管理
- ⬜ 合格判定界面

### 阶段二：pPQR模块（2-3周）

**后端**:
- ⬜ 数据模型
- ⬜ 模块化模板系统
- ⬜ 业务逻辑服务
- ⬜ 转换为PQR功能
- ⬜ 参数对比功能

**前端**:
- ⬜ 列表页面
- ⬜ 创建/编辑页面
- ⬜ 详情页面
- ⬜ 参数对比组件
- ⬜ 转换为PQR组件

### 阶段三：集成优化（1周）

- ⬜ PQR与WPS关联
- ⬜ pPQR与PQR关联
- ⬜ 性能优化
- ⬜ 文档完善

---

## 📝 API端点设计

### PQR API

```
GET    /api/v1/pqr                    # 获取列表
POST   /api/v1/pqr                    # 创建
GET    /api/v1/pqr/{id}               # 获取详情
PUT    /api/v1/pqr/{id}               # 更新
DELETE /api/v1/pqr/{id}               # 删除
POST   /api/v1/pqr/{id}/test-results  # 添加测试结果
POST   /api/v1/pqr/{id}/qualify       # 合格判定
GET    /api/v1/pqr/{id}/export/pdf    # 导出PDF
POST   /api/v1/pqr/{id}/link-wps      # 关联WPS
POST   /api/v1/pqr/search             # 高级搜索
```

### pPQR API

```
GET    /api/v1/ppqr                   # 获取列表
POST   /api/v1/ppqr                   # 创建
GET    /api/v1/ppqr/{id}              # 获取详情
PUT    /api/v1/ppqr/{id}              # 更新
DELETE /api/v1/ppqr/{id}              # 删除
PUT    /api/v1/ppqr/{id}/results      # 更新试验结果
POST   /api/v1/ppqr/{id}/convert-to-pqr  # 转换为PQR
POST   /api/v1/ppqr/compare           # 参数对比
POST   /api/v1/ppqr/{id}/share        # 共享（企业版）
POST   /api/v1/ppqr/{id}/comments     # 添加评论（企业版）
```

---

## 🎨 前端页面结构

### PQR页面

```
/pqr
  ├── /list          - PQR列表页
  ├── /create        - 创建PQR页（模块化表单）
  ├── /edit/:id      - 编辑PQR页
  ├── /detail/:id    - PQR详情页
  └── /templates     - PQR模板管理页
```

### pPQR页面

```
/ppqr
  ├── /list          - pPQR列表页
  ├── /create        - 创建pPQR页（模块化表单）
  ├── /edit/:id      - 编辑pPQR页
  ├── /detail/:id    - pPQR详情页
  ├── /compare       - 参数对比页（高级版）
  └── /templates     - pPQR模板管理页
```

---

## 💡 关键技术决策

### 1. 采用模块化模板 ✅

**理由**: 与WPS保持一致，灵活适应不同标准

### 2. 固定字段 + JSONB混合 ✅

**理由**: 平衡查询性能和灵活性

### 3. pPQR需要专业版 ✅

**理由**: 作为付费增值服务，鼓励升级

### 4. 转换功能需要高级版 ✅

**理由**: 高价值特性，避免滥用

---

## 📚 相关文档

- **主设计文档**: `PQR_PPQR_MODULE_DESIGN_DOCUMENT.md`
- **WPS开发指南**: `WPS_MANAGEMENT_DEVELOPMENT_GUIDE.md`
- **PQR开发指南**: `PQR_MANAGEMENT_DEVELOPMENT_GUIDE.md`
- **pPQR开发指南**: `PPQR_MANAGEMENT_DEVELOPMENT_GUIDE.md`
- **模块化系统**: `../md/MODULE_BASED_TEMPLATE_SYSTEM.md`
- **数据隔离**: `DATA_ISOLATION_IMPLEMENTATION_GUIDE.md`

---

## ✅ 下一步行动

1. **评审设计文档** - 团队评审和确认
2. **创建数据库迁移脚本** - PQR和pPQR表
3. **实现PQR后端** - 模型、服务、API
4. **实现PQR前端** - 页面和组件
5. **测试PQR模块** - 单元测试、集成测试
6. **实现pPQR模块** - 重复上述步骤
7. **集成和优化** - 关联功能、性能优化

---

**文档版本**: 1.0  
**最后更新**: 2025-10-25  
**状态**: 设计完成

