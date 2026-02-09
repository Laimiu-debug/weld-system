# 📋 四大模块详细实施计划

**制定日期**: 2025-10-20  
**预计总时间**: 3小时  
**实施顺序**: 焊材 → 焊工 → 生产 → 质量

---

## 🎯 总体目标

实现焊材管理、焊工管理、生产管理、质量管理四个模块的完整功能，包括：
- ✅ 数据隔离（个人/企业工作区）
- ✅ 权限管理（所有者/管理员/角色/默认）
- ✅ 配额管理（物理资产模块不受限制）
- ✅ 审计追踪
- ✅ 友好错误提示

---

## 📊 实施时间表

| 模块 | Schema | Service | API | 前端 | 测试 | 总计 |
|------|--------|---------|-----|------|------|------|
| 焊材管理 | 5分钟 | 15分钟 | 10分钟 | 5分钟 | 10分钟 | 45分钟 |
| 焊工管理 | 5分钟 | 15分钟 | 10分钟 | 5分钟 | 10分钟 | 45分钟 |
| 生产管理 | 5分钟 | 15分钟 | 10分钟 | 5分钟 | 10分钟 | 45分钟 |
| 质量管理 | 5分钟 | 15分钟 | 10分钟 | 5分钟 | 10分钟 | 45分钟 |
| **总计** | **20分钟** | **60分钟** | **40分钟** | **20分钟** | **40分钟** | **180分钟** |

---

## 1️⃣ 焊材管理模块实施计划

### 任务清单

#### 任务1.1：创建Pydantic Schema（5分钟）
**文件**: `backend/app/schemas/material.py`

**需要创建的Schema**:
- [ ] `MaterialBase` - 基础Schema
- [ ] `MaterialCreate` - 创建Schema
- [ ] `MaterialUpdate` - 更新Schema
- [ ] `MaterialResponse` - 响应Schema
- [ ] `MaterialListResponse` - 列表响应Schema

**关键字段**:
```python
# 基础字段
material_code: str
material_name: str
material_type: str
specification: Optional[str]
manufacturer: Optional[str]
current_stock: float
unit: str
min_stock_level: Optional[float]
```

#### 任务1.2：创建服务层（15分钟）
**文件**: `backend/app/services/material_service.py`

**需要实现的方法**:
- [ ] `__init__()` - 初始化DataAccessMiddleware和QuotaService
- [ ] `create_material()` - 创建焊材
  - 检查创建权限
  - 检查配额（会自动跳过）
  - 设置数据隔离字段
  - 设置访问级别
- [ ] `get_material_list()` - 获取列表
  - 检查查看权限
  - 应用数据过滤
  - 支持搜索和筛选
- [ ] `get_material_by_id()` - 获取详情
  - 检查查看权限
- [ ] `update_material()` - 更新焊材
  - 检查编辑权限
- [ ] `delete_material()` - 删除焊材
  - 检查删除权限
  - 更新配额（会自动跳过）
- [ ] `_check_create_permission()` - 创建权限检查辅助方法
- [ ] `_check_list_permission()` - 查看权限检查辅助方法

**参考**: `backend/app/services/equipment_service.py`

#### 任务1.3：实现API端点（10分钟）
**文件**: `backend/app/api/v1/endpoints/materials.py`

**需要实现的端点**:
- [ ] `GET /materials` - 获取列表
  - 构建WorkspaceContext
  - 调用service.get_material_list()
  - 错误处理
- [ ] `POST /materials` - 创建焊材
  - 构建WorkspaceContext
  - 调用service.create_material()
  - 错误处理
- [ ] `GET /materials/{id}` - 获取详情
  - 构建WorkspaceContext
  - 调用service.get_material_by_id()
  - 错误处理
- [ ] `PUT /materials/{id}` - 更新焊材
  - 构建WorkspaceContext
  - 调用service.update_material()
  - 错误处理
- [ ] `DELETE /materials/{id}` - 删除焊材
  - 构建WorkspaceContext
  - 调用service.delete_material()
  - 错误处理

**参考**: `backend/app/api/v1/endpoints/equipment.py`

#### 任务1.4：前端集成（5分钟）
**文件**: `frontend/src/pages/Materials/*.tsx`

**需要更新**:
- [ ] 更新API调用（移除模拟数据）
- [ ] 添加工作区参数
- [ ] 测试CRUD操作

#### 任务1.5：测试（10分钟）
- [ ] 个人工作区：创建、查看、编辑、删除
- [ ] 企业工作区：创建、查看、编辑、删除
- [ ] 权限测试：所有者、管理员、角色、默认
- [ ] 错误提示测试

---

## 2️⃣ 焊工管理模块实施计划

### 任务清单

#### 任务2.1：创建Pydantic Schema（5分钟）
**文件**: `backend/app/schemas/welder.py`

**需要创建的Schema**:
- [ ] `WelderBase` - 基础Schema
- [ ] `WelderCreate` - 创建Schema
- [ ] `WelderUpdate` - 更新Schema
- [ ] `WelderResponse` - 响应Schema
- [ ] `WelderListResponse` - 列表响应Schema
- [ ] `WelderCertificationCreate` - 证书创建Schema
- [ ] `WelderCertificationResponse` - 证书响应Schema

**关键字段**:
```python
# 基础字段
welder_code: str
full_name: str
gender: Optional[str]
phone: Optional[str]
primary_certification_number: Optional[str]
primary_certification_level: Optional[str]
skill_level: Optional[str]
status: str = "active"
```

#### 任务2.2：创建服务层（15分钟）
**文件**: `backend/app/services/welder_service.py`

**需要实现的方法**:
- [ ] `__init__()` - 初始化
- [ ] `create_welder()` - 创建焊工
- [ ] `get_welder_list()` - 获取列表
- [ ] `get_welder_by_id()` - 获取详情
- [ ] `update_welder()` - 更新焊工
- [ ] `delete_welder()` - 删除焊工
- [ ] `add_certification()` - 添加证书（可选）
- [ ] `_check_create_permission()` - 权限检查
- [ ] `_check_list_permission()` - 权限检查

#### 任务2.3：实现API端点（10分钟）
**文件**: `backend/app/api/v1/endpoints/welders.py`

**需要实现的端点**:
- [ ] `GET /welders` - 获取列表
- [ ] `POST /welders` - 创建焊工
- [ ] `GET /welders/{id}` - 获取详情
- [ ] `PUT /welders/{id}` - 更新焊工
- [ ] `DELETE /welders/{id}` - 删除焊工

#### 任务2.4：前端集成（5分钟）
- [ ] 更新API调用
- [ ] 测试CRUD操作

#### 任务2.5：测试（10分钟）
- [ ] 完整测试流程

---

## 3️⃣ 生产管理模块实施计划

### 任务清单

#### 任务3.1：创建Pydantic Schema（5分钟）
**文件**: `backend/app/schemas/production.py`

**需要创建的Schema**:
- [ ] `ProductionTaskBase` - 基础Schema
- [ ] `ProductionTaskCreate` - 创建Schema
- [ ] `ProductionTaskUpdate` - 更新Schema
- [ ] `ProductionTaskResponse` - 响应Schema
- [ ] `ProductionTaskListResponse` - 列表响应Schema

**关键字段**:
```python
# 基础字段
task_number: str
task_name: str
wps_id: Optional[int]
status: str = "pending"
priority: str = "normal"
planned_start_date: Optional[date]
planned_end_date: Optional[date]
assigned_welder_id: Optional[int]
assigned_equipment_id: Optional[int]
```

#### 任务3.2：创建服务层（15分钟）
**文件**: `backend/app/services/production_service.py`

**需要实现的方法**:
- [ ] `__init__()` - 初始化
- [ ] `create_task()` - 创建任务
- [ ] `get_task_list()` - 获取列表
- [ ] `get_task_by_id()` - 获取详情
- [ ] `update_task()` - 更新任务
- [ ] `delete_task()` - 删除任务
- [ ] `update_progress()` - 更新进度（可选）
- [ ] `_check_create_permission()` - 权限检查
- [ ] `_check_list_permission()` - 权限检查

#### 任务3.3：实现API端点（10分钟）
**文件**: `backend/app/api/v1/endpoints/production.py`

**需要实现的端点**:
- [ ] `GET /production/tasks` - 获取列表
- [ ] `POST /production/tasks` - 创建任务
- [ ] `GET /production/tasks/{id}` - 获取详情
- [ ] `PUT /production/tasks/{id}` - 更新任务
- [ ] `DELETE /production/tasks/{id}` - 删除任务

#### 任务3.4：前端集成（5分钟）
- [ ] 更新API调用
- [ ] 测试CRUD操作

#### 任务3.5：测试（10分钟）
- [ ] 完整测试流程

---

## 4️⃣ 质量管理模块实施计划

### 任务清单

#### 任务4.1：创建Pydantic Schema（5分钟）
**文件**: `backend/app/schemas/quality.py`

**需要创建的Schema**:
- [ ] `QualityInspectionBase` - 基础Schema
- [ ] `QualityInspectionCreate` - 创建Schema
- [ ] `QualityInspectionUpdate` - 更新Schema
- [ ] `QualityInspectionResponse` - 响应Schema
- [ ] `QualityInspectionListResponse` - 列表响应Schema

**关键字段**:
```python
# 基础字段
inspection_number: str
inspection_type: str
inspection_date: date
production_task_id: Optional[int]
inspector_id: Optional[int]
result: str = "pending"
defects_found: int = 0
```

#### 任务4.2：创建服务层（15分钟）
**文件**: `backend/app/services/quality_service.py`

**需要实现的方法**:
- [ ] `__init__()` - 初始化
- [ ] `create_inspection()` - 创建检验
- [ ] `get_inspection_list()` - 获取列表
- [ ] `get_inspection_by_id()` - 获取详情
- [ ] `update_inspection()` - 更新检验
- [ ] `delete_inspection()` - 删除检验
- [ ] `_check_create_permission()` - 权限检查
- [ ] `_check_list_permission()` - 权限检查

#### 任务4.3：实现API端点（10分钟）
**文件**: `backend/app/api/v1/endpoints/quality.py`

**需要实现的端点**:
- [ ] `GET /quality/inspections` - 获取列表
- [ ] `POST /quality/inspections` - 创建检验
- [ ] `GET /quality/inspections/{id}` - 获取详情
- [ ] `PUT /quality/inspections/{id}` - 更新检验
- [ ] `DELETE /quality/inspections/{id}` - 删除检验

#### 任务4.4：前端集成（5分钟）
- [ ] 更新API调用
- [ ] 测试CRUD操作

#### 任务4.5：测试（10分钟）
- [ ] 完整测试流程

---

## 🔑 关键实施要点

### 1. 统一的代码模式

所有模块都遵循相同的模式：

```python
# 服务层模式
class {Module}Service:
    def __init__(self, db: Session):
        self.db = db
        self.data_access = DataAccessMiddleware(db)
        self.quota_service = QuotaService(db)
    
    def create_{module}(self, current_user, data, workspace_context):
        # 1. 验证工作区
        workspace_context.validate()
        
        # 2. 检查权限（企业工作区）
        if workspace_context.workspace_type == "enterprise":
            self._check_create_permission(current_user, workspace_context)
        
        # 3. 检查配额（会自动跳过物理资产模块）
        self.quota_service.check_quota(current_user, workspace_context, "{module}", 1)
        
        # 4. 创建对象
        obj = {Module}(**data)
        obj.workspace_type = workspace_context.workspace_type
        obj.user_id = current_user.id
        obj.company_id = workspace_context.company_id
        obj.factory_id = workspace_context.factory_id
        obj.created_by = current_user.id
        
        # 5. 设置访问级别
        if workspace_context.workspace_type == "enterprise":
            obj.access_level = "company"
        else:
            obj.access_level = "private"
        
        # 6. 保存
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        
        # 7. 更新配额（会自动跳过）
        self.quota_service.update_quota_usage(current_user, workspace_context, "{module}", 1)
        
        return obj
```

### 2. 工作区上下文构建

```python
# API端点中
workspace_context = WorkspaceContext(
    workspace_type=workspace_type,
    user_id=current_user.id,
    company_id=company_id,
    factory_id=factory_id
)
```

### 3. 错误提示格式

```python
raise HTTPException(
    status_code=403,
    detail="权限不足：您没有{操作}{模块}的权限"
)
```

---

## ✅ 验收标准

每个模块完成后需要满足：

1. **功能完整性**
   - ✅ CRUD操作全部实现
   - ✅ 数据隔离正确
   - ✅ 权限检查正确

2. **代码质量**
   - ✅ 遵循统一的代码模式
   - ✅ 错误处理完善
   - ✅ 注释清晰

3. **测试覆盖**
   - ✅ 个人工作区测试通过
   - ✅ 企业工作区测试通过
   - ✅ 权限测试通过
   - ✅ 错误提示友好

---

## 📚 参考资源

- `QUICK_IMPLEMENTATION_GUIDE.md` - 快速实施指南
- `API_ENDPOINT_TEMPLATE.md` - API端点模板
- `backend/app/services/equipment_service.py` - 设备服务参考
- `backend/app/api/v1/endpoints/equipment.py` - 设备API参考

---

**准备开始实施！**

