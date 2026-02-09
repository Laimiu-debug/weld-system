# CORS 和 500 错误修复说明

## 问题描述

前端访问审批历史 API 时出现以下错误：

```
Access to XMLHttpRequest at 'http://localhost:8000/api/v1/approvals/34/history' 
from origin 'http://localhost:3000' has been blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.

GET http://localhost:8000/api/v1/approvals/34/history net::ERR_FAILED 500 (Internal Server Error)
```

## 根本原因

后端 API 端点直接返回 SQLAlchemy ORM 对象，FastAPI 无法正确序列化这些对象为 JSON。当序列化失败时：
1. 抛出 500 内部服务器错误
2. 错误响应中缺少 CORS 头，导致浏览器报 CORS 错误

## 修复方案

### 已修复的端点

在 `backend/app/api/v1/endpoints/approvals.py` 中修复了以下端点：

1. **`GET /api/v1/approvals/{instance_id}/history`**
   - 将 `ApprovalHistory` ORM 对象转换为字典列表
   - 正确处理日期时间和可选字段

2. **`GET /api/v1/approvals/pending`**
   - 使用 Pydantic schema 序列化 `ApprovalInstance` 对象

3. **`GET /api/v1/approvals/my-submissions`**
   - 使用 Pydantic schema 序列化 `ApprovalInstance` 对象

4. **`GET /api/v1/approvals/workflows/{workflow_id}`**
   - 将 `ApprovalWorkflowDefinition` ORM 对象转换为字典

5. **`GET /api/v1/approvals/{instance_id}`**
   - 将 `ApprovalInstance` 和 `ApprovalHistory` 对象转换为字典

### 修复示例

**修复前（错误）：**
```python
@router.get("/{instance_id}/history")
async def get_approval_history(instance_id: int, db: Session = Depends(get_db)) -> Any:
    history = approval_service.get_approval_history(instance_id)
    return {"success": True, "data": history}  # ❌ 直接返回 ORM 对象
```

**修复后（正确）：**
```python
@router.get("/{instance_id}/history")
async def get_approval_history(instance_id: int, db: Session = Depends(get_db)) -> Any:
    history = approval_service.get_approval_history(instance_id)
    
    # ✅ 将 ORM 对象转换为字典列表
    history_data = []
    for item in history:
        history_data.append({
            "id": item.id,
            "instance_id": item.instance_id,
            "step_number": item.step_number,
            "step_name": item.step_name,
            "action": item.action,
            "operator_id": item.operator_id,
            "operator_name": item.operator_name,
            "operator_role": item.operator_role,
            "comment": item.comment,
            "attachments": item.attachments or [],
            "result": item.result,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "ip_address": item.ip_address
        })
    
    return {"success": True, "data": history_data}
```

## 验证修复

### 1. 检查后端服务器

确保后端服务器正在运行并已重新加载代码：

```bash
# 如果使用 uvicorn 的热重载，代码会自动重新加载
# 否则需要重启服务器
```

### 2. 测试 CORS 配置

```bash
curl -X OPTIONS http://localhost:8000/api/v1/approvals/34/history \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: authorization"
```

预期响应头应包含：
- `access-control-allow-origin: http://localhost:3000`
- `access-control-allow-credentials: true`

### 3. 测试前端

1. 刷新前端页面（Ctrl+F5 强制刷新）
2. 登录系统
3. 访问审批历史页面
4. 检查浏览器控制台是否还有错误

## 注意事项

### CORS 配置

CORS 配置在 `backend/app/main.py` 中已正确设置：

```python
if settings.DEVELOPMENT:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 开发环境允许所有来源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
```

### 认证要求

所有审批相关的 API 端点都需要认证。确保：
1. 用户已登录
2. localStorage 中有有效的 token
3. API 请求头包含 `Authorization: Bearer <token>`

### 前端 API 配置

前端 API 配置在 `frontend/.env` 中：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## 最佳实践

为避免类似问题，遵循以下最佳实践：

### 1. 使用 Pydantic Schema

```python
# ✅ 推荐
from app.schemas.approval import ApprovalInstanceResponse

@router.get("/endpoint")
async def get_data(db: Session = Depends(get_db)) -> Any:
    items = db.query(Model).all()
    items_data = [ResponseSchema.model_validate(item).model_dump() for item in items]
    return {"success": True, "data": items_data}
```

### 2. 手动转换为字典

```python
# ✅ 可接受
@router.get("/endpoint")
async def get_data(db: Session = Depends(get_db)) -> Any:
    items = db.query(Model).all()
    items_data = [{
        "id": item.id,
        "name": item.name,
        "created_at": item.created_at.isoformat() if item.created_at else None
    } for item in items]
    return {"success": True, "data": items_data}
```

### 3. 避免直接返回 ORM 对象

```python
# ❌ 错误
@router.get("/endpoint")
async def get_data(db: Session = Depends(get_db)) -> Any:
    items = db.query(Model).all()
    return {"success": True, "data": items}  # 不要这样做！
```

## 相关文件

- `backend/app/api/v1/endpoints/approvals.py` - 修复的主要文件
- `backend/app/schemas/approval.py` - Pydantic schemas
- `backend/app/models/approval.py` - SQLAlchemy models
- `backend/app/main.py` - CORS 配置
- `frontend/src/services/api.ts` - 前端 API 配置
- `frontend/src/components/Approval/ApprovalHistory.tsx` - 审批历史组件

## 故障排除

### 如果仍然看到 CORS 错误

1. 检查后端服务器是否正在运行
2. 检查 `backend/app/core/config.py` 中 `DEVELOPMENT = True`
3. 清除浏览器缓存并刷新页面

### 如果仍然看到 500 错误

1. 检查后端日志中的详细错误信息
2. 确保数据库连接正常
3. 检查审批实例 ID 是否存在

### 如果看到 401 错误

1. 确保已登录
2. 检查 localStorage 中是否有 token
3. 检查 token 是否过期

## 测试脚本

运行测试脚本验证修复：

```bash
python test_approval_history.py
```

这将测试：
- CORS 预检请求
- 未认证的请求（应返回 401）
- 已认证的请求（如果提供了有效的登录凭据）

