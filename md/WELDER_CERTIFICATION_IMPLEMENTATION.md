# 焊工多证书管理功能实现文档

## 📋 功能概述

本次实现了焊工多证书管理功能，支持一个焊工持有多个证书，并突出显示**合格项目**和**合格范围**信息，满足焊接工程师在实际工作中分配任务的需求。

---

## 🎯 核心特性

### 1. **多证书管理**
- 每个焊工可以持有多个证书
- 支持不同类型的证书：焊工等级证书、特种焊接技术证书、国际认证、行业认证等
- 可标记主要证书（is_primary）

### 2. **认证体系支持**
支持多种国际和国内认证体系：
- **ASME**（美国机械工程师协会）
- **国标**（中国国家标准）
- **欧标**（欧洲标准）
- **AWS**（美国焊接学会）
- **API**（美国石油学会）
- **DNV**（挪威船级社）
- 其他

### 3. **合格项目管理**
证书包含详细的合格项目信息：
- **合格工艺**：SMAW、GTAW、GMAW、FCAW、SAW 等
- **合格材料组**：碳钢、不锈钢、铝合金、镍基合金、钛合金等
- **合格填充材料**：如 E7018、ER308L 等

### 4. **合格范围管理**
证书包含详细的合格范围信息：
- **合格位置**：1G、2G、3G、4G、5G、6G
- **合格厚度范围**：如 3-12mm
- **合格直径范围**：如 DN50-DN300

### 5. **复审管理**
完整的证书复审生命周期管理：
- 最近复审日期
- 复审次数
- 下次复审日期
- 复审结果（通过/未通过）
- 复审备注

### 6. **证书状态管理**
- 有效（valid）
- 即将过期（expiring_soon）
- 已过期（expired）
- 已暂停（suspended）
- 已吊销（revoked）

### 7. **智能筛选**
支持按以下条件筛选证书：
- 认证体系
- 证书状态
- 搜索关键词（证书编号、类型、工艺、材料等）

### 8. **未来扩展支持**
数据结构设计支持未来的焊工自动匹配功能：
- 根据项目需求自动筛选合适焊工
- 多条件组合查询
- 资格覆盖范围判断

---

## 🏗️ 技术实现

### 一、数据库层

#### 1. 数据库表结构
表名：`welder_certifications`

**主要字段：**
```sql
-- 证书基本信息
certification_number VARCHAR(100)      -- 证书编号
certification_type VARCHAR(100)        -- 证书类型
certification_level VARCHAR(50)        -- 证书等级
certification_standard VARCHAR(100)    -- 认证标准（如 ASME IX）
certification_system VARCHAR(50)       -- 认证体系（如 ASME、国标）
project_name VARCHAR(200)              -- 项目名称

-- 颁发信息
issuing_authority VARCHAR(255)         -- 颁发机构
issuing_country VARCHAR(50)            -- 颁发国家
issue_date DATE                        -- 颁发日期
expiry_date DATE                       -- 过期日期

-- 合格项目
qualified_process VARCHAR(100)         -- 合格工艺
qualified_material_group VARCHAR(100)  -- 合格材料组
qualified_filler_material VARCHAR(100) -- 合格填充材料

-- 合格范围
qualified_thickness_range VARCHAR(100) -- 合格厚度范围
qualified_diameter_range VARCHAR(100)  -- 合格直径范围
qualified_position VARCHAR(100)        -- 合格位置

-- 考试信息
exam_date DATE                         -- 考试日期
exam_location VARCHAR(255)             -- 考试地点
exam_score FLOAT                       -- 考试成绩
practical_test_result VARCHAR(50)      -- 实操测试结果
theory_test_result VARCHAR(50)         -- 理论测试结果

-- 复审信息
renewal_date DATE                      -- 最近复审日期
renewal_count INTEGER                  -- 复审次数
next_renewal_date DATE                 -- 下次复审日期
renewal_result VARCHAR(50)             -- 复审结果
renewal_notes TEXT                     -- 复审备注

-- 状态和附件
status VARCHAR(50)                     -- 状态
is_primary BOOLEAN                     -- 是否主要证书
certificate_file_url VARCHAR(500)      -- 证书文件URL
attachments TEXT                       -- 附件(JSON)
notes TEXT                             -- 备注
```

#### 2. 索引优化
为支持高效查询和未来的焊工自动匹配功能，创建了以下索引：

```sql
-- 单列索引
CREATE INDEX idx_welder_certifications_system ON welder_certifications(certification_system);
CREATE INDEX idx_welder_certifications_process ON welder_certifications(qualified_process);
CREATE INDEX idx_welder_certifications_material ON welder_certifications(qualified_material_group);
CREATE INDEX idx_welder_certifications_position ON welder_certifications(qualified_position);

-- 复合索引（用于焊工自动匹配）
CREATE INDEX idx_welder_certifications_matching 
ON welder_certifications(welder_id, status, qualified_process, qualified_material_group, qualified_position) 
WHERE is_active = true AND status = 'valid';
```

### 二、后端层

#### 1. 数据模型
文件：`backend/app/models/welder.py`

更新了 `WelderCertification` 模型，添加了新字段：
- `certification_system`
- `project_name`
- `renewal_result`
- `renewal_notes`

#### 2. Schema 定义
文件：`backend/app/schemas/welder.py`

创建了完整的 Schema：
- `WelderCertificationBase` - 基础 Schema
- `WelderCertificationCreate` - 创建 Schema
- `WelderCertificationUpdate` - 更新 Schema
- `WelderCertificationResponse` - 响应 Schema

#### 3. 服务层
文件：`backend/app/services/welder_service.py`

实现了完整的 CRUD 方法：
- `get_certifications()` - 获取证书列表
- `add_certification()` - 添加证书
- `update_certification()` - 更新证书
- `delete_certification()` - 删除证书（软删除）

#### 4. API 接口
文件：`backend/app/api/v1/endpoints/welders.py`

提供了 RESTful API：
- `GET /welders/{welder_id}/certifications` - 获取证书列表
- `POST /welders/{welder_id}/certifications` - 创建证书
- `PUT /welders/{welder_id}/certifications/{cert_id}` - 更新证书
- `DELETE /welders/{welder_id}/certifications/{cert_id}` - 删除证书

### 三、前端层

#### 1. 服务层
文件：`frontend/src/services/certifications.ts`

封装了所有证书相关的 API 调用：
- `getList()` - 获取证书列表
- `create()` - 创建证书
- `update()` - 更新证书
- `delete()` - 删除证书
- `uploadAttachment()` - 上传附件（预留）

#### 2. 组件层

**CertificationModal** (`frontend/src/components/Welders/Certifications/CertificationModal.tsx`)
- 证书添加/编辑表单
- 包含所有字段的输入
- 支持日期选择、下拉选择、多选标签等

**CertificationCard** (`frontend/src/components/Welders/Certifications/CertificationCard.tsx`)
- 证书卡片展示组件
- **突出显示合格项目和合格范围**
- 显示证书状态、有效期、复审信息等
- 提供编辑、删除操作

**CertificationList** (`frontend/src/components/Welders/Certifications/CertificationList.tsx`)
- 证书列表管理组件
- 支持按认证体系、状态筛选
- 支持关键词搜索
- 集成添加、编辑、删除功能

#### 3. 页面集成
文件：`frontend/src/pages/Welders/WeldersDetail.tsx`

在焊工详情页添加了"证书管理"标签页，集成了 `CertificationList` 组件。

---

## 📊 界面设计

### 证书卡片展示（重点突出合格项目和范围）

```
┌─────────────────────────────────────────────────────────────┐
│ 📄 特种焊接技术证书  [国标]  [主要证书]          [编辑] [删除] │
├─────────────────────────────────────────────────────────────┤
│ 证书编号：CERT-2024-001                                      │
│ 认证标准：GB/T 3091                                          │
│                                                             │
│ 合格工艺：[SMAW] [GTAW] [GMAW]                              │
│ 合格材料：[碳钢] [不锈钢]                                    │
│ 合格位置：[1G] [2G] [3G] [4G] [5G] [6G]                     │
│ 厚度范围：[3-12mm]    直径范围：[DN50-DN300]                │
│                                                             │
│ 颁发机构：质监局                                             │
│ 颁发日期：2024-01-01                                         │
│ 有效期至：2027-01-01  [即将过期]                            │
│ 状态：✅ 有效                                                │
│                                                             │
│ 最近复审：2025-01-01    复审次数：1 次                       │
│ 下次复审：2026-01-01    [通过]                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 使用指南

### 1. 数据库迁移

已完成数据库迁移，添加了新字段和索引。

迁移脚本：`backend/migrations/add_certification_fields.sql`
执行脚本：`backend/run_certification_migration.py`

### 2. 启动后端服务

```bash
cd backend
python main.py
```

### 3. 启动前端服务

```bash
cd frontend
npm run dev
```

### 4. 访问证书管理

1. 登录系统
2. 进入"焊工管理"模块
3. 点击任意焊工查看详情
4. 切换到"证书管理"标签页
5. 点击"添加证书"按钮添加新证书

---

## 🔍 功能测试

### 测试场景

1. **添加证书**
   - 填写完整的证书信息
   - 选择认证体系和标准
   - 填写合格项目和范围
   - 保存并验证

2. **编辑证书**
   - 点击证书卡片的"编辑"按钮
   - 修改证书信息
   - 保存并验证更新

3. **删除证书**
   - 点击证书卡片的"删除"按钮
   - 确认删除
   - 验证证书已被软删除

4. **筛选证书**
   - 按认证体系筛选
   - 按证书状态筛选
   - 使用关键词搜索

5. **复审管理**
   - 添加复审信息
   - 更新复审结果
   - 查看复审历史

---

## 📈 未来扩展

### 1. 焊工自动匹配功能

基于当前的数据结构，可以实现以下功能：

```typescript
// 示例：根据项目需求自动匹配焊工
interface ProjectRequirement {
  process: string;        // 需要的工艺
  material: string;       // 需要的材料
  position: string;       // 需要的位置
  standard: string;       // 需要的标准
}

async function matchWelders(requirement: ProjectRequirement) {
  // 查询符合条件的证书
  // 返回持有相应证书的焊工列表
}
```

### 2. 证书过期提醒

- 自动检测即将过期的证书
- 发送邮件或系统通知
- 生成复审计划

### 3. 证书统计分析

- 按认证体系统计
- 按合格工艺统计
- 证书有效率分析

### 4. 附件管理

- 上传证书扫描件
- 上传考试成绩单
- 上传复审记录

---

## 📝 注意事项

1. **数据完整性**
   - 证书编号必须唯一
   - 颁发日期和有效期必须合理
   - 合格项目和范围应尽量完整

2. **权限控制**
   - 遵循现有的工作区权限体系
   - 个人工作区只能管理自己的焊工证书
   - 企业工作区根据角色权限管理

3. **性能优化**
   - 已创建索引支持高效查询
   - 复合索引支持焊工自动匹配场景

4. **向后兼容**
   - 保留了焊工表中的主要证书字段
   - 可以将主要证书信息同步到证书表

---

## 🎉 总结

本次实现完成了焊工多证书管理的完整功能，包括：

✅ 数据库表结构设计和迁移
✅ 后端 API 接口实现
✅ 前端组件开发
✅ 焊工详情页集成
✅ 合格项目和范围突出显示
✅ 复审管理功能
✅ 智能筛选功能
✅ 未来扩展支持

该功能满足了焊接工程师在实际工作中的需求，为未来的焊工自动匹配功能奠定了基础。

---

*实现日期：2025-10-20*
*文档版本：v1.0*

