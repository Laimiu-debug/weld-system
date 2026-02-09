# PQR与pPQR模块设计文档

## 📋 文档概述

本文档基于现有WPS模块的实现经验，详细说明PQR（焊接工艺评定记录）和pPQR（预备工艺评定记录）模块的设计与实现方案。

**文档版本**: 1.0  
**创建日期**: 2025-10-25  
**作者**: 系统架构团队

---

## 第一部分：WPS模块功能总结

### 1.1 WPS模块核心功能

WPS（焊接工艺规程）模块是系统的核心模块，提供以下主要功能：

#### 1.1.1 基础管理功能
- ✅ **创建WPS**: 基于模板创建焊接工艺规程
- ✅ **编辑WPS**: 修改WPS数据和参数
- ✅ **删除WPS**: 软删除WPS记录
- ✅ **查看WPS**: 详细信息展示和预览
- ✅ **复制WPS**: 基于现有WPS创建新记录
- ✅ **搜索WPS**: 按编号、工艺、状态等多维度搜索
- ✅ **筛选WPS**: 按工艺类型、标准、日期等筛选

#### 1.1.2 模板系统
- ✅ **系统模板**: 预设的标准WPS模板
- ✅ **自定义模板**: 用户创建的个性化模板
- ✅ **模板管理**: 创建、编辑、删除、共享模板
- ✅ **模板选择**: 根据焊接工艺和标准筛选模板

#### 1.1.3 数据隔离与权限
- ✅ **个人工作区**: 个人WPS数据隔离
- ✅ **企业工作区**: 企业内部数据共享
- ✅ **工厂级隔离**: 支持工厂级别的数据隔离
- ✅ **权限控制**: 基于角色的访问控制（RBAC）

#### 1.1.4 配额管理
- ✅ **会员配额**: 不同会员等级的WPS数量限制
- ✅ **配额检查**: 创建前自动检查配额
- ✅ **配额统计**: 实时显示配额使用情况

#### 1.1.5 版本管理
- ✅ **版本号管理**: 支持版本号（A, B, C等）
- ✅ **版本历史**: 记录修改历史
- ✅ **状态管理**: draft, active, archived等状态

#### 1.1.6 审核流程
- ✅ **审核机制**: 支持审核人审核
- ✅ **批准机制**: 支持批准人批准
- ✅ **审核记录**: 记录审核和批准时间、人员

#### 1.1.7 导出功能
- ✅ **PDF导出**: 生成标准WPS文档
- ✅ **Excel导出**: 导出WPS数据
- ✅ **批量导出**: 批量导出多个WPS

#### 1.1.8 关联管理
- ✅ **关联PQR**: 关联支持的PQR记录
- ✅ **关联焊工**: 关联合格焊工
- ✅ **关联设备**: 关联使用的设备

### 1.2 WPS数据模型特点

#### 1.2.1 核心字段
```sql
-- 数据隔离核心字段
user_id          -- 创建用户ID
workspace_type   -- 工作区类型: personal/enterprise
company_id       -- 企业ID
factory_id       -- 工厂ID

-- 基本信息
title            -- 标题
wps_number       -- WPS编号
revision         -- 版本号
status           -- 状态
template_id      -- 使用的模板ID

-- 焊接工艺参数（50+个固定字段）
welding_process  -- 焊接工艺
base_material_*  -- 母材相关参数
filler_material_* -- 填充材料参数
current_*        -- 电流参数
voltage_*        -- 电压参数
heat_input_*     -- 热输入参数
preheat_temp_*   -- 预热温度参数
...
```

#### 1.2.2 JSONB动态字段
```sql
-- 新架构：完全灵活的模块数据存储
modules_data JSONB  -- 所有模块数据
-- 结构: { "module_instance_id": { "field_key": value, ... }, ... }

-- 旧架构（向后兼容，逐步废弃）
header_info JSONB
summary_info JSONB
diagram_info JSONB
weld_layers JSONB
additional_info JSONB
```

### 1.3 WPS技术栈

#### 后端技术
- **FastAPI**: Web框架
- **SQLAlchemy**: ORM
- **PostgreSQL**: 数据库（JSONB支持）
- **Pydantic**: 数据验证

#### 前端技术
- **React**: UI框架
- **TypeScript**: 类型安全
- **Ant Design**: UI组件库
- **React Router**: 路由管理

---

## 第二部分：自定义模块模板架构

### 2.1 模块化模板系统概述

WPS采用了创新的**三层模块化架构**，实现了高度灵活和可扩展的模板系统。

### 2.2 三层架构设计

```
┌─────────────────────────────────────────┐
│    第一层：预设模块库（系统提供）          │
│  - 15+个预设字段模块                     │
│  - 涵盖所有常用焊接参数                   │
│  - 按7大分类组织                         │
│  - 系统维护，所有用户可用                 │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│    第二层：用户自定义模块                 │
│  - 用户创建自己的字段模块                 │
│  - 支持个人私有/企业共享/公开              │
│  - 完全自定义字段定义                     │
│  - 支持数据隔离                          │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│    第三层：模板（模块组合）                │
│  - 通过拖拽选择需要的模块                 │
│  - 调整模块顺序                          │
│  - 复制模块（多层多道焊）                 │
│  - 保存为可重用模板                       │
└─────────────────────────────────────────┘
```

### 2.3 核心数据结构

#### 2.3.1 字段模块 (FieldModule)
```typescript
interface FieldModule {
  id: string                    // 模块ID
  name: string                  // 模块名称
  description: string           // 模块描述
  icon: string                  // 图标
  category: string              // 分类
  repeatable: boolean           // 是否可重复
  fields: Record<string, FieldDefinition>  // 字段定义
}
```

#### 2.3.2 字段定义 (FieldDefinition)
```typescript
interface FieldDefinition {
  label: string                 // 字段标签
  type: string                  // 字段类型
  unit?: string                 // 单位
  options?: string[]            // 选项
  default?: any                 // 默认值
  required?: boolean            // 是否必填
  readonly?: boolean            // 是否只读
  placeholder?: string          // 占位符
  min?: number                  // 最小值
  max?: number                  // 最大值
}
```

#### 2.3.3 模块实例 (ModuleInstance)
```typescript
interface ModuleInstance {
  instanceId: string            // 实例唯一ID
  moduleId: string              // 模块定义ID
  order: number                 // 排序
  customName?: string           // 自定义名称
}
```

### 2.4 模块分类体系

| 分类 | 英文名 | 说明 | 示例模块 |
|------|--------|------|----------|
| 基本信息 | basic | 焊接工艺基本参数 | 基本信息、预热参数 |
| 材料信息 | material | 填充材料和电极 | 填充金属、电极处理、钨电极 |
| 气体信息 | gas | 保护气体参数 | 保护气体、背部保护气、等离子气 |
| 电气参数 | electrical | 电流电压参数 | 电流电压、电流脉冲 |
| 运动参数 | motion | 焊接运动参数 | 焊接速度、送丝速度、抖动参数 |
| 设备信息 | equipment | 焊接设备信息 | 喷嘴参数、焊接设备 |
| 计算结果 | calculation | 自动计算值 | 热输入 |

### 2.5 数据库设计

#### 2.5.1 自定义模块表
```sql
CREATE TABLE custom_modules (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    icon VARCHAR(50) DEFAULT 'BlockOutlined',
    category VARCHAR(20) DEFAULT 'basic',
    repeatable BOOLEAN DEFAULT FALSE,
    
    -- 字段定义（JSONB格式）
    fields JSONB NOT NULL DEFAULT '{}',
    
    -- 数据隔离字段
    user_id INTEGER REFERENCES users(id),
    workspace_type VARCHAR(20) DEFAULT 'personal',
    company_id INTEGER REFERENCES companies(id),
    factory_id INTEGER REFERENCES factories(id),
    
    -- 访问控制
    is_shared BOOLEAN DEFAULT FALSE,
    access_level VARCHAR(20) DEFAULT 'private',
    
    -- 统计信息
    usage_count INTEGER DEFAULT 0,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2.5.2 WPS模板表
```sql
CREATE TABLE wps_templates (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- 适用范围
    welding_process VARCHAR(50),
    welding_process_name VARCHAR(100),
    standard VARCHAR(50),
    
    -- 模块实例列表（JSONB）
    module_instances JSONB NOT NULL,
    
    -- 数据隔离
    user_id INTEGER,
    workspace_type VARCHAR(20),
    company_id INTEGER,
    
    -- 时间戳
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### 2.6 模块化模板的优势

#### 2.6.1 降低学习成本
- ✅ 用户无需理解复杂的字段定义
- ✅ 通过拖拽即可创建模板
- ✅ 预设模块保证规范性

#### 2.6.2 提高创建效率
- ✅ 快速组合模块
- ✅ 一键复制模块（多层多道焊）
- ✅ 模板可重用

#### 2.6.3 灵活性强
- ✅ 支持自定义模块
- ✅ 支持模块组合
- ✅ 支持企业共享

#### 2.6.4 可扩展性好
- ✅ 轻松添加新模块
- ✅ 模块化设计
- ✅ 易于维护

### 2.7 实现关键点

#### 2.7.1 后端服务层
```python
class CustomModuleService:
    def get_available_modules(
        self,
        current_user: User,
        workspace_context: WorkspaceContext,
        category: Optional[str] = None
    ) -> List[CustomModule]:
        """获取可用模块（系统+用户+企业）"""
        # 1. 系统模块（所有人可见）
        # 2. 个人模块（仅自己可见）
        # 3. 企业共享模块（企业内可见）
        pass
    
    def create_module(
        self,
        module_data: CustomModuleCreate,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> CustomModule:
        """创建自定义模块"""
        pass
```

#### 2.7.2 前端组件架构
```
ModuleLibrary (模块库)
  ├── 显示所有可用模块
  ├── 按分类分组
  ├── 支持搜索和过滤
  └── 可拖拽到画布

TemplateCanvas (模板画布)
  ├── 接收拖拽的模块
  ├── 显示已选择的模块列表
  ├── 支持模块排序
  ├── 支持模块复制
  └── 支持模块删除

ModuleCard (模块卡片)
  ├── 显示模块信息
  ├── 显示字段数量
  ├── 可拖拽
  └── 可复制

TemplatePreview (模板预览)
  ├── 实时预览生成的表单
  ├── 显示所有字段
  └── 按模块分组显示
```

---

## 第三部分：PQR模块设计方案

### 3.1 PQR模块概述

**PQR (Procedure Qualification Record)** - 焊接工艺评定记录

#### 功能定位
记录焊接工艺试验的参数和测试结果，为WPS提供技术支持和合格依据。

#### 开发优先级
**第一阶段** - 核心功能，立即开发

### 3.2 PQR与WPS的关系

```
┌─────────────┐
│    PQR      │  焊接工艺评定记录
│  (试验记录)  │  - 记录实际试验数据
│             │  - 力学性能测试
│             │  - 无损检测结果
└──────┬──────┘
       │ 支持
       ↓
┌─────────────┐
│    WPS      │  焊接工艺规程
│  (工艺文件)  │  - 基于PQR制定
│             │  - 指导实际生产
└─────────────┘
```

### 3.3 PQR功能设计

#### 3.3.1 基础管理功能
- **创建PQR**: 填写工艺评定记录
- **编辑PQR**: 修改PQR数据
- **删除PQR**: 软删除PQR
- **查看PQR**: 详细信息展示
- **复制PQR**: 基于现有PQR创建新记录
- **搜索PQR**: 按编号、标准、状态搜索
- **筛选PQR**: 按测试结果、日期等筛选

#### 3.3.2 焊接参数记录
- **实际焊接参数**: 记录实际使用的焊接参数
- **电流电压记录**: 记录各层道的电流电压
- **温度记录**: 预热温度、层间温度
- **焊接速度**: 记录焊接行走速度
- **热输入计算**: 自动计算热输入值

#### 3.3.3 力学性能测试（高级版及以上）
- **拉伸试验**: 记录抗拉强度、屈服强度
- **弯曲试验**: 记录弯曲角度和结果
- **冲击试验**: 记录冲击功和温度
- **硬度试验**: 记录各区域硬度值
- **宏观检验**: 上传宏观照片
- **金相检验**: 上传金相照片

#### 3.3.4 无损检测（高级版及以上）
- **射线检测 (RT)**: 记录RT结果
- **超声检测 (UT)**: 记录UT结果
- **磁粉检测 (MT)**: 记录MT结果
- **渗透检测 (PT)**: 记录PT结果
- **检测照片**: 上传检测照片
- **检测报告**: 上传检测报告

#### 3.3.5 测试结果管理
- **合格判定**: 根据标准自动判定
- **不合格处理**: 记录不合格原因和处理措施
- **重新测试**: 记录重测信息
- **测试报告**: 生成完整测试报告

#### 3.3.6 关联管理
- **关联WPS**: 关联支持的WPS
- **关联焊工**: 记录执行焊接的焊工
- **关联设备**: 记录使用的焊接设备
- **关联标准**: 关联评定标准

#### 3.3.7 导出功能（专业版及以上）
- **导出PDF**: 生成标准PQR报告
- **导出Excel**: 导出测试数据
- **批量导出**: 批量导出多个PQR
- **自定义模板**: 使用自定义报告模板

### 3.4 PQR会员权限设计

| 会员等级 | 访问权限 | 数量限制 | 功能范围 |
|---------|---------|---------|---------|
| 游客模式 | ✅ 可访问 | 0 (仅查看示例) | 只读查看示例数据 |
| 个人免费版 | ✅ 可访问 | 最多 10 个 | 基础增删改查 |
| 个人专业版 | ✅ 可访问 | 最多 30 个 | 基础功能 + 导出导入 |
| 个人高级版 | ✅ 可访问 | 最多 50 个 | 完整功能 + 测试管理 |
| 个人旗舰版 | ✅ 可访问 | 最多 100 个 | 完整功能 + 高级特性 |
| 企业版 | ✅ 可访问 | 最多 200 个 | 完整功能 + 企业协作 |
| 企业PRO | ✅ 可访问 | 最多 400 个 | 完整功能 + 企业协作 |
| 企业PRO MAX | ✅ 可访问 | 最多 500 个 | 完整功能 + 企业协作 |

**游客模式说明**:
- 游客仅可查看系统预设的示例PQR数据
- 无法创建、修改或删除任何数据
- 用于体验系统功能和界面

### 3.5 PQR数据模型设计

#### 3.5.1 核心表结构
```sql
CREATE TABLE pqr_records (
    -- 主键和基础字段
    id INTEGER PRIMARY KEY,

    -- 数据隔离核心字段（继承WPS模式）
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    workspace_type VARCHAR(20) NOT NULL DEFAULT 'personal',
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,

    -- PQR基本信息
    pqr_number VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    test_date DATE,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, qualified, failed, retest
    standard VARCHAR(100),

    -- 关联信息
    wps_number VARCHAR(50),  -- 对应的WPS编号
    company VARCHAR(100),
    project_name VARCHAR(100),
    test_location VARCHAR(100),
    welding_operator VARCHAR(100),

    -- 焊接工艺参数（实际使用）
    welding_process VARCHAR(100),
    base_material_spec VARCHAR(255),
    base_material_thickness DECIMAL(8,2),
    filler_material_spec VARCHAR(255),
    filler_material_classification VARCHAR(100),
    filler_material_diameter DECIMAL(8,2),
    joint_type VARCHAR(100),
    welding_position VARCHAR(50),

    -- 温度参数（实际测量）
    preheat_temp_min DECIMAL(10,2),
    preheat_temp_max DECIMAL(10,2),
    interpass_temp_max DECIMAL(10,2),

    -- 电气参数（实际测量）
    current_type VARCHAR(20),
    current_polarity VARCHAR(20),
    current_range VARCHAR(50),
    voltage_range VARCHAR(50),

    -- 保护气体
    shielding_gas VARCHAR(100),
    gas_flow_rate DECIMAL(8,2),
    gas_composition VARCHAR(100),

    -- 焊接速度和热输入
    welding_speed DECIMAL(10,2),
    travel_speed DECIMAL(10,2),
    heat_input_min DECIMAL(10,2),
    heat_input_max DECIMAL(10,2),

    -- 焊后热处理
    pwht_required BOOLEAN DEFAULT FALSE,
    pwht_temperature DECIMAL(10,2),
    pwht_time DECIMAL(10,2),

    -- 力学性能测试结果（JSONB）
    tensile_test_results JSONB,
    bend_test_results JSONB,
    impact_test_results JSONB,
    hardness_test_results JSONB,
    macro_examination JSONB,

    -- 无损检测结果
    ndt_results JSONB,
    rt_result VARCHAR(50),
    ut_result VARCHAR(50),
    mt_result VARCHAR(50),
    pt_result VARCHAR(50),

    -- 合格判定
    qualification_result VARCHAR(20),  -- qualified, failed, retest
    qualification_date DATE,
    qualified_by INTEGER REFERENCES users(id),
    failure_reason TEXT,
    corrective_action TEXT,

    -- 附加信息
    test_notes TEXT,
    deviation_notes TEXT,
    recommendations TEXT,
    test_reports TEXT,
    attachments TEXT,

    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    -- 索引
    INDEX idx_user (user_id),
    INDEX idx_workspace (workspace_type, company_id, factory_id),
    INDEX idx_pqr_number (pqr_number),
    INDEX idx_status (status),
    INDEX idx_test_date (test_date)
);
```

#### 3.5.2 测试试样表
```sql
CREATE TABLE pqr_test_specimens (
    id INTEGER PRIMARY KEY,
    pqr_id INTEGER NOT NULL REFERENCES pqr_records(id) ON DELETE CASCADE,

    specimen_type VARCHAR(50) NOT NULL,  -- tensile, bend, impact, hardness
    specimen_number VARCHAR(50),
    test_location VARCHAR(100),
    test_result JSONB,
    is_pass BOOLEAN,
    test_date TIMESTAMP,
    tester_id INTEGER REFERENCES users(id),

    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_pqr (pqr_id),
    INDEX idx_type (specimen_type)
);
```

### 3.6 PQR模块化模板设计

**关键决策**: PQR是否采用模块化模板？

#### 方案A：采用模块化模板（推荐）
**优势**:
- ✅ 与WPS保持一致的用户体验
- ✅ 灵活适应不同标准的PQR要求
- ✅ 用户可自定义测试项目
- ✅ 支持企业特殊测试要求

**实现方式**:
```typescript
// PQR专用模块分类
const PQR_MODULE_CATEGORIES = {
  basic: '基本信息',
  welding_params: '焊接参数',
  mechanical_tests: '力学性能测试',
  ndt_tests: '无损检测',
  qualification: '合格判定',
  attachments: '附件管理'
}

// PQR预设模块示例
const PQR_PRESET_MODULES = [
  {
    id: 'pqr_basic_info',
    name: 'PQR基本信息',
    category: 'basic',
    fields: {
      pqr_number: { label: 'PQR编号', type: 'text', required: true },
      test_date: { label: '试验日期', type: 'date', required: true },
      standard: { label: '评定标准', type: 'select', options: [...] }
    }
  },
  {
    id: 'tensile_test',
    name: '拉伸试验',
    category: 'mechanical_tests',
    repeatable: true,  // 可重复，支持多个试样
    fields: {
      specimen_number: { label: '试样编号', type: 'text' },
      tensile_strength: { label: '抗拉强度', type: 'number', unit: 'MPa' },
      yield_strength: { label: '屈服强度', type: 'number', unit: 'MPa' },
      elongation: { label: '延伸率', type: 'number', unit: '%' }
    }
  }
]
```

#### 方案B：固定字段模式
**优势**:
- ✅ 实现简单快速
- ✅ 标准化程度高

**劣势**:
- ❌ 灵活性差
- ❌ 难以适应不同标准
- ❌ 与WPS体验不一致

**推荐**: 采用**方案A（模块化模板）**，保持系统一致性。

### 3.7 PQR业务逻辑设计

#### 3.7.1 创建PQR流程
```python
class PQRService:
    def create_pqr(
        self,
        db: Session,
        pqr_data: PQRCreate,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> PQR:
        """创建PQR记录"""

        # 1. 验证工作区上下文
        workspace_context.validate()

        # 2. 检查配额
        quota_service = QuotaService(db)
        if not quota_service.check_quota(
            current_user,
            workspace_context,
            "pqr_records"
        ):
            raise HTTPException(403, "PQR配额已满")

        # 3. 检查PQR编号唯一性
        existing = self.get_by_number(
            db,
            pqr_data.pqr_number,
            workspace_context
        )
        if existing:
            raise ValueError("PQR编号已存在")

        # 4. 创建PQR记录
        pqr = PQR(
            **pqr_data.dict(),
            user_id=current_user.id,
            workspace_type=workspace_context.workspace_type,
            company_id=workspace_context.company_id,
            factory_id=workspace_context.factory_id,
            status="pending"
        )

        db.add(pqr)
        db.commit()
        db.refresh(pqr)

        # 5. 更新配额使用
        quota_service.increment_usage(
            current_user,
            workspace_context,
            "pqr_records"
        )

        return pqr
```

#### 3.7.2 合格判定逻辑
```python
def qualify_pqr(
    self,
    db: Session,
    pqr_id: int,
    qualification_data: PQRQualificationUpdate,
    current_user: User,
    workspace_context: WorkspaceContext
) -> PQR:
    """PQR合格判定"""

    # 1. 获取PQR记录
    pqr = self.get(db, pqr_id, workspace_context)
    if not pqr:
        raise HTTPException(404, "PQR不存在")

    # 2. 检查权限
    if not self._check_permission(pqr, current_user, "qualify"):
        raise HTTPException(403, "无权限进行合格判定")

    # 3. 检查所有测试是否完成
    if not self._all_tests_completed(pqr):
        raise HTTPException(400, "测试未完成，无法进行合格判定")

    # 4. 更新合格判定信息
    pqr.qualification_result = qualification_data.qualification_result
    pqr.qualification_date = qualification_data.qualification_date
    pqr.qualified_by = current_user.id
    pqr.status = "qualified" if qualification_data.qualification_result == "qualified" else "failed"

    db.commit()
    db.refresh(pqr)

    return pqr
```

#### 3.7.3 热输入自动计算
```python
def calculate_heat_input(
    self,
    current: float,
    voltage: float,
    travel_speed: float
) -> float:
    """
    计算热输入 (kJ/mm)
    公式: 热输入 = (电流 × 电压 × 60) / (1000 × 焊接速度)
    """
    if travel_speed <= 0:
        raise ValueError("焊接速度必须大于0")

    heat_input = (current * voltage * 60) / (1000 * travel_speed)
    return round(heat_input, 2)
```

### 3.8 PQR API设计

#### 3.8.1 核心端点
```python
# 获取PQR列表
GET /api/v1/pqr
Query: skip, limit, status, search_term
Headers: X-Workspace-ID

# 创建PQR
POST /api/v1/pqr
Headers: X-Workspace-ID
Body: PQRCreate

# 获取PQR详情
GET /api/v1/pqr/{id}
Headers: X-Workspace-ID

# 更新PQR
PUT /api/v1/pqr/{id}
Headers: X-Workspace-ID
Body: PQRUpdate

# 删除PQR（软删除）
DELETE /api/v1/pqr/{id}
Headers: X-Workspace-ID

# 添加测试结果
POST /api/v1/pqr/{id}/test-results
Headers: X-Workspace-ID
Body: PQRTestSpecimenCreate

# 合格判定
POST /api/v1/pqr/{id}/qualify
Headers: X-Workspace-ID
Body: PQRQualificationUpdate

# 导出PDF
GET /api/v1/pqr/{id}/export/pdf
Headers: X-Workspace-ID

# 关联WPS
POST /api/v1/pqr/{id}/link-wps
Headers: X-Workspace-ID
Body: { wps_ids: [...] }

# 高级搜索
POST /api/v1/pqr/search
Headers: X-Workspace-ID
Body: PQRSearchParams
```

### 3.9 PQR前端设计

#### 3.9.1 页面结构
```
/pqr
  ├── /list          - PQR列表页
  ├── /create        - 创建PQR页
  ├── /edit/:id      - 编辑PQR页
  ├── /detail/:id    - PQR详情页
  └── /templates     - PQR模板管理页
```

#### 3.9.2 核心组件
```typescript
// PQR列表组件
<PQRList>
  - 数据表格
  - 搜索筛选
  - 批量操作
  - 状态标签
  - 快速操作按钮

// PQR创建/编辑组件
<PQRForm>
  - 步骤导航（基本信息 → 焊接参数 → 测试结果 → 合格判定）
  - 模块化表单（基于模板）
  - 自动计算（热输入等）
  - 文件上传（测试照片、报告）
  - 实时验证

// PQR详情组件
<PQRDetail>
  - 基本信息展示
  - 焊接参数展示
  - 测试结果展示（表格+图表）
  - 合格判定信息
  - 关联WPS列表
  - 附件下载
  - 操作按钮（编辑、删除、导出、复制）

// 测试结果管理组件
<TestResultsManager>
  - 添加测试结果
  - 编辑测试结果
  - 删除测试结果
  - 测试结果列表
  - 合格/不合格标记
```

---

## 第四部分：pPQR模块设计方案

### 4.1 pPQR模块概述

**pPQR (Preliminary Procedure Qualification Record)** - 预备工艺评定记录

#### 功能定位
管理预备工艺评定记录，是正式PQR之前的试验性评定，用于工艺开发和优化。

#### 开发优先级
**第二阶段** - 重要功能，优先开发

### 4.2 pPQR与PQR的关系

```
┌─────────────┐
│   pPQR      │  预备工艺评定记录
│  (试验阶段)  │  - 工艺参数探索
│             │  - 多组对比试验
│             │  - 快速验证
└──────┬──────┘
       │ 转换
       ↓
┌─────────────┐
│    PQR      │  正式工艺评定记录
│  (正式评定)  │  - 完整测试
│             │  - 合格判定
└──────┬──────┘
       │ 支持
       ↓
┌─────────────┐
│    WPS      │  焊接工艺规程
│  (生产指导)  │  - 指导生产
└─────────────┘
```

### 4.3 pPQR功能设计

#### 4.3.1 基础管理功能
- **创建pPQR**: 填写预备评定记录
- **编辑pPQR**: 修改pPQR数据
- **删除pPQR**: 软删除pPQR
- **查看pPQR**: 详细信息展示
- **复制pPQR**: 基于现有pPQR创建新记录
- **搜索pPQR**: 按编号、目的、状态搜索
- **筛选pPQR**: 按试验结果、日期等筛选

#### 4.3.2 试验参数记录
- **试验目的**: 记录试验目的和预期目标
- **试验方案**: 记录试验方案和步骤
- **参数设置**: 记录计划使用的参数
- **实际参数**: 记录实际使用的参数
- **参数调整**: 记录参数调整过程
- **多组试验**: 支持记录多组对比试验

#### 4.3.3 试验结果记录
- **外观检查**: 记录焊缝外观质量
- **尺寸测量**: 记录焊缝尺寸数据
- **简易测试**: 记录简单的力学测试
- **缺陷记录**: 记录发现的缺陷
- **试验照片**: 上传试验过程照片
- **试验视频**: 上传试验视频（旗舰版）

#### 4.3.4 参数优化（高级版及以上）
- **参数对比**: 对比不同参数组的结果
- **趋势分析**: 分析参数变化趋势
- **最优参数**: 标记最优参数组合
- **优化建议**: 系统给出优化建议

#### 4.3.5 转换功能（高级版及以上）
- **转换为PQR**: 将成功的pPQR转换为正式PQR
- **数据迁移**: 自动迁移相关数据
- **补充信息**: 补充PQR所需的额外信息
- **关联保持**: 保持与原pPQR的关联

#### 4.3.6 协作功能（企业版）
- **团队共享**: 与团队成员共享pPQR
- **评论讨论**: 团队成员可以评论
- **版本对比**: 对比不同人员的试验结果
- **知识积累**: 形成企业工艺知识库

#### 4.3.7 导出功能
- **导出PDF**: 生成试验报告
- **导出Excel**: 导出试验数据
- **导出对比报告**: 导出参数对比分析报告
- **批量导出**: 批量导出多个pPQR

### 4.4 pPQR会员权限设计

| 会员等级 | 访问权限 | 数量限制 | 功能范围 |
|---------|---------|---------|---------|
| 游客模式 | ❌ 不可访问 | 0 | - |
| 个人免费版 | ❌ 不可访问 | 0 | - |
| 个人专业版 | ✅ 可访问 | 最多 30 个 | 基础增删改查 + 导出 |
| 个人高级版 | ✅ 可访问 | 最多 50 个 | 完整功能 + 试验管理 + 转换PQR |
| 个人旗舰版 | ✅ 可访问 | 最多 100 个 | 完整功能 + 高级特性 |
| 企业版 | ✅ 可访问 | 最多 200 个 | 完整功能 + 企业协作 |
| 企业PRO | ✅ 可访问 | 最多 400 个 | 完整功能 + 企业协作 |
| 企业PRO MAX | ✅ 可访问 | 最多 500 个 | 完整功能 + 企业协作 |

**重要说明**:
- pPQR功能仅对**个人专业版及以上**会员开放
- 免费版和游客模式不可访问
- 转换为PQR功能需要**高级版及以上**

### 4.5 pPQR数据模型设计

#### 4.5.1 核心表结构
```sql
CREATE TABLE ppqr_records (
    -- 主键和基础字段
    id INTEGER PRIMARY KEY,

    -- 数据隔离核心字段（继承WPS模式）
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    workspace_type VARCHAR(20) NOT NULL DEFAULT 'personal',
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,

    -- pPQR基本信息
    ppqr_number VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    test_date DATE,
    status VARCHAR(50) DEFAULT 'draft',  -- draft, testing, completed, converted
    purpose TEXT,  -- 试验目的
    test_plan TEXT,  -- 试验方案

    -- 关联信息
    company VARCHAR(100),
    project_name VARCHAR(100),
    test_location VARCHAR(100),
    welding_operator VARCHAR(100),

    -- 焊接工艺参数（计划）
    planned_parameters JSONB,

    -- 焊接工艺参数（实际使用）
    welding_process VARCHAR(100),
    base_material VARCHAR(255),
    base_material_thickness DECIMAL(8,2),
    filler_material VARCHAR(255),
    joint_type VARCHAR(100),
    welding_position VARCHAR(50),

    -- 实际参数
    actual_parameters JSONB,
    parameter_adjustments JSONB,  -- 参数调整记录

    -- 温度参数
    preheat_temp DECIMAL(10,2),
    interpass_temp DECIMAL(10,2),

    -- 电气参数
    welding_current DECIMAL(10,2),
    welding_voltage DECIMAL(10,2),
    travel_speed DECIMAL(10,2),
    heat_input DECIMAL(10,2),

    -- 保护气体
    shielding_gas VARCHAR(100),
    gas_flow_rate DECIMAL(8,2),

    -- 试验结果
    visual_inspection JSONB,  -- 外观检查结果
    dimension_measurements JSONB,  -- 尺寸测量结果
    simple_tests JSONB,  -- 简易测试结果
    defects_found JSONB,  -- 发现的缺陷

    -- 试验评价
    is_successful BOOLEAN,
    success_criteria TEXT,
    evaluation_notes TEXT,
    improvement_suggestions TEXT,

    -- 试验人员
    welder_id INTEGER REFERENCES welders(id),
    tester_id INTEGER REFERENCES users(id),

    -- 多组试验
    test_group_number INTEGER DEFAULT 1,
    parent_ppqr_id INTEGER REFERENCES ppqr_records(id),  -- 父pPQR（用于对比试验）

    -- 转换信息
    converted_to_pqr_id INTEGER REFERENCES pqr_records(id),
    converted_at TIMESTAMP,
    converted_by INTEGER REFERENCES users(id),

    -- 附件
    test_photos JSONB,
    test_videos JSONB,
    attachments JSONB,

    -- 协作
    shared_with JSONB,  -- 共享给的用户列表
    comments JSONB,  -- 评论列表

    -- 备注
    notes TEXT,
    tags JSONB,

    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    -- 索引
    INDEX idx_user (user_id),
    INDEX idx_workspace (workspace_type, company_id, factory_id),
    INDEX idx_ppqr_number (ppqr_number),
    INDEX idx_status (status),
    INDEX idx_test_date (test_date),
    INDEX idx_parent (parent_ppqr_id),
    INDEX idx_converted (converted_to_pqr_id)
);
```

#### 4.5.2 参数对比表
```sql
CREATE TABLE ppqr_parameter_comparisons (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    comparison_name VARCHAR(255),
    ppqr_ids JSONB NOT NULL,  -- 参与对比的pPQR ID列表
    comparison_results JSONB,  -- 对比结果
    best_parameters JSONB,  -- 最优参数

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_user (user_id)
);
```

### 4.6 pPQR模块化模板设计

**采用模块化模板**，与WPS和PQR保持一致。

#### pPQR专用模块分类
```typescript
const PPQR_MODULE_CATEGORIES = {
  basic: '基本信息',
  test_plan: '试验方案',
  planned_params: '计划参数',
  actual_params: '实际参数',
  test_results: '试验结果',
  evaluation: '试验评价',
  attachments: '附件管理'
}
```

#### pPQR预设模块示例
```typescript
const PPQR_PRESET_MODULES = [
  {
    id: 'ppqr_basic_info',
    name: 'pPQR基本信息',
    category: 'basic',
    fields: {
      ppqr_number: { label: 'pPQR编号', type: 'text', required: true },
      title: { label: '标题', type: 'text', required: true },
      test_date: { label: '试验日期', type: 'date' },
      purpose: { label: '试验目的', type: 'textarea', required: true }
    }
  },
  {
    id: 'test_plan',
    name: '试验方案',
    category: 'test_plan',
    fields: {
      test_plan: { label: '试验方案', type: 'textarea' },
      success_criteria: { label: '成功标准', type: 'textarea' },
      test_steps: { label: '试验步骤', type: 'textarea' }
    }
  },
  {
    id: 'parameter_comparison',
    name: '参数对比组',
    category: 'planned_params',
    repeatable: true,  // 可重复，支持多组对比
    fields: {
      group_name: { label: '参数组名称', type: 'text' },
      current_plan: { label: '计划电流', type: 'number', unit: 'A' },
      voltage_plan: { label: '计划电压', type: 'number', unit: 'V' },
      speed_plan: { label: '计划速度', type: 'number', unit: 'mm/min' }
    }
  },
  {
    id: 'visual_inspection',
    name: '外观检查',
    category: 'test_results',
    fields: {
      appearance: { label: '外观质量', type: 'select', options: ['优秀', '良好', '一般', '差'] },
      surface_defects: { label: '表面缺陷', type: 'textarea' },
      weld_profile: { label: '焊缝成型', type: 'select', options: ['良好', '一般', '不良'] }
    }
  }
]
```

### 4.7 pPQR业务逻辑设计

#### 4.7.1 创建pPQR流程
```python
class PPQRService:
    def create_ppqr(
        self,
        db: Session,
        ppqr_data: PPQRCreate,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> PPQR:
        """创建pPQR记录"""

        # 1. 检查会员等级（需要专业版及以上）
        if current_user.membership_tier in ['free', 'guest']:
            raise HTTPException(
                403,
                "pPQR功能需要专业版及以上会员"
            )

        # 2. 验证工作区上下文
        workspace_context.validate()

        # 3. 检查配额
        quota_service = QuotaService(db)
        if not quota_service.check_quota(
            current_user,
            workspace_context,
            "ppqr_records"
        ):
            raise HTTPException(403, "pPQR配额已满")

        # 4. 生成pPQR编号
        if not ppqr_data.ppqr_number:
            ppqr_data.ppqr_number = self._generate_ppqr_number(
                current_user.id,
                db
            )

        # 5. 创建pPQR记录
        ppqr = PPQR(
            **ppqr_data.dict(),
            user_id=current_user.id,
            workspace_type=workspace_context.workspace_type,
            company_id=workspace_context.company_id,
            factory_id=workspace_context.factory_id,
            status="draft"
        )

        db.add(ppqr)
        db.commit()
        db.refresh(ppqr)

        # 6. 更新配额使用
        quota_service.increment_usage(
            current_user,
            workspace_context,
            "ppqr_records"
        )

        return ppqr
```

#### 4.7.2 转换为PQR流程
```python
def convert_to_pqr(
    self,
    db: Session,
    ppqr_id: int,
    conversion_data: PPQRConversionData,
    current_user: User,
    workspace_context: WorkspaceContext
) -> PQR:
    """将pPQR转换为正式PQR（需要高级版及以上）"""

    # 1. 检查会员等级（需要高级版及以上）
    if current_user.membership_tier not in ['advanced', 'flagship', 'enterprise', 'enterprise_pro', 'enterprise_pro_max']:
        raise HTTPException(
            403,
            "转换为PQR功能需要高级版及以上会员"
        )

    # 2. 获取pPQR记录
    ppqr = self.get(db, ppqr_id, workspace_context)
    if not ppqr:
        raise HTTPException(404, "pPQR不存在")

    # 3. 检查pPQR状态
    if not ppqr.is_successful:
        raise HTTPException(400, "只能转换成功的pPQR")

    if ppqr.status == "converted":
        raise HTTPException(400, "该pPQR已经转换过")

    # 4. 创建PQR记录
    pqr_service = PQRService(db)
    pqr = pqr_service.create_pqr(
        db=db,
        pqr_data=PQRCreate(
            pqr_number=conversion_data.pqr_number,
            title=ppqr.title,
            test_date=ppqr.test_date or datetime.now().date(),
            welding_process=ppqr.welding_process,
            base_material_spec=ppqr.base_material,
            base_material_thickness=ppqr.base_material_thickness,
            filler_material_spec=ppqr.filler_material,
            joint_type=ppqr.joint_type,
            welding_position=ppqr.welding_position,
            preheat_temp_min=ppqr.preheat_temp,
            preheat_temp_max=ppqr.preheat_temp,
            interpass_temp_max=ppqr.interpass_temp,
            current_range=str(ppqr.welding_current),
            voltage_range=str(ppqr.welding_voltage),
            travel_speed=ppqr.travel_speed,
            heat_input_min=ppqr.heat_input,
            heat_input_max=ppqr.heat_input,
            shielding_gas=ppqr.shielding_gas,
            gas_flow_rate=ppqr.gas_flow_rate,
            # 补充PQR所需的额外信息
            **conversion_data.additional_data
        ),
        current_user=current_user,
        workspace_context=workspace_context
    )

    # 5. 更新pPQR状态
    ppqr.converted_to_pqr_id = pqr.id
    ppqr.converted_at = datetime.now()
    ppqr.converted_by = current_user.id
    ppqr.status = "converted"

    db.commit()

    return pqr
```

#### 4.7.3 参数对比分析
```python
def compare_parameters(
    self,
    db: Session,
    ppqr_ids: List[int],
    comparison_name: str,
    current_user: User,
    workspace_context: WorkspaceContext
) -> Dict[str, Any]:
    """对比多个pPQR的参数（需要高级版及以上）"""

    # 1. 检查会员等级
    if current_user.membership_tier not in ['advanced', 'flagship', 'enterprise', 'enterprise_pro', 'enterprise_pro_max']:
        raise HTTPException(
            403,
            "参数对比功能需要高级版及以上会员"
        )

    # 2. 获取pPQR记录
    ppqrs = []
    for ppqr_id in ppqr_ids:
        ppqr = self.get(db, ppqr_id, workspace_context)
        if ppqr:
            ppqrs.append(ppqr)

    if len(ppqrs) < 2:
        raise HTTPException(400, "至少需要2个pPQR进行对比")

    # 3. 提取参数进行对比
    comparison_result = {
        "comparison_name": comparison_name,
        "ppqrs": [],
        "parameter_analysis": {},
        "best_result": None
    }

    for ppqr in ppqrs:
        comparison_result["ppqrs"].append({
            "id": ppqr.id,
            "ppqr_number": ppqr.ppqr_number,
            "title": ppqr.title,
            "current": ppqr.welding_current,
            "voltage": ppqr.welding_voltage,
            "speed": ppqr.travel_speed,
            "heat_input": ppqr.heat_input,
            "is_successful": ppqr.is_successful,
            "visual_inspection": ppqr.visual_inspection
        })

    # 4. 分析最优参数
    successful_ppqrs = [p for p in ppqrs if p.is_successful]
    if successful_ppqrs:
        # 选择热输入最低的成功试验作为最优
        best_ppqr = min(
            successful_ppqrs,
            key=lambda p: p.heat_input or float('inf')
        )
        comparison_result["best_result"] = {
            "ppqr_id": best_ppqr.id,
            "ppqr_number": best_ppqr.ppqr_number,
            "parameters": {
                "current": best_ppqr.welding_current,
                "voltage": best_ppqr.welding_voltage,
                "speed": best_ppqr.travel_speed,
                "heat_input": best_ppqr.heat_input
            }
        }

    # 5. 保存对比记录
    comparison_record = PPQRParameterComparison(
        user_id=current_user.id,
        comparison_name=comparison_name,
        ppqr_ids=ppqr_ids,
        comparison_results=comparison_result
    )
    db.add(comparison_record)
    db.commit()

    return comparison_result
```

### 4.8 pPQR API设计

#### 4.8.1 核心端点
```python
# 获取pPQR列表
GET /api/v1/ppqr
Query: skip, limit, status, search_term
Headers: X-Workspace-ID

# 创建pPQR
POST /api/v1/ppqr
Headers: X-Workspace-ID
Body: PPQRCreate

# 获取pPQR详情
GET /api/v1/ppqr/{id}
Headers: X-Workspace-ID

# 更新pPQR
PUT /api/v1/ppqr/{id}
Headers: X-Workspace-ID
Body: PPQRUpdate

# 删除pPQR（软删除）
DELETE /api/v1/ppqr/{id}
Headers: X-Workspace-ID

# 更新试验结果
PUT /api/v1/ppqr/{id}/results
Headers: X-Workspace-ID
Body: PPQRTestResults

# 转换为PQR（高级版及以上）
POST /api/v1/ppqr/{id}/convert-to-pqr
Headers: X-Workspace-ID
Body: PPQRConversionData

# 参数对比（高级版及以上）
POST /api/v1/ppqr/compare
Headers: X-Workspace-ID
Body: { ppqr_ids: [...], comparison_name: "..." }

# 共享pPQR（企业版）
POST /api/v1/ppqr/{id}/share
Headers: X-Workspace-ID
Body: { user_ids: [...] }

# 添加评论（企业版）
POST /api/v1/ppqr/{id}/comments
Headers: X-Workspace-ID
Body: { comment: "..." }

# 导出PDF
GET /api/v1/ppqr/{id}/export/pdf
Headers: X-Workspace-ID
```

### 4.9 pPQR前端设计

#### 4.9.1 页面结构
```
/ppqr
  ├── /list          - pPQR列表页
  ├── /create        - 创建pPQR页
  ├── /edit/:id      - 编辑pPQR页
  ├── /detail/:id    - pPQR详情页
  ├── /compare       - 参数对比页（高级版）
  └── /templates     - pPQR模板管理页
```

#### 4.9.2 核心组件
```typescript
// pPQR列表组件
<PPQRList>
  - 数据表格
  - 搜索筛选
  - 批量操作
  - 状态标签（draft, testing, completed, converted）
  - 快速操作按钮
  - 会员等级提示（免费版显示升级提示）

// pPQR创建/编辑组件
<PPQRForm>
  - 步骤导航（基本信息 → 试验方案 → 参数设置 → 试验结果 → 评价）
  - 模块化表单（基于模板）
  - 多组参数对比（可添加多组）
  - 文件上传（照片、视频）
  - 实时验证

// pPQR详情组件
<PPQRDetail>
  - 基本信息展示
  - 试验方案展示
  - 参数对比表格
  - 试验结果展示
  - 评价信息
  - 转换状态（如已转换，显示关联的PQR）
  - 操作按钮（编辑、删除、导出、复制、转换为PQR）

// 参数对比组件（高级版）
<ParameterComparison>
  - 选择多个pPQR
  - 参数对比表格
  - 可视化图表（电流、电压、热输入对比）
  - 最优参数推荐
  - 导出对比报告

// 转换为PQR组件（高级版）
<ConvertToPQR>
  - 显示pPQR数据
  - 补充PQR所需信息
  - 选择需要进行的测试
  - 确认转换
```

---

## 第五部分：实施计划与路线图

### 5.1 开发阶段划分

#### 阶段一：PQR模块开发（优先级：高）
**预计时间**: 2-3周

**后端任务**:
1. ✅ 创建PQR数据模型（pqr_records表）
2. ✅ 创建PQR测试试样表（pqr_test_specimens表）
3. ✅ 实现PQR Pydantic Schemas
4. ✅ 实现PQRService业务逻辑
5. ✅ 实现PQR API端点
6. ⬜ 实现PQR模块化模板系统
7. ⬜ 实现热输入自动计算
8. ⬜ 实现合格判定逻辑
9. ⬜ 实现PDF导出功能
10. ⬜ 编写单元测试

**前端任务**:
1. ⬜ 创建PQR类型定义
2. ⬜ 创建PQR API服务
3. ⬜ 实现PQR列表页面
4. ⬜ 实现PQR创建/编辑页面（模块化表单）
5. ⬜ 实现PQR详情页面
6. ⬜ 实现测试结果管理组件
7. ⬜ 实现合格判定界面
8. ⬜ 实现PQR模板管理
9. ⬜ 集成到主导航
10. ⬜ 编写E2E测试

#### 阶段二：pPQR模块开发（优先级：中）
**预计时间**: 2-3周

**后端任务**:
1. ⬜ 创建pPQR数据模型（ppqr_records表）
2. ⬜ 创建参数对比表（ppqr_parameter_comparisons表）
3. ⬜ 实现pPQR Pydantic Schemas
4. ⬜ 实现PPQRService业务逻辑
5. ⬜ 实现pPQR API端点
6. ⬜ 实现pPQR模块化模板系统
7. ⬜ 实现转换为PQR功能
8. ⬜ 实现参数对比分析功能
9. ⬜ 实现协作功能（企业版）
10. ⬜ 编写单元测试

**前端任务**:
1. ⬜ 创建pPQR类型定义
2. ⬜ 创建pPQR API服务
3. ⬜ 实现pPQR列表页面
4. ⬜ 实现pPQR创建/编辑页面（模块化表单）
5. ⬜ 实现pPQR详情页面
6. ⬜ 实现参数对比组件（高级版）
7. ⬜ 实现转换为PQR组件（高级版）
8. ⬜ 实现协作功能界面（企业版）
9. ⬜ 实现会员等级检查和升级提示
10. ⬜ 编写E2E测试

#### 阶段三：集成与优化（优先级：中）
**预计时间**: 1周

**任务**:
1. ⬜ PQR与WPS关联功能
2. ⬜ pPQR与PQR关联功能
3. ⬜ 数据迁移工具
4. ⬜ 性能优化
5. ⬜ 用户体验优化
6. ⬜ 文档完善
7. ⬜ 培训材料准备

### 5.2 技术栈总结

#### 后端技术栈
```
FastAPI          - Web框架
SQLAlchemy       - ORM
PostgreSQL       - 数据库（JSONB支持）
Pydantic         - 数据验证
Alembic          - 数据库迁移
```

#### 前端技术栈
```
React            - UI框架
TypeScript       - 类型安全
Ant Design       - UI组件库
React Router     - 路由管理
@dnd-kit         - 拖拽功能（模块化模板）
Axios            - HTTP客户端
```

### 5.3 数据库迁移计划

#### 迁移脚本顺序
```sql
-- 1. 创建PQR表
migrations/create_pqr_records_table.sql

-- 2. 创建PQR测试试样表
migrations/create_pqr_test_specimens_table.sql

-- 3. 创建pPQR表
migrations/create_ppqr_records_table.sql

-- 4. 创建pPQR参数对比表
migrations/create_ppqr_parameter_comparisons_table.sql

-- 5. 添加PQR模块化模板支持
migrations/add_pqr_template_support.sql

-- 6. 添加pPQR模块化模板支持
migrations/add_ppqr_template_support.sql

-- 7. 更新配额表（添加PQR和pPQR配额）
migrations/update_quota_for_pqr_ppqr.sql
```

### 5.4 模块化模板实施策略

#### 5.4.1 复用WPS模块化架构
- ✅ 复用CustomModule表和服务
- ✅ 复用ModuleInstance数据结构
- ✅ 复用前端拖拽组件
- ✅ 扩展模块分类（添加PQR和pPQR专用分类）

#### 5.4.2 PQR/pPQR专用模块
```typescript
// 创建PQR专用预设模块
const PQR_MODULES = [
  // 基本信息类
  'pqr_basic_info',
  'pqr_test_info',

  // 焊接参数类
  'pqr_welding_params',
  'pqr_temperature_params',
  'pqr_electrical_params',

  // 测试结果类
  'tensile_test',
  'bend_test',
  'impact_test',
  'hardness_test',
  'macro_examination',

  // 无损检测类
  'rt_test',
  'ut_test',
  'mt_test',
  'pt_test',

  // 合格判定类
  'qualification_info'
]

// 创建pPQR专用预设模块
const PPQR_MODULES = [
  // 基本信息类
  'ppqr_basic_info',
  'test_plan',

  // 参数类
  'planned_parameters',
  'actual_parameters',
  'parameter_adjustments',

  // 试验结果类
  'visual_inspection',
  'dimension_measurement',
  'simple_tests',
  'defect_records',

  // 评价类
  'test_evaluation',
  'improvement_suggestions'
]
```

#### 5.4.3 模板创建流程
```
1. 用户选择创建PQR/pPQR模板
   ↓
2. 打开模块化模板创建器
   ↓
3. 从模块库拖拽所需模块
   - 系统预设模块
   - 用户自定义模块
   - 企业共享模块
   ↓
4. 调整模块顺序和配置
   ↓
5. 预览生成的表单
   ↓
6. 保存模板
   ↓
7. 使用模板创建PQR/pPQR记录
```

### 5.5 关键技术决策

#### 5.5.1 模块化 vs 固定字段
**决策**: 采用模块化模板系统

**理由**:
- ✅ 与WPS保持一致的用户体验
- ✅ 灵活适应不同标准（AWS, ASME, EN, GB等）
- ✅ 支持企业自定义测试项目
- ✅ 易于扩展和维护

#### 5.5.2 数据存储方式
**决策**: 固定字段 + JSONB混合模式

**理由**:
- ✅ 常用字段使用固定列（便于查询和索引）
- ✅ 灵活字段使用JSONB（支持自定义）
- ✅ 平衡性能和灵活性

#### 5.5.3 会员权限控制
**决策**:
- PQR: 所有会员可用（免费版10个）
- pPQR: 专业版及以上可用

**理由**:
- ✅ PQR是核心功能，应对所有用户开放
- ✅ pPQR是高级功能，作为付费增值服务
- ✅ 鼓励用户升级到专业版

#### 5.5.4 pPQR转PQR功能
**决策**: 高级版及以上可用

**理由**:
- ✅ 转换功能是高价值特性
- ✅ 鼓励用户升级到高级版
- ✅ 避免免费用户滥用

### 5.6 风险与挑战

#### 5.6.1 技术风险
| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| JSONB性能问题 | 中 | 合理使用索引，常用字段使用固定列 |
| 模块化复杂度 | 中 | 复用WPS已验证的架构 |
| 数据迁移 | 低 | 新功能，无历史数据 |

#### 5.6.2 业务风险
| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 用户学习成本 | 中 | 提供详细文档和视频教程 |
| 标准适配性 | 中 | 支持多种国际标准 |
| 会员转化率 | 中 | 提供试用期和演示数据 |

### 5.7 测试策略

#### 5.7.1 单元测试
```python
# 后端单元测试
tests/test_pqr_service.py
tests/test_ppqr_service.py
tests/test_pqr_api.py
tests/test_ppqr_api.py
tests/test_pqr_conversion.py
```

#### 5.7.2 集成测试
```python
# 集成测试
tests/integration/test_pqr_workflow.py
tests/integration/test_ppqr_to_pqr_conversion.py
tests/integration/test_pqr_wps_association.py
```

#### 5.7.3 E2E测试
```typescript
// 前端E2E测试
e2e/pqr/create-pqr.spec.ts
e2e/pqr/edit-pqr.spec.ts
e2e/pqr/qualify-pqr.spec.ts
e2e/ppqr/create-ppqr.spec.ts
e2e/ppqr/convert-to-pqr.spec.ts
e2e/ppqr/compare-parameters.spec.ts
```

---

## 第六部分：总结与建议

### 6.1 设计亮点

#### 6.1.1 模块化架构
- ✅ 完全复用WPS的模块化模板系统
- ✅ 统一的用户体验
- ✅ 高度灵活和可扩展

#### 6.1.2 数据隔离
- ✅ 继承WPS的工作区隔离机制
- ✅ 支持个人/企业/工厂级隔离
- ✅ 完善的权限控制

#### 6.1.3 会员体系
- ✅ 合理的功能分级
- ✅ 清晰的升级路径
- ✅ 平衡免费和付费功能

#### 6.1.4 业务流程
- ✅ pPQR → PQR → WPS 完整链路
- ✅ 数据自动迁移
- ✅ 关联关系清晰

### 6.2 实施建议

#### 6.2.1 开发顺序
1. **优先开发PQR模块**（核心功能，所有用户需要）
2. **其次开发pPQR模块**（高级功能，付费用户需要）
3. **最后完善集成**（关联、导出、优化）

#### 6.2.2 迭代策略
- **MVP版本**: 基础CRUD + 固定字段
- **V1.0版本**: 模块化模板 + 测试管理
- **V1.1版本**: 高级功能（转换、对比、协作）
- **V2.0版本**: AI辅助、智能推荐

#### 6.2.3 用户培训
- 📚 编写详细的用户手册
- 🎥 录制视频教程
- 💡 提供示例数据和模板
- 🎓 举办在线培训课程

### 6.3 后续扩展方向

#### 6.3.1 AI辅助功能
- 🤖 基于历史数据的参数推荐
- 🤖 自动合格判定
- 🤖 缺陷识别（图像识别）
- 🤖 智能报告生成

#### 6.3.2 数据分析
- 📊 PQR统计分析
- 📊 参数趋势分析
- 📊 合格率分析
- 📊 成本分析

#### 6.3.3 移动端支持
- 📱 移动端查看PQR/pPQR
- 📱 现场拍照上传
- 📱 扫码关联设备
- 📱 离线数据采集

---

## 附录

### A. 术语表

| 术语 | 英文全称 | 中文说明 |
|------|---------|---------|
| WPS | Welding Procedure Specification | 焊接工艺规程 |
| PQR | Procedure Qualification Record | 焊接工艺评定记录 |
| pPQR | Preliminary Procedure Qualification Record | 预备工艺评定记录 |
| NDT | Non-Destructive Testing | 无损检测 |
| RT | Radiographic Testing | 射线检测 |
| UT | Ultrasonic Testing | 超声检测 |
| MT | Magnetic Particle Testing | 磁粉检测 |
| PT | Penetrant Testing | 渗透检测 |
| PWHT | Post Weld Heat Treatment | 焊后热处理 |
| SMAW | Shielded Metal Arc Welding | 手工电弧焊（111） |
| GTAW | Gas Tungsten Arc Welding | 钨极氩弧焊（141） |
| GMAW | Gas Metal Arc Welding | 熔化极气体保护焊（135） |

### B. 参考标准

- AWS D1.1 - Structural Welding Code - Steel
- ASME Section IX - Welding and Brazing Qualifications
- EN ISO 15609-1 - Specification and qualification of welding procedures
- GB/T 15169 - 钢熔化焊手工电弧焊焊接工艺评定

### C. 相关文档

- `modules/WPS_MANAGEMENT_DEVELOPMENT_GUIDE.md` - WPS模块开发指南
- `modules/PQR_MANAGEMENT_DEVELOPMENT_GUIDE.md` - PQR模块开发指南
- `modules/PPQR_MANAGEMENT_DEVELOPMENT_GUIDE.md` - pPQR模块开发指南
- `md/MODULE_BASED_TEMPLATE_SYSTEM.md` - 模块化模板系统设计
- `md/MODULAR_TEMPLATE_IMPLEMENTATION_SUMMARY.md` - 模块化模板实现总结
- `modules/DATA_ISOLATION_IMPLEMENTATION_GUIDE.md` - 数据隔离实现指南

---

**文档结束**

**版本**: 1.0
**最后更新**: 2025-10-25
**状态**: 设计完成，待评审
**下一步**: 开始PQR模块后端开发


