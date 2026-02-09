# 企业员工管理模块 - 开发指南

## 📋 模块概述

### 功能定位
企业员工管理模块用于企业会员管理员工账号、分配权限、管理工厂和部门，实现企业内部的协作管理。

### 适用场景
- 企业员工账号管理
- 员工权限分配
- 工厂和部门管理
- 员工工作量统计
- 跨工厂数据管理

### 开发优先级
**第二阶段** - 重要功能，优先开发

---

## 🎯 会员权限

### 访问权限
| 会员等级 | 访问权限 | 功能范围 |
|---------|---------|---------|
| 游客模式 | ❌ 不可访问 | - |
| 个人免费版 | ❌ 不可访问 | - |
| 个人专业版 | ❌ 不可访问 | - |
| 个人高级版 | ❌ 不可访问 | - |
| 个人旗舰版 | ❌ 不可访问 | - |
| 企业版 | ✅ 可访问 | 完整功能（1工厂，10员工） |
| 企业PRO | ✅ 可访问 | 完整功能（3工厂，20员工） |
| 企业PRO MAX | ✅ 可访问 | 完整功能（5工厂，50员工） |

**重要说明**:
- 企业员工管理功能**仅对企业会员开放**（企业版、企业PRO、企业PRO MAX）
- 个人会员（包括旗舰版）无法访问此功能
- 员工默认继承**个人专业版**权限
- 企业管理员可以额外分配或限制员工权限

---

## 📊 功能清单

### 1. 员工管理
- **邀请员工**: 通过邮箱邀请员工加入
- **员工列表**: 查看所有员工
- **员工详情**: 查看员工详细信息
- **停用员工**: 停用员工账号
- **删除员工**: 删除员工账号
- **员工搜索**: 搜索员工

### 2. 权限管理
- **角色分配**: 分配员工角色（管理员、普通员工）
- **权限设置**: 设置员工权限
- **模块访问**: 控制员工可访问的模块
- **数据权限**: 控制员工可访问的数据范围
- **操作权限**: 控制员工可执行的操作

### 3. 工厂管理
- **创建工厂**: 创建新工厂
- **编辑工厂**: 修改工厂信息
- **删除工厂**: 删除工厂
- **工厂分配**: 分配员工到工厂
- **工厂切换**: 员工切换工作工厂

### 4. 部门管理
- **创建部门**: 创建部门
- **编辑部门**: 修改部门信息
- **删除部门**: 删除部门
- **部门分配**: 分配员工到部门

### 5. 员工统计
- **员工数量**: 统计员工数量
- **活跃度统计**: 统计员工活跃度
- **工作量统计**: 统计员工工作量
- **权限分布**: 统计权限分布

### 6. 邀请管理
- **发送邀请**: 发送邀请邮件
- **邀请列表**: 查看所有邀请
- **取消邀请**: 取消未接受的邀请
- **重新发送**: 重新发送邀请

---

## 🗄️ 数据模型

### 员工邀请表
```sql
CREATE TABLE employee_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    invited_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 邀请信息
    email VARCHAR(255) NOT NULL,                   -- 被邀请人邮箱
    invitation_code VARCHAR(100) UNIQUE NOT NULL,  -- 邀请码
    status VARCHAR(50) DEFAULT 'pending',          -- 状态: pending, accepted, expired, cancelled
    
    -- 权限设置
    role VARCHAR(50) DEFAULT 'employee',           -- 角色: admin, employee
    factory_id UUID REFERENCES factories(id),      -- 分配的工厂
    department_id UUID REFERENCES departments(id), -- 分配的部门
    permissions JSONB,                             -- 权限设置
    
    -- 时间信息
    expires_at TIMESTAMP,                          -- 过期时间
    accepted_at TIMESTAMP,                         -- 接受时间
    accepted_by UUID REFERENCES users(id),         -- 接受人
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_company (company_id),
    INDEX idx_email (email),
    INDEX idx_invitation_code (invitation_code),
    INDEX idx_status (status)
);
```

### 员工关系表
```sql
CREATE TABLE company_employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 员工信息
    employee_number VARCHAR(100),                  -- 员工编号
    role VARCHAR(50) DEFAULT 'employee',           -- 角色: admin, employee
    status VARCHAR(50) DEFAULT 'active',           -- 状态: active, inactive
    
    -- 分配信息
    factory_id UUID REFERENCES factories(id),      -- 所属工厂
    department_id UUID REFERENCES departments(id), -- 所属部门
    position VARCHAR(100),                         -- 职位
    
    -- 权限
    permissions JSONB,                             -- 额外权限
    data_access_scope VARCHAR(50) DEFAULT 'factory', -- 数据访问范围: factory, company
    
    -- 时间信息
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 加入时间
    left_at TIMESTAMP,                             -- 离职时间
    
    -- 统计信息
    total_wps_created INTEGER DEFAULT 0,           -- 创建的 WPS 数量
    total_tasks_completed INTEGER DEFAULT 0,       -- 完成的任务数量
    last_active_at TIMESTAMP,                      -- 最后活跃时间
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    
    -- 索引
    INDEX idx_company (company_id),
    INDEX idx_user (user_id),
    INDEX idx_factory (factory_id),
    INDEX idx_department (department_id),
    INDEX idx_status (status),
    
    UNIQUE (company_id, user_id)
);
```

### 部门表
```sql
CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    factory_id UUID REFERENCES factories(id) ON DELETE CASCADE,
    
    -- 部门信息
    department_code VARCHAR(100) NOT NULL,         -- 部门编码
    department_name VARCHAR(255) NOT NULL,         -- 部门名称
    description TEXT,                              -- 描述
    
    -- 负责人
    manager_id UUID REFERENCES users(id),          -- 部门经理
    
    -- 统计信息
    employee_count INTEGER DEFAULT 0,              -- 员工数量
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP,
    
    -- 索引
    INDEX idx_company (company_id),
    INDEX idx_factory (factory_id),
    INDEX idx_department_code (department_code),
    INDEX idx_deleted (deleted_at),
    
    UNIQUE (company_id, department_code)
);
```

---

## 🔌 API接口

### 1. 邀请员工
```http
POST /api/v1/enterprise/employees/invite
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "employee@example.com",
  "role": "employee",
  "factory_id": "uuid",
  "department_id": "uuid",
  "permissions": {
    "can_create_wps": true,
    "can_approve_wps": false
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "invitation_id": "uuid",
    "invitation_code": "INV-2025-XXXXX",
    "email": "employee@example.com",
    "expires_at": "2025-10-23T10:00:00Z",
    "invitation_link": "https://app.example.com/accept-invitation?code=INV-2025-XXXXX"
  }
}
```

### 2. 员工列表
```http
GET /api/v1/enterprise/employees?page=1&page_size=20&status=active
Authorization: Bearer <token>
```

### 3. 更新员工权限
```http
PUT /api/v1/enterprise/employees/{employee_id}/permissions
Authorization: Bearer <token>
Content-Type: application/json

{
  "role": "admin",
  "permissions": {
    "can_create_wps": true,
    "can_approve_wps": true,
    "can_manage_employees": true
  },
  "data_access_scope": "company"
}
```

### 4. 停用员工
```http
POST /api/v1/enterprise/employees/{employee_id}/deactivate
Authorization: Bearer <token>
```

### 5. 创建工厂
```http
POST /api/v1/enterprise/factories
Authorization: Bearer <token>
Content-Type: application/json

{
  "factory_code": "F001",
  "factory_name": "北京工厂",
  "address": "北京市朝阳区",
  "contact_person": "张三",
  "phone": "13800138000"
}
```

### 6. 创建部门
```http
POST /api/v1/enterprise/departments
Authorization: Bearer <token>
Content-Type: application/json

{
  "department_code": "D001",
  "department_name": "焊接部",
  "factory_id": "uuid",
  "manager_id": "uuid"
}
```

### 7. 员工统计
```http
GET /api/v1/enterprise/employees/statistics
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total_employees": 15,
    "active_employees": 14,
    "inactive_employees": 1,
    "by_factory": {
      "工厂A": 8,
      "工厂B": 7
    },
    "by_role": {
      "admin": 2,
      "employee": 13
    },
    "quota_usage": {
      "current": 15,
      "max": 20,
      "percentage": 75
    }
  }
}
```

---

## 💼 业务逻辑

### 1. 邀请员工
```python
class EnterpriseService:
    @require_feature("employee_management")  # 需要企业版
    async def invite_employee(
        self,
        invitation_data: EmployeeInvitation,
        user_id: UUID,
        db: Session
    ) -> Dict[str, Any]:
        """邀请员工"""
        
        # 检查是否为企业管理员
        user = db.query(User).filter(User.id == user_id).first()
        if user.membership_type != "enterprise":
            raise HTTPException(403, "仅企业会员可以邀请员工")
        
        # 检查员工配额
        company = db.query(Company).filter(Company.id == user.company_id).first()
        current_employees = db.query(CompanyEmployee).filter(
            CompanyEmployee.company_id == user.company_id,
            CompanyEmployee.status == "active"
        ).count()
        
        max_employees = self._get_max_employees(user.membership_tier)
        if current_employees >= max_employees:
            raise HTTPException(403, f"员工数量已达上限（{max_employees}人）")
        
        # 生成邀请码
        invitation_code = self._generate_invitation_code()
        
        # 创建邀请
        invitation = EmployeeInvitation(
            company_id=user.company_id,
            invited_by=user_id,
            email=invitation_data.email,
            invitation_code=invitation_code,
            role=invitation_data.role,
            factory_id=invitation_data.factory_id,
            department_id=invitation_data.department_id,
            permissions=invitation_data.permissions,
            expires_at=datetime.now() + timedelta(days=7)
        )
        
        db.add(invitation)
        db.commit()
        
        # 发送邀请邮件
        await self._send_invitation_email(invitation)
        
        return {
            "invitation_id": str(invitation.id),
            "invitation_code": invitation_code,
            "email": invitation_data.email,
            "expires_at": invitation.expires_at,
            "invitation_link": f"https://app.example.com/accept-invitation?code={invitation_code}"
        }
    
    def _get_max_employees(self, tier: str) -> int:
        """获取最大员工数"""
        limits = {
            "enterprise": 10,
            "enterprise_pro": 20,
            "enterprise_pro_max": 50
        }
        return limits.get(tier, 0)
```

### 2. 接受邀请
```python
async def accept_invitation(
    self,
    invitation_code: str,
    user_id: UUID,
    db: Session
) -> CompanyEmployee:
    """接受邀请"""
    
    invitation = db.query(EmployeeInvitation).filter(
        EmployeeInvitation.invitation_code == invitation_code,
        EmployeeInvitation.status == "pending"
    ).first()
    
    if not invitation:
        raise HTTPException(404, "邀请不存在或已失效")
    
    if invitation.expires_at < datetime.now():
        invitation.status = "expired"
        db.commit()
        raise HTTPException(400, "邀请已过期")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user.email != invitation.email:
        raise HTTPException(403, "邮箱不匹配")
    
    # 创建员工关系
    employee = CompanyEmployee(
        company_id=invitation.company_id,
        user_id=user_id,
        role=invitation.role,
        factory_id=invitation.factory_id,
        department_id=invitation.department_id,
        permissions=invitation.permissions,
        status="active"
    )
    
    db.add(employee)
    
    # 更新邀请状态
    invitation.status = "accepted"
    invitation.accepted_at = datetime.now()
    invitation.accepted_by = user_id
    
    # 更新用户信息
    user.company_id = invitation.company_id
    user.factory_id = invitation.factory_id
    
    db.commit()
    
    return employee
```

### 3. 员工权限检查
```python
def check_employee_permission(
    self,
    user_id: UUID,
    permission: str,
    db: Session
) -> bool:
    """检查员工权限"""
    
    employee = db.query(CompanyEmployee).filter(
        CompanyEmployee.user_id == user_id,
        CompanyEmployee.status == "active"
    ).first()
    
    if not employee:
        return False
    
    # 管理员拥有所有权限
    if employee.role == "admin":
        return True
    
    # 检查额外权限
    if employee.permissions and permission in employee.permissions:
        return employee.permissions[permission]
    
    # 默认权限（继承专业版）
    default_permissions = {
        "can_create_wps": True,
        "can_create_pqr": True,
        "can_create_ppqr": True,
        "can_manage_welders": True,
        "can_manage_materials": True,
        "can_approve_wps": False,
        "can_manage_employees": False
    }
    
    return default_permissions.get(permission, False)
```

---

## 🔐 权限控制

### 企业管理员检查
```python
def require_enterprise_admin(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """要求企业管理员权限"""
    
    if current_user.membership_type != "enterprise":
        raise HTTPException(403, "需要企业会员")
    
    employee = db.query(CompanyEmployee).filter(
        CompanyEmployee.user_id == current_user.id,
        CompanyEmployee.company_id == current_user.company_id,
        CompanyEmployee.status == "active"
    ).first()
    
    if not employee or employee.role != "admin":
        raise HTTPException(403, "需要企业管理员权限")
    
    return current_user

@router.post("/enterprise/employees/invite")
async def invite_employee(
    invitation_data: EmployeeInvitation,
    current_user: User = Depends(require_enterprise_admin),
    db: Session = Depends(get_db)
):
    """邀请员工（仅企业管理员）"""
    service = EnterpriseService(db)
    return await service.invite_employee(invitation_data, current_user.id, db)
```

---

## 🎨 前端界面

### 员工管理页面
```typescript
// src/pages/Enterprise/EmployeeManagement.tsx

const EmployeeManagement: React.FC = () => {
  const { employees, loading } = useEmployees();
  const { quota } = useEmployeeQuota();
  
  const columns = [
    { title: '员工编号', dataIndex: 'employee_number' },
    { title: '姓名', dataIndex: 'name' },
    { title: '邮箱', dataIndex: 'email' },
    { title: '角色', dataIndex: 'role', render: renderRole },
    { title: '工厂', dataIndex: 'factory_name' },
    { title: '部门', dataIndex: 'department_name' },
    { title: '状态', dataIndex: 'status', render: renderStatus },
    { title: '操作', render: renderActions }
  ];
  
  return (
    <div>
      <Card>
        <Statistic 
          title="员工配额" 
          value={quota.current} 
          suffix={`/ ${quota.max}`}
        />
        <Progress percent={quota.percentage} />
        <Button 
          type="primary" 
          onClick={handleInvite}
          disabled={quota.current >= quota.max}
        >
          邀请员工
        </Button>
      </Card>
      
      <Table columns={columns} dataSource={employees} loading={loading} />
    </div>
  );
};
```

---

**文档版本**: 1.0  
**最后更新**: 2025-10-16  
**开发状态**: 待开发

