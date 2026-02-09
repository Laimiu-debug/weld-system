# 质量管理模块 - 开发指南

## 📋 模块概述

### 功能定位
质量管理模块用于管理焊接质量检验、不合格品处理、质量统计分析，确保焊接质量符合标准要求。

### 适用场景
- 质量检验计划和执行
- 检验结果记录
- 不合格品管理
- 质量问题追溯
- 质量统计分析
- 质量改进措施

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

**重要说明**: 质量管理功能仅对**个人高级版及以上**会员开放。

---

## 📊 功能清单

### 1. 质量检验管理
- **创建检验**: 创建质量检验计划
- **执行检验**: 记录检验结果
- **检验报告**: 生成检验报告
- **检验历史**: 查看检验历史
- **检验统计**: 统计检验数据

### 2. 检验类型
- **外观检验**: 焊缝外观质量检验
- **尺寸检验**: 焊缝尺寸测量
- **无损检测**: RT、UT、MT、PT 等
- **力学性能**: 拉伸、弯曲、冲击等
- **其他检验**: 自定义检验项目

### 3. 不合格品管理
- **不合格登记**: 记录不合格品
- **原因分析**: 分析不合格原因
- **处理措施**: 记录处理措施
- **返工记录**: 记录返工情况
- **报废记录**: 记录报废情况

### 4. 质量追溯
- **关联生产任务**: 追溯到生产任务
- **关联焊工**: 追溯到焊工
- **关联 WPS**: 追溯到使用的 WPS
- **关联焊材**: 追溯到使用的焊材
- **关联设备**: 追溯到使用的设备

### 5. 质量统计
- **合格率统计**: 统计合格率
- **缺陷统计**: 统计缺陷类型和数量
- **趋势分析**: 分析质量趋势
- **对比分析**: 对比不同时期质量

### 6. 质量改进
- **改进措施**: 记录改进措施
- **效果跟踪**: 跟踪改进效果
- **经验总结**: 总结质量经验
- **知识库**: 建立质量知识库

---

## 🗄️ 数据模型

### 质量检验表
```sql
CREATE TABLE quality_inspections (
    -- 主键和基础字段
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    factory_id UUID REFERENCES factories(id) ON DELETE SET NULL,
    
    -- 检验基本信息
    inspection_number VARCHAR(100) NOT NULL,       -- 检验编号
    inspection_type VARCHAR(50),                   -- 检验类型: visual, dimensional, ndt, mechanical
    inspection_date DATE NOT NULL,                 -- 检验日期
    inspection_standard VARCHAR(100),              -- 检验标准
    
    -- 关联信息
    production_task_id UUID REFERENCES production_tasks(id),
    wps_id UUID REFERENCES wps_records(id),
    welder_id UUID REFERENCES welders(id),
    
    -- 检验项目
    inspection_items JSONB,                        -- 检验项目列表
    
    -- 检验结果
    result VARCHAR(50) DEFAULT 'pending',          -- 结果: pass, fail, conditional_pass, pending
    overall_rating VARCHAR(20),                    -- 总体评级: excellent, good, acceptable, poor
    
    -- 合格判定
    acceptance_criteria TEXT,                      -- 验收标准
    is_qualified BOOLEAN,                          -- 是否合格
    
    -- 缺陷记录
    defects_found JSONB,                          -- 发现的缺陷
    defect_count INTEGER DEFAULT 0,                -- 缺陷数量
    defect_severity VARCHAR(20),                   -- 缺陷严重程度: minor, major, critical
    
    -- 测量数据
    measurements JSONB,                            -- 测量数据
    
    -- 无损检测结果
    ndt_results JSONB,                            -- 无损检测结果
    rt_result VARCHAR(50),                        -- 射线检测结果
    ut_result VARCHAR(50),                        -- 超声检测结果
    mt_result VARCHAR(50),                        -- 磁粉检测结果
    pt_result VARCHAR(50),                        -- 渗透检测结果
    
    -- 检验人员
    inspector_id UUID REFERENCES users(id),        -- 检验员
    inspector_name VARCHAR(100),                   -- 检验员姓名
    witness_id UUID REFERENCES users(id),          -- 见证人
    
    -- 处理信息
    disposition VARCHAR(50),                       -- 处置: accept, rework, repair, scrap
    corrective_action TEXT,                        -- 纠正措施
    rework_required BOOLEAN DEFAULT FALSE,         -- 是否需要返工
    
    -- 附件
    inspection_photos JSONB,                       -- 检验照片
    inspection_reports JSONB,                      -- 检验报告
    ndt_films JSONB,                              -- 射线底片
    
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
    INDEX idx_inspection_number (inspection_number),
    INDEX idx_inspection_type (inspection_type),
    INDEX idx_inspection_date (inspection_date),
    INDEX idx_result (result),
    INDEX idx_production_task (production_task_id),
    INDEX idx_welder (welder_id),
    INDEX idx_inspector (inspector_id),
    INDEX idx_deleted (deleted_at),
    
    UNIQUE (user_id, inspection_number)
);
```

### 不合格品记录表
```sql
CREATE TABLE nonconformance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inspection_id UUID REFERENCES quality_inspections(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 不合格信息
    ncr_number VARCHAR(100) NOT NULL,              -- 不合格品编号
    ncr_date DATE NOT NULL,                        -- 记录日期
    severity VARCHAR(20),                          -- 严重程度: minor, major, critical
    
    -- 不合格描述
    defect_description TEXT,                       -- 缺陷描述
    defect_type VARCHAR(100),                      -- 缺陷类型
    defect_location TEXT,                          -- 缺陷位置
    quantity_affected INTEGER,                     -- 影响数量
    
    -- 原因分析
    root_cause TEXT,                               -- 根本原因
    contributing_factors TEXT,                     -- 影响因素
    
    -- 责任方
    responsible_party VARCHAR(100),                -- 责任方
    responsible_person_id UUID REFERENCES users(id),
    
    -- 处理措施
    disposition VARCHAR(50),                       -- 处置方式: rework, repair, use_as_is, scrap
    corrective_action TEXT,                        -- 纠正措施
    preventive_action TEXT,                        -- 预防措施
    
    -- 返工信息
    rework_date DATE,                              -- 返工日期
    rework_by UUID REFERENCES users(id),           -- 返工人
    rework_result VARCHAR(50),                     -- 返工结果
    
    -- 验证
    verification_date DATE,                        -- 验证日期
    verified_by UUID REFERENCES users(id),         -- 验证人
    is_closed BOOLEAN DEFAULT FALSE,               -- 是否关闭
    
    -- 成本
    cost_impact DECIMAL(12,2),                    -- 成本影响
    
    -- 附件
    photos JSONB,
    documents JSONB,
    
    -- 备注
    notes TEXT,
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    
    -- 索引
    INDEX idx_inspection (inspection_id),
    INDEX idx_user (user_id),
    INDEX idx_ncr_number (ncr_number),
    INDEX idx_ncr_date (ncr_date),
    INDEX idx_severity (severity),
    INDEX idx_disposition (disposition),
    INDEX idx_is_closed (is_closed)
);
```

---

## 🔌 API接口

### 1. 检验列表
```http
GET /api/v1/quality/inspections?page=1&page_size=20&result=pass
Authorization: Bearer <token>
```

### 2. 创建检验
```http
POST /api/v1/quality/inspections
Authorization: Bearer <token>
Content-Type: application/json

{
  "inspection_number": "QI-2025-001",
  "inspection_type": "visual",
  "inspection_date": "2025-10-16",
  "production_task_id": "uuid",
  "inspector_id": "uuid",
  "inspection_items": [
    {
      "item": "焊缝外观",
      "requirement": "无裂纹、气孔",
      "result": "合格"
    }
  ]
}
```

### 3. 记录检验结果
```http
PUT /api/v1/quality/inspections/{id}/result
Authorization: Bearer <token>
Content-Type: application/json

{
  "result": "pass",
  "is_qualified": true,
  "defects_found": [],
  "notes": "检验合格"
}
```

### 4. 创建不合格品记录
```http
POST /api/v1/quality/nonconformance
Authorization: Bearer <token>
Content-Type: application/json

{
  "inspection_id": "uuid",
  "ncr_number": "NCR-2025-001",
  "ncr_date": "2025-10-16",
  "severity": "major",
  "defect_description": "焊缝存在气孔",
  "disposition": "rework",
  "corrective_action": "重新焊接"
}
```

### 5. 质量统计
```http
GET /api/v1/quality/statistics?start_date=2025-09-01&end_date=2025-10-16
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total_inspections": 100,
    "passed": 95,
    "failed": 5,
    "pass_rate": 95.0,
    "defect_types": {
      "气孔": 3,
      "裂纹": 1,
      "未焊透": 1
    },
    "trend": [
      {"date": "2025-09-01", "pass_rate": 94.5},
      {"date": "2025-09-08", "pass_rate": 95.2}
    ]
  }
}
```

---

## 💼 业务逻辑

### 1. 检验结果判定
```python
class QualityService:
    def record_inspection_result(
        self,
        inspection_id: UUID,
        result_data: InspectionResult,
        user_id: UUID,
        db: Session
    ) -> QualityInspection:
        """记录检验结果"""
        
        inspection = db.query(QualityInspection).filter(
            QualityInspection.id == inspection_id,
            QualityInspection.user_id == user_id
        ).first()
        
        if not inspection:
            raise HTTPException(404, "检验记录不存在")
        
        # 更新检验结果
        inspection.result = result_data.result
        inspection.is_qualified = result_data.is_qualified
        inspection.defects_found = result_data.defects_found
        inspection.defect_count = len(result_data.defects_found) if result_data.defects_found else 0
        
        # 如果不合格，自动创建不合格品记录
        if not result_data.is_qualified:
            self._create_nonconformance_record(inspection, db)
        
        inspection.updated_at = datetime.now()
        db.commit()
        
        return inspection
```

### 2. 质量统计
```python
def get_quality_statistics(
    self,
    user_id: UUID,
    start_date: date,
    end_date: date,
    db: Session
) -> Dict[str, Any]:
    """获取质量统计数据"""
    
    inspections = db.query(QualityInspection).filter(
        QualityInspection.user_id == user_id,
        QualityInspection.inspection_date >= start_date,
        QualityInspection.inspection_date <= end_date,
        QualityInspection.deleted_at.is_(None)
    ).all()
    
    total = len(inspections)
    passed = len([i for i in inspections if i.result == "pass"])
    failed = len([i for i in inspections if i.result == "fail"])
    
    # 统计缺陷类型
    defect_types = {}
    for inspection in inspections:
        if inspection.defects_found:
            for defect in inspection.defects_found:
                defect_type = defect.get("type", "未知")
                defect_types[defect_type] = defect_types.get(defect_type, 0) + 1
    
    return {
        "total_inspections": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / total * 100, 2) if total > 0 else 0,
        "defect_types": defect_types
    }
```

---

## 🔐 权限控制

```python
@router.get("/quality/inspections")
@require_feature("quality_management")  # 需要高级版及以上
async def get_inspection_list(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取质量检验列表"""
    service = QualityService(db)
    return service.get_inspection_list(current_user.id, db)
```

---

## 🎨 前端界面

### 质量检验列表
```typescript
// src/pages/Quality/InspectionList.tsx

const InspectionList: React.FC = () => {
  const { data, loading } = useInspections();
  
  const columns = [
    { title: '检验编号', dataIndex: 'inspection_number' },
    { title: '检验类型', dataIndex: 'inspection_type' },
    { title: '检验日期', dataIndex: 'inspection_date' },
    { title: '结果', dataIndex: 'result', render: renderResult },
    { title: '缺陷数', dataIndex: 'defect_count' },
    { title: '操作', render: renderActions }
  ];
  
  return (
    <div>
      <Statistic title="合格率" value={passRate} suffix="%" />
      <Table columns={columns} dataSource={data} loading={loading} />
    </div>
  );
};
```

---

**文档版本**: 1.0  
**最后更新**: 2025-10-16  
**开发状态**: 已实现（需测试）

