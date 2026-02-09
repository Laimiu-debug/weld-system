# 仪表盘模块 - 开发指南

## 📋 模块概述

### 功能定位
仪表盘是系统的核心入口，为用户提供系统概览、关键指标监控和实时状态展示。通过数据可视化帮助用户快速了解业务状态。

### 适用场景
- 用户登录后的首页展示
- 快速查看关键业务指标
- 监控系统使用情况和配额
- 查看最近活动和待办事项

### 开发优先级
**第一阶段** - 核心功能，立即开发

---

## 🎯 会员权限

### 访问权限
| 会员等级 | 访问权限 | 功能范围 |
|---------|---------|---------|
| 游客模式 | ✅ 可访问 | 只读示例数据展示 |
| 个人免费版 | ✅ 可访问 | 基础数据展示 |
| 个人专业版 | ✅ 可访问 | 基础数据 + 部分统计 |
| 个人高级版 | ✅ 可访问 | 完整数据 + 高级统计 |
| 个人旗舰版 | ✅ 可访问 | 完整数据 + 高级统计 + 自定义 |
| 企业版 | ✅ 可访问 | 完整数据 + 企业统计 |
| 企业PRO | ✅ 可访问 | 完整数据 + 企业统计 |
| 企业PRO MAX | ✅ 可访问 | 完整数据 + 企业统计 |

**说明**:
- 仪表盘是所有会员等级均可访问的通用功能
- 游客模式仅可查看系统预设的示例数据，无法查看真实用户数据
- 显示的数据范围和统计维度根据会员等级有所不同

---

## 📊 功能清单

### 1. 关键指标卡片
- **WPS 统计**: 总数、草稿、审批中、已批准
- **PQR 统计**: 总数、合格、不合格、待测试
- **pPQR 统计**: 总数、草稿、审核中、已批准（专业版及以上）
- **焊工统计**: 总数、在职、证书即将过期（专业版及以上）
- **焊材统计**: 总数、低库存预警（专业版及以上）
- **设备统计**: 总数、运行中、维护中（高级版及以上）
- **生产任务**: 总数、进行中、已完成（高级版及以上）
- **质量检验**: 总数、合格率（高级版及以上）

### 2. 配额使用情况
- **WPS 配额**: 当前使用/最大限制，使用率进度条
- **PQR 配额**: 当前使用/最大限制，使用率进度条
- **pPQR 配额**: 当前使用/最大限制，使用率进度条（专业版及以上）
- **存储空间**: 已使用/总空间，使用率进度条
- **配额预警**: 超过80%时显示警告，超过95%时显示危险提示

### 3. 最近活动
- **最近创建的 WPS**: 最新5条记录
- **最近创建的 PQR**: 最新5条记录
- **最近修改的记录**: 最新10条记录
- **待审批项目**: 需要用户审批的项目列表（高级版及以上）

### 4. 快捷操作
- **创建 WPS**: 快速跳转到 WPS 创建页面
- **创建 PQR**: 快速跳转到 PQR 创建页面
- **创建 pPQR**: 快速跳转到 pPQR 创建页面（专业版及以上）
- **查看报表**: 跳转到报表统计页面（旗舰版及以上）

### 5. 数据趋势图表（高级版及以上）
- **WPS 创建趋势**: 最近30天的创建数量折线图
- **PQR 测试趋势**: 最近30天的测试数量和合格率
- **生产任务完成率**: 最近30天的任务完成情况
- **质量检验合格率**: 最近30天的质量趋势

### 6. 系统通知
- **系统公告**: 管理员发布的系统通知
- **会员到期提醒**: 订阅即将到期提醒
- **配额预警**: 配额即将用完提醒
- **证书过期提醒**: 焊工证书即将过期提醒（专业版及以上）

### 7. 企业统计（仅企业会员）
- **工厂概览**: 各工厂的数据统计
- **员工活跃度**: 员工使用情况统计
- **跨工厂数据**: 多工厂数据对比
- **部门统计**: 各部门的业务数据

---

## 🗄️ 数据模型

### 仪表盘数据聚合（无独立表）
仪表盘数据通过聚合以下表获得：

#### 依赖的数据表
```sql
-- WPS 数据
SELECT COUNT(*) FROM wps_records WHERE user_id = ? AND status = 'approved';

-- PQR 数据
SELECT COUNT(*) FROM pqr_records WHERE user_id = ? AND status = 'qualified';

-- pPQR 数据
SELECT COUNT(*) FROM ppqr_records WHERE user_id = ?;

-- 焊工数据
SELECT COUNT(*) FROM welders WHERE user_id = ? AND is_active = true;

-- 焊材数据
SELECT COUNT(*) FROM welding_materials WHERE user_id = ? AND current_stock < min_stock_level;

-- 设备数据
SELECT COUNT(*) FROM equipment WHERE user_id = ? AND status = 'operational';

-- 生产任务数据
SELECT COUNT(*) FROM production_tasks WHERE user_id = ? AND status = 'in_progress';

-- 质量检验数据
SELECT COUNT(*) FROM quality_inspections WHERE user_id = ? AND result = 'pass';
```

#### 配额计算
```sql
-- 获取用户配额信息
SELECT 
    membership_tier,
    (SELECT COUNT(*) FROM wps_records WHERE user_id = ?) as wps_count,
    (SELECT COUNT(*) FROM pqr_records WHERE user_id = ?) as pqr_count,
    (SELECT COUNT(*) FROM ppqr_records WHERE user_id = ?) as ppqr_count
FROM users WHERE id = ?;
```

---

## 🔌 API接口

### 1. 获取仪表盘概览数据
```http
GET /api/v1/dashboard/overview
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "key_metrics": {
      "wps": {
        "total": 25,
        "draft": 5,
        "in_review": 3,
        "approved": 17
      },
      "pqr": {
        "total": 20,
        "qualified": 18,
        "failed": 2,
        "pending": 0
      },
      "ppqr": {
        "total": 10,
        "draft": 3,
        "in_review": 2,
        "approved": 5
      }
    },
    "quotas": {
      "wps": {
        "current": 25,
        "max": 30,
        "percentage": 83.3,
        "warning": true
      },
      "pqr": {
        "current": 20,
        "max": 30,
        "percentage": 66.7,
        "warning": false
      },
      "storage": {
        "used_mb": 350,
        "total_mb": 500,
        "percentage": 70.0,
        "warning": false
      }
    },
    "recent_activities": [
      {
        "id": "uuid",
        "type": "wps",
        "action": "created",
        "title": "WPS-2025-001",
        "timestamp": "2025-10-16T10:30:00Z"
      }
    ],
    "alerts": [
      {
        "type": "quota_warning",
        "message": "WPS 配额使用已超过 80%",
        "severity": "warning"
      }
    ]
  }
}
```

### 2. 获取数据趋势
```http
GET /api/v1/dashboard/trends?period=30
Authorization: Bearer <token>
```

**查询参数**:
- `period`: 时间范围（天数），默认30天

**响应示例**:
```json
{
  "success": true,
  "data": {
    "wps_trend": [
      {"date": "2025-09-16", "count": 2},
      {"date": "2025-09-17", "count": 1},
      ...
    ],
    "pqr_trend": [
      {"date": "2025-09-16", "qualified": 3, "failed": 0},
      ...
    ],
    "quality_rate": [
      {"date": "2025-09-16", "rate": 98.5},
      ...
    ]
  }
}
```

### 3. 获取企业统计（仅企业会员）
```http
GET /api/v1/dashboard/enterprise-stats
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "factories": [
      {
        "id": "uuid",
        "name": "工厂A",
        "wps_count": 50,
        "employee_count": 5
      }
    ],
    "employee_activity": [
      {
        "user_id": "uuid",
        "name": "张三",
        "last_active": "2025-10-16T10:00:00Z",
        "wps_created": 5
      }
    ]
  }
}
```

---

## 💼 业务逻辑

### 1. 数据聚合逻辑
```python
# app/services/dashboard_service.py

class DashboardService:
    def get_overview(self, user_id: UUID, db: Session) -> Dict[str, Any]:
        """获取仪表盘概览数据"""
        
        # 1. 获取用户会员信息
        user = db.query(User).filter(User.id == user_id).first()
        membership_tier = user.membership_tier
        
        # 2. 根据会员等级决定显示哪些数据
        data = {
            "key_metrics": self._get_key_metrics(user_id, membership_tier, db),
            "quotas": self._get_quotas(user_id, membership_tier, db),
            "recent_activities": self._get_recent_activities(user_id, db),
            "alerts": self._get_alerts(user_id, db)
        }
        
        # 3. 高级版及以上显示趋势图
        if membership_tier in ["advanced", "flagship", "enterprise", "enterprise_pro", "enterprise_pro_max"]:
            data["trends"] = self._get_trends(user_id, db)
        
        # 4. 企业会员显示企业统计
        if user.membership_type == "enterprise":
            data["enterprise_stats"] = self._get_enterprise_stats(user_id, db)
        
        return data
```

### 2. 配额预警逻辑
```python
def _check_quota_warnings(self, user_id: UUID, db: Session) -> List[Dict]:
    """检查配额预警"""
    warnings = []
    
    checker = QuotaChecker(db)
    user = db.query(User).filter(User.id == user_id).first()
    
    # 检查 WPS 配额
    wps_quota = checker.get_user_quota(user, "wps_records")
    if wps_quota["percentage"] > 80:
        warnings.append({
            "type": "quota_warning",
            "resource": "wps",
            "message": f"WPS 配额使用已超过 {wps_quota['percentage']}%",
            "severity": "warning" if wps_quota["percentage"] < 95 else "danger"
        })
    
    return warnings
```

### 3. 数据隔离
- 所有数据查询必须包含 `user_id` 过滤
- 企业会员可以查看 `company_id` 下的所有数据
- 工厂管理员可以查看 `factory_id` 下的数据

---

## 🔐 权限控制

### 1. 访问控制
```python
@router.get("/dashboard/overview")
async def get_dashboard_overview(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """所有会员等级均可访问"""
    service = DashboardService(db)
    return service.get_overview(current_user.id, db)
```

### 2. 功能权限
```python
@router.get("/dashboard/trends")
@require_feature("advanced_reports")  # 需要高级版及以上
async def get_dashboard_trends(
    period: int = 30,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    service = DashboardService(db)
    return service.get_trends(current_user.id, period, db)
```

### 3. 数据范围
- **个人会员**: 只能看到自己的数据
- **企业会员**: 可以看到企业下所有数据
- **企业管理员**: 可以看到跨工厂数据

---

## 🎨 前端界面

### 页面布局
```
┌─────────────────────────────────────────────────────────┐
│  仪表盘                                    [刷新] [设置]  │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ WPS     │ │ PQR     │ │ pPQR    │ │ 焊工    │       │
│  │ 25/30   │ │ 20/30   │ │ 10/30   │ │ 15      │       │
│  │ 83%     │ │ 67%     │ │ 33%     │ │ 活跃    │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
├─────────────────────────────────────────────────────────┤
│  配额使用情况                                            │
│  WPS:  ████████████████░░░░  83% (25/30)               │
│  PQR:  ████████████░░░░░░░░  67% (20/30)               │
│  存储: ██████████░░░░░░░░░░  70% (350MB/500MB)         │
├─────────────────────────────────────────────────────────┤
│  最近活动                          │  快捷操作           │
│  • WPS-2025-001 已创建            │  [+ 创建 WPS]       │
│  • PQR-2025-015 测试通过          │  [+ 创建 PQR]       │
│  • WPS-2025-002 已修改            │  [+ 创建 pPQR]      │
│                                   │  [📊 查看报表]      │
├─────────────────────────────────────────────────────────┤
│  数据趋势 (最近30天)                                     │
│  [折线图: WPS 创建趋势]                                  │
│  [折线图: PQR 合格率]                                    │
└─────────────────────────────────────────────────────────┘
```

### 组件设计
```typescript
// src/pages/Dashboard/index.tsx

interface DashboardProps {}

const Dashboard: React.FC<DashboardProps> = () => {
  const { data, loading } = useDashboard();
  
  return (
    <div className="dashboard">
      <KeyMetricsCards metrics={data.key_metrics} />
      <QuotaProgress quotas={data.quotas} />
      <Row gutter={16}>
        <Col span={16}>
          <RecentActivities activities={data.recent_activities} />
          {data.trends && <TrendsCharts trends={data.trends} />}
        </Col>
        <Col span={8}>
          <QuickActions />
          <Alerts alerts={data.alerts} />
        </Col>
      </Row>
    </div>
  );
};
```

---

## 📝 开发检查清单

### 后端开发
- [ ] 创建 `DashboardService` 类
- [ ] 实现数据聚合逻辑
- [ ] 实现配额计算逻辑
- [ ] 实现趋势数据查询
- [ ] 实现企业统计查询
- [ ] 创建 API 路由
- [ ] 添加权限控制
- [ ] 编写单元测试

### 前端开发
- [ ] 创建仪表盘页面组件
- [ ] 实现关键指标卡片组件
- [ ] 实现配额进度条组件
- [ ] 实现最近活动列表组件
- [ ] 实现快捷操作组件
- [ ] 实现趋势图表组件（使用 ECharts 或 Recharts）
- [ ] 实现企业统计组件
- [ ] 添加响应式布局
- [ ] 添加数据刷新功能

### 测试
- [ ] 测试不同会员等级的数据显示
- [ ] 测试配额预警功能
- [ ] 测试数据隔离
- [ ] 测试企业统计功能
- [ ] 性能测试（数据聚合查询优化）

---

**文档版本**: 1.0  
**最后更新**: 2025-10-16  
**开发状态**: 待开发

