# 设备管理工作区隔离问题修复

## 问题描述

用户在企业工作区创建了设备，但切换到个人工作区后仍然能看到该设备。这违反了工作区数据隔离的原则。

## 根本原因分析

### 问题1：创建设备时未使用前端工作区上下文

**位置**: `backend/app/api/v1/endpoints/equipment.py` - `create_equipment` 函数

**问题**:
- 创建设备时，后端直接使用 `get_user_company_info()` 自动判断工作区类型
- 没有接收前端传递的 `workspace_type` 参数
- 导致即使用户在个人工作区操作，如果用户有企业关系，设备也会被创建为企业设备

**影响**:
```python
# 原代码逻辑
workspace_type, company_id, factory_id = get_user_company_info(db, current_user.id)
# 如果用户有企业关系，总是创建企业设备，忽略用户当前所在的工作区
```

### 问题2：查询设备时的过滤逻辑不完整

**位置**: `backend/app/services/equipment_service.py` - `get_equipment_list` 方法

**问题**:
```python
# 原代码逻辑（第184-188行）
if workspace_context.company_id:
    query = query.filter(Equipment.company_id == workspace_context.company_id)
else:
    query = query.filter(Equipment.user_id == current_user.id)
```

**缺陷**:
- 只根据 `company_id` 是否存在来过滤，没有检查 `workspace_type`
- 当切换到个人工作区时，`company_id` 为 `None`
- 但只过滤 `user_id`，会查出该用户创建的**所有设备**（包括个人的和企业的）
- 缺少对 `workspace_type` 字段的过滤

**正确逻辑应该是**:
- **个人工作区**: `workspace_type='personal' AND user_id=当前用户`
- **企业工作区**: `workspace_type='enterprise' AND company_id=企业ID`

## 修复方案

### 1. 后端API修改

#### 1.1 创建设备API (`POST /equipment`)

**修改内容**:
- 添加 `workspace_type` 查询参数
- 根据前端传递的工作区类型创建相应的工作区上下文
- 支持三种模式：
  - `workspace_type=personal`: 强制创建个人设备
  - `workspace_type=company`: 创建企业设备
  - 未指定: 自动判断（向后兼容）

**代码变更**:
```python
@router.post("/")
async def create_equipment(
    equipment_data: EquipmentCreate,
    workspace_type: Optional[str] = Query(None, description="工作区类型: personal/company"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    # 根据前端传递的工作区类型创建工作区上下文
    if workspace_type == "personal":
        workspace_context = WorkspaceContext(
            user_id=current_user.id,
            workspace_type="personal",
            company_id=None,
            factory_id=None
        )
    elif workspace_type == "company":
        user_workspace_type, user_company_id, user_factory_id = get_user_company_info(db, current_user.id)
        workspace_context = WorkspaceContext(
            user_id=current_user.id,
            workspace_type=user_workspace_type,
            company_id=user_company_id,
            factory_id=user_factory_id
        )
    # ... 其他逻辑
```

#### 1.2 查询设备列表服务

**修改内容**:
- 在 `EquipmentService.get_equipment_list()` 中添加严格的工作区类型过滤
- 同时检查 `workspace_type` 和相应的 ID 字段

**代码变更**:
```python
# 应用工作区过滤 - 根据工作区类型严格过滤
if workspace_context.workspace_type == "personal":
    # 个人工作区：只查询个人设备
    query = query.filter(
        Equipment.workspace_type == "personal",
        Equipment.user_id == current_user.id
    )
elif workspace_context.workspace_type == "company" or workspace_context.workspace_type == "enterprise":
    # 企业工作区：只查询企业设备
    if workspace_context.company_id:
        query = query.filter(
            Equipment.workspace_type == "enterprise",
            Equipment.company_id == workspace_context.company_id
        )
    else:
        # 如果没有company_id，返回空结果
        query = query.filter(Equipment.id == -1)
```

#### 1.3 其他设备API

同样的修改应用到：
- `GET /equipment/{equipment_id}` - 获取设备详情
- `PUT /equipment/{equipment_id}` - 更新设备
- `DELETE /equipment/{equipment_id}` - 删除设备

所有这些API都添加了 `workspace_type` 查询参数。

### 2. 前端服务修改

#### 2.1 设备服务 (`frontend/src/services/equipment.ts`)

**修改内容**:
- 在所有设备操作中添加当前工作区类型参数
- 从本地存储读取当前工作区信息
- 将工作区类型转换为API期望的格式

**代码变更**:
```typescript
// 添加辅助方法获取当前工作区
private getCurrentWorkspace() {
  try {
    const workspaceData = localStorage.getItem('current_workspace')
    return workspaceData ? JSON.parse(workspaceData) : null
  } catch (error) {
    console.error('获取当前工作区失败:', error)
    return null
  }
}

// 创建设备时传递工作区类型
async createEquipment(data: CreateEquipmentData): Promise<ApiResponse<Equipment>> {
  const currentWorkspace = this.getCurrentWorkspace()
  const workspaceType = currentWorkspace?.type === 'enterprise' ? 'company' : 'personal'
  
  const response = await apiService.post<Equipment>(
    `/equipment?workspace_type=${workspaceType}`, 
    data
  )
  return response.data
}

// 更新设备时传递工作区类型
async updateEquipment(equipmentId: string, data: UpdateEquipmentData): Promise<ApiResponse<Equipment>> {
  const currentWorkspace = this.getCurrentWorkspace()
  const workspaceType = currentWorkspace?.type === 'enterprise' ? 'company' : 'personal'
  
  const response = await apiService.put<Equipment>(
    `/equipment/${equipmentId}?workspace_type=${workspaceType}`, 
    data
  )
  return response.data
}

// 删除设备时传递工作区类型
async deleteEquipment(equipmentId: string): Promise<ApiResponse<void>> {
  const currentWorkspace = this.getCurrentWorkspace()
  const workspaceType = currentWorkspace?.type === 'enterprise' ? 'company' : 'personal'
  
  const response = await apiService.delete<void>(
    `/equipment/${equipmentId}?workspace_type=${workspaceType}`
  )
  return response.data
}
```

## 修复效果

### 修复前
1. 用户在企业工作区创建设备 → 设备被标记为企业设备（`workspace_type='enterprise'`, `company_id=X`）
2. 用户切换到个人工作区 → 查询时只过滤 `user_id`，仍能看到企业设备
3. **问题**: 数据隔离失效

### 修复后
1. 用户在企业工作区创建设备 → 设备被标记为企业设备（`workspace_type='enterprise'`, `company_id=X`）
2. 用户切换到个人工作区 → 查询时过滤 `workspace_type='personal' AND user_id=当前用户`
3. **结果**: 只能看到个人设备，企业设备不可见
4. 用户在个人工作区创建设备 → 设备被标记为个人设备（`workspace_type='personal'`, `company_id=NULL`）
5. 用户切换到企业工作区 → 查询时过滤 `workspace_type='enterprise' AND company_id=X`
6. **结果**: 只能看到企业设备，个人设备不可见

## 数据隔离原则

### 核心规则
1. **创建时**: 根据当前工作区类型设置 `workspace_type` 和相应的 ID 字段
2. **查询时**: 必须同时检查 `workspace_type` 和相应的 ID 字段
3. **更新/删除时**: 必须在当前工作区上下文中验证权限

### 字段组合
| 工作区类型 | workspace_type | user_id | company_id | factory_id |
|-----------|----------------|---------|------------|------------|
| 个人工作区 | 'personal' | 必填 | NULL | NULL |
| 企业工作区 | 'enterprise' | 必填（创建者） | 必填 | 可选 |

### 查询过滤规则
```sql
-- 个人工作区查询
WHERE workspace_type = 'personal' 
  AND user_id = :current_user_id

-- 企业工作区查询
WHERE workspace_type = 'enterprise' 
  AND company_id = :company_id
  AND (factory_id = :factory_id OR factory_id IS NULL)  -- 可选的工厂过滤
```

## 测试建议

### 测试场景
1. **个人工作区创建设备**
   - 创建设备
   - 验证 `workspace_type='personal'`, `company_id=NULL`
   - 切换到企业工作区，验证设备不可见

2. **企业工作区创建设备**
   - 创建设备
   - 验证 `workspace_type='enterprise'`, `company_id=企业ID`
   - 切换到个人工作区，验证设备不可见

3. **工作区切换**
   - 在两个工作区分别创建设备
   - 切换工作区，验证只能看到当前工作区的设备

4. **设备操作权限**
   - 在个人工作区尝试访问企业设备（应失败）
   - 在企业工作区尝试访问个人设备（应失败）

## 相关文件

### 后端文件
- `backend/app/api/v1/endpoints/equipment.py` - 设备API端点
- `backend/app/services/equipment_service.py` - 设备服务层
- `backend/app/core/data_access.py` - 数据访问控制

### 前端文件
- `frontend/src/services/equipment.ts` - 设备服务
- `frontend/src/pages/Equipment/EquipmentList.tsx` - 设备列表页面
- `frontend/src/services/workspace.ts` - 工作区服务

## 后续改进建议

1. **统一工作区上下文传递**
   - 考虑在请求头中传递工作区信息，而不是查询参数
   - 可以使用中间件自动注入工作区上下文

2. **数据库约束**
   - 添加检查约束确保数据一致性
   - 例如: `CHECK ((workspace_type = 'personal' AND company_id IS NULL) OR (workspace_type = 'enterprise' AND company_id IS NOT NULL))`

3. **其他模块应用相同修复**
   - WPS、PQR、焊工、焊材等模块应用相同的修复逻辑
   - 确保所有业务模块都遵循相同的数据隔离原则

4. **添加集成测试**
   - 编写自动化测试验证工作区隔离
   - 测试覆盖所有CRUD操作

