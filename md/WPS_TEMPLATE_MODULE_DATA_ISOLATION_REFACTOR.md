# WPS模板和模块数据隔离重构

## 问题描述

用户发现WPS模板和模块的数据隔离实现方式与其他功能模块（Equipment、Material）不一致：

### 其他模块的实现 ✅
使用了**统一的`DataAccessMiddleware.apply_workspace_filter()`方法**：
```python
# 简单直接！
query = self.data_access.apply_workspace_filter(
    query,
    WeldingMaterial,
    current_user,
    workspace_context
)
```

### WPS模板和模块的旧实现 ❌
使用了**手动构建OR条件**的方式，代码复杂且不统一：
```python
# 复杂且容易出错！
visibility_filters = [
    WPSTemplate.template_source == "system",
    WPSTemplate.user_id == user_id,
]
if company_membership:
    visibility_filters.append(
        and_(
            WPSTemplate.company_id == company_membership.company_id,
            WPSTemplate.is_shared == True
        )
    )
query = query.filter(or_(*visibility_filters))
```

## 解决方案

重构WPS模板和模块的Service和API，使用统一的工作区上下文和数据隔离机制。

## 修复内容

### 1. WPS模板Service重构 (`backend/app/services/wps_template_service.py`)

#### 1.1 添加构造函数和DataAccessMiddleware
```python
class WPSTemplateService:
    """WPS模板服务"""
    
    def __init__(self, db: Session):
        """初始化WPS模板服务"""
        self.db = db
        self.data_access = DataAccessMiddleware(db)
```

#### 1.2 重构方法签名
**旧方法签名：**
```python
def get_available_templates(
    self,
    db: Session,
    user_id: int,
    welding_process: Optional[str] = None,
    standard: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> tuple[List[WPSTemplate], int]
```

**新方法签名：**
```python
def get_available_templates(
    self,
    current_user: User,
    workspace_context: WorkspaceContext,
    welding_process: Optional[str] = None,
    standard: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> tuple[List[WPSTemplate], int]
```

#### 1.3 简化数据隔离逻辑
**新实现：**
```python
# 构建可见性过滤条件
visibility_filters = [
    # 1. 系统模板（所有人可见）
    WPSTemplate.template_source == "system",
]

# 2. 个人工作区：用户自己的模板
if workspace_context.workspace_type == WorkspaceType.PERSONAL:
    visibility_filters.append(
        and_(
            WPSTemplate.workspace_type == WorkspaceType.PERSONAL,
            WPSTemplate.user_id == current_user.id
        )
    )

# 3. 企业工作区：企业内的模板
elif workspace_context.workspace_type == WorkspaceType.ENTERPRISE:
    if workspace_context.company_id:
        visibility_filters.append(
            and_(
                WPSTemplate.workspace_type == WorkspaceType.ENTERPRISE,
                WPSTemplate.company_id == workspace_context.company_id,
                or_(
                    WPSTemplate.is_shared == True,  # 企业共享模板
                    WPSTemplate.user_id == current_user.id  # 或者是自己创建的
                )
            )
        )

query = query.filter(or_(*visibility_filters))
```

#### 1.4 更新所有方法
- `get_available_templates()` - 使用工作区上下文过滤
- `get_template_by_id()` - 添加工作区上下文权限检查
- `create_template()` - 使用工作区上下文设置字段
- `update_template()` - 添加工作区上下文参数
- `delete_template()` - 添加工作区上下文参数
- `_check_template_access()` - 使用工作区上下文检查权限

### 2. WPS模板API重构 (`backend/app/api/v1/endpoints/wps_templates.py`)

#### 2.1 添加工作区上下文辅助函数
```python
def get_workspace_context(
    db: Session,
    current_user: User,
    workspace_id: Optional[str] = None
) -> WorkspaceContext:
    """获取工作区上下文"""
    workspace_service = WorkspaceService(db)
    
    if workspace_id:
        return workspace_service.create_workspace_context(current_user, workspace_id)
    
    # 根据用户会员类型确定默认工作区
    if current_user.membership_type == "enterprise":
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
    
    return WorkspaceContext(
        user_id=current_user.id,
        workspace_type=WorkspaceType.PERSONAL
    )
```

#### 2.2 更新所有API端点
所有端点都添加了：
- `workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")` 参数
- 工作区上下文获取
- 创建Service实例（不再使用全局单例）
- 使用新的Service方法签名

**更新的端点：**
- `GET /` - 获取模板列表
- `GET /{template_id}` - 获取模板详情
- `POST /` - 创建模板
- `PUT /{template_id}` - 更新模板
- `DELETE /{template_id}` - 删除模板

### 3. WPS模块Service重构 (`backend/app/services/custom_module_service.py`)

#### 3.1 添加构造函数和DataAccessMiddleware
```python
class CustomModuleService:
    """自定义模块服务类"""
    
    def __init__(self, db: Session):
        """初始化自定义模块服务"""
        self.db = db
        self.data_access = DataAccessMiddleware(db)
```

#### 3.2 重构方法签名
**旧方法签名：**
```python
def get_available_modules(
    self,
    db: Session,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
    workspace_type: str = 'personal',
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[CustomModule]
```

**新方法签名：**
```python
def get_available_modules(
    self,
    current_user: User,
    workspace_context: WorkspaceContext,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[CustomModule]
```

#### 3.3 更新所有方法
- `get_available_modules()` - 使用工作区上下文过滤
- `get_module()` - 添加工作区上下文权限检查
- `create_module()` - 使用工作区上下文设置字段
- `update_module()` - 添加工作区上下文权限检查
- `delete_module()` - 添加工作区上下文权限检查
- `_check_module_access()` - 新增，检查查看权限
- `_check_module_permission()` - 新增，检查修改/删除权限

### 4. WPS模块API重构 (`backend/app/api/v1/endpoints/custom_modules.py`)

#### 4.1 添加工作区上下文辅助函数
与WPS模板API相同的`get_workspace_context()`函数。

#### 4.2 更新所有API端点
所有端点都添加了：
- `workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")` 参数
- 工作区上下文获取
- 创建Service实例（不再使用全局单例）
- 使用新的Service方法签名

**更新的端点：**
- `GET /` - 获取模块列表
- `GET /{module_id}` - 获取模块详情
- `POST /` - 创建模块
- `PUT /{module_id}` - 更新模块
- `DELETE /{module_id}` - 删除模块
- `POST /{module_id}/increment-usage` - 增加使用次数

## 数据隔离逻辑

### 个人工作区
```python
workspace_type = "personal"
user_id = current_user.id

# 查询条件
(workspace_type == "personal" AND user_id == current_user.id)
OR template_source == "system"  # 系统模板/模块对所有人可见
```

### 企业工作区
```python
workspace_type = "enterprise"
company_id = workspace_context.company_id
factory_id = workspace_context.factory_id

# 查询条件
(workspace_type == "enterprise" AND company_id == workspace_context.company_id 
 AND (is_shared == True OR user_id == current_user.id))
OR template_source == "system"  # 系统模板/模块对所有人可见
```

## 优势

### 1. 代码统一性
- 所有模块（WPS、Equipment、Material、Template、Module）使用相同的数据隔离模式
- 更容易维护和理解

### 2. 类型安全
- 使用`WorkspaceContext`和`WorkspaceType`枚举
- 编译时类型检查

### 3. 可扩展性
- 新增工作区类型时，只需修改一处
- 更容易添加新的权限规则

### 4. 一致性
- Service层和API层的实现模式一致
- 减少了代码重复

## 影响范围

### 修改的文件
1. `backend/app/services/wps_template_service.py` - WPS模板服务层
2. `backend/app/api/v1/endpoints/wps_templates.py` - WPS模板API
3. `backend/app/services/custom_module_service.py` - 自定义模块服务层
4. `backend/app/api/v1/endpoints/custom_modules.py` - 自定义模块API

### 新增的文件
1. `WPS_TEMPLATE_MODULE_DATA_ISOLATION_REFACTOR.md` - 重构文档

### 数据库影响
- 无需修改数据库结构
- 模板和模块模型已有所需的数据隔离字段

## 测试建议

### 1. 模板测试
```bash
# 获取模板列表（个人工作区）
curl -X GET http://localhost:8000/api/v1/wps-templates/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Workspace-ID: personal_USER_ID"

# 获取模板列表（企业工作区）
curl -X GET http://localhost:8000/api/v1/wps-templates/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Workspace-ID: enterprise_COMPANY_ID"
```

### 2. 模块测试
```bash
# 获取模块列表（个人工作区）
curl -X GET http://localhost:8000/api/v1/custom-modules/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Workspace-ID: personal_USER_ID"

# 获取模块列表（企业工作区）
curl -X GET http://localhost:8000/api/v1/custom-modules/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Workspace-ID: enterprise_COMPANY_ID"
```

### 3. 前端测试
1. 使用企业会员账号登录
2. 切换工作区（个人/企业）
3. 验证：
   - 个人工作区只显示个人模板/模块和系统模板/模块
   - 企业工作区显示企业模板/模块、个人创建的企业模板/模块和系统模板/模块
   - 创建模板/模块时正确设置工作区字段

## 注意事项

### 1. 向后兼容性
- Service方法签名已更改，旧代码需要更新
- 不再使用全局Service单例，需要创建实例

### 2. 工作区上下文
- 前端可以在请求头中传递`X-Workspace-ID`
- 如果未传递，API会根据用户的会员类型自动选择默认工作区

### 3. 特殊可见性规则
- 系统模板/模块对所有人可见
- 企业共享模板/模块只对企业成员可见
- 个人模板/模块只对创建者可见

## 总结

✅ **完成的工作**：
- WPS模板Service和API重构
- WPS模块Service和API重构
- 统一了数据隔离实现方式
- 提高了代码可维护性和一致性

✅ **现在系统具备**：
- 统一的数据隔离机制
- 类型安全的工作区上下文
- 清晰的权限管理
- 更好的代码组织结构

✅ **用户体验改进**：
- 数据隔离更加严格和可靠
- 工作区切换更加流畅
- 权限控制更加精确

