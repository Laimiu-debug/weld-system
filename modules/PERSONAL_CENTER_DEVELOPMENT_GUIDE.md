# 个人中心模块 - 开发指南

## 📋 模块概述

### 功能定位
个人中心模块用于管理用户个人信息、账号设置、会员订阅、安全设置等个人相关功能。

### 适用场景
- 个人信息管理
- 账号安全设置
- 会员订阅管理
- 使用统计查看
- 偏好设置

### 开发优先级
**第一阶段** - 核心功能，立即开发

---

## 🎯 会员权限

### 访问权限
| 会员等级 | 访问权限 | 功能范围 |
|---------|---------|---------|
| 游客模式 | ✅ 可访问 | 基础信息查看 |
| 个人免费版 | ✅ 可访问 | 完整功能 |
| 个人专业版 | ✅ 可访问 | 完整功能 |
| 个人高级版 | ✅ 可访问 | 完整功能 |
| 个人旗舰版 | ✅ 可访问 | 完整功能 |
| 企业版 | ✅ 可访问 | 完整功能 + 企业信息 |
| 企业PRO | ✅ 可访问 | 完整功能 + 企业信息 |
| 企业PRO MAX | ✅ 可访问 | 完整功能 + 企业信息 |

**说明**: 个人中心是所有用户均可访问的通用功能。

---

## 📊 功能清单

### 1. 个人信息管理
- **基本信息**: 姓名、邮箱、手机号
- **头像上传**: 上传和更换头像
- **个人简介**: 编辑个人简介
- **联系方式**: 管理联系方式
- **时区设置**: 设置时区
- **语言设置**: 选择界面语言

### 2. 账号安全
- **修改密码**: 修改登录密码
- **双因素认证**: 启用/禁用 2FA
- **登录历史**: 查看登录记录
- **活跃会话**: 管理活跃会话
- **安全问题**: 设置安全问题
- **账号注销**: 注销账号

### 3. 会员订阅
- **当前套餐**: 查看当前会员等级
- **配额使用**: 查看配额使用情况
- **升级会员**: 升级到更高等级
- **续费订阅**: 续费会员订阅
- **订阅历史**: 查看订阅历史
- **发票管理**: 下载发票

### 4. 使用统计
- **数据统计**: 查看使用数据统计
- **活跃度**: 查看活跃度统计
- **存储使用**: 查看存储空间使用
- **操作日志**: 查看操作日志

### 5. 通知设置
- **邮件通知**: 设置邮件通知偏好
- **系统通知**: 设置系统通知偏好
- **提醒设置**: 设置各类提醒
- **通知历史**: 查看通知历史

### 6. 偏好设置
- **界面主题**: 选择界面主题（亮色/暗色）
- **默认视图**: 设置默认视图
- **快捷键**: 自定义快捷键
- **数据展示**: 设置数据展示偏好

### 7. 企业信息（企业会员）
- **企业信息**: 查看企业信息
- **工厂信息**: 查看所属工厂
- **部门信息**: 查看所属部门
- **员工信息**: 查看同事信息

---

## 🗄️ 数据模型

### 用户偏好设置表
```sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 界面设置
    theme VARCHAR(20) DEFAULT 'light',             -- 主题: light, dark
    language VARCHAR(10) DEFAULT 'zh-CN',          -- 语言
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',  -- 时区
    
    -- 通知设置
    email_notifications JSONB DEFAULT '{}',        -- 邮件通知设置
    system_notifications JSONB DEFAULT '{}',       -- 系统通知设置
    
    -- 显示设置
    default_view VARCHAR(50),                      -- 默认视图
    items_per_page INTEGER DEFAULT 20,             -- 每页显示数量
    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD',  -- 日期格式
    
    -- 快捷键
    keyboard_shortcuts JSONB,                      -- 快捷键设置
    
    -- 其他偏好
    preferences JSONB,                             -- 其他偏好设置
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_user (user_id),
    
    UNIQUE (user_id)
);
```

### 登录历史表
```sql
CREATE TABLE login_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 登录信息
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_time TIMESTAMP,
    ip_address VARCHAR(50),                        -- IP 地址
    user_agent TEXT,                               -- 浏览器信息
    device_type VARCHAR(50),                       -- 设备类型
    location VARCHAR(255),                         -- 登录位置
    
    -- 登录结果
    login_status VARCHAR(20),                      -- 状态: success, failed
    failure_reason TEXT,                           -- 失败原因
    
    -- 会话信息
    session_id VARCHAR(255),                       -- 会话ID
    is_active BOOLEAN DEFAULT TRUE,                -- 是否活跃
    
    -- 索引
    INDEX idx_user (user_id),
    INDEX idx_login_time (login_time),
    INDEX idx_session (session_id)
);
```

### 通知记录表
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 通知信息
    notification_type VARCHAR(50),                 -- 类型: system, quota, certificate, etc.
    title VARCHAR(255),                            -- 标题
    content TEXT,                                  -- 内容
    priority VARCHAR(20) DEFAULT 'normal',         -- 优先级: low, normal, high
    
    -- 状态
    is_read BOOLEAN DEFAULT FALSE,                 -- 是否已读
    read_at TIMESTAMP,                             -- 阅读时间
    
    -- 关联信息
    related_type VARCHAR(50),                      -- 关联类型
    related_id UUID,                               -- 关联ID
    
    -- 操作
    action_url VARCHAR(500),                       -- 操作链接
    action_text VARCHAR(100),                      -- 操作文本
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_user (user_id),
    INDEX idx_is_read (is_read),
    INDEX idx_created_at (created_at)
);
```

---

## 🔌 API接口

### 1. 获取个人信息
```http
GET /api/v1/profile
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "user123",
    "email": "user@example.com",
    "full_name": "张三",
    "phone": "13800138000",
    "avatar_url": "https://...",
    "membership_tier": "pro",
    "membership_type": "personal",
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

### 2. 更新个人信息
```http
PUT /api/v1/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "张三",
  "phone": "13800138000",
  "bio": "焊接工程师"
}
```

### 3. 上传头像
```http
POST /api/v1/profile/avatar
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <图片文件>
```

### 4. 修改密码
```http
POST /api/v1/profile/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "old_password",
  "new_password": "new_password",
  "confirm_password": "new_password"
}
```

### 5. 获取使用统计
```http
GET /api/v1/profile/statistics
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": {
    "wps_count": 25,
    "pqr_count": 20,
    "ppqr_count": 10,
    "storage_used_mb": 350,
    "last_login": "2025-10-16T10:00:00Z",
    "total_logins": 150,
    "account_age_days": 289
  }
}
```

### 6. 获取配额使用
```http
GET /api/v1/profile/quotas
Authorization: Bearer <token>
```

### 7. 获取登录历史
```http
GET /api/v1/profile/login-history?page=1&page_size=20
Authorization: Bearer <token>
```

### 8. 获取通知列表
```http
GET /api/v1/profile/notifications?page=1&page_size=20&is_read=false
Authorization: Bearer <token>
```

### 9. 标记通知已读
```http
POST /api/v1/profile/notifications/{id}/mark-read
Authorization: Bearer <token>
```

### 10. 获取偏好设置
```http
GET /api/v1/profile/preferences
Authorization: Bearer <token>
```

### 11. 更新偏好设置
```http
PUT /api/v1/profile/preferences
Authorization: Bearer <token>
Content-Type: application/json

{
  "theme": "dark",
  "language": "zh-CN",
  "email_notifications": {
    "quota_warning": true,
    "certificate_expiry": true
  }
}
```

### 12. 注销账号
```http
POST /api/v1/profile/deactivate
Authorization: Bearer <token>
Content-Type: application/json

{
  "password": "user_password",
  "reason": "不再使用"
}
```

---

## 💼 业务逻辑

### 1. 更新个人信息
```python
class ProfileService:
    async def update_profile(
        self,
        user_id: UUID,
        profile_data: ProfileUpdate,
        db: Session
    ) -> User:
        """更新个人信息"""
        
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(404, "用户不存在")
        
        # 更新字段
        if profile_data.full_name:
            user.full_name = profile_data.full_name
        if profile_data.phone:
            user.phone = profile_data.phone
        if profile_data.bio:
            user.bio = profile_data.bio
        
        user.updated_at = datetime.now()
        db.commit()
        db.refresh(user)
        
        return user
```

### 2. 修改密码
```python
async def change_password(
    self,
    user_id: UUID,
    password_data: PasswordChange,
    db: Session
) -> bool:
    """修改密码"""
    
    user = db.query(User).filter(User.id == user_id).first()
    
    # 验证当前密码
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(400, "当前密码错误")
    
    # 验证新密码
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(400, "两次输入的密码不一致")
    
    # 更新密码
    user.hashed_password = hash_password(password_data.new_password)
    user.updated_at = datetime.now()
    
    db.commit()
    
    # 发送密码修改通知
    await self._send_password_change_notification(user)
    
    return True
```

### 3. 创建通知
```python
async def create_notification(
    self,
    user_id: UUID,
    notification_data: NotificationCreate,
    db: Session
) -> Notification:
    """创建通知"""
    
    notification = Notification(
        user_id=user_id,
        notification_type=notification_data.notification_type,
        title=notification_data.title,
        content=notification_data.content,
        priority=notification_data.priority,
        related_type=notification_data.related_type,
        related_id=notification_data.related_id,
        action_url=notification_data.action_url,
        action_text=notification_data.action_text
    )
    
    db.add(notification)
    db.commit()
    
    # 如果用户启用了邮件通知，发送邮件
    user = db.query(User).filter(User.id == user_id).first()
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()
    
    if preferences and preferences.email_notifications.get(notification_data.notification_type):
        await self._send_email_notification(user, notification)
    
    return notification
```

---

## 🔐 权限控制

```python
@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_active_user)
):
    """获取个人信息（所有用户）"""
    return current_user

@router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新个人信息"""
    service = ProfileService(db)
    return await service.update_profile(current_user.id, profile_data, db)
```

---

## 🎨 前端界面

### 个人中心页面
```typescript
// src/pages/Profile/index.tsx

const ProfileCenter: React.FC = () => {
  const { user, loading } = useCurrentUser();
  const [activeTab, setActiveTab] = useState('info');
  
  return (
    <div className="profile-center">
      <Card>
        <Avatar size={100} src={user.avatar_url} />
        <h2>{user.full_name}</h2>
        <Tag color="blue">{getMembershipTierName(user.membership_tier)}</Tag>
      </Card>
      
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="个人信息" key="info">
          <ProfileInfo user={user} />
        </TabPane>
        
        <TabPane tab="账号安全" key="security">
          <SecuritySettings user={user} />
        </TabPane>
        
        <TabPane tab="会员订阅" key="subscription">
          <SubscriptionManagement user={user} />
        </TabPane>
        
        <TabPane tab="使用统计" key="statistics">
          <UsageStatistics user={user} />
        </TabPane>
        
        <TabPane tab="通知设置" key="notifications">
          <NotificationSettings user={user} />
        </TabPane>
        
        <TabPane tab="偏好设置" key="preferences">
          <PreferencesSettings user={user} />
        </TabPane>
      </Tabs>
    </div>
  );
};
```

### 会员订阅管理
```typescript
// src/pages/Profile/SubscriptionManagement.tsx

const SubscriptionManagement: React.FC = () => {
  const { subscription, quotas } = useSubscription();
  
  return (
    <div>
      <Card title="当前套餐">
        <Descriptions>
          <Descriptions.Item label="会员等级">
            {getMembershipTierName(subscription.tier)}
          </Descriptions.Item>
          <Descriptions.Item label="价格">
            ¥{subscription.price}/月
          </Descriptions.Item>
          <Descriptions.Item label="到期时间">
            {subscription.expires_at}
          </Descriptions.Item>
        </Descriptions>
        
        <Button type="primary" onClick={handleUpgrade}>
          升级会员
        </Button>
        <Button onClick={handleRenew}>
          续费
        </Button>
      </Card>
      
      <Card title="配额使用">
        <QuotaProgress quotas={quotas} />
      </Card>
    </div>
  );
};
```

---

**文档版本**: 1.0  
**最后更新**: 2025-10-16  
**开发状态**: 待开发

