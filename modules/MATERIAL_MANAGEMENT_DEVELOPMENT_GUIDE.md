# 焊材管理模块 - 开发指南

## 📋 模块概述

### 功能定位
焊材管理模块用于管理焊接材料的库存、采购、使用和供应商信息，确保焊材供应充足且质量可控。

### 适用场景
- 焊材库存管理
- 焊材出入库记录
- 低库存预警
- 供应商管理
- 焊材使用追溯
- 焊材质量管理

### 开发优先级
**第二阶段** - 重要功能，优先开发

---

## 🎯 会员权限

### 访问权限
| 会员等级 | 访问权限 | 数量限制 | 功能范围 |
|---------|---------|---------|---------|
| 游客模式 | ❌ 不可访问 | 0 | - |
| 个人免费版 | ❌ 不可访问 | 0 | - |
| 个人专业版 | ✅ 可访问 | 无限制（基础管理） | 基础库存管理 |
| 个人高级版 | ✅ 可访问 | 无限制（完整功能） | 完整功能 + 供应商管理 |
| 个人旗舰版 | ✅ 可访问 | 无限制（完整功能） | 完整功能 + 高级特性 |
| 企业版 | ✅ 可访问 | 无限制（完整功能） | 完整功能 + 企业协作 |
| 企业PRO | ✅ 可访问 | 无限制（完整功能） | 完整功能 + 企业协作 |
| 企业PRO MAX | ✅ 可访问 | 无限制（完整功能） | 完整功能 + 企业协作 |

**重要说明**: 焊材管理功能仅对**个人专业版及以上**会员开放。

### 功能权限矩阵
| 功能 | 免费版 | 专业版 | 高级版 | 旗舰版 | 企业版 |
|------|--------|--------|--------|--------|--------|
| 焊材基础管理 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 库存管理 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 出入库记录 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 低库存预警 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 供应商管理 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 采购管理 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 质量追溯 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 统计报表 | ❌ | ❌ | ✅ | ✅ | ✅ |

---

## 📊 功能清单

### 1. 焊材基础管理
- **添加焊材**: 录入焊材基本信息
- **编辑焊材**: 修改焊材信息
- **删除焊材**: 软删除焊材记录
- **查看焊材**: 查看焊材详细信息
- **搜索焊材**: 按名称、型号、规格搜索
- **分类管理**: 按焊材类型分类

### 2. 库存管理
- **当前库存**: 实时库存数量
- **库存预警**: 低于最小库存量时预警
- **库存盘点**: 定期库存盘点
- **库存调整**: 手动调整库存数量
- **库存历史**: 查看库存变化历史
- **多仓库管理**: 支持多个仓库（企业版）

### 3. 出入库管理
- **入库登记**: 记录焊材入库
- **出库登记**: 记录焊材出库
- **批次管理**: 按批次管理焊材
- **出入库单**: 生成出入库单据
- **库存流水**: 完整的出入库流水记录

### 4. 低库存预警
- **预警设置**: 设置最小库存量
- **预警通知**: 库存低于预警值时通知
- **预警列表**: 查看所有低库存焊材
- **自动采购建议**: 根据使用量建议采购（旗舰版）

### 5. 供应商管理（高级版及以上）
- **供应商信息**: 管理供应商基本信息
- **供应商评级**: 供应商质量评级
- **采购记录**: 记录采购历史
- **供应商对比**: 对比不同供应商

### 6. 采购管理（高级版及以上）
- **采购申请**: 创建采购申请
- **采购订单**: 生成采购订单
- **采购入库**: 采购入库登记
- **采购统计**: 采购数据统计

### 7. 质量管理（高级版及以上）
- **质量证书**: 上传焊材质量证书
- **检验记录**: 记录入库检验结果
- **质量追溯**: 追溯焊材使用情况
- **不合格处理**: 记录不合格焊材处理

### 8. 使用追溯
- **关联 WPS**: 记录焊材适用的 WPS
- **关联生产任务**: 记录焊材使用的生产任务
- **使用统计**: 统计焊材使用量
- **成本核算**: 计算焊材成本（旗舰版）

---

## 🗄️ 数据模型

### 焊材基本信息表
```sql
CREATE TABLE welding_materials (
    -- 主键和基础字段
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    factory_id UUID REFERENCES factories(id) ON DELETE SET NULL,
    
    -- 基本信息
    material_code VARCHAR(100) NOT NULL,           -- 焊材编码
    material_name VARCHAR(255) NOT NULL,           -- 焊材名称
    material_type VARCHAR(100),                    -- 焊材类型: electrode, wire, flux, gas
    specification VARCHAR(255),                    -- 规格型号
    classification VARCHAR(100),                   -- 分类标准 (AWS, ISO等)
    
    -- 技术参数
    diameter DECIMAL(8,2),                        -- 直径/厚度
    length DECIMAL(8,2),                          -- 长度
    weight_per_unit DECIMAL(10,3),                -- 单位重量
    
    -- 适用范围
    applicable_base_materials JSONB,               -- 适用母材
    applicable_welding_processes JSONB,            -- 适用焊接方法
    applicable_positions JSONB,                    -- 适用焊接位置
    
    -- 库存信息
    current_stock DECIMAL(12,2) DEFAULT 0,        -- 当前库存
    unit VARCHAR(20) DEFAULT 'kg',                -- 单位: kg, piece, box
    min_stock_level DECIMAL(12,2),                -- 最小库存量
    max_stock_level DECIMAL(12,2),                -- 最大库存量
    reorder_point DECIMAL(12,2),                  -- 再订货点
    
    -- 存储条件
    storage_conditions TEXT,                       -- 存储条件
    shelf_life_days INTEGER,                       -- 保质期（天）
    storage_location VARCHAR(100),                 -- 存储位置
    
    -- 价格信息
    unit_price DECIMAL(12,2),                     -- 单价
    currency VARCHAR(10) DEFAULT 'CNY',           -- 货币
    
    -- 供应商
    primary_supplier_id UUID REFERENCES material_suppliers(id),
    
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
    INDEX idx_material_code (material_code),
    INDEX idx_material_type (material_type),
    INDEX idx_stock_level (current_stock, min_stock_level),
    INDEX idx_deleted (deleted_at),
    
    UNIQUE (user_id, material_code)
);
```

### 焊材出入库记录表
```sql
CREATE TABLE material_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id UUID NOT NULL REFERENCES welding_materials(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 交易信息
    transaction_type VARCHAR(20) NOT NULL,         -- 类型: in, out, adjust
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quantity DECIMAL(12,2) NOT NULL,              -- 数量
    unit VARCHAR(20),                             -- 单位
    
    -- 批次信息
    batch_number VARCHAR(100),                     -- 批次号
    production_date DATE,                          -- 生产日期
    expiry_date DATE,                             -- 到期日期
    
    -- 来源/去向
    source_destination VARCHAR(255),               -- 来源/去向
    supplier_id UUID REFERENCES material_suppliers(id),
    production_task_id UUID REFERENCES production_tasks(id),
    
    -- 单据信息
    document_number VARCHAR(100),                  -- 单据号
    document_type VARCHAR(50),                     -- 单据类型
    
    -- 质量信息
    quality_certificate JSONB,                     -- 质量证书
    inspection_result VARCHAR(50),                 -- 检验结果: pass, fail, pending
    
    -- 经办人
    operator_id UUID REFERENCES users(id),         -- 经办人
    
    -- 备注
    notes TEXT,
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    
    -- 索引
    INDEX idx_material (material_id),
    INDEX idx_user (user_id),
    INDEX idx_transaction_type (transaction_type),
    INDEX idx_transaction_date (transaction_date),
    INDEX idx_batch_number (batch_number),
    INDEX idx_supplier (supplier_id)
);
```

### 供应商表
```sql
CREATE TABLE material_suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    
    -- 基本信息
    supplier_code VARCHAR(100) NOT NULL,           -- 供应商编码
    supplier_name VARCHAR(255) NOT NULL,           -- 供应商名称
    contact_person VARCHAR(100),                   -- 联系人
    phone VARCHAR(50),                             -- 电话
    email VARCHAR(100),                            -- 邮箱
    address TEXT,                                  -- 地址
    
    -- 评级信息
    rating INTEGER,                                -- 评级 (1-5)
    is_qualified BOOLEAN DEFAULT TRUE,             -- 是否合格
    
    -- 统计信息
    total_purchases DECIMAL(15,2) DEFAULT 0,      -- 总采购额
    total_orders INTEGER DEFAULT 0,                -- 总订单数
    
    -- 备注
    notes TEXT,
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP,
    
    -- 索引
    INDEX idx_user (user_id),
    INDEX idx_company (company_id),
    INDEX idx_supplier_code (supplier_code),
    INDEX idx_deleted (deleted_at),
    
    UNIQUE (user_id, supplier_code)
);
```

---

## 🔌 API接口

### 1. 焊材列表
```http
GET /api/v1/materials?page=1&page_size=20&low_stock=true
Authorization: Bearer <token>
```

### 2. 创建焊材
```http
POST /api/v1/materials
Authorization: Bearer <token>
Content-Type: application/json

{
  "material_code": "MAT-2025-001",
  "material_name": "E7018 焊条",
  "material_type": "electrode",
  "specification": "Φ3.2mm",
  "current_stock": 100,
  "unit": "kg",
  "min_stock_level": 20,
  "unit_price": 25.50
}
```

### 3. 入库
```http
POST /api/v1/materials/{id}/stock-in
Authorization: Bearer <token>
Content-Type: application/json

{
  "quantity": 50,
  "batch_number": "BATCH-2025-001",
  "supplier_id": "uuid",
  "document_number": "PO-2025-001",
  "production_date": "2025-10-01"
}
```

### 4. 出库
```http
POST /api/v1/materials/{id}/stock-out
Authorization: Bearer <token>
Content-Type: application/json

{
  "quantity": 10,
  "production_task_id": "uuid",
  "operator_id": "uuid",
  "notes": "用于生产任务 PT-2025-001"
}
```

### 5. 低库存预警
```http
GET /api/v1/materials/low-stock-alerts
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "material_code": "MAT-2025-001",
      "material_name": "E7018 焊条",
      "current_stock": 15,
      "min_stock_level": 20,
      "shortage": 5,
      "unit": "kg"
    }
  ]
}
```

### 6. 库存统计
```http
GET /api/v1/materials/statistics
Authorization: Bearer <token>
```

---

## 💼 业务逻辑

### 1. 库存变更
```python
class MaterialService:
    def stock_in(
        self,
        material_id: UUID,
        transaction_data: MaterialStockIn,
        user_id: UUID,
        db: Session
    ) -> WeldingMaterial:
        """焊材入库"""
        
        material = db.query(WeldingMaterial).filter(
            WeldingMaterial.id == material_id,
            WeldingMaterial.user_id == user_id
        ).first()
        
        if not material:
            raise HTTPException(404, "焊材不存在")
        
        # 更新库存
        material.current_stock += transaction_data.quantity
        material.updated_at = datetime.now()
        
        # 创建交易记录
        transaction = MaterialTransaction(
            material_id=material_id,
            user_id=user_id,
            transaction_type="in",
            quantity=transaction_data.quantity,
            batch_number=transaction_data.batch_number,
            supplier_id=transaction_data.supplier_id,
            created_by=user_id
        )
        
        db.add(transaction)
        db.commit()
        
        return material
    
    def stock_out(
        self,
        material_id: UUID,
        transaction_data: MaterialStockOut,
        user_id: UUID,
        db: Session
    ) -> WeldingMaterial:
        """焊材出库"""
        
        material = db.query(WeldingMaterial).filter(
            WeldingMaterial.id == material_id,
            WeldingMaterial.user_id == user_id
        ).first()
        
        if not material:
            raise HTTPException(404, "焊材不存在")
        
        # 检查库存
        if material.current_stock < transaction_data.quantity:
            raise HTTPException(400, "库存不足")
        
        # 更新库存
        material.current_stock -= transaction_data.quantity
        material.updated_at = datetime.now()
        
        # 创建交易记录
        transaction = MaterialTransaction(
            material_id=material_id,
            user_id=user_id,
            transaction_type="out",
            quantity=transaction_data.quantity,
            production_task_id=transaction_data.production_task_id,
            operator_id=transaction_data.operator_id,
            created_by=user_id
        )
        
        db.add(transaction)
        db.commit()
        
        # 检查是否需要预警
        self._check_low_stock_alert(material)
        
        return material
```

### 2. 低库存检查
```python
def get_low_stock_materials(
    self,
    user_id: UUID,
    db: Session
) -> List[WeldingMaterial]:
    """获取低库存焊材"""
    
    materials = db.query(WeldingMaterial).filter(
        WeldingMaterial.user_id == user_id,
        WeldingMaterial.current_stock < WeldingMaterial.min_stock_level,
        WeldingMaterial.deleted_at.is_(None)
    ).all()
    
    return materials
```

---

## 🔐 权限控制

```python
@router.get("/materials")
@require_feature("material_management")  # 需要专业版及以上
async def get_material_list(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取焊材列表"""
    service = MaterialService(db)
    return service.get_material_list(current_user.id, db)
```

---

## 🎨 前端界面

### 焊材列表页面
```typescript
// src/pages/Materials/List.tsx

const MaterialList: React.FC = () => {
  const { data, loading } = useMaterials();
  
  const columns = [
    { title: '焊材编码', dataIndex: 'material_code' },
    { title: '焊材名称', dataIndex: 'material_name' },
    { title: '规格', dataIndex: 'specification' },
    { title: '当前库存', dataIndex: 'current_stock', render: renderStock },
    { title: '单位', dataIndex: 'unit' },
    { title: '状态', render: renderStockStatus },
    { title: '操作', render: renderActions }
  ];
  
  return (
    <div>
      <Alert 
        message={`${lowStockCount} 种焊材库存不足`} 
        type="warning" 
        showIcon 
      />
      <Table columns={columns} dataSource={data} loading={loading} />
    </div>
  );
};
```

---

**文档版本**: 1.0  
**最后更新**: 2025-10-16  
**开发状态**: 已实现（需测试）

