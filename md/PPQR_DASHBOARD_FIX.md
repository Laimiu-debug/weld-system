# pPQR仪表盘配额显示修复

## 问题描述

用户 `testuser176070001@example.com` 在仪表盘中查看pPQR配额时，显示"未开通"，但实际上用户有2条pPQR记录。

## 问题分析

### 1. 数据库调查

```sql
-- 用户信息
用户ID: 21
用户名: testuser176070001
会员等级(member_tier): enterprise
会员类型(membership_type): enterprise
ppqr_quota_used: 2

-- pPQR记录
实际pPQR记录数(全部): 2
实际pPQR记录数(个人工作区): 0

-- pPQR记录详情
ID: 3, 编号: 222221, 工作区类型: enterprise
ID: 7, 编号: 222221-COPY-1761551616, 工作区类型: enterprise

-- 企业员工记录
公司ID: 4
工厂ID: 5
状态: active
```

### 2. 根本原因

1. **Company模型缺少`max_ppqr_records`字段**
   - 企业表中没有pPQR配额限制字段
   - 导致企业工作区的pPQR配额限制显示为0
   - 前端判断配额限制为0时显示"未开通"

2. **用户的pPQR记录都在企业工作区**
   - 用户的2条pPQR记录都在企业工作区（`workspace_type='enterprise'`）
   - 如果前端在个人工作区模式下查看，会显示0条记录

## 修复方案

### 1. 添加`max_ppqr_records`字段到Company模型

**文件**: `backend/app/models/company.py`

```python
# 配额限制
max_factories = Column(Integer, default=1)
max_employees = Column(Integer, default=10)
max_wps_records = Column(Integer, default=200)
max_pqr_records = Column(Integer, default=200)
max_ppqr_records = Column(Integer, default=200)  # ✅ 新增
```

### 2. 数据库迁移

```sql
-- 添加字段
ALTER TABLE companies 
ADD COLUMN max_ppqr_records INTEGER DEFAULT 200;

-- 更新现有记录
UPDATE companies 
SET max_ppqr_records = 200 
WHERE max_ppqr_records IS NULL;
```

### 3. 验证结果

#### 企业工作区模式
```
仪表盘统计数据:
  WPS记录数: 4
  PQR记录数: 3
  pPQR记录数: 2

会员配额使用情况:
  WPS: 4/200
  PQR: 3/200
  pPQR: 2/200  ✅ 正确显示
```

#### 个人工作区模式
```
仪表盘统计数据:
  WPS记录数: 1
  PQR记录数: 1
  pPQR记录数: 0

会员配额使用情况:
  WPS: 16/200
  PQR: 6/200
  pPQR: 2/200  ✅ 正确显示
```

## 工作区上下文逻辑

### 仪表盘API的工作区判断逻辑

**文件**: `backend/app/api/v1/endpoints/dashboard.py`

```python
def get_workspace_context(
    db: Session,
    current_user: User,
    workspace_id: Optional[str] = None
) -> WorkspaceContext:
    # 如果提供了workspace_id，使用它
    if workspace_id:
        return workspace_service.create_workspace_context(current_user, workspace_id)

    # 否则，根据用户的会员类型确定默认工作区
    if current_user.membership_type == "enterprise":
        # 企业用户，查找其企业
        employee = db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == current_user.id,
            CompanyEmployee.status == "active"
        ).first()

        if employee:
            return WorkspaceContext(
                user_id=current_user.id,
                workspace_type=WorkspaceType.ENTERPRISE,
                company_id=employee.company_id,
                factory_id=employee.factory_id
            )

    # 默认使用个人工作区
    return WorkspaceContext(
        user_id=current_user.id,
        workspace_type=WorkspaceType.PERSONAL
    )
```

### 前端工作区设置

**文件**: `frontend/src/services/api.ts`

```typescript
// 请求拦截器
this.api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 添加工作区上下文header
    const currentWorkspace = localStorage.getItem('current_workspace')
    if (currentWorkspace) {
      try {
        const workspace = JSON.parse(currentWorkspace)
        if (workspace.id) {
          config.headers['X-Workspace-ID'] = workspace.id
        }
      } catch (error) {
        console.error('解析工作区信息失败:', error)
      }
    }

    return config
  }
)
```

## 用户操作建议

如果用户仍然看到"未开通"，可能是因为：

1. **前端在个人工作区模式下查看**
   - 解决方案：切换到企业工作区
   - 或者：刷新页面，让后端自动判断工作区类型

2. **前端缓存问题**
   - 解决方案：清除浏览器缓存或硬刷新（Ctrl+F5）

3. **工作区ID未正确设置**
   - 解决方案：检查`localStorage`中的`current_workspace`值

## 测试步骤

1. 登录用户 `testuser176070001@example.com`
2. 访问仪表盘页面
3. 检查pPQR配额显示：
   - 应该显示 `2` 条记录
   - 配额应该显示 `2/200`（如果在企业工作区）
   - 或者显示 `0` 条记录，配额 `2/200`（如果在个人工作区）

## 相关文件

- `backend/app/models/company.py` - Company模型定义
- `backend/app/api/v1/endpoints/dashboard.py` - 仪表盘API
- `backend/app/services/dashboard_service.py` - 仪表盘服务
- `frontend/src/services/api.ts` - API服务（工作区头部设置）
- `frontend/src/pages/Dashboard/index.tsx` - 仪表盘页面

## 修复日期

2025-10-27

