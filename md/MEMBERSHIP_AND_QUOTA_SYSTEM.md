# 💎 会员体系与配额管理系统

## 📋 目录

1. [会员体系概述](#会员体系概述)
2. [会员等级配置](#会员等级配置)
3. [配额管理机制](#配额管理机制)
4. [实现细节](#实现细节)
5. [新模块集成指南](#新模块集成指南)

---

## 🎯 会员体系概述

### 双轨会员制

系统采用**个人会员**和**企业会员**双轨制：

```
用户
├─> 个人工作区
│   └─> 使用个人会员配额（User.membership_tier）
│
└─> 企业工作区
    └─> 使用企业会员配额（Company.membership_tier）
```

**关键特点**：
- ✅ 个人和企业配额**完全独立**
- ✅ 同一用户在不同工作区使用不同配额
- ✅ 物理资产模块**不受配额限制**
- ✅ 文档类模块**受配额限制**

---

## 💎 会员等级配置

### 个人会员等级

| 等级 | 代码 | 价格 | WPS配额 | PQR配额 | pPQR配额 | 物理资产 | 多工厂数量 |
|------|------|------|---------|---------|----------|----------|-----------|
| 个人免费版 | `free` | 免费 | 10个 | 10个 | 0（不支持） | ∞ | - |
| 个人专业版 | `personal_pro` | ¥19/月 | 30个 | 30个 | 30个 | ∞ | - |
| 个人高级版 | `personal_advanced` | ¥49/月 | 50个 | 50个 | 50个 | ∞ | - |
| 个人旗舰版 | `personal_flagship` | ¥99/月 | 100个 | 100个 | 100个 | ∞ | - |

### 企业会员等级

| 等级 | 代码 | 价格 | WPS配额 | PQR配额 | pPQR配额 | 物理资产 | 多工厂数量 |
|------|------|------|---------|---------|----------|----------|-----------|
| 企业版 | `enterprise` | ¥199/月 | 200个 | 200个 | 200个 | ∞ | 10人 |
| 企业版PRO | `enterprise_pro` | ¥399/月 | 400个 | 400个 | 400个 | ∞ | 20人 |
| 企业版PRO MAX | `enterprise_pro_max` | ¥899/月 | 500个 | 500个 | 500个 | ∞ | 50人 |

**注意**：
- ✅ 个人免费版不支持pPQR功能
- ✅ 物理资产模块（设备、焊材、焊工、生产、质量）所有等级都不受限制
- ✅ 多工厂数量仅适用于企业版

**配置文件位置**：
- `backend/app/core/config.py`
- `frontend/src/config/membership.ts`

---

## 📊 配额管理机制

### 模块分类

#### 文档类模块（受配额限制）

```python
DOCUMENT_MODULES = {
    "wps",      # WPS焊接工艺规程
    "pqr",      # PQR工艺评定记录
    "ppqr"      # pPQR预工艺评定记录
}
```

**特点**：
- ✅ 创建时检查配额
- ✅ 创建成功后增加使用量
- ✅ 删除后减少使用量
- ✅ 受会员等级限制

#### 物理资产类模块（不受配额限制）

```python
PHYSICAL_ASSET_MODULES = {
    "equipment",   # 设备管理
    "materials",   # 焊材管理
    "welders",     # 焊工管理
    "production",  # 生产管理
    "quality"      # 质量管理
}
```

**特点**：
- ✅ 创建时**不检查配额**
- ✅ 删除时**不更新配额**
- ✅ **不受会员等级限制**
- ✅ 所有会员等级都可以无限创建

### 配额检查流程

```
创建资源
    ↓
判断模块类型
    ├─> 物理资产模块 → 跳过配额检查 → 直接创建 ✅
    │
    └─> 文档类模块
        ↓
    判断工作区类型
        ├─> 个人工作区
        │   ├─> 获取用户会员等级
        │   ├─> 获取配额限制
        │   ├─> 获取当前使用量
        │   └─> 判断是否超出限制
        │       ├─> 未超出 → 创建 ✅
        │       └─> 超出 → 提示升级会员 ❌
        │
        └─> 企业工作区
            ├─> 获取企业会员等级
            ├─> 获取配额限制
            ├─> 获取当前使用量
            └─> 判断是否超出限制
                ├─> 未超出 → 创建 ✅
                └─> 超出 → 提示升级会员 ❌
```

---

## 🔧 实现细节

### 数据模型

#### 用户表（User）

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    
    # ============ 个人会员信息 ============
    membership_tier = Column(String(50), default="free", comment="会员等级")
    membership_expires_at = Column(DateTime, nullable=True, comment="会员到期时间")
    
    # ============ 个人工作区配额使用统计 ============
    wps_usage = Column(Integer, default=0, comment="WPS使用量")
    pqr_usage = Column(Integer, default=0, comment="PQR使用量")
    ppqr_usage = Column(Integer, default=0, comment="pPQR使用量")
    
    # 注意：物理资产模块不需要usage字段
```

#### 企业表（Company）

```python
class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True)
    company_name = Column(String(200))
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # ============ 企业会员信息 ============
    membership_tier = Column(String(50), default="enterprise", comment="会员等级")
    membership_expires_at = Column(DateTime, nullable=True, comment="会员到期时间")
    
    # ============ 企业工作区配额使用统计 ============
    wps_usage = Column(Integer, default=0, comment="WPS使用量")
    pqr_usage = Column(Integer, default=0, comment="PQR使用量")
    ppqr_usage = Column(Integer, default=0, comment="pPQR使用量")
    
    # 注意：物理资产模块不需要usage字段
```

### 配额服务（QuotaService）

#### 配额检查

```python
class QuotaService:
    def check_quota(
        self,
        user: User,
        workspace_context: WorkspaceContext,
        quota_type: str,
        increment: int = 1
    ):
        """
        检查配额
        
        Args:
            user: 当前用户
            workspace_context: 工作区上下文
            quota_type: 配额类型（wps/pqr/ppqr/equipment/materials等）
            increment: 增量（通常为1）
        
        Returns:
            True: 配额充足
        
        Raises:
            HTTPException: 配额不足
        """
        
        # 1. 物理资产模块：直接返回True
        if quota_type in ["equipment", "materials", "welders", "production", "quality"]:
            return True
        
        # 2. 文档类模块：检查配额
        if workspace_context.workspace_type == "personal":
            return self._check_personal_quota(user, quota_type, increment)
        elif workspace_context.workspace_type == "enterprise":
            return self._check_enterprise_quota(
                workspace_context.company_id, quota_type, increment
            )
    
    def _check_personal_quota(self, user: User, quota_type: str, increment: int):
        """检查个人工作区配额"""
        # 获取会员等级配置
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
                detail=f"配额不足：您的{tier_config['name']}配额已用完（{current_usage}/{quota_limit}），请升级会员"
            )
        
        return True
    
    def _check_enterprise_quota(self, company_id: int, quota_type: str, increment: int):
        """检查企业工作区配额"""
        company = self.db.query(Company).filter(Company.id == company_id).first()

        if not company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="企业不存在"
            )

        # 获取会员等级配置
        tier = company.membership_tier or "enterprise"
        tier_config = ENTERPRISE_TIERS.get(tier, ENTERPRISE_TIERS["enterprise"])
        
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
                detail=f"配额不足：企业的{tier_config['name']}配额已用完（{current_usage}/{quota_limit}），请升级会员"
            )
        
        return True
```

#### 配额更新

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
    
    Args:
        user: 当前用户
        workspace_context: 工作区上下文
        quota_type: 配额类型
        increment: 增量（正数=增加，负数=减少）
    """
    
    # 1. 物理资产模块：直接返回
    if quota_type in ["equipment", "materials", "welders", "production", "quality"]:
        return
    
    # 2. 文档类模块：更新配额
    if workspace_context.workspace_type == "personal":
        self._update_personal_quota(user, quota_type, increment)
    elif workspace_context.workspace_type == "enterprise":
        self._update_enterprise_quota(
            workspace_context.company_id, quota_type, increment
        )

def _update_personal_quota(self, user: User, quota_type: str, increment: int):
    """更新个人工作区配额"""
    current_usage = getattr(user, f"{quota_type}_usage", 0)
    new_usage = max(0, current_usage + increment)  # 不能小于0
    setattr(user, f"{quota_type}_usage", new_usage)
    self.db.commit()

def _update_enterprise_quota(self, company_id: int, quota_type: str, increment: int):
    """更新企业工作区配额"""
    company = self.db.query(Company).filter(Company.id == company_id).first()
    
    if company:
        current_usage = getattr(company, f"{quota_type}_usage", 0)
        new_usage = max(0, current_usage + increment)
        setattr(company, f"{quota_type}_usage", new_usage)
        self.db.commit()
```

---

## 🚀 新模块集成指南

### 文档类模块（需要配额管理）

#### 示例：WPS模块

```python
class WPSService:
    def __init__(self, db: Session):
        self.db = db
        self.quota_service = QuotaService(db)
    
    def create_wps(self, current_user: User, wps_data: Dict, 
                   workspace_context: WorkspaceContext):
        # 1. 检查配额
        self.quota_service.check_quota(
            current_user, workspace_context, "wps", 1
        )
        
        # 2. 创建WPS
        wps = WPS(**wps_data)
        self.db.add(wps)
        self.db.commit()
        
        # 3. 更新配额使用（创建成功后）
        self.quota_service.update_quota_usage(
            current_user, workspace_context, "wps", 1
        )
        
        return wps
    
    def delete_wps(self, wps_id: int, current_user: User,
                   workspace_context: WorkspaceContext):
        # 1. 删除WPS
        wps = self.get_wps_by_id(wps_id, current_user, workspace_context)
        wps.is_active = False
        self.db.commit()
        
        # 2. 更新配额使用（减少）
        self.quota_service.update_quota_usage(
            current_user, workspace_context, "wps", -1
        )
        
        return True
```

### 物理资产类模块（不需要配额管理）

#### 示例：焊材模块

```python
class MaterialService:
    def __init__(self, db: Session):
        self.db = db
        self.quota_service = QuotaService(db)  # 仍然需要初始化
    
    def create_material(self, current_user: User, material_data: Dict,
                        workspace_context: WorkspaceContext):
        # 1. 检查配额（物理资产模块会自动跳过）
        self.quota_service.check_quota(
            current_user, workspace_context, "materials", 1
        )
        
        # 2. 创建焊材
        material = Material(**material_data)
        self.db.add(material)
        self.db.commit()
        
        # 3. 更新配额使用（物理资产模块会自动跳过）
        self.quota_service.update_quota_usage(
            current_user, workspace_context, "materials", 1
        )
        
        return material
    
    def delete_material(self, material_id: int, current_user: User,
                        workspace_context: WorkspaceContext):
        # 1. 删除焊材
        material = self.get_material_by_id(material_id, current_user, workspace_context)
        material.is_active = False
        self.db.commit()
        
        # 2. 更新配额使用（物理资产模块会自动跳过）
        self.quota_service.update_quota_usage(
            current_user, workspace_context, "materials", -1
        )
        
        return True
```

**关键点**：
- ✅ 物理资产模块**仍然调用**配额检查和更新方法
- ✅ QuotaService内部会**自动判断**模块类型并跳过
- ✅ 这样保持了代码的**一致性**和**可维护性**

---

## ✅ 实施检查清单

### 新增文档类模块

- [ ] 在`DOCUMENT_MODULES`中添加模块名称
- [ ] 在`User`表中添加`{module}_usage`字段
- [ ] 在`Company`表中添加`{module}_usage`字段
- [ ] 在`PERSONAL_TIERS`中配置各等级配额
- [ ] 在`ENTERPRISE_TIERS`中配置各等级配额
- [ ] 在创建方法中调用`check_quota()`
- [ ] 在创建成功后调用`update_quota_usage(+1)`
- [ ] 在删除方法中调用`update_quota_usage(-1)`
- [ ] 测试配额限制功能
- [ ] 测试配额使用统计

### 新增物理资产类模块

- [ ] 在`PHYSICAL_ASSET_MODULES`中添加模块名称
- [ ] **不需要**在`User`表中添加usage字段
- [ ] **不需要**在`Company`表中添加usage字段
- [ ] **不需要**配置配额限制
- [ ] 在创建方法中调用`check_quota()`（会自动跳过）
- [ ] 在删除方法中调用`update_quota_usage()`（会自动跳过）
- [ ] 测试可以无限创建

---

## 🎯 总结

### 核心原则

1. **双轨会员制**：个人和企业配额完全独立
2. **模块分类**：文档类受限，物理资产不受限
3. **统一接口**：所有模块都调用相同的配额方法
4. **自动判断**：QuotaService内部自动判断是否需要检查

### 优势

1. ✅ **代码一致性**：所有模块使用相同的配额管理代码
2. ✅ **易于维护**：新增模块只需添加到对应分类
3. ✅ **灵活配置**：可以轻松调整各等级的配额限制
4. ✅ **用户友好**：物理资产模块不受限制，降低使用门槛

### 注意事项

1. ⚠️ 物理资产模块**仍然需要调用**配额方法（保持一致性）
2. ⚠️ 配额类型名称必须与模块名称**完全一致**
3. ⚠️ 删除操作必须调用`update_quota_usage(-1)`来释放配额
4. ⚠️ 配额检查应该在**权限检查之后**，避免浪费检查

---

**通过这套会员体系和配额管理系统，我们可以灵活地控制不同模块的使用限制，同时保持代码的简洁和一致性！** 🚀

