# 自动通知系统

## 概述

自动通知系统可以自动发送各种系统通知给用户，无需管理员手动创建公告。系统会根据用户的会员状态、配额使用情况、账号安全等自动生成并发送通知。

## 功能特性

### 1. 会员相关通知

#### 1.1 会员即将到期提醒
- **触发条件**: 会员到期前 7天、3天、1天
- **通知类型**: 
  - 7天前: 信息通知（普通优先级）
  - 3天前: 警告通知（高优先级）
  - 1天前: 警告通知（紧急优先级）
- **通知内容**: 包含会员等级、到期时间、续费优惠信息

#### 1.2 会员已过期通知
- **触发条件**: 会员过期后立即发送
- **通知类型**: 错误通知（紧急优先级）
- **通知内容**: 包含过期时间、降级说明、功能限制说明
- **特点**: 置顶显示，30天后过期

#### 1.3 会员续费成功通知
- **触发条件**: 手动续费或自动续费成功后
- **通知类型**: 成功通知（普通优先级）
- **通知内容**: 包含新的到期时间、感谢信息

#### 1.4 自动续费失败通知
- **触发条件**: 自动续费失败时
- **通知类型**: 错误通知（紧急优先级）
- **通知内容**: 包含失败原因、解决方案、到期时间
- **特点**: 置顶显示

### 2. 配额相关通知

#### 2.1 配额使用警告
- **触发条件**: 配额使用达到 80%、90%、100%
- **通知类型**:
  - 80%: 信息通知（普通优先级）
  - 90%: 警告通知（高优先级）
  - 100%: 错误通知（紧急优先级）
- **支持的配额类型**:
  - WPS记录配额
  - PQR记录配额
  - pPQR记录配额
  - 存储空间配额

### 3. 账号安全通知

#### 3.1 异常登录通知
- **触发条件**: 检测到异地登录或新设备登录
- **通知类型**: 警告通知（紧急优先级）
- **通知内容**: 包含登录时间、IP地址、登录地点
- **特点**: 置顶显示

#### 3.2 密码修改通知
- **触发条件**: 用户修改密码后
- **通知类型**: 信息通知（高优先级）
- **通知内容**: 包含修改时间、安全提示

## 使用方式

### 方式一：管理员门户手动触发

1. 登录管理员门户
2. 进入"公告管理"页面
3. 在"自动通知任务"卡片中点击相应按钮：
   - **运行每日任务**: 执行所有自动通知任务
   - **到期提醒(7天/3天/1天)**: 发送指定天数的会员到期提醒
   - **配额警告**: 检查并发送配额使用警告

### 方式二：定时任务自动执行

#### 使用Python脚本

```bash
# 运行每日通知任务
cd backend
python -m app.tasks.notification_tasks
```

#### 使用cron定时任务（Linux/Mac）

```bash
# 编辑crontab
crontab -e

# 添加以下行（每天早上8点执行）
0 8 * * * cd /path/to/backend && python -m app.tasks.notification_tasks
```

#### 使用Windows任务计划程序

1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器：每天早上8点
4. 操作：启动程序
   - 程序：`python`
   - 参数：`-m app.tasks.notification_tasks`
   - 起始于：`G:\CODE\sdweld1024晚\backend`

### 方式三：API调用

#### 运行每日通知任务
```http
POST /api/v1/admin/system/notifications/tasks/daily
Authorization: Bearer {admin_token}
```

响应：
```json
{
  "success": true,
  "message": "每日通知任务执行完成",
  "data": {
    "expiring_count": 5,
    "expired_count": 2,
    "renewed_count": 3,
    "quota_count": 8,
    "total_notifications": 18
  }
}
```

#### 运行会员到期提醒任务
```http
POST /api/v1/admin/system/notifications/tasks/expiring?days_ahead=7
Authorization: Bearer {admin_token}
```

响应：
```json
{
  "success": true,
  "message": "已发送 5 条会员到期提醒",
  "data": {
    "count": 5,
    "days_ahead": 7
  }
}
```

#### 运行配额警告任务
```http
POST /api/v1/admin/system/notifications/tasks/quota
Authorization: Bearer {admin_token}
```

响应：
```json
{
  "success": true,
  "message": "已发送 8 条配额警告",
  "data": {
    "count": 8
  }
}
```

## 代码集成

### 在业务代码中调用通知服务

```python
from app.services.notification_service import NotificationService
from app.core.database import get_db

# 获取数据库会话
db = next(get_db())

# 创建通知服务实例
notification_service = NotificationService(db)

# 示例1: 发送会员到期提醒
notification_service.notify_membership_expiring_soon(user, days_left=3)

# 示例2: 发送会员过期通知
notification_service.notify_membership_expired(user)

# 示例3: 发送续费成功通知
notification_service.notify_membership_renewed(user, is_auto_renewal=True)

# 示例4: 发送自动续费失败通知
notification_service.notify_auto_renewal_failed(user, reason="支付失败")

# 示例5: 发送配额警告
notification_service.notify_quota_warning(user, quota_type="wps", usage_percent=90)

# 示例6: 发送异常登录通知
notification_service.notify_unusual_login(user, ip="192.168.1.100", location="北京")

# 示例7: 发送密码修改通知
notification_service.notify_password_changed(user)
```

## 建议的定时任务配置

### 每日任务（每天早上8点）
- 检查并通知即将到期的会员（7天、3天、1天前）
- 检查并通知已过期的会员
- 处理自动续费
- 检查配额使用情况

### 每小时任务
- 检查即将到期的会员（1天内）
- 紧急配额警告（100%使用）

## 注意事项

1. **避免重复通知**: 系统会自动检查是否已发送过相同的通知，避免重复打扰用户
2. **通知过期时间**: 不同类型的通知有不同的过期时间，过期后自动从用户通知中心移除
3. **目标受众**: 通知会根据用户的会员类型自动设置目标受众（个人用户/企业用户）
4. **优先级**: 紧急通知会置顶显示，确保用户第一时间看到
5. **性能考虑**: 批量检查任务建议在低峰期执行，避免影响系统性能

## 扩展功能

未来可以考虑添加：

1. **邮件通知**: 重要通知同时发送邮件
2. **短信通知**: 紧急通知发送短信
3. **微信通知**: 通过微信公众号推送通知
4. **通知去重**: 更智能的去重机制，避免短时间内重复通知
5. **通知模板**: 支持自定义通知模板
6. **通知统计**: 统计通知的发送量、阅读率等
7. **用户偏好**: 允许用户设置通知偏好（接收哪些类型的通知）
8. **定时发布**: 支持定时发布通知

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      自动通知系统                              │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
        ┌───────▼──────┐ ┌───▼────┐ ┌─────▼──────┐
        │ 定时任务触发  │ │ API触发 │ │ 业务代码触发 │
        └───────┬──────┘ └───┬────┘ └─────┬──────┘
                │             │             │
                └─────────────┼─────────────┘
                              │
                    ┌─────────▼──────────┐
                    │ NotificationService │
                    └─────────┬──────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
        ┌───────▼──────┐ ┌───▼────┐ ┌─────▼──────┐
        │ 会员相关通知  │ │配额通知 │ │ 安全通知    │
        └───────┬──────┘ └───┬────┘ └─────┬──────┘
                │             │             │
                └─────────────┼─────────────┘
                              │
                    ┌─────────▼──────────┐
                    │ SystemAnnouncement │
                    │   (数据库表)        │
                    └────────────────────┘
```

## 相关文件

- **服务层**: `backend/app/services/notification_service.py`
- **定时任务**: `backend/app/tasks/notification_tasks.py`
- **API端点**: `backend/app/api/v1/endpoints/system_admin.py`
- **前端页面**: `admin-portal/src/pages/AnnouncementManagement.tsx`
- **API服务**: `admin-portal/src/services/announcements.ts`
- **数据模型**: `backend/app/models/system_announcement.py`

