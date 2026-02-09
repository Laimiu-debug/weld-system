# 数据隔离和工作区架构设计

## 一、系统现状总结

### 已完成的核心功能

#### 1. 用户认证和会员体系 ✅
- **用户模型**: User表包含基础信息、会员等级、配额字段
- **会员类型**: 
  - 个人会员: free, professional, advanced, flagship
  - 企业会员: enterprise, enterprise_pro, enterprise_pro_max
- **认证系统**: JWT Token认证、登录/注册、密码重置

#### 2. 企业管理系统 ✅
- **企业模型**: Company表（企业信息、配额限制）
- **工厂模型**: Factory表（工厂信息、地址、联系方式）
- **员工模型**: CompanyEmployee表（员工关系、角色、权限）
- **角色模型**: CompanyRole表（企业角色、权限配置）

#### 3. 业务模块 ✅
- **WPS管理**: 完整的WPS数据模型和CRUD操作
- **PQR管理**: 完整的PQR数据模型和CRUD操作
- **pPQR管理**: 基础的pPQR功能（需要完善）

#### 4. 权限系统 ✅
- **系统角色**: Role和Permission表
- **企业角色**: CompanyRole表（企业级角色管理）
- **权限检查**: 基础的权限检查中间件

### 现有问题和缺失功能

#### 1. 数据隔离不完整 ❌
- WPS/PQR模型只有owner_id，缺少company_id和factory_id
- 没有workspace_type字段区分个人/企业数据
- 无法实现个人工作区和企业工作区的隔离

#### 2. 缺少业务模块 ❌
- 焊材管理（materials）模型不存在
- 焊工管理（welders）模型不存在
- 设备管理（equipment）模型不存在
- 生产管理（production）模型不存在
- 质量管理（quality）模型不存在

#### 3. 配额管理不完善 ❌
- 企业配额池未实现
- 个人配额和企业配额混淆
- 无法区分个人工作区和企业工作区的配额使用

#### 4. 跨工厂数据隔离未实现 ❌
- 无法控制不同工厂间的数据可见性
- 缺少工厂级别的数据访问控制

---

## 二、核心架构设计

### 1. 双工作区模型

#### 1.1 工作区类型定义
```python
class WorkspaceType(str, Enum):
    PERSONAL = "personal"      # 个人工作区
    ENTERPRISE = "enterprise"  # 企业工作区
```

#### 1.2 工作区特性对比

| 特性 | 个人工作区 | 企业工作区 |
|------|-----------|-----------|
| **数据所有权** | 个人独占 | 企业共享 |
| **配额来源** | 个人会员等级 | 企业会员等级 |
| **数据可见性** | 仅创建者可见 | 企业成员可见（根据权限） |
| **数据编辑权** | 仅创建者可编辑 | 根据角色权限决定 |
| **工厂关联** | 无 | 可关联到具体工厂 |
| **配额共享** | 否 | 是（所有成员共享） |

#### 1.3 工作区切换机制
```python
# 用户上下文包含当前工作区信息
class UserContext:
    user_id: int
    workspace_type: WorkspaceType
    company_id: Optional[int]  # 企业工作区时有值
    factory_id: Optional[int]  # 可选的工厂过滤
    permissions: Dict[str, bool]  # 当前工作区的权限
```

### 2. 数据模型统一规范

#### 2.1 所有业务模块必须包含的字段
```python
class BaseBusinessModel(Base):
    """所有业务模块的基类"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 数据隔离核心字段
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    workspace_type = Column(String(20), nullable=False, default="personal", index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=True, index=True)
    
    # 数据访问控制
    is_shared = Column(Boolean, default=False)  # 是否在企业内共享
    access_level = Column(String(20), default="private")  # private, factory, company
    
    # 审计字段
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
```

#### 2.2 数据访问级别定义
```python
class AccessLevel(str, Enum):
    PRIVATE = "private"      # 仅创建者可见
    FACTORY = "factory"      # 同工厂成员可见
    COMPANY = "company"      # 全公司成员可见
    PUBLIC = "public"        # 公开（用于模板等）
```

### 3. 配额管理体系

#### 3.1 个人配额管理
```python
class PersonalQuota:
    """个人会员配额"""
    user_id: int
    membership_tier: str  # free, professional, advanced, flagship
    
    # 个人工作区配额
    wps_quota: int
    pqr_quota: int
    ppqr_quota: int
    storage_quota: int  # MB
    
    # 已使用配额（仅统计个人工作区）
    wps_used: int
    pqr_used: int
    ppqr_used: int
    storage_used: int
```

#### 3.2 企业配额管理
```python
class EnterpriseQuota:
    """企业配额池"""
    company_id: int
    owner_id: int  # 企业创始人
    membership_tier: str  # enterprise, enterprise_pro, enterprise_pro_max
    
    # 企业配额池（由创始人会员等级决定）
    total_wps_quota: int
    total_pqr_quota: int
    total_ppqr_quota: int
    total_storage_quota: int  # MB
    
    # 已使用配额（所有成员共享）
    wps_used: int
    pqr_used: int
    ppqr_used: int
    storage_used: int
    
    # 成员限制
    max_employees: int
    max_factories: int
    current_employees: int
    current_factories: int
```

### 4. 数据访问权限矩阵

#### 4.1 个人工作区权限
| 操作 | 数据创建者 | 其他用户 |
|------|-----------|---------|
| 查看 | ✅ | ❌ |
| 编辑 | ✅ | ❌ |
| 删除 | ✅ | ❌ |
| 导出 | ✅ | ❌ |

#### 4.2 企业工作区权限（基于角色）
| 操作 | 管理员 | 经理 | 普通员工 | 只读员工 |
|------|-------|------|---------|---------|
| 查看全部数据 | ✅ | ✅ | ✅ | ✅ |
| 创建数据 | ✅ | ✅ | ✅ | ❌ |
| 编辑自己的数据 | ✅ | ✅ | ✅ | ❌ |
| 编辑他人的数据 | ✅ | ✅ | ❌ | ❌ |
| 删除数据 | ✅ | ✅ | ❌ | ❌ |
| 导出数据 | ✅ | ✅ | ✅ | ✅ |
| 管理员工 | ✅ | ❌ | ❌ | ❌ |

#### 4.3 跨工厂数据访问控制
```python
class FactoryDataAccess:
    """工厂数据访问配置"""
    company_id: int
    source_factory_id: int  # 数据所属工厂
    target_factory_id: int  # 访问者所属工厂
    
    # 访问权限配置
    can_view: bool = False
    can_edit: bool = False
    can_delete: bool = False
    
    # 模块级别的访问控制
    module_permissions: Dict[str, Dict[str, bool]] = {
        "wps": {"view": True, "edit": False, "delete": False},
        "pqr": {"view": True, "edit": False, "delete": False},
        "materials": {"view": False, "edit": False, "delete": False},
        # ...
    }
```

---

## 三、实施方案

### 阶段一：数据模型扩展（优先级：🔴 最高）

#### 1. 更新现有模型
- [ ] WPS模型添加workspace_type, company_id, factory_id, access_level
- [ ] PQR模型添加workspace_type, company_id, factory_id, access_level
- [ ] pPQR模型添加workspace_type, company_id, factory_id, access_level

#### 2. 创建新业务模块模型
- [ ] WeldingMaterial（焊材管理）
- [ ] Welder（焊工管理）
- [ ] Equipment（设备管理）
- [ ] ProductionTask（生产管理）
- [ ] QualityInspection（质量管理）

#### 3. 创建配额管理模型
- [ ] UserQuotaUsage（用户配额使用记录）
- [ ] CompanyQuotaUsage（企业配额使用记录）

### 阶段二：权限和访问控制（优先级：🔴 最高）

#### 1. 创建数据访问中间件
```python
class DataAccessMiddleware:
    """统一的数据访问权限检查"""
    
    async def check_access(
        self,
        user: User,
        resource: BaseBusinessModel,
        action: str,  # view, edit, delete
        db: Session
    ) -> bool:
        # 1. 个人工作区数据：仅创建者可访问
        if resource.workspace_type == WorkspaceType.PERSONAL:
            return resource.user_id == user.id
        
        # 2. 企业工作区数据：检查企业成员身份和权限
        if resource.workspace_type == WorkspaceType.ENTERPRISE:
            return await self._check_enterprise_access(user, resource, action, db)
        
        return False
    
    async def _check_enterprise_access(
        self,
        user: User,
        resource: BaseBusinessModel,
        action: str,
        db: Session
    ) -> bool:
        # 获取员工信息
        employee = db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == user.id,
            CompanyEmployee.company_id == resource.company_id,
            CompanyEmployee.status == "active"
        ).first()
        
        if not employee:
            return False
        
        # 检查工厂级别访问控制
        if resource.factory_id and employee.factory_id != resource.factory_id:
            # 检查跨工厂访问权限
            has_cross_factory_access = await self._check_cross_factory_access(
                employee, resource, action, db
            )
            if not has_cross_factory_access:
                return False
        
        # 检查角色权限
        return await self._check_role_permission(employee, resource, action, db)
```

#### 2. 实现配额检查中间件
```python
class QuotaMiddleware:
    """配额检查中间件"""
    
    async def check_quota(
        self,
        user: User,
        workspace_type: WorkspaceType,
        resource_type: str,  # wps, pqr, ppqr, etc.
        db: Session
    ) -> bool:
        if workspace_type == WorkspaceType.PERSONAL:
            return await self._check_personal_quota(user, resource_type, db)
        else:
            return await self._check_enterprise_quota(user, resource_type, db)
```

### 阶段三：API层实现（优先级：🟡 高）

#### 1. 工作区切换API
```python
@router.post("/workspace/switch")
async def switch_workspace(
    workspace_type: WorkspaceType,
    company_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """切换工作区"""
    # 验证切换请求
    # 更新用户上下文
    # 返回新的工作区信息和权限
```

#### 2. 统一的数据查询API
```python
@router.get("/{module}/list")
async def list_resources(
    module: str,
    workspace_type: Optional[WorkspaceType] = None,
    factory_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """统一的资源列表查询"""
    # 根据工作区类型和权限过滤数据
    # 应用工厂级别过滤
    # 返回用户有权访问的数据
```

### 阶段四：数据库迁移（优先级：🟡 高）

#### 1. 创建Alembic迁移脚本
```bash
# 添加workspace_type等字段到现有表
alembic revision -m "add_workspace_fields_to_existing_tables"

# 创建新的业务模块表
alembic revision -m "create_business_module_tables"

# 创建配额管理表
alembic revision -m "create_quota_management_tables"
```

#### 2. 数据迁移策略
- 现有数据默认设置为个人工作区（workspace_type='personal'）
- company_id和factory_id设置为NULL
- 保持向后兼容性

---

## 四、技术实现细节

### 1. 数据查询过滤器
```python
def apply_workspace_filter(
    query: Query,
    user: User,
    workspace_type: Optional[WorkspaceType] = None,
    company_id: Optional[int] = None,
    factory_id: Optional[int] = None
) -> Query:
    """应用工作区过滤"""
    
    if workspace_type == WorkspaceType.PERSONAL or not workspace_type:
        # 个人工作区：只查询用户自己的数据
        query = query.filter(
            Model.workspace_type == WorkspaceType.PERSONAL,
            Model.user_id == user.id
        )
    elif workspace_type == WorkspaceType.ENTERPRISE:
        # 企业工作区：查询企业内有权访问的数据
        if company_id:
            query = query.filter(
                Model.workspace_type == WorkspaceType.ENTERPRISE,
                Model.company_id == company_id
            )
            
            # 应用工厂过滤
            if factory_id:
                query = query.filter(Model.factory_id == factory_id)
    
    return query
```

### 2. 配额使用统计
```python
async def update_quota_usage(
    user_id: int,
    workspace_type: WorkspaceType,
    resource_type: str,
    operation: str,  # create, delete
    db: Session
):
    """更新配额使用情况"""
    
    if workspace_type == WorkspaceType.PERSONAL:
        # 更新个人配额
        user = db.query(User).filter(User.id == user_id).first()
        if operation == "create":
            setattr(user, f"{resource_type}_quota_used", 
                   getattr(user, f"{resource_type}_quota_used") + 1)
        elif operation == "delete":
            setattr(user, f"{resource_type}_quota_used",
                   max(0, getattr(user, f"{resource_type}_quota_used") - 1))
    else:
        # 更新企业配额
        employee = db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == user_id
        ).first()
        
        if employee:
            company = db.query(Company).filter(
                Company.id == employee.company_id
            ).first()
            
            if operation == "create":
                setattr(company, f"{resource_type}_quota_used",
                       getattr(company, f"{resource_type}_quota_used") + 1)
            elif operation == "delete":
                setattr(company, f"{resource_type}_quota_used",
                       max(0, getattr(company, f"{resource_type}_quota_used") - 1))
    
    db.commit()
```

---

## 五、前端集成方案

### 1. 工作区切换组件
```typescript
interface WorkspaceContext {
  workspaceType: 'personal' | 'enterprise'
  companyId?: number
  factoryId?: number
  permissions: Record<string, boolean>
  quota: {
    total: number
    used: number
    remaining: number
  }
}

// 工作区切换器
const WorkspaceSwitcher: React.FC = () => {
  const [workspace, setWorkspace] = useState<WorkspaceContext>()
  
  const switchWorkspace = async (type: 'personal' | 'enterprise') => {
    const response = await api.post('/workspace/switch', { workspace_type: type })
    setWorkspace(response.data)
  }
  
  return (
    <Select value={workspace?.workspaceType} onChange={switchWorkspace}>
      <Option value="personal">个人工作区</Option>
      <Option value="enterprise">企业工作区</Option>
    </Select>
  )
}
```

### 2. 数据列表过滤
```typescript
// 自动应用工作区过滤
const fetchData = async (params: any) => {
  const workspace = getWorkspaceContext()
  
  const response = await api.get('/wps/list', {
    params: {
      ...params,
      workspace_type: workspace.workspaceType,
      company_id: workspace.companyId,
      factory_id: workspace.factoryId
    }
  })
  
  return response.data
}
```

---

## 六、测试计划

### 1. 单元测试
- [ ] 数据访问权限检查
- [ ] 配额计算和更新
- [ ] 工作区切换逻辑

### 2. 集成测试
- [ ] 个人工作区数据隔离
- [ ] 企业工作区数据共享
- [ ] 跨工厂数据访问控制
- [ ] 配额池管理

### 3. 端到端测试
- [ ] 用户创建个人数据
- [ ] 用户加入企业后切换工作区
- [ ] 企业管理员配置跨工厂权限
- [ ] 配额耗尽时的行为

---

## 七、部署和迁移

### 1. 数据库迁移步骤
```bash
# 1. 备份数据库
pg_dump weld_db > backup_$(date +%Y%m%d).sql

# 2. 运行迁移
alembic upgrade head

# 3. 验证迁移
python verify_migration.py

# 4. 更新现有数据
python migrate_existing_data.py
```

### 2. 回滚计划
- 保留原有API兼容性
- 提供数据回滚脚本
- 监控系统性能和错误率

---

## 八、后续优化

### 1. 性能优化
- 添加数据库索引（workspace_type, company_id, factory_id）
- 实现查询结果缓存
- 优化复杂权限检查逻辑

### 2. 功能增强
- 数据导入导出（跨工作区）
- 数据模板共享
- 审计日志增强
- 数据统计和报表（分工作区）

---

*文档创建时间: 2025-10-18*
*最后更新: 2025-10-18*

