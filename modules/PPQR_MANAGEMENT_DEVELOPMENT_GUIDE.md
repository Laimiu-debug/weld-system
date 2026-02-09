# pPQR管理模块 - 开发指南

## 📋 模块概述

### 功能定位
pPQR (Preliminary Procedure Qualification Record) 管理模块用于管理预备工艺评定记录，是正式 PQR 之前的试验性评定，用于工艺开发和优化。

### 适用场景
- 新工艺开发前的预备试验
- 工艺参数优化和调整
- 快速验证工艺可行性
- 为正式 PQR 提供参考
- 工艺研发记录管理

### 开发优先级
**第二阶段** - 重要功能，优先开发

---

## 🎯 会员权限

### 访问权限
| 会员等级 | 访问权限 | 数量限制 | 功能范围 |
|---------|---------|---------|---------|
| 游客模式 | ❌ 不可访问 | 0 | - |
| 个人免费版 | ❌ 不可访问 | 0 | - |
| 个人专业版 | ✅ 可访问 | 最多 30 个 | 基础增删改查 + 导出 |
| 个人高级版 | ✅ 可访问 | 最多 50 个 | 完整功能 + 试验管理 |
| 个人旗舰版 | ✅ 可访问 | 最多 100 个 | 完整功能 + 高级特性 |
| 企业版 | ✅ 可访问 | 最多 200 个 | 完整功能 + 企业协作 |
| 企业PRO | ✅ 可访问 | 最多 400 个 | 完整功能 + 企业协作 |
| 企业PRO MAX | ✅ 可访问 | 最多 500 个 | 完整功能 + 企业协作 |

**重要说明**: pPQR 功能仅对**个人专业版及以上**会员开放，免费版和游客模式不可访问。

### 功能权限矩阵
| 功能 | 免费版 | 专业版 | 高级版 | 旗舰版 | 企业版 |
|------|--------|--------|--------|--------|--------|
| 创建 pPQR | ❌ | ✅ | ✅ | ✅ | ✅ |
| 编辑 pPQR | ❌ | ✅ | ✅ | ✅ | ✅ |
| 删除 pPQR | ❌ | ✅ | ✅ | ✅ | ✅ |
| 查看 pPQR | ❌ | ✅ | ✅ | ✅ | ✅ |
| 导出报告 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 试验数据管理 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 转换为 PQR | ❌ | ❌ | ✅ | ✅ | ✅ |
| 参数对比分析 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 批量试验 | ❌ | ❌ | ❌ | ✅ | ✅ |

---

## 📊 功能清单

### 1. pPQR 基础管理
- **创建 pPQR**: 填写预备评定记录
- **编辑 pPQR**: 修改 pPQR 数据
- **删除 pPQR**: 软删除 pPQR
- **查看 pPQR**: 详细信息展示
- **复制 pPQR**: 基于现有 pPQR 创建新记录
- **搜索 pPQR**: 按编号、目的、状态搜索
- **筛选 pPQR**: 按试验结果、日期等筛选

### 2. 试验参数记录
- **试验目的**: 记录试验目的和预期目标
- **试验方案**: 记录试验方案和步骤
- **参数设置**: 记录计划使用的参数
- **实际参数**: 记录实际使用的参数
- **参数调整**: 记录参数调整过程
- **多组试验**: 支持记录多组对比试验

### 3. 试验结果记录
- **外观检查**: 记录焊缝外观质量
- **尺寸测量**: 记录焊缝尺寸数据
- **简易测试**: 记录简单的力学测试
- **缺陷记录**: 记录发现的缺陷
- **试验照片**: 上传试验过程照片
- **试验视频**: 上传试验视频（旗舰版）

### 4. 参数优化（高级版及以上）
- **参数对比**: 对比不同参数组的结果
- **趋势分析**: 分析参数变化趋势
- **最优参数**: 标记最优参数组合
- **优化建议**: 系统给出优化建议

### 5. 转换功能（高级版及以上）
- **转换为 PQR**: 将成功的 pPQR 转换为正式 PQR
- **数据迁移**: 自动迁移相关数据
- **补充信息**: 补充 PQR 所需的额外信息
- **关联保持**: 保持与原 pPQR 的关联

### 6. 协作功能（企业版）
- **团队共享**: 与团队成员共享 pPQR
- **评论讨论**: 团队成员可以评论
- **版本对比**: 对比不同人员的试验结果
- **知识积累**: 形成企业工艺知识库

### 7. 导出功能
- **导出 PDF**: 生成试验报告
- **导出 Excel**: 导出试验数据
- **导出对比报告**: 导出参数对比分析报告
- **批量导出**: 批量导出多个 pPQR

---

## 🗄️ 数据模型

### pPQR 记录表
```sql
CREATE TABLE ppqr_records (
    -- 主键和基础字段
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    factory_id UUID REFERENCES factories(id) ON DELETE SET NULL,
    
    -- pPQR 基本信息
    ppqr_number VARCHAR(100) NOT NULL,             -- pPQR 编号
    title VARCHAR(255) NOT NULL,                   -- 标题
    test_date DATE,                                -- 试验日期
    status VARCHAR(50) DEFAULT 'draft',            -- 状态: draft, testing, completed, converted
    purpose TEXT,                                  -- 试验目的
    test_plan TEXT,                                -- 试验方案
    
    -- 试验参数（计划）
    planned_parameters JSONB,                      -- 计划参数
    
    -- 焊接工艺参数（实际使用）
    base_material VARCHAR(255),                    -- 母材
    base_material_thickness DECIMAL(8,2),          -- 母材厚度
    filler_material VARCHAR(255),                  -- 填充材料
    welding_process VARCHAR(100),                  -- 焊接方法
    joint_type VARCHAR(100),                       -- 接头类型
    welding_position VARCHAR(50),                  -- 焊接位置
    
    -- 实际参数
    actual_parameters JSONB,                       -- 实际参数
    parameter_adjustments JSONB,                   -- 参数调整记录
    
    -- 温度参数
    preheat_temp DECIMAL(10,2),                   -- 预热温度
    interpass_temp DECIMAL(10,2),                 -- 层间温度
    
    -- 电气参数
    welding_current DECIMAL(10,2),                -- 焊接电流
    welding_voltage DECIMAL(10,2),                -- 焊接电压
    travel_speed DECIMAL(10,2),                   -- 行走速度
    heat_input DECIMAL(10,2),                     -- 热输入
    
    -- 试验结果
    visual_inspection JSONB,                       -- 外观检查结果
    dimension_measurements JSONB,                  -- 尺寸测量结果
    simple_tests JSONB,                           -- 简易测试结果
    defects_found JSONB,                          -- 发现的缺陷
    
    -- 试验评价
    is_successful BOOLEAN,                         -- 是否成功
    success_criteria TEXT,                         -- 成功标准
    evaluation_notes TEXT,                         -- 评价说明
    improvement_suggestions TEXT,                  -- 改进建议
    
    -- 试验人员
    welder_id UUID REFERENCES welders(id),         -- 焊工
    tester_id UUID REFERENCES users(id),           -- 试验人员
    
    -- 多组试验
    test_group_number INTEGER DEFAULT 1,           -- 试验组号
    parent_ppqr_id UUID REFERENCES ppqr_records(id), -- 父 pPQR（用于对比试验）
    
    -- 转换信息
    converted_to_pqr_id UUID REFERENCES pqr_records(id), -- 转换后的 PQR ID
    converted_at TIMESTAMP,                        -- 转换时间
    converted_by UUID REFERENCES users(id),        -- 转换人
    
    -- 附件
    test_photos JSONB,                            -- 试验照片
    test_videos JSONB,                            -- 试验视频
    attachments JSONB,                            -- 其他附件
    
    -- 协作
    shared_with JSONB,                            -- 共享给的用户列表
    comments JSONB,                               -- 评论列表
    
    -- 备注
    notes TEXT,                                    -- 备注
    tags JSONB,                                   -- 标签
    
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
    INDEX idx_ppqr_number (ppqr_number),
    INDEX idx_status (status),
    INDEX idx_test_date (test_date),
    INDEX idx_welder (welder_id),
    INDEX idx_parent (parent_ppqr_id),
    INDEX idx_converted (converted_to_pqr_id),
    INDEX idx_deleted (deleted_at)
);
```

### pPQR 参数对比表
```sql
CREATE TABLE ppqr_parameter_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    comparison_name VARCHAR(255),                  -- 对比名称
    ppqr_ids JSONB NOT NULL,                      -- 参与对比的 pPQR ID 列表
    comparison_results JSONB,                      -- 对比结果
    best_parameters JSONB,                         -- 最优参数
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user (user_id)
);
```

---

## 🔌 API接口

### 1. pPQR 列表
```http
GET /api/v1/ppqr?page=1&page_size=20&status=completed
Authorization: Bearer <token>
```

### 2. 创建 pPQR
```http
POST /api/v1/ppqr
Authorization: Bearer <token>
Content-Type: application/json

{
  "ppqr_number": "pPQR-2025-001",
  "title": "Q235B 新工艺预备试验",
  "test_date": "2025-10-15",
  "purpose": "验证新的焊接参数组合",
  "base_material": "Q235B",
  "filler_material": "E7018",
  "welding_process": "SMAW",
  "planned_parameters": {
    "current": "100-120A",
    "voltage": "22-25V"
  }
}
```

### 3. 更新试验结果
```http
PUT /api/v1/ppqr/{id}/results
Authorization: Bearer <token>
Content-Type: application/json

{
  "actual_parameters": {
    "current": 110,
    "voltage": 23
  },
  "visual_inspection": {
    "appearance": "良好",
    "defects": []
  },
  "is_successful": true
}
```

### 4. 转换为 PQR（高级版及以上）
```http
POST /api/v1/ppqr/{id}/convert-to-pqr
Authorization: Bearer <token>
Content-Type: application/json

{
  "pqr_number": "PQR-2025-001",
  "additional_tests": {
    "tensile_test": true,
    "bend_test": true
  }
}
```

### 5. 参数对比（高级版及以上）
```http
POST /api/v1/ppqr/compare
Authorization: Bearer <token>
Content-Type: application/json

{
  "ppqr_ids": ["uuid1", "uuid2", "uuid3"],
  "comparison_name": "电流参数对比"
}
```

### 6. 共享 pPQR（企业版）
```http
POST /api/v1/ppqr/{id}/share
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_ids": ["uuid1", "uuid2"]
}
```

---

## 💼 业务逻辑

### 1. 创建 pPQR
```python
class PPQRService:
    @require_quota("ppqr_records")
    @require_feature("ppqr_crud")  # 需要专业版及以上
    async def create_ppqr(
        self,
        ppqr_data: PPQRCreate,
        user_id: UUID,
        db: Session
    ) -> PPQRRecord:
        """创建 pPQR"""
        
        # 检查会员等级
        user = db.query(User).filter(User.id == user_id).first()
        if user.membership_tier == "free":
            raise HTTPException(403, "pPQR 功能需要专业版及以上会员")
        
        # 检查配额
        checker = QuotaChecker(db)
        if not checker.check_quota(user, "ppqr_records"):
            raise HTTPException(403, "pPQR 配额已满")
        
        # 生成编号
        if not ppqr_data.ppqr_number:
            ppqr_data.ppqr_number = self._generate_ppqr_number(user_id, db)
        
        # 创建记录
        ppqr = PPQRRecord(
            **ppqr_data.dict(),
            user_id=user_id,
            created_by=user_id,
            status="draft"
        )
        
        db.add(ppqr)
        db.commit()
        
        return ppqr
```

### 2. 转换为 PQR
```python
@require_feature("ppqr_to_pqr_conversion")  # 需要高级版及以上
async def convert_to_pqr(
    self,
    ppqr_id: UUID,
    conversion_data: PPQRConversion,
    user_id: UUID,
    db: Session
) -> PQRRecord:
    """将 pPQR 转换为 PQR"""
    
    ppqr = db.query(PPQRRecord).filter(
        PPQRRecord.id == ppqr_id,
        PPQRRecord.user_id == user_id
    ).first()
    
    if not ppqr:
        raise HTTPException(404, "pPQR 不存在")
    
    if not ppqr.is_successful:
        raise HTTPException(400, "只能转换成功的 pPQR")
    
    # 创建 PQR
    pqr = PQRRecord(
        pqr_number=conversion_data.pqr_number,
        title=ppqr.title,
        base_material=ppqr.base_material,
        filler_material=ppqr.filler_material,
        welding_process=ppqr.welding_process,
        # ... 复制其他字段
        user_id=user_id,
        created_by=user_id,
        status="pending"
    )
    
    db.add(pqr)
    
    # 更新 pPQR
    ppqr.converted_to_pqr_id = pqr.id
    ppqr.converted_at = datetime.now()
    ppqr.converted_by = user_id
    ppqr.status = "converted"
    
    db.commit()
    
    return pqr
```

### 3. 参数对比分析
```python
@require_feature("parameter_comparison")  # 需要高级版及以上
async def compare_parameters(
    self,
    ppqr_ids: List[UUID],
    user_id: UUID,
    db: Session
) -> Dict[str, Any]:
    """对比多个 pPQR 的参数"""
    
    ppqrs = db.query(PPQRRecord).filter(
        PPQRRecord.id.in_(ppqr_ids),
        PPQRRecord.user_id == user_id
    ).all()
    
    if len(ppqrs) < 2:
        raise HTTPException(400, "至少需要2个 pPQR 进行对比")
    
    # 提取参数
    comparison = {
        "ppqrs": [],
        "parameters": {},
        "best_result": None
    }
    
    for ppqr in ppqrs:
        comparison["ppqrs"].append({
            "id": str(ppqr.id),
            "number": ppqr.ppqr_number,
            "current": ppqr.welding_current,
            "voltage": ppqr.welding_voltage,
            "heat_input": ppqr.heat_input,
            "is_successful": ppqr.is_successful
        })
    
    # 找出最优参数
    successful_ppqrs = [p for p in ppqrs if p.is_successful]
    if successful_ppqrs:
        comparison["best_result"] = successful_ppqrs[0]
    
    return comparison
```

---

## 🔐 权限控制

### 会员等级检查
```python
@router.get("/ppqr")
@require_feature("ppqr_crud")  # 自动检查是否为专业版及以上
async def get_ppqr_list(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取 pPQR 列表（仅专业版及以上）"""
    service = PPQRService(db)
    return service.get_ppqr_list(current_user.id, db)
```

---

## 🎨 前端界面

### pPQR 创建页面
```typescript
// src/pages/PPQR/Create.tsx

const PPQRCreate: React.FC = () => {
  const { membership } = useAuth();
  
  // 检查会员等级
  if (membership.tier === 'free') {
    return <UpgradePrompt feature="pPQR管理" requiredTier="专业版" />;
  }
  
  return (
    <Form onFinish={handleSubmit}>
      <Form.Item label="试验目的" name="purpose">
        <TextArea rows={4} />
      </Form.Item>
      
      <Form.Item label="计划参数">
        <ParameterInput />
      </Form.Item>
      
      <Button type="primary" htmlType="submit">
        创建 pPQR
      </Button>
    </Form>
  );
};
```

---

**文档版本**: 1.0  
**最后更新**: 2025-10-16  
**开发状态**: 待开发

