# 管理员门户模块 - 开发指南

## 📋 模块概述

### 功能定位
管理员门户是系统管理员专用的后台管理系统，用于管理所有用户、监控系统运行、处理系统配置等管理任务。

### 适用场景
- 用户管理和审核
- 系统监控和维护
- 数据统计和分析
- 系统配置管理
- 内容审核
- 日志查看

### 开发优先级
**第三阶段** - 管理功能，后续开发

---

## 🎯 访问权限

### 权限要求
- **必须条件**: `is_admin = true`
- **访问级别**: 超级管理员
- **独立系统**: 与用户门户完全分离

**重要说明**: 
- 管理员门户是独立的系统，需要超级管理员权限
- 普通用户（包括企业管理员）无法访问
- 管理员账号由系统初始化时创建

---

## 📊 功能清单

### 1. 用户管理
- **用户列表**: 查看所有用户
- **用户详情**: 查看用户详细信息
- **用户搜索**: 搜索用户
- **用户审核**: 审核用户注册
- **用户禁用**: 禁用/启用用户
- **用户删除**: 删除用户账号
- **会员调整**: 调整用户会员等级
- **配额调整**: 调整用户配额

### 2. 企业管理
- **企业列表**: 查看所有企业
- **企业审核**: 审核企业认证
- **企业详情**: 查看企业详细信息
- **企业禁用**: 禁用/启用企业
- **企业统计**: 企业数据统计

### 3. 订阅管理
- **订阅列表**: 查看所有订阅
- **订阅详情**: 查看订阅详细信息
- **订阅调整**: 手动调整订阅
- **退款处理**: 处理退款请求
- **发票管理**: 管理发票

### 4. 系统监控
- **系统状态**: 查看系统运行状态
- **性能监控**: 监控系统性能
- **错误日志**: 查看错误日志
- **访问日志**: 查看访问日志
- **数据库监控**: 监控数据库状态
- **API 监控**: 监控 API 调用

### 5. 数据统计
- **用户统计**: 用户增长、活跃度统计
- **订阅统计**: 订阅转化率、收入统计
- **使用统计**: 功能使用统计
- **性能统计**: 系统性能统计
- **趋势分析**: 各类趋势分析

### 6. 内容管理
- **公告管理**: 发布系统公告
- **帮助文档**: 管理帮助文档
- **FAQ 管理**: 管理常见问题
- **模板管理**: 管理系统模板

### 7. 系统配置
- **基础配置**: 系统基础配置
- **会员配置**: 会员等级配置
- **功能开关**: 功能开关管理
- **参数配置**: 系统参数配置
- **邮件配置**: 邮件服务配置
- **存储配置**: 存储服务配置

### 8. 安全管理
- **权限管理**: 管理员权限管理
- **IP 白名单**: IP 访问控制
- **安全日志**: 查看安全日志
- **异常检测**: 检测异常行为

---

## 🗄️ 数据模型

### 管理员表
```sql
CREATE TABLE admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 管理员信息
    admin_level VARCHAR(20) DEFAULT 'admin',       -- 级别: super_admin, admin
    permissions JSONB,                             -- 权限列表
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,                -- 是否活跃
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    
    -- 索引
    INDEX idx_user (user_id),
    INDEX idx_admin_level (admin_level),
    
    UNIQUE (user_id)
);
```

### 系统公告表
```sql
CREATE TABLE system_announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 公告信息
    title VARCHAR(255) NOT NULL,                   -- 标题
    content TEXT NOT NULL,                         -- 内容
    announcement_type VARCHAR(50),                 -- 类型: info, warning, maintenance
    priority VARCHAR(20) DEFAULT 'normal',         -- 优先级
    
    -- 显示设置
    is_published BOOLEAN DEFAULT FALSE,            -- 是否发布
    is_pinned BOOLEAN DEFAULT FALSE,               -- 是否置顶
    target_audience VARCHAR(50) DEFAULT 'all',     -- 目标受众: all, free, pro, enterprise
    
    -- 时间设置
    publish_at TIMESTAMP,                          -- 发布时间
    expire_at TIMESTAMP,                           -- 过期时间
    
    -- 统计
    view_count INTEGER DEFAULT 0,                  -- 查看次数
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    
    -- 索引
    INDEX idx_is_published (is_published),
    INDEX idx_publish_at (publish_at),
    INDEX idx_expire_at (expire_at)
);
```

### 系统日志表
```sql
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 日志信息
    log_level VARCHAR(20),                         -- 级别: debug, info, warning, error, critical
    log_type VARCHAR(50),                          -- 类型: api, database, security, system
    message TEXT,                                  -- 消息
    details JSONB,                                 -- 详细信息
    
    -- 来源信息
    user_id UUID REFERENCES users(id),             -- 用户ID
    ip_address VARCHAR(50),                        -- IP 地址
    user_agent TEXT,                               -- 浏览器信息
    
    -- 请求信息
    request_method VARCHAR(10),                    -- 请求方法
    request_path VARCHAR(500),                     -- 请求路径
    request_params JSONB,                          -- 请求参数
    response_status INTEGER,                       -- 响应状态码
    response_time DECIMAL(10,3),                  -- 响应时间（毫秒）
    
    -- 错误信息
    error_message TEXT,                            -- 错误消息
    stack_trace TEXT,                              -- 堆栈跟踪
    
    -- 时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_log_level (log_level),
    INDEX idx_log_type (log_type),
    INDEX idx_user (user_id),
    INDEX idx_created_at (created_at)
);
```

---

## 🔌 API接口

### 1. 用户管理

#### 获取用户列表
```http
GET /api/v1/admin/users?page=1&page_size=20&membership_tier=pro
Authorization: Bearer <admin_token>
```

#### 获取用户详情
```http
GET /api/v1/admin/users/{user_id}
Authorization: Bearer <admin_token>
```

#### 调整用户会员
```http
POST /api/v1/admin/users/{user_id}/adjust-membership
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "membership_tier": "enterprise",
  "expires_at": "2026-10-16",
  "reason": "特殊申请批准"
}
```

#### 禁用用户
```http
POST /api/v1/admin/users/{user_id}/disable
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "reason": "违反服务条款"
}
```

### 2. 系统监控

#### 获取系统状态
```http
GET /api/v1/admin/system/status
Authorization: Bearer <admin_token>
```

**响应**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "uptime_seconds": 86400,
    "cpu_usage": 45.2,
    "memory_usage": 62.8,
    "disk_usage": 38.5,
    "database_status": "connected",
    "redis_status": "connected",
    "active_users": 150,
    "api_requests_per_minute": 320
  }
}
```

#### 获取错误日志
```http
GET /api/v1/admin/logs/errors?page=1&page_size=50&level=error
Authorization: Bearer <admin_token>
```

### 3. 数据统计

#### 获取用户统计
```http
GET /api/v1/admin/statistics/users?start_date=2025-09-01&end_date=2025-10-16
Authorization: Bearer <admin_token>
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total_users": 1500,
    "new_users": 150,
    "active_users": 800,
    "by_tier": {
      "free": 800,
      "pro": 400,
      "advanced": 200,
      "flagship": 50,
      "enterprise": 50
    },
    "growth_rate": 11.1,
    "trend": [
      {"date": "2025-09-01", "count": 1350},
      {"date": "2025-10-01", "count": 1450}
    ]
  }
}
```

#### 获取订阅统计
```http
GET /api/v1/admin/statistics/subscriptions?start_date=2025-09-01&end_date=2025-10-16
Authorization: Bearer <admin_token>
```

### 4. 系统配置

#### 获取系统配置
```http
GET /api/v1/admin/config
Authorization: Bearer <admin_token>
```

#### 更新系统配置
```http
PUT /api/v1/admin/config
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "maintenance_mode": false,
  "registration_enabled": true,
  "max_upload_size_mb": 100,
  "session_timeout_minutes": 60
}
```

### 5. 公告管理

#### 创建公告
```http
POST /api/v1/admin/announcements
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "title": "系统维护通知",
  "content": "系统将于本周六进行维护...",
  "announcement_type": "maintenance",
  "priority": "high",
  "target_audience": "all",
  "publish_at": "2025-10-17T00:00:00Z",
  "expire_at": "2025-10-20T00:00:00Z"
}
```

#### 发布公告
```http
POST /api/v1/admin/announcements/{id}/publish
Authorization: Bearer <admin_token>
```

---

## 💼 业务逻辑

### 1. 用户管理
```python
class AdminService:
    def get_user_list(
        self,
        filters: Dict,
        page: int,
        page_size: int,
        db: Session
    ) -> Dict[str, Any]:
        """获取用户列表"""
        
        query = db.query(User)
        
        # 应用筛选
        if filters.get("membership_tier"):
            query = query.filter(User.membership_tier == filters["membership_tier"])
        
        if filters.get("membership_type"):
            query = query.filter(User.membership_type == filters["membership_type"])
        
        if filters.get("is_active") is not None:
            query = query.filter(User.is_active == filters["is_active"])
        
        # 分页
        total = query.count()
        users = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "items": users,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    def adjust_user_membership(
        self,
        user_id: UUID,
        adjustment_data: MembershipAdjustment,
        admin_id: UUID,
        db: Session
    ) -> User:
        """调整用户会员等级"""
        
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(404, "用户不存在")
        
        # 记录调整前的状态
        old_tier = user.membership_tier
        
        # 更新会员等级
        user.membership_tier = adjustment_data.membership_tier
        user.subscription_expires_at = adjustment_data.expires_at
        user.updated_at = datetime.now()
        
        db.commit()
        
        # 记录操作日志
        self._log_admin_action(
            admin_id,
            "adjust_membership",
            f"调整用户 {user.email} 会员等级从 {old_tier} 到 {adjustment_data.membership_tier}",
            {"user_id": str(user_id), "reason": adjustment_data.reason},
            db
        )
        
        return user
```

### 2. 系统监控
```python
def get_system_status(self) -> Dict[str, Any]:
    """获取系统状态"""
    
    import psutil
    
    # CPU 使用率
    cpu_usage = psutil.cpu_percent(interval=1)
    
    # 内存使用率
    memory = psutil.virtual_memory()
    memory_usage = memory.percent
    
    # 磁盘使用率
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent
    
    # 系统运行时间
    uptime_seconds = time.time() - psutil.boot_time()
    
    return {
        "status": "healthy",
        "uptime_seconds": int(uptime_seconds),
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "disk_usage": disk_usage,
        "database_status": self._check_database_status(),
        "redis_status": self._check_redis_status()
    }
```

### 3. 数据统计
```python
def get_user_statistics(
    self,
    start_date: date,
    end_date: date,
    db: Session
) -> Dict[str, Any]:
    """获取用户统计"""
    
    # 总用户数
    total_users = db.query(User).count()
    
    # 新增用户
    new_users = db.query(User).filter(
        User.created_at >= start_date,
        User.created_at <= end_date
    ).count()
    
    # 活跃用户（最近30天有登录）
    active_users = db.query(User).filter(
        User.last_login_at >= datetime.now() - timedelta(days=30)
    ).count()
    
    # 按会员等级统计
    by_tier = db.query(
        User.membership_tier,
        func.count(User.id)
    ).group_by(User.membership_tier).all()
    
    return {
        "total_users": total_users,
        "new_users": new_users,
        "active_users": active_users,
        "by_tier": dict(by_tier),
        "growth_rate": round(new_users / total_users * 100, 2) if total_users > 0 else 0
    }
```

---

## 🔐 权限控制

### 管理员权限检查
```python
def require_admin(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """要求管理员权限"""
    
    if not current_user.is_admin:
        raise HTTPException(403, "需要管理员权限")
    
    admin = db.query(Admin).filter(
        Admin.user_id == current_user.id,
        Admin.is_active == True
    ).first()
    
    if not admin:
        raise HTTPException(403, "管理员账号未激活")
    
    return current_user

@router.get("/admin/users")
async def get_users(
    page: int = 1,
    page_size: int = 20,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取用户列表（仅管理员）"""
    service = AdminService(db)
    return service.get_user_list({}, page, page_size, db)
```

---

## 🎨 前端界面

### 管理员仪表盘
```typescript
// src/pages/Admin/Dashboard.tsx

const AdminDashboard: React.FC = () => {
  const { systemStatus, loading } = useSystemStatus();
  const { statistics } = useStatistics();
  
  return (
    <div className="admin-dashboard">
      <Row gutter={16}>
        <Col span={6}>
          <Statistic title="总用户数" value={statistics.total_users} />
        </Col>
        <Col span={6}>
          <Statistic title="活跃用户" value={statistics.active_users} />
        </Col>
        <Col span={6}>
          <Statistic title="CPU 使用率" value={systemStatus.cpu_usage} suffix="%" />
        </Col>
        <Col span={6}>
          <Statistic title="内存使用率" value={systemStatus.memory_usage} suffix="%" />
        </Col>
      </Row>
      
      <Card title="用户增长趋势">
        <Chart data={statistics.trend} type="line" />
      </Card>
      
      <Card title="最近错误日志">
        <ErrorLogTable />
      </Card>
    </div>
  );
};
```

---

**文档版本**: 1.0  
**最后更新**: 2025-10-16  
**开发状态**: 待开发

