# 模块总览与依赖关系

## 📋 文档概述

本文档提供了焊接工艺管理系统所有功能模块的总览，包括模块清单、会员权限矩阵、模块依赖关系和开发优先级。

**文档版本**: 1.0  
**最后更新**: 2025-10-16  
**状态**: ✅ 完成

---

## 🎯 模块清单

### 用户门户模块 (11个)

| 序号 | 模块名称 | 英文名称 | 文档路径 | 开发状态 |
|-----|---------|---------|---------|---------|
| 1 | 仪表盘 | Dashboard | `DASHBOARD_DEVELOPMENT_GUIDE.md` | ✅ 已实现 |
| 2 | WPS管理 | WPS Management | `WPS_MANAGEMENT_DEVELOPMENT_GUIDE.md` | ✅ 已实现 |
| 3 | PQR管理 | PQR Management | `PQR_MANAGEMENT_DEVELOPMENT_GUIDE.md` | ✅ 已实现 |
| 4 | pPQR管理 | pPQR Management | `PPQR_MANAGEMENT_DEVELOPMENT_GUIDE.md` | ✅ 已实现 |
| 5 | 焊工管理 | Welder Management | `WELDER_MANAGEMENT_DEVELOPMENT_GUIDE.md` | ✅ 已实现 |
| 6 | 焊材管理 | Material Management | `MATERIAL_MANAGEMENT_DEVELOPMENT_GUIDE.md` | ✅ 已实现 |
| 7 | 设备管理 | Equipment Management | `EQUIPMENT_MANAGEMENT_DEVELOPMENT_GUIDE.md` | ✅ 已实现 |
| 8 | 生产管理 | Production Management | `PRODUCTION_MANAGEMENT_DEVELOPMENT_GUIDE.md` | ✅ 已实现 |
| 9 | 质量管理 | Quality Management | `QUALITY_MANAGEMENT_DEVELOPMENT_GUIDE.md` | ✅ 已实现 |
| 10 | 报表统计 | Reports & Statistics | `REPORTS_STATISTICS_DEVELOPMENT_GUIDE.md` | ⏳ 待开发 |
| 11 | 企业员工管理 | Enterprise Employee Management | `ENTERPRISE_EMPLOYEE_MANAGEMENT_DEVELOPMENT_GUIDE.md` | ⏳ 待开发 |
| 12 | 个人中心 | Personal Center | `PERSONAL_CENTER_DEVELOPMENT_GUIDE.md` | ⏳ 待开发 |

### 管理员门户模块 (1个)

| 序号 | 模块名称 | 英文名称 | 文档路径 | 开发状态 |
|-----|---------|---------|---------|---------|
| 13 | 管理员门户 | Admin Portal | `ADMIN_PORTAL_DEVELOPMENT_GUIDE.md` | ⏳ 待开发 |

**总计**: 13个功能模块

---

## 🎯 会员权限矩阵

### 个人会员

| 模块 | 游客 | 免费版 | 专业版 | 高级版 | 旗舰版 |
|-----|-----|-------|-------|-------|-------|
| **仪表盘** | ✅ 只读 | ✅ | ✅ | ✅ | ✅ |
| **WPS管理** | ✅ 只读 | ✅ 10个 | ✅ 30个 | ✅ 50个 | ✅ 100个 |
| **PQR管理** | ✅ 只读 | ✅ 10个 | ✅ 30个 | ✅ 50个 | ✅ 100个 |
| **pPQR管理** | ❌ | ❌ | ✅ 30个 | ✅ 50个 | ✅ 100个 |
| **焊工管理** | ❌ | ❌ | ✅ 基础 | ✅ 完整 | ✅ 完整 |
| **焊材管理** | ❌ | ❌ | ✅ 基础 | ✅ 完整 | ✅ 完整 |
| **设备管理** | ❌ | ❌ | ❌ | ✅ 完整 | ✅ 完整 |
| **生产管理** | ❌ | ❌ | ❌ | ✅ 完整 | ✅ 完整 |
| **质量管理** | ❌ | ❌ | ❌ | ✅ 完整 | ✅ 完整 |
| **报表统计** | ❌ | ❌ | ❌ | ✅ 基础 | ✅ 自定义 |
| **企业员工管理** | ❌ | ❌ | ❌ | ❌ | ❌ |
| **个人中心** | ✅ 基础 | ✅ | ✅ | ✅ | ✅ |

### 企业会员

| 模块 | 企业版 | 企业PRO | 企业PRO MAX |
|-----|-------|---------|-------------|
| **仪表盘** | ✅ | ✅ | ✅ |
| **WPS管理** | ✅ 200个 | ✅ 400个 | ✅ 500个 |
| **PQR管理** | ✅ 200个 | ✅ 400个 | ✅ 500个 |
| **pPQR管理** | ✅ 200个 | ✅ 400个 | ✅ 500个 |
| **焊工管理** | ✅ 完整 | ✅ 完整 | ✅ 完整 |
| **焊材管理** | ✅ 完整 | ✅ 完整 | ✅ 完整 |
| **设备管理** | ✅ 完整 | ✅ 完整 | ✅ 完整 |
| **生产管理** | ✅ 完整 | ✅ 完整 | ✅ 完整 |
| **质量管理** | ✅ 完整 | ✅ 完整 | ✅ 完整 |
| **报表统计** | ✅ 企业报表 | ✅ 企业报表 | ✅ 企业报表 |
| **企业员工管理** | ✅ 10员工 | ✅ 20员工 | ✅ 50员工 |
| **个人中心** | ✅ | ✅ | ✅ |

### 管理员

| 模块 | 系统管理员 |
|-----|-----------|
| **管理员门户** | ✅ 完整权限 |

---

## 📊 模块依赖关系

### 核心依赖

```
用户认证系统 (Authentication)
    ├── 会员体系 (Membership System)
    │   ├── 配额管理 (Quota Management)
    │   └── 权限控制 (Permission Control)
    └── 租户隔离 (Tenant Isolation)
        ├── 用户级隔离 (User-level)
        ├── 企业级隔离 (Company-level)
        └── 工厂级隔离 (Factory-level)
```

### 模块间依赖

#### 1. 仪表盘 (Dashboard)
**依赖模块**:
- WPS管理 - 获取 WPS 统计数据
- PQR管理 - 获取 PQR 统计数据
- 焊工管理 - 获取焊工统计数据
- 生产管理 - 获取生产进度数据
- 质量管理 - 获取质量统计数据

**被依赖**: 无

#### 2. WPS管理 (WPS Management)
**依赖模块**:
- 焊工管理 - 关联焊工信息
- 焊材管理 - 关联焊材信息
- 设备管理 - 关联设备信息

**被依赖**:
- PQR管理 - PQR 关联 WPS
- 生产管理 - 生产任务关联 WPS
- 仪表盘 - 显示 WPS 统计

#### 3. PQR管理 (PQR Management)
**依赖模块**:
- WPS管理 - 关联 WPS
- pPQR管理 - 从 pPQR 转换

**被依赖**:
- WPS管理 - WPS 关联 PQR
- 仪表盘 - 显示 PQR 统计

#### 4. pPQR管理 (pPQR Management)
**依赖模块**:
- WPS管理 - 参考 WPS 参数

**被依赖**:
- PQR管理 - 转换为 PQR

#### 5. 焊工管理 (Welder Management)
**依赖模块**: 无

**被依赖**:
- WPS管理 - WPS 关联焊工
- 生产管理 - 生产任务分配焊工
- 质量管理 - 质量检验关联焊工

#### 6. 焊材管理 (Material Management)
**依赖模块**: 无

**被依赖**:
- WPS管理 - WPS 关联焊材
- 生产管理 - 生产任务消耗焊材

#### 7. 设备管理 (Equipment Management)
**依赖模块**: 无

**被依赖**:
- WPS管理 - WPS 关联设备
- 生产管理 - 生产任务使用设备

#### 8. 生产管理 (Production Management)
**依赖模块**:
- WPS管理 - 生产任务关联 WPS
- 焊工管理 - 分配焊工
- 焊材管理 - 消耗焊材
- 设备管理 - 使用设备

**被依赖**:
- 质量管理 - 质量检验关联生产任务
- 仪表盘 - 显示生产进度

#### 9. 质量管理 (Quality Management)
**依赖模块**:
- 生产管理 - 关联生产任务
- 焊工管理 - 关联焊工

**被依赖**:
- 仪表盘 - 显示质量统计

#### 10. 报表统计 (Reports & Statistics)
**依赖模块**:
- 所有业务模块 - 汇总统计数据

**被依赖**: 无

#### 11. 企业员工管理 (Enterprise Employee Management)
**依赖模块**:
- 用户认证系统 - 用户账号管理
- 会员体系 - 员工配额检查

**被依赖**:
- 所有模块 - 员工权限控制

#### 12. 个人中心 (Personal Center)
**依赖模块**:
- 用户认证系统 - 用户信息
- 会员体系 - 会员信息
- 所有业务模块 - 使用统计

**被依赖**: 无

#### 13. 管理员门户 (Admin Portal)
**依赖模块**:
- 所有模块 - 管理和监控

**被依赖**: 无

---

## 🚀 开发优先级

### 第一阶段 - 核心功能（部分完成）
**优先级**: 🔴 最高

1. ✅ **用户认证系统** - 登录、注册、权限
2. ✅ **会员体系** - 会员等级、配额管理
3. ✅ **仪表盘** - 系统概览
4. ✅ **WPS管理** - 核心业务
5. ✅ **PQR管理** - 核心业务
6. ✅ **pPQR管理** - 核心业务
7. ⏳ **个人中心** - 用户管理

### 第二阶段 - 重要功能（部分完成）
**优先级**: 🟡 高

8. ✅ **焊工管理** - 资源管理
9. ✅ **焊材管理** - 资源管理
10. ✅ **设备管理** - 资源管理
11. ⏳ **企业员工管理** - 企业协作（仅企业会员）

### 第三阶段 - 增强功能（部分完成）
**优先级**: 🟢 中

12. ✅ **生产管理** - 生产流程
13. ✅ **质量管理** - 质量控制
14. ⏳ **报表统计** - 数据分析

### 第四阶段 - 管理功能（待开发）
**优先级**: 🔵 低

15. ⏳ **管理员门户** - 系统管理

---

## 📈 开发进度统计

### 总体进度
- **总模块数**: 13个
- **已完成**: 9个 (69%)
- **待开发**: 4个 (31%)

### 按类型统计
- **用户门户**: 12个模块
  - 已完成: 9个
  - 待开发: 3个
- **管理员门户**: 1个模块
  - 已完成: 0个
  - 待开发: 1个

### 按优先级统计
- **第一阶段（核心）**: 7个模块
  - 已完成: 6个 (86%)
  - 待开发: 1个 (14%)
- **第二阶段（重要）**: 4个模块
  - 已完成: 3个 (75%)
  - 待开发: 1个 (25%)
- **第三阶段（增强）**: 3个模块
  - 已完成: 2个 (67%)
  - 待开发: 1个 (33%)
- **第四阶段（管理）**: 1个模块
  - 已完成: 0个 (0%)
  - 待开发: 1个 (100%)

---

## 🗂️ 数据库表依赖

### 核心表
- `users` - 用户表（所有模块依赖）
- `companies` - 企业表（企业功能依赖）
- `factories` - 工厂表（企业功能依赖）

### 业务表
- `wps_records` - WPS 记录
- `pqr_records` - PQR 记录
- `ppqr_records` - pPQR 记录
- `welders` - 焊工信息
- `welder_certifications` - 焊工证书
- `welding_materials` - 焊材信息
- `material_transactions` - 焊材交易
- `equipment` - 设备信息
- `equipment_maintenance` - 设备维护
- `production_tasks` - 生产任务
- `production_records` - 生产记录
- `quality_inspections` - 质量检验
- `nonconformance_records` - 不合格品记录

### 管理表
- `company_employees` - 企业员工关系
- `employee_invitations` - 员工邀请
- `departments` - 部门信息
- `report_templates` - 报表模板
- `user_preferences` - 用户偏好
- `notifications` - 通知记录
- `login_history` - 登录历史
- `admins` - 管理员
- `system_announcements` - 系统公告
- `system_logs` - 系统日志

**总计**: 约 25+ 张表

---

## 🔗 API端点统计

### 已实现的API端点
- **仪表盘**: 3个端点
- **WPS管理**: 9个端点
- **PQR管理**: 7个端点
- **pPQR管理**: 6个端点
- **焊工管理**: 13个端点
- **焊材管理**: 10个端点
- **设备管理**: 10个端点
- **生产管理**: 11个端点
- **质量管理**: 11个端点

**已实现总计**: 约 80个 API端点

### 待开发的API端点
- **报表统计**: 约 10个端点
- **企业员工管理**: 约 15个端点
- **个人中心**: 约 12个端点
- **管理员门户**: 约 30个端点

**待开发总计**: 约 67个 API端点

**系统总计**: 约 147个 API端点

---

## 📝 下一步行动

### 立即行动
1. ✅ 完成所有模块开发文档（已完成）
2. ⏳ 开发个人中心模块
3. ⏳ 开发企业员工管理模块
4. ⏳ 开发报表统计模块

### 后续计划
5. ⏳ 开发管理员门户模块
6. ⏳ 编写单元测试
7. ⏳ 编写集成测试
8. ⏳ 性能优化
9. ⏳ 前端开发
10. ⏳ 部署上线

---

## 📚 相关文档

### 系统设计文档
- `docs/development-docs.md` - 系统开发总文档
- `docs/MEMBERSHIP_SYSTEM_DESIGN.md` - 会员体系设计
- `docs/FEATURE_PERMISSIONS_MATRIX.md` - 功能权限矩阵

### 模块开发文档
所有模块开发文档位于 `docs/modules/` 目录下：
- 仪表盘: `DASHBOARD_DEVELOPMENT_GUIDE.md`
- WPS管理: `WPS_MANAGEMENT_DEVELOPMENT_GUIDE.md`
- PQR管理: `PQR_MANAGEMENT_DEVELOPMENT_GUIDE.md`
- pPQR管理: `PPQR_MANAGEMENT_DEVELOPMENT_GUIDE.md`
- 焊工管理: `WELDER_MANAGEMENT_DEVELOPMENT_GUIDE.md`
- 焊材管理: `MATERIAL_MANAGEMENT_DEVELOPMENT_GUIDE.md`
- 设备管理: `EQUIPMENT_MANAGEMENT_DEVELOPMENT_GUIDE.md`
- 生产管理: `PRODUCTION_MANAGEMENT_DEVELOPMENT_GUIDE.md`
- 质量管理: `QUALITY_MANAGEMENT_DEVELOPMENT_GUIDE.md`
- 报表统计: `REPORTS_STATISTICS_DEVELOPMENT_GUIDE.md`
- 企业员工管理: `ENTERPRISE_EMPLOYEE_MANAGEMENT_DEVELOPMENT_GUIDE.md`
- 个人中心: `PERSONAL_CENTER_DEVELOPMENT_GUIDE.md`
- 管理员门户: `ADMIN_PORTAL_DEVELOPMENT_GUIDE.md`

---

**文档维护**: 请在添加新模块或修改现有模块时及时更新本文档。

**最后更新**: 2025-10-16  
**维护者**: 开发团队

