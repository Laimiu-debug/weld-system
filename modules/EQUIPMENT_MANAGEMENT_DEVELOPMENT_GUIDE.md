# 设备管理模块 - 开发指南

## 📋 模块概述

### 功能定位
设备管理模块用于管理焊接设备的基本信息、维护保养、使用记录和设备状态监控，确保设备正常运行。

### 适用场景
- 焊接设备档案管理
- 设备维护保养计划
- 设备使用记录
- 设备状态监控
- 设备故障管理
- 设备检定校准

### 开发优先级
**第二阶段** - 重要功能，优先开发

---

## 🎯 会员权限

### 访问权限
| 会员等级 | 访问权限 | 数量限制 | 功能范围 |
|---------|---------|---------|---------|
| 游客模式 | ❌ 不可访问 | 0 | - |
| 个人免费版 | ❌ 不可访问 | 0 | - |
| 个人专业版 | ❌ 不可访问 | 0 | - |
| 个人高级版 | ✅ 可访问 | 无限制 | 完整功能 |
| 个人旗舰版 | ✅ 可访问 | 无限制 | 完整功能 + 高级特性 |
| 企业版 | ✅ 可访问 | 无限制 | 完整功能 + 企业协作 |
| 企业PRO | ✅ 可访问 | 无限制 | 完整功能 + 企业协作 |
| 企业PRO MAX | ✅ 可访问 | 无限制 | 完整功能 + 企业协作 |

**重要说明**: 设备管理功能仅对**个人高级版及以上**会员开放。

### 功能权限矩阵
| 功能 | 免费版 | 专业版 | 高级版 | 旗舰版 | 企业版 |
|------|--------|--------|--------|--------|--------|
| 设备基础管理 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 维护保养管理 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 使用记录 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 故障管理 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 检定校准 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 维护提醒 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 统计报表 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 设备监控 | ❌ | ❌ | ❌ | ✅ | ✅ |

---

## 📊 功能清单

### 1. 设备基础管理
- **添加设备**: 录入设备基本信息
- **编辑设备**: 修改设备信息
- **删除设备**: 软删除设备记录
- **查看设备**: 查看设备详细信息
- **设备档案**: 完整的设备档案
- **设备分类**: 按设备类型分类

### 2. 维护保养管理
- **维护计划**: 制定维护保养计划
- **维护记录**: 记录维护保养情况
- **维护提醒**: 到期提醒维护
- **维护历史**: 查看维护历史
- **维护成本**: 记录维护成本
- **预防性维护**: 预防性维护管理

### 3. 使用记录
- **使用登记**: 记录设备使用情况
- **使用时长**: 统计设备使用时长
- **使用人员**: 记录使用人员
- **关联生产任务**: 关联使用的生产任务
- **使用统计**: 设备使用统计分析

### 4. 故障管理
- **故障报告**: 记录设备故障
- **故障处理**: 记录故障处理过程
- **故障分析**: 故障原因分析
- **故障统计**: 故障率统计
- **停机时间**: 统计停机时间

### 5. 检定校准
- **检定记录**: 记录设备检定情况
- **校准记录**: 记录设备校准情况
- **检定证书**: 上传检定证书
- **检定提醒**: 到期提醒检定
- **检定历史**: 查看检定历史

### 6. 设备状态监控
- **运行状态**: 实时设备状态
- **状态变更**: 记录状态变更
- **设备利用率**: 计算设备利用率
- **设备效率**: 分析设备效率

### 7. 统计分析
- **设备统计**: 按状态、类型统计
- **维护统计**: 维护次数、成本统计
- **故障统计**: 故障率、停机时间统计
- **使用统计**: 使用时长、利用率统计

---

## 🗄️ 数据模型

### 设备基本信息表
```sql
CREATE TABLE equipment (
    -- 主键和基础字段
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    factory_id UUID REFERENCES factories(id) ON DELETE SET NULL,
    
    -- 基本信息
    equipment_code VARCHAR(100) NOT NULL,          -- 设备编号
    equipment_name VARCHAR(255) NOT NULL,          -- 设备名称
    equipment_type VARCHAR(100),                   -- 设备类型: welding_machine, cutting_machine, etc.
    model VARCHAR(100),                            -- 型号
    manufacturer VARCHAR(255),                     -- 制造商
    serial_number VARCHAR(100),                    -- 序列号
    
    -- 技术参数
    rated_power DECIMAL(10,2),                    -- 额定功率 (kW)
    rated_current DECIMAL(10,2),                  -- 额定电流 (A)
    rated_voltage DECIMAL(10,2),                  -- 额定电压 (V)
    welding_process VARCHAR(100),                  -- 适用焊接方法
    technical_specs JSONB,                         -- 技术规格
    
    -- 采购信息
    purchase_date DATE,                            -- 采购日期
    purchase_price DECIMAL(15,2),                 -- 采购价格
    supplier VARCHAR(255),                         -- 供应商
    warranty_period INTEGER,                       -- 保修期（月）
    warranty_expiry_date DATE,                     -- 保修到期日期
    
    -- 状态信息
    status VARCHAR(50) DEFAULT 'operational',      -- 状态: operational, maintenance, fault, retired
    location VARCHAR(255),                         -- 存放位置
    responsible_person_id UUID REFERENCES users(id), -- 责任人
    
    -- 维护信息
    last_maintenance_date DATE,                    -- 上次维护日期
    next_maintenance_date DATE,                    -- 下次维护日期
    maintenance_interval_days INTEGER DEFAULT 90, -- 维护间隔（天）
    
    -- 检定信息
    last_calibration_date DATE,                    -- 上次检定日期
    next_calibration_date DATE,                    -- 下次检定日期
    calibration_interval_days INTEGER DEFAULT 365, -- 检定间隔（天）
    calibration_certificate JSONB,                 -- 检定证书
    
    -- 统计信息
    total_usage_hours DECIMAL(12,2) DEFAULT 0,    -- 总使用时长（小时）
    total_maintenance_count INTEGER DEFAULT 0,     -- 总维护次数
    total_fault_count INTEGER DEFAULT 0,           -- 总故障次数
    
    -- 附件
    photos JSONB,                                  -- 设备照片
    manuals JSONB,                                 -- 使用手册
    attachments JSONB,                             -- 其他附件
    
    -- 备注
    notes TEXT,
    tags JSONB,
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP,
    
    -- 索引
    INDEX idx_user (user_id),
    INDEX idx_company (company_id),
    INDEX idx_factory (factory_id),
    INDEX idx_equipment_code (equipment_code),
    INDEX idx_equipment_type (equipment_type),
    INDEX idx_status (status),
    INDEX idx_next_maintenance (next_maintenance_date),
    INDEX idx_next_calibration (next_calibration_date),
    INDEX idx_deleted (deleted_at),
    
    UNIQUE (user_id, equipment_code)
);
```

### 设备维护记录表
```sql
CREATE TABLE equipment_maintenance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 维护信息
    maintenance_type VARCHAR(50),                  -- 维护类型: routine, preventive, corrective
    maintenance_date DATE NOT NULL,                -- 维护日期
    maintenance_description TEXT,                  -- 维护内容
    
    -- 维护人员
    technician_id UUID REFERENCES users(id),       -- 维护人员
    technician_name VARCHAR(100),                  -- 维护人员姓名
    
    -- 维护结果
    maintenance_result VARCHAR(50),                -- 维护结果: completed, pending, failed
    issues_found TEXT,                             -- 发现的问题
    actions_taken TEXT,                            -- 采取的措施
    
    -- 成本
    labor_cost DECIMAL(12,2),                     -- 人工成本
    parts_cost DECIMAL(12,2),                     -- 配件成本
    total_cost DECIMAL(12,2),                     -- 总成本
    
    -- 停机时间
    downtime_hours DECIMAL(8,2),                  -- 停机时长（小时）
    
    -- 下次维护
    next_maintenance_date DATE,                    -- 下次维护日期
    
    -- 附件
    maintenance_photos JSONB,                      -- 维护照片
    maintenance_report JSONB,                      -- 维护报告
    
    -- 备注
    notes TEXT,
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    
    -- 索引
    INDEX idx_equipment (equipment_id),
    INDEX idx_user (user_id),
    INDEX idx_maintenance_date (maintenance_date),
    INDEX idx_maintenance_type (maintenance_type)
);
```

### 设备使用记录表
```sql
CREATE TABLE equipment_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 使用信息
    usage_date DATE NOT NULL,                      -- 使用日期
    start_time TIMESTAMP,                          -- 开始时间
    end_time TIMESTAMP,                            -- 结束时间
    usage_hours DECIMAL(8,2),                     -- 使用时长（小时）
    
    -- 使用人员
    operator_id UUID REFERENCES users(id),         -- 操作人员
    operator_name VARCHAR(100),                    -- 操作人员姓名
    
    -- 关联信息
    production_task_id UUID REFERENCES production_tasks(id),
    wps_id UUID REFERENCES wps_records(id),
    
    -- 使用情况
    usage_description TEXT,                        -- 使用说明
    equipment_condition VARCHAR(50),               -- 设备状况: good, normal, poor
    
    -- 备注
    notes TEXT,
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    
    -- 索引
    INDEX idx_equipment (equipment_id),
    INDEX idx_user (user_id),
    INDEX idx_usage_date (usage_date),
    INDEX idx_operator (operator_id),
    INDEX idx_production_task (production_task_id)
);
```

---

## 🔌 API接口

### 1. 设备列表
```http
GET /api/v1/equipment?page=1&page_size=20&status=operational
Authorization: Bearer <token>
```

### 2. 创建设备
```http
POST /api/v1/equipment
Authorization: Bearer <token>
Content-Type: application/json

{
  "equipment_code": "EQ-2025-001",
  "equipment_name": "焊接机器人",
  "equipment_type": "welding_machine",
  "model": "ABB IRB 1600",
  "manufacturer": "ABB",
  "purchase_date": "2025-01-01",
  "maintenance_interval_days": 90
}
```

### 3. 添加维护记录
```http
POST /api/v1/equipment/{id}/maintenance
Authorization: Bearer <token>
Content-Type: application/json

{
  "maintenance_type": "routine",
  "maintenance_date": "2025-10-15",
  "maintenance_description": "定期保养",
  "technician_id": "uuid",
  "total_cost": 500,
  "next_maintenance_date": "2026-01-15"
}
```

### 4. 获取维护提醒
```http
GET /api/v1/equipment/maintenance-alerts?days=30
Authorization: Bearer <token>
```

### 5. 设备统计
```http
GET /api/v1/equipment/statistics
Authorization: Bearer <token>
```

---

## 💼 业务逻辑

### 1. 维护提醒检查
```python
class EquipmentService:
    def get_maintenance_alerts(
        self,
        user_id: UUID,
        days: int,
        db: Session
    ) -> List[Equipment]:
        """获取需要维护的设备"""
        
        alert_date = date.today() + timedelta(days=days)
        
        equipment_list = db.query(Equipment).filter(
            Equipment.user_id == user_id,
            Equipment.status == "operational",
            Equipment.next_maintenance_date <= alert_date,
            Equipment.next_maintenance_date >= date.today(),
            Equipment.deleted_at.is_(None)
        ).all()
        
        return equipment_list
```

### 2. 使用时长统计
```python
def record_usage(
    self,
    equipment_id: UUID,
    usage_data: EquipmentUsage,
    user_id: UUID,
    db: Session
) -> Equipment:
    """记录设备使用"""
    
    equipment = db.query(Equipment).filter(
        Equipment.id == equipment_id,
        Equipment.user_id == user_id
    ).first()
    
    if not equipment:
        raise HTTPException(404, "设备不存在")
    
    # 计算使用时长
    if usage_data.start_time and usage_data.end_time:
        duration = (usage_data.end_time - usage_data.start_time).total_seconds() / 3600
        usage_data.usage_hours = round(duration, 2)
    
    # 创建使用记录
    usage = EquipmentUsage(
        **usage_data.dict(),
        equipment_id=equipment_id,
        user_id=user_id,
        created_by=user_id
    )
    
    db.add(usage)
    
    # 更新设备总使用时长
    equipment.total_usage_hours += usage_data.usage_hours
    equipment.updated_at = datetime.now()
    
    db.commit()
    
    return equipment
```

---

## 🔐 权限控制

```python
@router.get("/equipment")
@require_feature("equipment_management")  # 需要高级版及以上
async def get_equipment_list(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取设备列表"""
    service = EquipmentService(db)
    return service.get_equipment_list(current_user.id, db)
```

---

## 🎨 前端界面

### 设备列表页面
```typescript
// src/pages/Equipment/List.tsx

const EquipmentList: React.FC = () => {
  const { data, loading } = useEquipment();
  
  const columns = [
    { title: '设备编号', dataIndex: 'equipment_code' },
    { title: '设备名称', dataIndex: 'equipment_name' },
    { title: '型号', dataIndex: 'model' },
    { title: '状态', dataIndex: 'status', render: renderStatus },
    { title: '下次维护', dataIndex: 'next_maintenance_date' },
    { title: '操作', render: renderActions }
  ];
  
  return (
    <div>
      <Table columns={columns} dataSource={data} loading={loading} />
    </div>
  );
};
```

---

**文档版本**: 1.0  
**最后更新**: 2025-10-16  
**开发状态**: 已实现（需测试）

