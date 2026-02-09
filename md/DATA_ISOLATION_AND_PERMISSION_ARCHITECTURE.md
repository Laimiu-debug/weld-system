# 🏗️ 数据隔离与权限管理架构文档

## 📋 目录

1. [架构概述](#架构概述)
2. [核心概念](#核心概念)
3. [数据隔离实现](#数据隔离实现)
4. [权限管理实现](#权限管理实现)
5. [配额管理实现](#配额管理实现)
6. [设备管理模块实现](#设备管理模块实现)
7. [通用模式总结](#通用模式总结)
8. [后续模块实施指南](#后续模块实施指南)

---

## 🎯 架构概述

### 设计目标

1. **数据隔离**：个人工作区和企业工作区的数据完全隔离
2. **权限控制**：基于角色的细粒度权限管理（RBAC）
3. **配额管理**：根据会员等级限制资源使用
4. **可扩展性**：统一的架构模式，便于新模块快速实现

### 架构分层

```
┌─────────────────────────────────────────────────────────┐
│                    前端展示层                              │
│  (EquipmentList, MaterialList, WelderList...)           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    API端点层                              │
│  (equipment.py, material.py, welder.py...)              │
│  - 工作区上下文构建                                        │
│  - 参数验证                                               │
│  - 错误处理                                               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    业务逻辑层                              │
│  (EquipmentService, MaterialService, WelderService...)  │
│  - 业务逻辑处理                                           │
│  - 权限检查调用                                           │
│  - 配额检查调用                                           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  核心服务层                                │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │ DataAccessService│  │  QuotaService    │            │
│  │  - 数据隔离      │  │  - 配额检查      │            │
│  │  - 权限验证      │  │  - 配额更新      │            │
│  └──────────────────┘  └──────────────────┘            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    数据模型层                              │
│  (Equipment, Material, Welder, User, Company...)        │
└─────────────────────────────────────────────────────────┘
```

---

## 🔑 核心概念

### 1. 工作区类型 (WorkspaceType)

```python
class WorkspaceType(str, Enum):
    PERSONAL = "personal"    # 个人工作区
    ENTERPRISE = "enterprise" # 企业工作区
```

**特点**：
- **个人工作区**：用户私有数据，完全隔离
- **企业工作区**：企业共享数据，基于角色权限控制

### 2. 工作区上下文 (WorkspaceContext)

```python
class WorkspaceContext:
    user_id: int              # 当前用户ID
    workspace_type: str       # 工作区类型
    company_id: Optional[int] # 企业ID（企业工作区必需）
    factory_id: Optional[int] # 工厂ID（可选）
```

**作用**：
- 携带当前操作的上下文信息
- 用于数据隔离和权限检查
- 贯穿整个请求生命周期

### 3. 访问级别 (AccessLevel)

```python
class AccessLevel(str, Enum):
    PRIVATE = "private"   # 私有：仅创建者可访问
    FACTORY = "factory"   # 工厂：同工厂成员可访问
    COMPANY = "company"   # 企业：全企业成员可访问（需权限）
    PUBLIC = "public"     # 公开：所有企业成员可查看
```

**推荐配置**：
- **个人工作区**：默认 `private`
- **企业工作区**：默认 `company`（权限由角色控制）

### 4. 数据访问范围 (DataAccessScope)

```python
data_access_scope: str  # "factory" 或 "company"
```

**作用**：
- 控制员工可以访问的数据范围
- `factory`：只能访问所在工厂的数据
- `company`：可以访问整个企业的数据

### 5. 角色权限结构

```python
{
  "equipment_management": {
    "view": true,
    "create": true,
    "edit": true,
    "delete": true
  },
  "material_management": {
    "view": true,
    "create": false,
    "edit": false,
    "delete": false
  }
}
```

---

## 🔒 数据隔离实现

### 数据模型必需字段

所有需要数据隔离的模型必须包含以下字段：

```python
class Equipment(Base):
    __tablename__ = "equipment"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 数据隔离字段（必需）
    workspace_type = Column(String(20), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=True, index=True)
    access_level = Column(String(20), default="private", nullable=False)
    
    # 业务字段
    equipment_name = Column(String(200), nullable=False)
    # ...
```

**字段说明**：
- `workspace_type`：工作区类型，用于第一层隔离
- `user_id`：创建者ID，用于个人工作区隔离
- `company_id`：企业ID，用于企业工作区隔离
- `factory_id`：工厂ID，用于工厂级别隔离
- `access_level`：访问级别，用于细粒度控制

### 数据查询过滤

#### 方式1：使用 `apply_workspace_filter`（推荐）

```python
def get_equipment_by_id(self, equipment_id: int, current_user: User, 
                        workspace_context: WorkspaceContext):
    query = self.db.query(Equipment).filter(Equipment.id == equipment_id)
    
    # 应用工作区过滤
    query = self.data_access.apply_workspace_filter(
        query, Equipment, current_user, workspace_context
    )
    
    equipment = query.first()
    
    if equipment:
        # 检查访问权限
        self.data_access.check_access(
            current_user, equipment, "view", workspace_context
        )
    
    return equipment
```

#### 方式2：手动过滤 + 权限检查

```python
def get_equipment_list(self, current_user: User, workspace_context: WorkspaceContext):
    # 检查查看权限并获取访问范围
    access_info = self._check_list_permission(current_user, workspace_context)
    
    query = self.db.query(Equipment)
    
    # 个人工作区：只查询自己的数据
    if workspace_context.workspace_type == "personal":
        query = query.filter(
            Equipment.workspace_type == "personal",
            Equipment.user_id == current_user.id
        )
    
    # 企业工作区：根据data_access_scope过滤
    elif workspace_context.workspace_type == "enterprise":
        query = query.filter(
            Equipment.workspace_type == "enterprise",
            Equipment.company_id == workspace_context.company_id
        )
        
        # 工厂级别访问：只能看到所在工厂的数据
        if access_info["data_access_scope"] == "factory":
            query = query.filter(
                Equipment.factory_id == access_info["factory_id"]
            )
    
    return query.all()
```

---

## 🛡️ 权限管理实现

### 权限检查层次

```
1. 企业所有者 (company.owner_id == user.id)
   └─> 拥有所有权限，跳过后续检查

2. 企业管理员 (employee.role == "admin")
   └─> 拥有所有权限，跳过后续检查

3. 角色权限检查 (employee.company_role_id)
   └─> 检查角色的permissions字段

4. 默认权限（无角色）
   └─> view + create，edit/delete仅限自己创建的数据
```

### 创建操作权限检查

```python
def create_equipment(self, current_user: User, equipment_data: Dict, 
                     workspace_context: WorkspaceContext):
    # 企业工作区：检查创建权限
    if workspace_context.workspace_type == "enterprise":
        self._check_create_permission(current_user, workspace_context)
    
    # 检查配额
    self.quota_service.check_quota(
        current_user, workspace_context, "equipment", 1
    )
    
    # 创建设备
    equipment = Equipment(**equipment_data)
    equipment.workspace_type = workspace_context.workspace_type
    equipment.user_id = current_user.id
    equipment.company_id = workspace_context.company_id
    equipment.factory_id = workspace_context.factory_id
    
    # 设置访问级别
    if workspace_context.workspace_type == "enterprise":
        equipment.access_level = "company"  # 企业工作区默认company
    else:
        equipment.access_level = "private"  # 个人工作区默认private
    
    self.db.add(equipment)
    self.db.commit()
    
    return equipment
```

### 查看操作权限检查

```python
def _check_list_permission(self, current_user: User, 
                           workspace_context: WorkspaceContext):
    # 个人工作区：可以查看自己的数据
    if workspace_context.workspace_type == "personal":
        return {
            "can_view": True,
            "data_access_scope": "personal",
            "factory_id": None
        }
    
    # 企业工作区：检查权限
    company = self.db.query(Company).filter(
        Company.id == workspace_context.company_id
    ).first()
    
    # 企业所有者：可以查看所有数据
    if company and company.owner_id == current_user.id:
        return {
            "can_view": True,
            "data_access_scope": "company",
            "factory_id": None
        }
    
    # 获取员工信息
    employee = self.db.query(CompanyEmployee).filter(
        CompanyEmployee.user_id == current_user.id,
        CompanyEmployee.company_id == workspace_context.company_id,
        CompanyEmployee.status == "active"
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=403,
            detail="权限不足：您不是该企业的成员"
        )
    
    # 企业管理员：可以查看所有数据
    if employee.role == "admin":
        return {
            "can_view": True,
            "data_access_scope": "company",
            "factory_id": None
        }
    
    # 检查角色权限
    if employee.company_role_id:
        role = self.db.query(CompanyRole).filter(
            CompanyRole.id == employee.company_role_id,
            CompanyRole.is_active == True
        ).first()
        
        if role:
            permissions = role.permissions or {}
            equipment_permissions = permissions.get("equipment_management", {})
            
            if not equipment_permissions.get("view", False):
                raise HTTPException(
                    status_code=403,
                    detail="权限不足：您没有查看设备的权限"
                )
            
            # 返回访问范围
            data_access_scope = role.data_access_scope or employee.data_access_scope or "factory"
            return {
                "can_view": True,
                "data_access_scope": data_access_scope,
                "factory_id": employee.factory_id if data_access_scope == "factory" else None
            }
    
    # 无角色：默认可以查看，但只能查看所在工厂的数据
    return {
        "can_view": True,
        "data_access_scope": employee.data_access_scope or "factory",
        "factory_id": employee.factory_id
    }
```

### 编辑/删除操作权限检查

```python
def update_equipment(self, equipment_id: int, current_user: User, 
                     update_data: Dict, workspace_context: WorkspaceContext):
    # 获取设备（已包含数据隔离过滤）
    equipment = self.get_equipment_by_id(
        equipment_id, current_user, workspace_context
    )
    
    if not equipment:
        raise HTTPException(
            status_code=404,
            detail="设备不存在或无权访问"
        )
    
    # 检查编辑权限
    self.data_access.check_access(
        current_user, equipment, "edit", workspace_context
    )
    
    # 更新设备
    for key, value in update_data.items():
        setattr(equipment, key, value)
    
    equipment.updated_by = current_user.id
    equipment.updated_at = datetime.utcnow()
    
    self.db.commit()
    return equipment
```

---

## 📊 配额管理实现

### 会员体系架构

#### 会员等级

```python
# 个人会员等级
PERSONAL_TIERS = {
    "free": {
        "name": "个人免费版",
        "price": "免费",
        "wps_quota": 10,
        "pqr_quota": 10,
        "ppqr_quota": 0  # 免费版不支持pPQR
    },
    "personal_pro": {
        "name": "个人专业版",
        "price": "¥19/月",
        "wps_quota": 30,
        "pqr_quota": 30,
        "ppqr_quota": 30
    },
    "personal_advanced": {
        "name": "个人高级版",
        "price": "¥49/月",
        "wps_quota": 50,
        "pqr_quota": 50,
        "ppqr_quota": 50
    },
    "personal_flagship": {
        "name": "个人旗舰版",
        "price": "¥99/月",
        "wps_quota": 100,
        "pqr_quota": 100,
        "ppqr_quota": 100
    }
}

# 企业会员等级
ENTERPRISE_TIERS = {
    "enterprise": {
        "name": "企业版",
        "price": "¥199/月",
        "wps_quota": 200,
        "pqr_quota": 200,
        "ppqr_quota": 200,
        "max_employees": 10  # 多工厂数量（员工数）
    },
    "enterprise_pro": {
        "name": "企业版PRO",
        "price": "¥399/月",
        "wps_quota": 400,
        "pqr_quota": 400,
        "ppqr_quota": 400,
        "max_employees": 20
    },
    "enterprise_pro_max": {
        "name": "企业版PRO MAX",
        "price": "¥899/月",
        "wps_quota": 500,
        "pqr_quota": 500,
        "ppqr_quota": 500,
        "max_employees": 50
    }
}
```

#### 会员数据模型

```python
# 用户表
class User(Base):
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)

    # 个人会员信息
    membership_tier = Column(String(50), default="free")  # 会员等级
    membership_expires_at = Column(DateTime, nullable=True)  # 会员到期时间

    # 配额使用统计（个人工作区）
    wps_usage = Column(Integer, default=0)
    pqr_usage = Column(Integer, default=0)
    ppqr_usage = Column(Integer, default=0)

# 企业表
class Company(Base):
    id = Column(Integer, primary_key=True)
    company_name = Column(String(200))
    owner_id = Column(Integer, ForeignKey("users.id"))

    # 企业会员信息
    membership_tier = Column(String(50), default="enterprise")
    membership_expires_at = Column(DateTime, nullable=True)

    # 配额使用统计（企业工作区）
    wps_usage = Column(Integer, default=0)
    pqr_usage = Column(Integer, default=0)
    ppqr_usage = Column(Integer, default=0)
```

### 配额类型分类

```python
# 文档类模块：检查配额，受会员等级限制
DOCUMENT_MODULES = {
    "wps",      # WPS焊接工艺规程
    "pqr",      # PQR工艺评定记录
    "ppqr"      # pPQR预工艺评定记录
}

# 物理资产类模块：不检查配额，不受会员等级限制
PHYSICAL_ASSET_MODULES = {
    "equipment",  # 设备
    "materials",  # 焊材
    "welders",    # 焊工
    "production", # 生产
    "quality"     # 质量
}
```

### 配额检查流程

```python
def check_quota(
    self,
    user: User,
    workspace_context: WorkspaceContext,
    quota_type: str,
    increment: int = 1
):
    """
    检查配额

    流程：
    1. 判断是否为物理资产模块 → 跳过检查
    2. 判断工作区类型
       - 个人工作区 → 检查用户会员等级和配额
       - 企业工作区 → 检查企业会员等级和配额
    3. 获取配额限制和当前使用量
    4. 判断是否超出限制
    """

    # 物理资产模块：跳过配额检查
    if quota_type in PHYSICAL_ASSET_MODULES:
        return True

    # 个人工作区：检查用户配额
    if workspace_context.workspace_type == "personal":
        # 获取用户会员等级
        tier = user.membership_tier or "free"
        tier_config = PERSONAL_TIERS.get(tier, PERSONAL_TIERS["free"])

        # 获取配额限制
        quota_limit = tier_config.get(f"{quota_type}_quota", 0)

        # -1表示无限配额
        if quota_limit == -1:
            return True

        # 获取当前使用量
        current_usage = getattr(user, f"{quota_type}_usage", 0)

        # 检查是否超出限制
        if current_usage + increment > quota_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"配额不足：您的{tier_config['name']}配额已用完，请升级会员"
            )

    # 企业工作区：检查企业配额
    elif workspace_context.workspace_type == "enterprise":
        company = self.db.query(Company).filter(
            Company.id == workspace_context.company_id
        ).first()

        if not company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="企业不存在"
            )

        # 获取企业会员等级
        tier = company.membership_tier or "enterprise_basic"
        tier_config = ENTERPRISE_TIERS.get(tier, ENTERPRISE_TIERS["enterprise_basic"])

        # 获取配额限制
        quota_limit = tier_config.get(f"{quota_type}_quota", 0)

        # -1表示无限配额
        if quota_limit == -1:
            return True

        # 获取当前使用量
        current_usage = getattr(company, f"{quota_type}_usage", 0)

        # 检查是否超出限制
        if current_usage + increment > quota_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"配额不足：企业的{tier_config['name']}配额已用完，请升级会员"
            )

    return True
```

### 配额更新

```python
def update_quota_usage(
    self,
    user: User,
    workspace_context: WorkspaceContext,
    quota_type: str,
    increment: int = 1
):
    """
    更新配额使用量

    - increment > 0: 增加使用量（创建）
    - increment < 0: 减少使用量（删除）
    """

    # 物理资产模块：跳过配额更新
    if quota_type in PHYSICAL_ASSET_MODULES:
        return

    # 个人工作区：更新用户配额
    if workspace_context.workspace_type == "personal":
        current_usage = getattr(user, f"{quota_type}_usage", 0)
        new_usage = max(0, current_usage + increment)  # 不能小于0
        setattr(user, f"{quota_type}_usage", new_usage)
        self.db.commit()

    # 企业工作区：更新企业配额
    elif workspace_context.workspace_type == "enterprise":
        company = self.db.query(Company).filter(
            Company.id == workspace_context.company_id
        ).first()

        if company:
            current_usage = getattr(company, f"{quota_type}_usage", 0)
            new_usage = max(0, current_usage + increment)
            setattr(company, f"{quota_type}_usage", new_usage)
            self.db.commit()
```

### 会员权益对比

#### 个人会员

| 功能模块 | 免费版 | 专业版 | 高级版 | 旗舰版 |
|---------|--------|--------|--------|--------|
| **价格** | 免费 | ¥19/月 | ¥49/月 | ¥99/月 |
| **WPS** | 10 | 30 | 50 | 100 |
| **PQR** | 10 | 30 | 50 | 100 |
| **pPQR** | 0 | 30 | 50 | 100 |
| **设备** | ∞ | ∞ | ∞ | ∞ |
| **焊材** | ∞ | ∞ | ∞ | ∞ |
| **焊工** | ∞ | ∞ | ∞ | ∞ |
| **生产** | ∞ | ∞ | ∞ | ∞ |
| **质量** | ∞ | ∞ | ∞ | ∞ |

#### 企业会员

| 功能模块 | 企业版 | 企业PRO | 企业PRO MAX |
|---------|--------|---------|-------------|
| **价格** | ¥199/月 | ¥399/月 | ¥899/月 |
| **WPS** | 200 | 400 | 500 |
| **PQR** | 200 | 400 | 500 |
| **pPQR** | 200 | 400 | 500 |
| **设备** | ∞ | ∞ | ∞ |
| **焊材** | ∞ | ∞ | ∞ |
| **焊工** | ∞ | ∞ | ∞ |
| **生产** | ∞ | ∞ | ∞ |
| **质量** | ∞ | ∞ | ∞ |
| **多工厂数量** | 10人 | 20人 | 50人 |

**说明**：
- ✅ 文档类模块（WPS、PQR、pPQR）受配额限制
- ✅ 物理资产类模块（设备、焊材、焊工、生产、质量）不受配额限制
- ✅ 个人免费版不支持pPQR功能

---

## 🎯 设备管理模块实现

### 文件结构

```
backend/
├── app/
│   ├── models/
│   │   └── equipment.py          # 数据模型
│   ├── services/
│   │   └── equipment_service.py  # 业务逻辑
│   ├── api/v1/endpoints/
│   │   └── equipment.py          # API端点
│   └── core/
│       ├── data_access.py        # 数据访问控制（通用）
│       └── workspace.py          # 工作区上下文（通用）

frontend/
├── src/
│   ├── pages/Equipment/
│   │   ├── EquipmentList.tsx     # 列表页面
│   │   ├── EquipmentCreate.tsx   # 创建页面
│   │   └── EquipmentDetail.tsx   # 详情页面
│   └── services/
│       └── equipment.ts          # API服务
```

### 关键实现点

#### 1. 数据模型（equipment.py）

```python
class Equipment(Base):
    # 数据隔离字段
    workspace_type = Column(String(20), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=True)
    access_level = Column(String(20), default="private")
    
    # 审计字段
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
```

#### 2. 业务逻辑（equipment_service.py）

```python
class EquipmentService:
    def __init__(self, db: Session):
        self.db = db
        self.data_access = DataAccessMiddleware(db)
        self.quota_service = QuotaService(db)
    
    def create_equipment(self, ...):
        # 1. 权限检查
        # 2. 配额检查
        # 3. 创建数据
        # 4. 设置隔离字段
        pass
    
    def get_equipment_list(self, ...):
        # 1. 权限检查
        # 2. 数据过滤
        # 3. 返回结果
        pass
    
    def update_equipment(self, ...):
        # 1. 获取数据（含隔离过滤）
        # 2. 权限检查
        # 3. 更新数据
        pass
    
    def delete_equipment(self, ...):
        # 1. 获取数据（含隔离过滤）
        # 2. 权限检查
        # 3. 软删除
        # 4. 更新配额
        pass
```

#### 3. API端点（equipment.py）

```python
@router.post("/")
async def create_equipment(
    equipment_data: EquipmentCreate,
    workspace_type: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    # 1. 构建工作区上下文
    workspace_context = build_workspace_context(...)
    
    # 2. 调用服务层
    equipment_service = EquipmentService(db)
    equipment = equipment_service.create_equipment(
        current_user, equipment_data.dict(), workspace_context
    )
    
    # 3. 返回结果
    return {"success": True, "data": equipment}
```

---

## 📚 通用模式总结

### 模式1：CRUD操作标准流程

#### 创建（Create）
```
1. 构建工作区上下文
2. 检查创建权限（企业工作区）
3. 检查配额
4. 创建数据并设置隔离字段
5. 提交事务
6. 返回结果
```

#### 查询（Read）
```
1. 构建工作区上下文
2. 检查查看权限并获取访问范围
3. 应用数据隔离过滤
4. 应用业务过滤（搜索、状态等）
5. 返回结果
```

#### 更新（Update）
```
1. 构建工作区上下文
2. 获取数据（含隔离过滤）
3. 检查编辑权限
4. 更新数据
5. 提交事务
6. 返回结果
```

#### 删除（Delete）
```
1. 构建工作区上下文
2. 获取数据（含隔离过滤）
3. 检查删除权限
4. 软删除（设置is_active=False）
5. 更新配额使用
6. 提交事务
7. 返回结果
```

### 模式2：错误处理标准

#### 后端错误信息
```python
# 统一格式："权限不足：具体原因"
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="权限不足：您没有删除设备的权限"
)
```

#### 前端错误处理
```typescript
catch (error: any) {
  console.error('操作失败:', error)
  // API拦截器已经显示了错误消息
  // 只在网络错误时显示
  if (!error.response) {
    message.error('网络错误，请检查连接')
  }
}
```

---

## 🚀 后续模块实施指南

### 焊材管理 (Material Management)

#### 1. 数据模型
```python
class Material(Base):
    __tablename__ = "materials"
    
    # 数据隔离字段（复制设备模型）
    workspace_type = Column(String(20), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=True)
    access_level = Column(String(20), default="private")
    
    # 业务字段
    material_name = Column(String(200), nullable=False)
    material_code = Column(String(100), unique=True)
    material_type = Column(String(50))  # 焊条、焊丝、焊剂等
    specification = Column(String(200))
    manufacturer = Column(String(200))
    # ...
```

#### 2. 权限配置
```python
# 在CompanyRole.permissions中添加
{
  "material_management": {
    "view": true,
    "create": true,
    "edit": true,
    "delete": true
  }
}
```

#### 3. 服务层实现
```python
class MaterialService:
    def __init__(self, db: Session):
        self.db = db
        self.data_access = DataAccessMiddleware(db)
        self.quota_service = QuotaService(db)
    
    # 复制设备服务的方法，修改模型名称
    def create_material(self, ...):
        # 与create_equipment相同的逻辑
        pass
    
    def get_material_list(self, ...):
        # 与get_equipment_list相同的逻辑
        pass
```

#### 4. API端点
```python
# 复制equipment.py，修改路由和模型
@router.post("/")
async def create_material(...):
    pass
```

### 焊工管理 (Welder Management)

#### 1. 数据模型
```python
class Welder(Base):
    __tablename__ = "welders"
    
    # 数据隔离字段（相同）
    workspace_type = Column(String(20), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=True)
    access_level = Column(String(20), default="private")
    
    # 业务字段
    welder_name = Column(String(100), nullable=False)
    welder_code = Column(String(100), unique=True)
    certificate_number = Column(String(100))
    certificate_type = Column(String(50))
    valid_until = Column(Date)
    # ...
```

#### 2. 权限配置
```python
{
  "welder_management": {
    "view": true,
    "create": true,
    "edit": true,
    "delete": true
  }
}
```

### 生产管理 (Production Management)

#### 1. 数据模型
```python
class ProductionRecord(Base):
    __tablename__ = "production_records"
    
    # 数据隔离字段（相同）
    workspace_type = Column(String(20), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=True)
    access_level = Column(String(20), default="private")
    
    # 业务字段
    production_date = Column(Date, nullable=False)
    project_name = Column(String(200))
    wps_id = Column(Integer, ForeignKey("wps.id"))
    welder_id = Column(Integer, ForeignKey("welders.id"))
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    # ...
```

### 质量管理 (Quality Management)

#### 1. 数据模型
```python
class QualityInspection(Base):
    __tablename__ = "quality_inspections"
    
    # 数据隔离字段（相同）
    workspace_type = Column(String(20), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=True)
    access_level = Column(String(20), default="private")
    
    # 业务字段
    inspection_date = Column(Date, nullable=False)
    inspection_type = Column(String(50))  # 外观检查、无损检测等
    production_record_id = Column(Integer, ForeignKey("production_records.id"))
    result = Column(String(20))  # 合格、不合格
    # ...
```

---

## ✅ 实施检查清单

### 新模块开发检查清单

#### 数据模型
- [ ] 包含所有数据隔离字段（workspace_type, user_id, company_id, factory_id, access_level）
- [ ] 包含审计字段（created_by, updated_by, created_at, updated_at, is_active）
- [ ] 添加必要的索引（workspace_type, user_id, company_id, factory_id）

#### 服务层
- [ ] 初始化DataAccessMiddleware和QuotaService
- [ ] create方法：检查权限、检查配额、设置隔离字段
- [ ] get_list方法：检查权限、应用数据过滤
- [ ] update方法：获取数据、检查权限、更新数据
- [ ] delete方法：获取数据、检查权限、软删除、更新配额

#### API端点
- [ ] 构建工作区上下文
- [ ] 调用服务层方法
- [ ] 统一错误处理
- [ ] 返回标准格式

#### 权限配置
- [ ] 在CompanyRole.permissions中添加模块权限
- [ ] 在DataAccessMiddleware中添加资源名称映射
- [ ] 测试各种权限场景

#### 前端
- [ ] 列表页面：显示数据、权限控制按钮
- [ ] 创建页面：表单验证、错误处理
- [ ] 详情页面：显示详情、操作按钮
- [ ] 错误处理：避免重复显示错误

---

## 🎯 总结

### 核心优势

1. **统一架构**：所有模块使用相同的数据隔离和权限管理模式
2. **高度可复用**：核心服务（DataAccessMiddleware、QuotaService）可被所有模块使用
3. **易于扩展**：新模块只需复制模式，修改业务逻辑
4. **安全可靠**：多层权限检查，确保数据安全

### 关键要点

1. **数据隔离**：通过workspace_type、user_id、company_id实现
2. **权限控制**：企业所有者 > 管理员 > 角色权限 > 默认权限
3. **配额管理**：文档类检查配额，物理资产类跳过
4. **错误提示**：统一格式，友好清晰

### 后续模块实施

按照本文档的模式，后续模块（焊材、焊工、生产、质量）可以快速实现：
1. 复制设备管理的代码结构
2. 修改模型名称和业务字段
3. 添加权限配置
4. 测试各种场景

---

**通过统一的架构模式，我们可以快速、安全地实现所有业务模块！** 🚀

