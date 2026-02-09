# 数据隔离和工作区管理 - 实施指南

## 📋 概述

本文档提供数据隔离和工作区管理功能的完整实施指南，包括部署步骤、API使用示例和测试方法。

## ✅ 已完成的功能

### 1. 数据模型层
- ✅ 所有业务模块数据模型（WPS、PQR、pPQR、焊材、焊工、设备、生产、质量）
- ✅ 统一的数据隔离字段（user_id、workspace_type、company_id、factory_id、access_level）
- ✅ 完整的审计字段（created_by、updated_by、created_at、updated_at）

### 2. 核心服务层
- ✅ 数据访问权限中间件（`DataAccessMiddleware`）
- ✅ 工作区管理服务（`WorkspaceService`）
- ✅ 配额管理服务（`QuotaService`）

### 3. API端点
- ✅ 工作区管理API（`/api/v1/workspace/*`）
  - 获取用户工作区列表
  - 切换工作区
  - 获取工作区配额信息

### 4. 数据库迁移
- ✅ SQL迁移脚本（`add_data_isolation_fields.sql`）
- ✅ Python迁移工具（`run_data_isolation_migration.py`）

## 🚀 部署步骤

### 步骤1：执行数据库迁移

```bash
cd backend
python run_data_isolation_migration.py
```

迁移脚本将：
1. 为现有的 WPS 和 PQR 表添加数据隔离字段
2. 创建 pPQR 表
3. 创建焊材管理表
4. 使用 SQLAlchemy 创建其他业务模块表
5. 验证迁移结果

### 步骤2：重启后端服务

```bash
# 停止现有服务
# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 步骤3：验证API端点

访问 API 文档：`http://localhost:8000/docs`

检查新增的工作区管理端点：
- `GET /api/v1/workspace/workspaces` - 获取工作区列表
- `GET /api/v1/workspace/workspaces/default` - 获取默认工作区
- `POST /api/v1/workspace/workspaces/switch` - 切换工作区
- `GET /api/v1/workspace/workspaces/{workspace_id}` - 获取工作区详情
- `GET /api/v1/workspace/workspaces/{workspace_id}/quota` - 获取配额信息

## 📖 API使用示例

### 1. 获取用户所有工作区

```http
GET /api/v1/workspace/workspaces
Authorization: Bearer <token>
```

响应示例：
```json
[
  {
    "type": "personal",
    "id": "personal_123",
    "name": "个人工作区",
    "description": "您的私人数据空间",
    "user_id": 123,
    "company_id": null,
    "factory_id": null,
    "is_default": true,
    "membership_tier": "professional",
    "quota_info": {
      "wps_used": 10,
      "wps_limit": 50,
      "pqr_used": 5,
      "pqr_limit": 30
    }
  },
  {
    "type": "enterprise",
    "id": "enterprise_456",
    "name": "XX焊接公司",
    "description": "XX焊接公司 - 企业共享工作区",
    "user_id": 123,
    "company_id": 456,
    "factory_id": 789,
    "factory_name": "北京工厂",
    "is_default": false,
    "role": "engineer",
    "membership_tier": "enterprise",
    "quota_info": {
      "wps_used": 50,
      "wps_limit": 500,
      "pqr_used": 30,
      "pqr_limit": 300
    }
  }
]
```

### 2. 切换工作区

```http
POST /api/v1/workspace/workspaces/switch
Authorization: Bearer <token>
Content-Type: application/json

{
  "workspace_id": "enterprise_456"
}
```

响应示例：
```json
{
  "success": true,
  "message": "已切换到工作区: XX焊接公司",
  "workspace": {
    "type": "enterprise",
    "id": "enterprise_456",
    "name": "XX焊接公司",
    ...
  }
}
```

### 3. 在指定工作区创建WPS

```python
from app.core.data_access import WorkspaceContext, DataAccessMiddleware
from app.services.quota_service import QuotaService, QuotaType

# 创建工作区上下文
workspace_context = WorkspaceContext(
    user_id=current_user.id,
    workspace_type="enterprise",
    company_id=456,
    factory_id=789
)

# 检查配额
quota_service = QuotaService(db)
quota_service.check_quota(
    current_user,
    workspace_context,
    QuotaType.WPS,
    increment=1
)

# 创建WPS记录
wps = WPS(
    user_id=current_user.id,
    workspace_type=workspace_context.workspace_type,
    company_id=workspace_context.company_id,
    factory_id=workspace_context.factory_id,
    is_shared=True,
    access_level="company",  # 全公司可见
    wps_number="WPS-2025-001",
    title="Q235B焊接工艺",
    created_by=current_user.id,
    # ... 其他字段
)

db.add(wps)
db.commit()

# 增加配额使用量
quota_service.increment_quota_usage(
    current_user,
    workspace_context,
    QuotaType.WPS,
    increment=1
)
```

### 4. 查询工作区数据（应用数据过滤）

```python
from sqlalchemy.orm import Query
from app.core.data_access import DataAccessMiddleware, WorkspaceContext

# 创建工作区上下文
workspace_context = WorkspaceContext(
    user_id=current_user.id,
    workspace_type="enterprise",
    company_id=456,
    factory_id=789
)

# 创建查询
query = db.query(WPS)

# 应用工作区过滤器
data_access = DataAccessMiddleware(db)
filtered_query = data_access.apply_workspace_filter(
    query,
    WPS,
    current_user,
    workspace_context
)

# 执行查询
wps_list = filtered_query.all()
```

### 5. 检查数据访问权限

```python
from app.core.data_access import DataAccessMiddleware, DataAccessAction

# 获取WPS记录
wps = db.query(WPS).filter(WPS.id == wps_id).first()

# 检查访问权限
data_access = DataAccessMiddleware(db)
has_access = data_access.check_access(
    current_user,
    wps,
    DataAccessAction.EDIT
)

if has_access:
    # 允许编辑
    wps.title = "更新后的标题"
    db.commit()
```

## 🔧 在现有API端点中集成

### 示例：更新WPS创建端点

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_verified_user
from app.models.user import User
from app.models.wps import WPS
from app.services.workspace_service import get_workspace_service
from app.services.quota_service import get_quota_service, QuotaType
from app.core.data_access import DataAccessMiddleware

router = APIRouter()

@router.post("/wps")
async def create_wps(
    wps_data: WPSCreate,
    workspace_id: str,  # 从请求头或查询参数获取
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    # 1. 创建工作区上下文
    workspace_service = get_workspace_service(db)
    workspace_context = workspace_service.create_workspace_context(
        current_user,
        workspace_id
    )
    
    # 2. 检查配额
    quota_service = get_quota_service(db)
    quota_service.check_quota(
        current_user,
        workspace_context,
        QuotaType.WPS,
        increment=1
    )
    
    # 3. 创建WPS记录
    wps = WPS(
        **wps_data.dict(),
        user_id=current_user.id,
        workspace_type=workspace_context.workspace_type,
        company_id=workspace_context.company_id,
        factory_id=workspace_context.factory_id,
        created_by=current_user.id
    )
    
    db.add(wps)
    db.commit()
    db.refresh(wps)
    
    # 4. 增加配额使用量
    quota_service.increment_quota_usage(
        current_user,
        workspace_context,
        QuotaType.WPS,
        increment=1
    )
    
    return wps
```

## 🧪 测试方法

### 1. 测试工作区隔离

```python
# 测试个人工作区数据隔离
def test_personal_workspace_isolation():
    # 用户A创建个人WPS
    wps_a = create_wps(user_a, workspace_type="personal")
    
    # 用户B尝试访问用户A的个人WPS
    with pytest.raises(HTTPException) as exc:
        data_access.check_access(user_b, wps_a, "view")
    
    assert exc.value.status_code == 403
```

### 2. 测试企业数据共享

```python
# 测试企业工作区数据共享
def test_enterprise_workspace_sharing():
    # 用户A在企业工作区创建WPS（公司级别）
    wps = create_wps(
        user_a,
        workspace_type="enterprise",
        company_id=company.id,
        access_level="company"
    )
    
    # 同企业的用户B可以访问
    has_access = data_access.check_access(user_b, wps, "view")
    assert has_access == True
```

### 3. 测试配额管理

```python
# 测试配额限制
def test_quota_limit():
    # 用户配额：5个WPS
    user.membership_tier = "free"
    user.wps_quota_used = 5
    
    # 尝试创建第6个WPS
    with pytest.raises(HTTPException) as exc:
        quota_service.check_quota(user, workspace_context, QuotaType.WPS)
    
    assert "配额不足" in str(exc.value.detail)
```

## 📝 注意事项

1. **工作区上下文传递**：所有数据操作都需要传递工作区上下文
2. **配额检查**：创建数据前必须检查配额
3. **数据过滤**：查询数据时必须应用工作区过滤器
4. **权限检查**：编辑/删除数据前必须检查访问权限
5. **审计追踪**：所有数据操作都要记录created_by和updated_by

## 🔄 后续优化建议

1. **跨工厂访问配置**：实现FactoryDataAccess配置表
2. **数据共享审批流程**：实现数据共享申请和审批
3. **配额预警**：配额使用达到80%时发送通知
4. **数据归档**：实现数据归档和恢复功能
5. **性能优化**：为大数据量场景优化查询性能

## 📞 技术支持

如有问题，请参考：
- 架构设计文档：`modules/DATA_ISOLATION_AND_WORKSPACE_ARCHITECTURE.md`
- 开发指南：`modules/development-docs.md`

