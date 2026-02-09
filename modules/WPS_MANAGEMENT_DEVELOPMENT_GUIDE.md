# WPS管理模块 - 开发指南

## 📋 模块概述

### 功能定位
WPS (Welding Procedure Specification) 管理模块是系统的核心功能之一，用于管理焊接工艺规程，包括工艺参数维护、版本控制、审批流程等。

### 适用场景
- 创建和维护焊接工艺规程
- 管理工艺参数和技术要求
- 工艺文件的版本控制
- 工艺评审和批准流程
- 工艺文件的导出和打印

### 开发优先级
**第一阶段** - 核心功能，立即开发

---

## 🎯 会员权限

### 访问权限
| 会员等级 | 访问权限 | 数量限制 | 功能范围 |
|---------|---------|---------|---------|
| 游客模式 | ✅ 可访问 | 0 (仅查看示例) | 只读查看示例数据 |
| 个人免费版 | ✅ 可访问 | 最多 10 个 | 基础增删改查 |
| 个人专业版 | ✅ 可访问 | 最多 30 个 | 基础功能 + 导出导入 |
| 个人高级版 | ✅ 可访问 | 最多 50 个 | 完整功能 + 审批流程 |
| 个人旗舰版 | ✅ 可访问 | 最多 100 个 | 完整功能 + 高级特性 |
| 企业版 | ✅ 可访问 | 最多 200 个 | 完整功能 + 企业协作 |
| 企业PRO | ✅ 可访问 | 最多 400 个 | 完整功能 + 企业协作 |
| 企业PRO MAX | ✅ 可访问 | 最多 500 个 | 完整功能 + 企业协作 |

**游客模式说明**:
- 游客仅可查看系统预设的示例 WPS 数据
- 无法创建、修改或删除任何数据
- 无法保存任何操作
- 用于体验系统功能和界面

### 功能权限矩阵
| 功能 | 免费版 | 专业版 | 高级版 | 旗舰版 | 企业版 |
|------|--------|--------|--------|--------|--------|
| 创建 WPS | ✅ | ✅ | ✅ | ✅ | ✅ |
| 编辑 WPS | ✅ | ✅ | ✅ | ✅ | ✅ |
| 删除 WPS | ✅ | ✅ | ✅ | ✅ | ✅ |
| 查看 WPS | ✅ | ✅ | ✅ | ✅ | ✅ |
| 导出 PDF | ❌ | ✅ | ✅ | ✅ | ✅ |
| 导出 Excel | ❌ | ✅ | ✅ | ✅ | ✅ |
| 批量导入 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 版本控制 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 审批流程 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 模板管理 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 高级搜索 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 批量操作 | ❌ | ❌ | ❌ | ✅ | ✅ |

---

## 📊 功能清单

### 1. WPS 基础管理
- **创建 WPS**: 填写完整的工艺参数表单
- **编辑 WPS**: 修改现有 WPS 记录
- **删除 WPS**: 软删除，支持恢复
- **查看 WPS**: 详细信息展示
- **复制 WPS**: 基于现有 WPS 创建新记录
- **搜索 WPS**: 按编号、标题、状态等搜索
- **筛选 WPS**: 按状态、标准、日期等筛选
- **排序 WPS**: 按创建时间、修改时间等排序

### 2. 版本控制（专业版及以上）
- **版本历史**: 查看所有历史版本
- **版本对比**: 对比不同版本的差异
- **版本回滚**: 恢复到历史版本
- **版本标签**: 为重要版本添加标签

### 3. 审批流程（高级版及以上）
- **提交审批**: 将 WPS 提交审批
- **审批通过**: 审批人批准 WPS
- **审批拒绝**: 审批人拒绝并说明原因
- **审批历史**: 查看审批记录
- **审批通知**: 审批状态变更通知

### 4. 导出功能（专业版及以上）
- **导出 PDF**: 生成标准格式 PDF 文件
- **导出 Excel**: 导出为 Excel 表格
- **批量导出**: 批量导出多个 WPS
- **自定义模板**: 使用自定义导出模板

### 5. 导入功能（专业版及以上）
- **Excel 导入**: 从 Excel 批量导入
- **模板下载**: 下载导入模板
- **数据验证**: 导入前验证数据
- **导入预览**: 预览导入结果

### 6. 模板管理（高级版及以上）
- **创建模板**: 基于现有 WPS 创建模板
- **使用模板**: 从模板快速创建 WPS
- **管理模板**: 编辑、删除模板
- **共享模板**: 企业内共享模板（企业版）

### 7. 关联管理
- **关联 PQR**: 关联支持的 PQR 记录
- **关联焊工**: 关联合格焊工
- **关联设备**: 关联适用设备
- **关联生产任务**: 关联使用该 WPS 的生产任务

### 8. 附件管理
- **上传附件**: 上传相关文件（图纸、照片等）
- **下载附件**: 下载已上传的附件
- **删除附件**: 删除不需要的附件
- **附件预览**: 在线预览图片和 PDF

---

## 🗄️ 数据模型

### WPS 记录表
```sql
CREATE TABLE wps_records (
    -- 主键和基础字段
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    factory_id UUID REFERENCES factories(id) ON DELETE SET NULL,
    
    -- WPS 基本信息
    wps_number VARCHAR(100) NOT NULL,              -- WPS 编号
    title VARCHAR(255) NOT NULL,                   -- 标题
    version VARCHAR(50) DEFAULT '1.0',             -- 版本号
    revision INTEGER DEFAULT 1,                    -- 修订版本号
    status VARCHAR(50) DEFAULT 'draft',            -- 状态: draft, review, approved, archived, obsolete
    priority VARCHAR(20) DEFAULT 'normal',         -- 优先级: low, normal, high, urgent
    
    -- 标准和规范
    standard VARCHAR(100),                         -- 使用的标准 (AWS, ISO, GB等)
    specification_number VARCHAR(100),             -- 规范编号
    pqr_support_uuids JSONB,                      -- 支持的PQR记录UUID列表
    
    -- 焊接工艺参数
    base_material VARCHAR(255),                    -- 母材
    base_material_group VARCHAR(100),              -- 母材组号
    base_material_thickness DECIMAL(8,2),          -- 母材厚度范围
    filler_material VARCHAR(255),                  -- 填充材料
    filler_material_classification VARCHAR(100),   -- 焊材分类
    welding_process VARCHAR(100),                  -- 焊接方法
    welding_process_variant VARCHAR(100),          -- 焊接工艺变体
    joint_type VARCHAR(100),                       -- 接头类型
    joint_design VARCHAR(255),                     -- 接头设计详情
    welding_position VARCHAR(50),                  -- 焊接位置
    welding_position_progression VARCHAR(50),      -- 焊接位置进展
    
    -- 温度参数
    preheat_temp_min DECIMAL(10,2),               -- 预热温度最小值
    preheat_temp_max DECIMAL(10,2),               -- 预热温度最大值
    interpass_temp_min DECIMAL(10,2),             -- 层间温度最小值
    interpass_temp_max DECIMAL(10,2),             -- 层间温度最大值
    post_weld_heat_treatment JSONB,               -- 焊后热处理参数
    
    -- 电气参数
    current_range VARCHAR(50),                     -- 电流范围
    voltage_range VARCHAR(50),                     -- 电压范围
    travel_speed VARCHAR(50),                      -- 行走速度
    heat_input_range VARCHAR(50),                  -- 热输入范围
    
    -- 保护气体
    gas_shield_type VARCHAR(100),                  -- 保护气体类型
    gas_flow_rate DECIMAL(8,2),                   -- 气体流量
    tungsten_electrode_type VARCHAR(100),          -- 钨极类型
    electrode_diameter DECIMAL(6,2),               -- 电极直径
    
    -- 技术信息
    technique_description TEXT,                    -- 工艺描述
    welder_qualification_requirement VARCHAR(255), -- 焊工资质要求
    inspection_requirements JSONB,                 -- 检验要求
    
    -- 附加信息
    notes TEXT,                                    -- 备注
    attachments JSONB,                            -- 附件信息
    tags JSONB,                                   -- 标签
    
    -- 审核和批准信息
    reviewed_by UUID REFERENCES users(id),         -- 审核人
    reviewed_at TIMESTAMP,                         -- 审核时间
    approved_by UUID REFERENCES users(id),         -- 批准人
    approved_at TIMESTAMP,                         -- 批准时间
    effective_date DATE,                           -- 生效日期
    expiry_date DATE,                             -- 过期日期
    
    -- 统计信息
    view_count INTEGER DEFAULT 0,                  -- 查看次数
    download_count INTEGER DEFAULT 0,              -- 下载次数
    last_viewed_at TIMESTAMP,                      -- 最后查看时间
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP,                          -- 软删除
    
    -- 索引
    INDEX idx_user (user_id),
    INDEX idx_company (company_id),
    INDEX idx_factory (factory_id),
    INDEX idx_wps_number (wps_number),
    INDEX idx_status (status),
    INDEX idx_standard (standard),
    INDEX idx_approval (approved_by, approved_at),
    INDEX idx_effective_date (effective_date, expiry_date),
    INDEX idx_deleted (deleted_at)
);
```

### WPS 模板表
```sql
CREATE TABLE wps_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    
    template_name VARCHAR(255) NOT NULL,
    template_description TEXT,
    template_data JSONB NOT NULL,                  -- 模板数据
    is_public BOOLEAN DEFAULT FALSE,               -- 是否公开（企业内）
    usage_count INTEGER DEFAULT 0,                 -- 使用次数
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user (user_id),
    INDEX idx_company (company_id)
);
```

---

## 🔌 API接口

### 1. WPS 列表
```http
GET /api/v1/wps?page=1&page_size=20&status=approved&search=WPS-2025
Authorization: Bearer <token>
```

**查询参数**:
- `page`: 页码，默认1
- `page_size`: 每页数量，默认20
- `status`: 状态筛选
- `search`: 搜索关键词
- `standard`: 标准筛选
- `sort_by`: 排序字段
- `sort_order`: 排序方向 (asc/desc)

**响应**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "wps_number": "WPS-2025-001",
        "title": "碳钢管道焊接工艺",
        "version": "1.0",
        "status": "approved",
        "created_at": "2025-10-16T10:00:00Z"
      }
    ],
    "total": 25,
    "page": 1,
    "page_size": 20,
    "total_pages": 2
  }
}
```

### 2. 创建 WPS
```http
POST /api/v1/wps
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**:
```json
{
  "wps_number": "WPS-2025-001",
  "title": "碳钢管道焊接工艺",
  "standard": "AWS D1.1",
  "base_material": "Q235B",
  "filler_material": "E7018",
  "welding_process": "SMAW",
  "joint_type": "Butt Joint",
  "welding_position": "1G",
  "preheat_temp_min": 50,
  "preheat_temp_max": 100,
  "current_range": "80-120A",
  "voltage_range": "20-25V"
}
```

### 3. 更新 WPS
```http
PUT /api/v1/wps/{id}
Authorization: Bearer <token>
```

### 4. 删除 WPS
```http
DELETE /api/v1/wps/{id}
Authorization: Bearer <token>
```

### 5. 获取 WPS 详情
```http
GET /api/v1/wps/{id}
Authorization: Bearer <token>
```

### 6. 提交审批
```http
POST /api/v1/wps/{id}/submit-approval
Authorization: Bearer <token>
```

### 7. 审批通过
```http
POST /api/v1/wps/{id}/approve
Authorization: Bearer <token>
Content-Type: application/json

{
  "comments": "审批通过"
}
```

### 8. 导出 PDF
```http
GET /api/v1/wps/{id}/export/pdf
Authorization: Bearer <token>
```

### 9. 批量导入
```http
POST /api/v1/wps/import
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <Excel文件>
```

---

## 💼 业务逻辑

### 1. 创建 WPS 逻辑
```python
# app/services/wps_service.py

class WPSService:
    @require_quota("wps_records")
    async def create_wps(
        self,
        wps_data: WPSCreate,
        user_id: UUID,
        db: Session
    ) -> WPSRecord:
        """创建 WPS"""
        
        # 1. 检查配额
        checker = QuotaChecker(db)
        if not checker.check_quota(user, "wps_records"):
            raise HTTPException(403, "WPS 配额已满")
        
        # 2. 生成 WPS 编号（如果未提供）
        if not wps_data.wps_number:
            wps_data.wps_number = self._generate_wps_number(user_id, db)
        
        # 3. 创建记录
        wps = WPSRecord(
            **wps_data.dict(),
            user_id=user_id,
            created_by=user_id,
            status="draft"
        )
        
        db.add(wps)
        db.commit()
        db.refresh(wps)
        
        return wps
```

### 2. 审批流程
```python
async def submit_for_approval(
    self,
    wps_id: UUID,
    user_id: UUID,
    db: Session
) -> WPSRecord:
    """提交审批"""
    
    wps = db.query(WPSRecord).filter(
        WPSRecord.id == wps_id,
        WPSRecord.user_id == user_id
    ).first()
    
    if not wps:
        raise HTTPException(404, "WPS 不存在")
    
    if wps.status != "draft":
        raise HTTPException(400, "只能提交草稿状态的 WPS")
    
    wps.status = "review"
    wps.updated_at = datetime.now()
    
    db.commit()
    
    # 发送审批通知
    await self._send_approval_notification(wps)
    
    return wps
```

### 3. 版本控制
```python
async def create_new_version(
    self,
    wps_id: UUID,
    user_id: UUID,
    db: Session
) -> WPSRecord:
    """创建新版本"""
    
    original = db.query(WPSRecord).filter(
        WPSRecord.id == wps_id,
        WPSRecord.user_id == user_id
    ).first()
    
    # 复制原记录
    new_wps = WPSRecord(**original.__dict__)
    new_wps.id = None
    new_wps.revision = original.revision + 1
    new_wps.version = f"{original.version}.{new_wps.revision}"
    new_wps.status = "draft"
    new_wps.created_at = datetime.now()
    
    db.add(new_wps)
    db.commit()
    
    return new_wps
```

---

## 🔐 权限控制

### 1. 数据隔离
```python
def get_wps_list(
    self,
    user_id: UUID,
    company_id: Optional[UUID],
    filters: Dict,
    db: Session
) -> List[WPSRecord]:
    """获取 WPS 列表（自动数据隔离）"""
    
    query = db.query(WPSRecord).filter(
        WPSRecord.user_id == user_id,
        WPSRecord.deleted_at.is_(None)
    )
    
    # 企业会员可以查看企业数据
    if company_id:
        query = query.filter(
            or_(
                WPSRecord.user_id == user_id,
                WPSRecord.company_id == company_id
            )
        )
    
    return query.all()
```

### 2. 操作权限
```python
@router.post("/wps/{id}/approve")
@require_feature("approval_workflow")  # 需要高级版及以上
async def approve_wps(
    wps_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """审批 WPS"""
    service = WPSService(db)
    return await service.approve_wps(wps_id, current_user.id, db)
```

---

## 🎨 前端界面

### WPS 列表页面
```typescript
// src/pages/WPS/List.tsx

const WPSList: React.FC = () => {
  const [wps, setWPS] = useState<WPS[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({});
  
  const columns = [
    { title: 'WPS编号', dataIndex: 'wps_number', key: 'wps_number' },
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '版本', dataIndex: 'version', key: 'version' },
    { title: '状态', dataIndex: 'status', key: 'status', render: renderStatus },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
    { title: '操作', key: 'actions', render: renderActions }
  ];
  
  return (
    <div>
      <WPSFilters onChange={setFilters} />
      <Table 
        columns={columns} 
        dataSource={wps} 
        loading={loading}
        pagination={{ pageSize: 20 }}
      />
    </div>
  );
};
```

---

**文档版本**: 1.0  
**最后更新**: 2025-10-16  
**开发状态**: 待开发

