# 焊工管理模块 - 开发指南

## 📋 模块概述

### 功能定位
焊工管理模块用于管理焊接人员的基本信息、资质证书、培训记录和工作履历，确保焊工资质符合要求。

### 适用场景
- 焊工基本信息管理
- 焊工资质证书管理
- 证书有效期监控
- 培训记录管理
- 焊工工作履历跟踪
- 焊工技能评估

### 开发优先级
**第一阶段** - 核心功能，立即开发

---

## 🎯 会员权限

### 访问权限
| 会员等级 | 访问权限 | 数量限制 | 功能范围 |
|---------|---------|---------|---------|
| 游客模式 | ❌ 不可访问 | 0 | - |
| 个人免费版 | ❌ 不可访问 | 0 | - |
| 个人专业版 | ✅ 可访问 | 无限制（基础管理） | 基础增删改查 |
| 个人高级版 | ✅ 可访问 | 无限制（完整功能） | 完整功能 + 培训管理 |
| 个人旗舰版 | ✅ 可访问 | 无限制（完整功能） | 完整功能 + 高级特性 |
| 企业版 | ✅ 可访问 | 无限制（完整功能） | 完整功能 + 企业协作 |
| 企业PRO | ✅ 可访问 | 无限制（完整功能） | 完整功能 + 企业协作 |
| 企业PRO MAX | ✅ 可访问 | 无限制（完整功能） | 完整功能 + 企业协作 |

**重要说明**: 焊工管理功能仅对**个人专业版及以上**会员开放。

### 功能权限矩阵
| 功能 | 免费版 | 专业版 | 高级版 | 旗舰版 | 企业版 |
|------|--------|--------|--------|--------|--------|
| 焊工基础管理 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 证书管理 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 证书到期提醒 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 培训记录 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 工作履历 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 技能评估 | ❌ | ❌ | ✅ | ✅ | ✅ |
| 批量导入 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 统计报表 | ❌ | ❌ | ✅ | ✅ | ✅ |

---

## 📊 功能清单

### 1. 焊工基础管理
- **添加焊工**: 录入焊工基本信息
- **编辑焊工**: 修改焊工信息
- **删除焊工**: 软删除焊工记录
- **查看焊工**: 查看焊工详细信息
- **搜索焊工**: 按姓名、工号、证书号搜索
- **筛选焊工**: 按状态、技能等级筛选
- **焊工档案**: 完整的焊工档案管理

### 2. 证书管理
- **添加证书**: 录入焊工资质证书
- **证书详情**: 查看证书详细信息
- **证书扫描件**: 上传证书扫描件
- **证书有效期**: 管理证书有效期
- **证书续期**: 记录证书续期信息
- **证书作废**: 标记失效证书
- **多证书管理**: 一个焊工可有多个证书

### 3. 证书到期提醒
- **到期预警**: 证书即将到期提醒（提前30/60/90天）
- **已过期提醒**: 已过期证书提醒
- **批量提醒**: 批量查看即将到期的证书
- **邮件通知**: 发送到期提醒邮件（旗舰版）
- **仪表盘显示**: 在仪表盘显示到期预警

### 4. 培训记录（高级版及以上）
- **添加培训**: 记录培训信息
- **培训类型**: 内部培训、外部培训、考核等
- **培训证明**: 上传培训证明文件
- **培训成绩**: 记录培训成绩
- **培训历史**: 查看完整培训历史

### 5. 工作履历（高级版及以上）
- **工作记录**: 记录焊工参与的项目
- **关联 WPS**: 关联焊工使用的 WPS
- **关联生产任务**: 关联焊工参与的生产任务
- **工作评价**: 记录工作表现评价
- **工作统计**: 统计焊工工作量

### 6. 技能评估（高级版及以上）
- **技能等级**: 设置焊工技能等级
- **评估记录**: 记录技能评估结果
- **评估标准**: 定义评估标准
- **技能矩阵**: 焊工技能矩阵展示

### 7. 批量操作
- **批量导入**: 从 Excel 批量导入焊工
- **批量导出**: 导出焊工数据
- **批量更新**: 批量更新焊工状态
- **模板下载**: 下载导入模板

### 8. 统计分析（高级版及以上）
- **焊工统计**: 按状态、技能等级统计
- **证书统计**: 证书类型、有效期统计
- **培训统计**: 培训次数、通过率统计
- **工作量统计**: 焊工工作量统计

---

## 🗄️ 数据模型

### 焊工基本信息表
```sql
CREATE TABLE welders (
    -- 主键和基础字段
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    factory_id UUID REFERENCES factories(id) ON DELETE SET NULL,
    
    -- 基本信息
    welder_number VARCHAR(100) NOT NULL,           -- 焊工工号
    name VARCHAR(100) NOT NULL,                    -- 姓名
    name_en VARCHAR(100),                          -- 英文名
    gender VARCHAR(10),                            -- 性别
    birth_date DATE,                               -- 出生日期
    id_card_number VARCHAR(50),                    -- 身份证号
    phone VARCHAR(50),                             -- 联系电话
    email VARCHAR(100),                            -- 邮箱
    address TEXT,                                  -- 地址
    
    -- 照片
    photo_url VARCHAR(500),                        -- 照片URL
    
    -- 工作信息
    employment_date DATE,                          -- 入职日期
    department VARCHAR(100),                       -- 部门
    position VARCHAR(100),                         -- 职位
    skill_level VARCHAR(50),                       -- 技能等级: junior, intermediate, senior, expert
    is_active BOOLEAN DEFAULT TRUE,                -- 是否在职
    resignation_date DATE,                         -- 离职日期
    
    -- 统计信息
    total_certifications INTEGER DEFAULT 0,        -- 证书总数
    active_certifications INTEGER DEFAULT 0,       -- 有效证书数
    total_trainings INTEGER DEFAULT 0,             -- 培训总次数
    total_work_hours DECIMAL(10,2) DEFAULT 0,     -- 总工作小时数
    
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
    INDEX idx_welder_number (welder_number),
    INDEX idx_name (name),
    INDEX idx_skill_level (skill_level),
    INDEX idx_is_active (is_active),
    INDEX idx_deleted (deleted_at),
    
    UNIQUE (user_id, welder_number)
);
```

### 焊工证书表
```sql
CREATE TABLE welder_certifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    welder_id UUID NOT NULL REFERENCES welders(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 证书信息
    certificate_number VARCHAR(100) NOT NULL,      -- 证书编号
    certificate_type VARCHAR(100),                 -- 证书类型
    issuing_authority VARCHAR(255),                -- 发证机构
    issue_date DATE,                               -- 发证日期
    expiry_date DATE,                              -- 到期日期
    is_valid BOOLEAN DEFAULT TRUE,                 -- 是否有效
    
    -- 资质范围
    welding_process VARCHAR(100),                  -- 焊接方法
    base_material VARCHAR(255),                    -- 母材
    filler_material VARCHAR(255),                  -- 填充材料
    welding_position VARCHAR(50),                  -- 焊接位置
    thickness_range VARCHAR(50),                   -- 厚度范围
    diameter_range VARCHAR(50),                    -- 直径范围
    
    -- 证书文件
    certificate_scan JSONB,                        -- 证书扫描件
    
    -- 续期记录
    renewal_history JSONB,                         -- 续期历史
    
    -- 备注
    notes TEXT,
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP,
    
    -- 索引
    INDEX idx_welder (welder_id),
    INDEX idx_user (user_id),
    INDEX idx_certificate_number (certificate_number),
    INDEX idx_expiry_date (expiry_date),
    INDEX idx_is_valid (is_valid),
    INDEX idx_deleted (deleted_at)
);
```

### 焊工培训记录表
```sql
CREATE TABLE welder_trainings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    welder_id UUID NOT NULL REFERENCES welders(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 培训信息
    training_name VARCHAR(255) NOT NULL,           -- 培训名称
    training_type VARCHAR(50),                     -- 培训类型: internal, external, exam
    training_provider VARCHAR(255),                -- 培训机构
    training_date DATE,                            -- 培训日期
    duration_hours DECIMAL(6,2),                  -- 培训时长（小时）
    
    -- 培训内容
    training_content TEXT,                         -- 培训内容
    training_objectives TEXT,                      -- 培训目标
    
    -- 培训结果
    score DECIMAL(5,2),                           -- 成绩
    is_passed BOOLEAN,                            -- 是否通过
    certificate_obtained VARCHAR(255),             -- 获得的证书
    
    -- 培训证明
    training_certificate JSONB,                    -- 培训证明文件
    
    -- 备注
    notes TEXT,
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    
    -- 索引
    INDEX idx_welder (welder_id),
    INDEX idx_user (user_id),
    INDEX idx_training_date (training_date),
    INDEX idx_training_type (training_type)
);
```

---

## 🔌 API接口

### 1. 焊工列表
```http
GET /api/v1/welders?page=1&page_size=20&is_active=true
Authorization: Bearer <token>
```

### 2. 创建焊工
```http
POST /api/v1/welders
Authorization: Bearer <token>
Content-Type: application/json

{
  "welder_number": "W-2025-001",
  "name": "张三",
  "gender": "male",
  "phone": "13800138000",
  "skill_level": "intermediate",
  "employment_date": "2025-01-01"
}
```

### 3. 添加证书
```http
POST /api/v1/welders/{welder_id}/certifications
Authorization: Bearer <token>
Content-Type: application/json

{
  "certificate_number": "CERT-2025-001",
  "certificate_type": "焊工资格证",
  "issuing_authority": "中国机械工程学会",
  "issue_date": "2025-01-01",
  "expiry_date": "2027-01-01",
  "welding_process": "SMAW",
  "welding_position": "All"
}
```

### 4. 获取即将到期证书
```http
GET /api/v1/welders/certifications/expiring?days=30
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "welder_name": "张三",
      "certificate_number": "CERT-2025-001",
      "expiry_date": "2025-11-15",
      "days_remaining": 30
    }
  ]
}
```

### 5. 添加培训记录
```http
POST /api/v1/welders/{welder_id}/trainings
Authorization: Bearer <token>
Content-Type: application/json

{
  "training_name": "SMAW 焊接技能培训",
  "training_type": "internal",
  "training_date": "2025-10-01",
  "duration_hours": 40,
  "score": 85,
  "is_passed": true
}
```

### 6. 焊工统计
```http
GET /api/v1/welders/statistics
Authorization: Bearer <token>
```

---

## 💼 业务逻辑

### 1. 证书到期检查
```python
class WelderService:
    def get_expiring_certifications(
        self,
        user_id: UUID,
        days: int,
        db: Session
    ) -> List[WelderCertification]:
        """获取即将到期的证书"""
        
        expiry_threshold = date.today() + timedelta(days=days)
        
        certifications = db.query(WelderCertification).join(
            Welder
        ).filter(
            Welder.user_id == user_id,
            WelderCertification.is_valid == True,
            WelderCertification.expiry_date <= expiry_threshold,
            WelderCertification.expiry_date >= date.today()
        ).all()
        
        return certifications
    
    def check_expired_certifications(
        self,
        user_id: UUID,
        db: Session
    ):
        """检查并更新过期证书"""
        
        expired_certs = db.query(WelderCertification).join(
            Welder
        ).filter(
            Welder.user_id == user_id,
            WelderCertification.is_valid == True,
            WelderCertification.expiry_date < date.today()
        ).all()
        
        for cert in expired_certs:
            cert.is_valid = False
            cert.updated_at = datetime.now()
        
        db.commit()
```

### 2. 焊工统计
```python
def get_welder_statistics(
    self,
    user_id: UUID,
    db: Session
) -> Dict[str, Any]:
    """获取焊工统计数据"""
    
    total = db.query(Welder).filter(
        Welder.user_id == user_id,
        Welder.deleted_at.is_(None)
    ).count()
    
    active = db.query(Welder).filter(
        Welder.user_id == user_id,
        Welder.is_active == True,
        Welder.deleted_at.is_(None)
    ).count()
    
    by_skill_level = db.query(
        Welder.skill_level,
        func.count(Welder.id)
    ).filter(
        Welder.user_id == user_id,
        Welder.deleted_at.is_(None)
    ).group_by(Welder.skill_level).all()
    
    return {
        "total": total,
        "active": active,
        "inactive": total - active,
        "by_skill_level": dict(by_skill_level)
    }
```

---

## 🔐 权限控制

### 会员等级检查
```python
@router.get("/welders")
@require_feature("welder_management")  # 需要专业版及以上
async def get_welder_list(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取焊工列表"""
    service = WelderService(db)
    return service.get_welder_list(current_user.id, db)
```

---

## 🎨 前端界面

### 焊工列表页面
```typescript
// src/pages/Welders/List.tsx

const WelderList: React.FC = () => {
  const { data, loading } = useWelders();
  
  const columns = [
    { title: '工号', dataIndex: 'welder_number' },
    { title: '姓名', dataIndex: 'name' },
    { title: '技能等级', dataIndex: 'skill_level', render: renderSkillLevel },
    { title: '有效证书', dataIndex: 'active_certifications' },
    { title: '状态', dataIndex: 'is_active', render: renderStatus },
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

