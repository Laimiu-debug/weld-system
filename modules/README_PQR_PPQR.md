# PQR与pPQR模块文档导航

## 📚 文档概览

本目录包含PQR（焊接工艺评定记录）和pPQR（预备工艺评定记录）模块的完整设计文档。

---

## 🗂️ 文档列表

### 1. 主设计文档（必读）

**文件**: `PQR_PPQR_MODULE_DESIGN_DOCUMENT.md` (1886行)

**内容**:
- ✅ WPS模块功能总结（第一部分）
- ✅ 自定义模块模板架构详解（第二部分）
- ✅ PQR模块完整设计（第三部分）
- ✅ pPQR模块完整设计（第四部分）
- ✅ 实施计划与路线图（第五部分）
- ✅ 总结与建议（第六部分）

**适合人群**: 架构师、技术负责人、全栈开发者

**阅读时间**: 约60分钟

---

### 2. 快速参考文档（推荐）

**文件**: `PQR_PPQR_QUICK_REFERENCE.md` (300行)

**内容**:
- 核心概念和模块关系
- 功能对比表
- 架构设计概览
- 数据模型要点
- 会员权限矩阵
- API端点列表
- 实施计划概要

**适合人群**: 所有团队成员、产品经理、项目经理

**阅读时间**: 约15分钟

---

### 3. 原始开发指南

#### PQR开发指南
**文件**: `PQR_MANAGEMENT_DEVELOPMENT_GUIDE.md` (478行)

**内容**:
- PQR模块概述
- 会员权限详细说明
- 功能清单
- 数据模型（SQL）
- API接口示例
- 业务逻辑代码示例
- 前端界面设计

**适合人群**: 后端开发者、前端开发者

---

#### pPQR开发指南
**文件**: `PPQR_MANAGEMENT_DEVELOPMENT_GUIDE.md` (507行)

**内容**:
- pPQR模块概述
- 会员权限详细说明
- 功能清单
- 数据模型（SQL）
- API接口示例
- 业务逻辑代码示例
- 前端界面设计

**适合人群**: 后端开发者、前端开发者

---

## 🎯 阅读建议

### 对于项目经理/产品经理

1. **先读**: `PQR_PPQR_QUICK_REFERENCE.md`
   - 了解核心概念和功能对比
   - 理解会员权限设计
   - 查看实施计划

2. **再读**: `PQR_PPQR_MODULE_DESIGN_DOCUMENT.md` 的第一、五、六部分
   - 了解WPS现状
   - 理解实施计划
   - 查看风险和建议

### 对于架构师/技术负责人

1. **先读**: `PQR_PPQR_MODULE_DESIGN_DOCUMENT.md` 完整文档
   - 全面理解设计思路
   - 评估技术方案
   - 确认架构决策

2. **参考**: `PQR_MANAGEMENT_DEVELOPMENT_GUIDE.md` 和 `PPQR_MANAGEMENT_DEVELOPMENT_GUIDE.md`
   - 查看具体实现细节
   - 确认API设计
   - 验证数据模型

### 对于后端开发者

1. **先读**: `PQR_PPQR_QUICK_REFERENCE.md`
   - 快速了解整体架构
   - 理解数据模型
   - 查看API端点

2. **再读**: `PQR_PPQR_MODULE_DESIGN_DOCUMENT.md` 的第二、三、四部分
   - 深入理解模块化模板系统
   - 学习业务逻辑设计
   - 查看代码示例

3. **参考**: `PQR_MANAGEMENT_DEVELOPMENT_GUIDE.md` 或 `PPQR_MANAGEMENT_DEVELOPMENT_GUIDE.md`
   - 查看详细的SQL定义
   - 参考业务逻辑代码
   - 了解权限控制

### 对于前端开发者

1. **先读**: `PQR_PPQR_QUICK_REFERENCE.md`
   - 了解页面结构
   - 查看API端点
   - 理解会员权限

2. **再读**: `PQR_PPQR_MODULE_DESIGN_DOCUMENT.md` 的第二、三、四部分
   - 理解模块化模板系统
   - 查看前端组件设计
   - 了解用户体验流程

3. **参考**: `PQR_MANAGEMENT_DEVELOPMENT_GUIDE.md` 或 `PPQR_MANAGEMENT_DEVELOPMENT_GUIDE.md`
   - 查看前端界面设计
   - 参考组件代码示例

---

## 🔗 相关文档链接

### WPS模块文档
- `WPS_MANAGEMENT_DEVELOPMENT_GUIDE.md` - WPS开发指南
- `../md/MODULE_BASED_TEMPLATE_SYSTEM.md` - 模块化模板系统设计
- `../md/MODULAR_TEMPLATE_IMPLEMENTATION_SUMMARY.md` - 模块化实现总结

### 系统架构文档
- `DATA_ISOLATION_IMPLEMENTATION_GUIDE.md` - 数据隔离实现指南
- `MODULE_OVERVIEW_AND_DEPENDENCIES.md` - 模块概览和依赖关系

### 前端相关
- `../frontend/src/types/wpsModules.ts` - 模块类型定义
- `../frontend/src/constants/wpsModules.ts` - 预设模块库

### 后端相关
- `../backend/app/models/custom_module.py` - 自定义模块模型
- `../backend/app/services/custom_module_service.py` - 模块服务
- `../backend/app/models/pqr.py` - PQR模型（已有）
- `../backend/app/services/pqr_service.py` - PQR服务（已有）

---

## 📊 文档结构图

```
PQR与pPQR模块文档
│
├── README_PQR_PPQR.md (本文档)
│   └── 文档导航和阅读指南
│
├── PQR_PPQR_QUICK_REFERENCE.md
│   └── 快速参考（15分钟阅读）
│
├── PQR_PPQR_MODULE_DESIGN_DOCUMENT.md (主文档)
│   ├── 第一部分：WPS模块功能总结
│   ├── 第二部分：自定义模块模板架构
│   ├── 第三部分：PQR模块设计
│   ├── 第四部分：pPQR模块设计
│   ├── 第五部分：实施计划与路线图
│   └── 第六部分：总结与建议
│
├── PQR_MANAGEMENT_DEVELOPMENT_GUIDE.md
│   └── PQR详细开发指南
│
└── PPQR_MANAGEMENT_DEVELOPMENT_GUIDE.md
    └── pPQR详细开发指南
```

---

## 🎨 设计亮点

### 1. 模块化架构
- ✅ 完全复用WPS的模块化模板系统
- ✅ 三层架构：预设模块 → 自定义模块 → 模板
- ✅ 统一的用户体验

### 2. 数据隔离
- ✅ 继承WPS的工作区隔离机制
- ✅ 支持个人/企业/工厂级隔离
- ✅ 完善的权限控制

### 3. 会员体系
- ✅ 合理的功能分级
- ✅ PQR对所有会员开放（免费版10个）
- ✅ pPQR仅对专业版及以上开放

### 4. 业务流程
- ✅ pPQR → PQR → WPS 完整链路
- ✅ 数据自动迁移
- ✅ 关联关系清晰

---

## 🚀 快速开始

### 第一步：了解现状
阅读 `PQR_PPQR_QUICK_REFERENCE.md` 的"核心概念"部分

### 第二步：理解架构
阅读 `PQR_PPQR_MODULE_DESIGN_DOCUMENT.md` 的第二部分（模块化模板架构）

### 第三步：查看设计
- 后端开发者：阅读第三、四部分的数据模型和业务逻辑
- 前端开发者：阅读第三、四部分的前端设计

### 第四步：开始开发
参考 `PQR_MANAGEMENT_DEVELOPMENT_GUIDE.md` 或 `PPQR_MANAGEMENT_DEVELOPMENT_GUIDE.md`

---

## ❓ 常见问题

### Q1: PQR和pPQR有什么区别？
**A**: 
- **pPQR**是预备试验，用于工艺探索和参数优化，测试要求简单
- **PQR**是正式评定，需要完整的力学测试和无损检测，用于支持WPS

### Q2: 为什么pPQR需要专业版？
**A**: 
- pPQR是高级功能，用于工艺研发
- 作为付费增值服务，鼓励用户升级
- 免费版用户可以直接使用PQR

### Q3: 是否采用模块化模板？
**A**: 
- ✅ 是的，PQR和pPQR都采用模块化模板
- 与WPS保持一致的用户体验
- 灵活适应不同标准和企业需求

### Q4: 如何从pPQR转换为PQR？
**A**: 
- 需要高级版及以上会员
- 在pPQR详情页点击"转换为PQR"
- 补充PQR所需的额外测试信息
- 系统自动迁移数据并保持关联

### Q5: 开发顺序是什么？
**A**: 
1. 第一阶段：PQR模块（2-3周）
2. 第二阶段：pPQR模块（2-3周）
3. 第三阶段：集成优化（1周）

---

## 📞 联系方式

如有疑问，请联系：
- **架构团队**: 技术架构和设计问题
- **产品团队**: 功能需求和用户体验
- **开发团队**: 实现细节和技术问题

---

## 📝 更新日志

### 2025-10-25
- ✅ 创建主设计文档（1886行）
- ✅ 创建快速参考文档（300行）
- ✅ 创建文档导航（本文档）
- ✅ 基于WPS模块经验完成完整设计
- ✅ 确定模块化模板架构
- ✅ 明确会员权限策略
- ✅ 制定实施计划

---

**文档版本**: 1.0  
**最后更新**: 2025-10-25  
**状态**: 设计完成，待评审  
**下一步**: 团队评审 → 开始PQR模块开发

