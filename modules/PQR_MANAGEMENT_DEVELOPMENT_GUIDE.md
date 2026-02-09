# PQR管理模块 - 开发指南

## 📋 模块概述

### 功能定位
PQR (Procedure Qualification Record) 管理模块用于管理焊接工艺评定记录，记录焊接工艺试验的参数和测试结果，为 WPS 提供技术支持。

### 适用场景
- 记录焊接工艺评定试验数据
- 管理力学性能测试结果
- 管理无损检测结果
- 为 WPS 提供技术依据
- 工艺评定报告生成

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
| 个人高级版 | ✅ 可访问 | 最多 50 个 | 完整功能 + 测试管理 |
| 个人旗舰版 | ✅ 可访问 | 最多 100 个 | 完整功能 + 高级特性 |
| 企业版 | ✅ 可访问 | 最多 200 个 | 完整功能 + 企业协作 |
| 企业PRO | ✅ 可访问 | 最多 400 个 | 完整功能 + 企业协作 |
| 企业PRO MAX | ✅ 可访问 | 最多 500 个 | 完整功能 + 企业协作 |

**游客模式说明**:
- 游客仅可查看系统预设的示例 PQR 数据
- 无法创建、修改或删除任何数据
- 无法保存任何操作
- 用于体验系统功能和界面

### 功能权限矩阵
| 功能 | 免费版 | 专业版 | 高级版 | 旗舰版 | 企业版 |
|------|--------|--------|--------|--------|--------|
| 创建 PQR | ✅ | ✅ | ✅ | ✅ | ✅ |
| 编辑 PQR | ✅ | ✅ | ✅ | ✅ | ✅ |
| 删除 PQR | ✅ | ✅ | ✅ | ✅ | ✅ |
| 查看 PQR | ✅ | ✅ | ✅ | ✅ | ✅ |
| 导出报告 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 批量导入 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 测试数据管理 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 测试结果分析 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 关联 WPS | ✅ | ✅ | ✅ | ✅ | ✅ |
| 测试照片管理 | ❌ | ✅ | ✅ | ✅ | ✅ |

---

## 📊 功能清单

### 1. PQR 基础管理
- **创建 PQR**: 填写工艺评定记录
- **编辑 PQR**: 修改 PQR 数据
- **删除 PQR**: 软删除 PQR
- **查看 PQR**: 详细信息展示
- **复制 PQR**: 基于现有 PQR 创建新记录
- **搜索 PQR**: 按编号、标准、状态搜索
- **筛选 PQR**: 按测试结果、日期等筛选

### 2. 焊接参数记录
- **实际焊接参数**: 记录实际使用的焊接参数
- **电流电压记录**: 记录各层道的电流电压
- **温度记录**: 预热温度、层间温度
- **焊接速度**: 记录焊接行走速度
- **热输入计算**: 自动计算热输入值

### 3. 力学性能测试（高级版及以上）
- **拉伸试验**: 记录抗拉强度、屈服强度
- **弯曲试验**: 记录弯曲角度和结果
- **冲击试验**: 记录冲击功和温度
- **硬度试验**: 记录各区域硬度值
- **宏观检验**: 上传宏观照片
- **金相检验**: 上传金相照片

### 4. 无损检测（高级版及以上）
- **射线检测 (RT)**: 记录 RT 结果
- **超声检测 (UT)**: 记录 UT 结果
- **磁粉检测 (MT)**: 记录 MT 结果
- **渗透检测 (PT)**: 记录 PT 结果
- **检测照片**: 上传检测照片
- **检测报告**: 上传检测报告

### 5. 测试结果管理
- **合格判定**: 根据标准自动判定
- **不合格处理**: 记录不合格原因和处理措施
- **重新测试**: 记录重测信息
- **测试报告**: 生成完整测试报告

### 6. 关联管理
- **关联 WPS**: 关联支持的 WPS
- **关联焊工**: 记录执行焊接的焊工
- **关联设备**: 记录使用的焊接设备
- **关联标准**: 关联评定标准

### 7. 导出功能（专业版及以上）
- **导出 PDF**: 生成标准 PQR 报告
- **导出 Excel**: 导出测试数据
- **批量导出**: 批量导出多个 PQR
- **自定义模板**: 使用自定义报告模板

---

## 🗄️ 数据模型

### PQR 记录表
```sql
CREATE TABLE pqr_records (
    -- 主键和基础字段
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    factory_id UUID REFERENCES factories(id) ON DELETE SET NULL,
    
    -- PQR 基本信息
    pqr_number VARCHAR(100) NOT NULL,              -- PQR 编号
    title VARCHAR(255) NOT NULL,                   -- 标题
    test_date DATE,                                -- 测试日期
    status VARCHAR(50) DEFAULT 'pending',          -- 状态: pending, qualified, failed, retest
    standard VARCHAR(100),                         -- 评定标准
    
    -- 焊接工艺参数（实际使用）
    base_material VARCHAR(255),                    -- 母材
    base_material_thickness DECIMAL(8,2),          -- 母材厚度
    filler_material VARCHAR(255),                  -- 填充材料
    welding_process VARCHAR(100),                  -- 焊接方法
    joint_type VARCHAR(100),                       -- 接头类型
    welding_position VARCHAR(50),                  -- 焊接位置
    
    -- 温度参数（实际测量）
    preheat_temp DECIMAL(10,2),                   -- 预热温度
    interpass_temp DECIMAL(10,2),                 -- 层间温度
    post_weld_heat_treatment JSONB,               -- 焊后热处理
    
    -- 电气参数（实际测量）
    welding_parameters JSONB,                      -- 各层道焊接参数
    heat_input DECIMAL(10,2),                     -- 热输入 (kJ/mm)
    
    -- 保护气体
    shielding_gas VARCHAR(100),                    -- 保护气体
    gas_flow_rate DECIMAL(8,2),                   -- 气体流量
    
    -- 力学性能测试结果
    tensile_test_results JSONB,                    -- 拉伸试验结果
    bend_test_results JSONB,                       -- 弯曲试验结果
    impact_test_results JSONB,                     -- 冲击试验结果
    hardness_test_results JSONB,                   -- 硬度试验结果
    macro_examination JSONB,                       -- 宏观检验结果
    
    -- 无损检测结果
    ndt_results JSONB,                            -- 无损检测结果
    rt_result VARCHAR(50),                        -- 射线检测结果
    ut_result VARCHAR(50),                        -- 超声检测结果
    mt_result VARCHAR(50),                        -- 磁粉检测结果
    pt_result VARCHAR(50),                        -- 渗透检测结果
    
    -- 测试人员
    welder_id UUID REFERENCES welders(id),         -- 焊工
    tester_id UUID REFERENCES users(id),           -- 测试人员
    witness_id UUID REFERENCES users(id),          -- 见证人
    
    -- 合格判定
    is_qualified BOOLEAN,                          -- 是否合格
    qualification_date DATE,                       -- 合格日期
    failure_reason TEXT,                           -- 不合格原因
    corrective_action TEXT,                        -- 纠正措施
    
    -- 关联信息
    supported_wps_uuids JSONB,                    -- 支持的WPS列表
    equipment_id UUID REFERENCES equipment(id),    -- 使用的设备
    
    -- 附件
    test_photos JSONB,                            -- 测试照片
    test_reports JSONB,                           -- 测试报告
    attachments JSONB,                            -- 其他附件
    
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
    INDEX idx_pqr_number (pqr_number),
    INDEX idx_status (status),
    INDEX idx_test_date (test_date),
    INDEX idx_welder (welder_id),
    INDEX idx_qualified (is_qualified),
    INDEX idx_deleted (deleted_at)
);
```

### 测试数据详细表
```sql
CREATE TABLE pqr_test_details (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pqr_id UUID NOT NULL REFERENCES pqr_records(id) ON DELETE CASCADE,
    
    test_type VARCHAR(50) NOT NULL,                -- 测试类型: tensile, bend, impact, hardness
    specimen_number VARCHAR(50),                   -- 试样编号
    test_location VARCHAR(100),                    -- 测试位置
    test_result JSONB,                            -- 测试结果数据
    is_pass BOOLEAN,                              -- 是否通过
    test_date TIMESTAMP,                          -- 测试时间
    tester_id UUID REFERENCES users(id),          -- 测试人员
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_pqr (pqr_id),
    INDEX idx_test_type (test_type)
);
```

---

## 🔌 API接口

### 1. PQR 列表
```http
GET /api/v1/pqr?page=1&page_size=20&status=qualified
Authorization: Bearer <token>
```

### 2. 创建 PQR
```http
POST /api/v1/pqr
Authorization: Bearer <token>
Content-Type: application/json

{
  "pqr_number": "PQR-2025-001",
  "title": "Q235B 对接焊工艺评定",
  "test_date": "2025-10-15",
  "standard": "AWS D1.1",
  "base_material": "Q235B",
  "filler_material": "E7018",
  "welding_process": "SMAW",
  "preheat_temp": 80,
  "heat_input": 1.5
}
```

### 3. 更新 PQR
```http
PUT /api/v1/pqr/{id}
Authorization: Bearer <token>
```

### 4. 添加测试结果
```http
POST /api/v1/pqr/{id}/test-results
Authorization: Bearer <token>
Content-Type: application/json

{
  "test_type": "tensile",
  "specimen_number": "T-1",
  "test_result": {
    "tensile_strength": 520,
    "yield_strength": 380,
    "elongation": 25
  },
  "is_pass": true
}
```

### 5. 合格判定
```http
POST /api/v1/pqr/{id}/qualify
Authorization: Bearer <token>
Content-Type: application/json

{
  "is_qualified": true,
  "qualification_date": "2025-10-16",
  "notes": "所有测试项目均合格"
}
```

### 6. 导出报告
```http
GET /api/v1/pqr/{id}/export/pdf
Authorization: Bearer <token>
```

### 7. 关联 WPS
```http
POST /api/v1/pqr/{id}/link-wps
Authorization: Bearer <token>
Content-Type: application/json

{
  "wps_ids": ["uuid1", "uuid2"]
}
```

---

## 💼 业务逻辑

### 1. 创建 PQR
```python
class PQRService:
    @require_quota("pqr_records")
    async def create_pqr(
        self,
        pqr_data: PQRCreate,
        user_id: UUID,
        db: Session
    ) -> PQRRecord:
        """创建 PQR"""
        
        # 检查配额
        checker = QuotaChecker(db)
        user = db.query(User).filter(User.id == user_id).first()
        if not checker.check_quota(user, "pqr_records"):
            raise HTTPException(403, "PQR 配额已满")
        
        # 生成编号
        if not pqr_data.pqr_number:
            pqr_data.pqr_number = self._generate_pqr_number(user_id, db)
        
        # 创建记录
        pqr = PQRRecord(
            **pqr_data.dict(),
            user_id=user_id,
            created_by=user_id,
            status="pending"
        )
        
        db.add(pqr)
        db.commit()
        
        return pqr
```

### 2. 合格判定逻辑
```python
async def qualify_pqr(
    self,
    pqr_id: UUID,
    qualification_data: PQRQualification,
    user_id: UUID,
    db: Session
) -> PQRRecord:
    """PQR 合格判定"""
    
    pqr = db.query(PQRRecord).filter(
        PQRRecord.id == pqr_id,
        PQRRecord.user_id == user_id
    ).first()
    
    if not pqr:
        raise HTTPException(404, "PQR 不存在")
    
    # 检查所有测试是否完成
    if not self._all_tests_completed(pqr):
        raise HTTPException(400, "测试未完成")
    
    # 更新状态
    pqr.is_qualified = qualification_data.is_qualified
    pqr.qualification_date = qualification_data.qualification_date
    pqr.status = "qualified" if qualification_data.is_qualified else "failed"
    
    db.commit()
    
    return pqr
```

### 3. 自动计算热输入
```python
def calculate_heat_input(
    self,
    current: float,
    voltage: float,
    travel_speed: float
) -> float:
    """计算热输入 (kJ/mm)"""
    
    # 热输入 = (电流 × 电压 × 60) / (1000 × 焊接速度)
    heat_input = (current * voltage * 60) / (1000 * travel_speed)
    
    return round(heat_input, 2)
```

---

## 🔐 权限控制

### 数据隔离
```python
def get_pqr_list(
    self,
    user_id: UUID,
    company_id: Optional[UUID],
    db: Session
) -> List[PQRRecord]:
    """获取 PQR 列表"""
    
    query = db.query(PQRRecord).filter(
        PQRRecord.user_id == user_id,
        PQRRecord.deleted_at.is_(None)
    )
    
    # 企业会员可查看企业数据
    if company_id:
        query = query.filter(
            or_(
                PQRRecord.user_id == user_id,
                PQRRecord.company_id == company_id
            )
        )
    
    return query.all()
```

---

## 🎨 前端界面

### PQR 详情页面
```typescript
// src/pages/PQR/Detail.tsx

const PQRDetail: React.FC<{ id: string }> = ({ id }) => {
  const { data: pqr, loading } = usePQR(id);
  
  return (
    <div className="pqr-detail">
      <Descriptions title="基本信息">
        <Descriptions.Item label="PQR编号">{pqr.pqr_number}</Descriptions.Item>
        <Descriptions.Item label="状态">
          <Badge status={getStatusBadge(pqr.status)} text={pqr.status} />
        </Descriptions.Item>
      </Descriptions>
      
      <Tabs>
        <TabPane tab="焊接参数" key="params">
          <WeldingParameters data={pqr} />
        </TabPane>
        <TabPane tab="力学性能" key="mechanical">
          <MechanicalTests data={pqr.tensile_test_results} />
        </TabPane>
        <TabPane tab="无损检测" key="ndt">
          <NDTResults data={pqr.ndt_results} />
        </TabPane>
        <TabPane tab="测试照片" key="photos">
          <TestPhotos photos={pqr.test_photos} />
        </TabPane>
      </Tabs>
    </div>
  );
};
```

---

**文档版本**: 1.0  
**最后更新**: 2025-10-16  
**开发状态**: 待开发

