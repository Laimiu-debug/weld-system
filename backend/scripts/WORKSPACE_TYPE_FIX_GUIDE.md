# 设备工作区类型修复指南

## 问题描述

设备创建后在列表中看不到，原因是 `workspace_type` 字段值不一致：

- **创建时保存**：`workspace_type = 'company'`
- **查询时期望**：`workspace_type = 'enterprise'`

## 根本原因

`get_user_company_info()` 函数之前返回 `"company"`，但查询逻辑期望的是 `"enterprise"`。

## 修复步骤

### 步骤 1：执行 SQL 修复现有数据

在 DBeaver 或其他 PostgreSQL 客户端中执行以下 SQL：

```sql
-- 1. 查看当前状态
SELECT 
    workspace_type,
    COUNT(*) as count
FROM equipment
GROUP BY workspace_type;

-- 2. 修复：将 'company' 改为 'enterprise'
UPDATE equipment
SET workspace_type = 'enterprise'
WHERE workspace_type = 'company';

-- 3. 同时修复 NULL 或空值
UPDATE equipment
SET workspace_type = 'enterprise'
WHERE (workspace_type IS NULL OR workspace_type = '')
  AND company_id IS NOT NULL;

UPDATE equipment
SET workspace_type = 'personal'
WHERE (workspace_type IS NULL OR workspace_type = '')
  AND company_id IS NULL;

-- 4. 验证修复结果
SELECT 
    workspace_type,
    COUNT(*) as count
FROM equipment
GROUP BY workspace_type;

-- 应该只看到 'personal' 和 'enterprise' 两种类型
```

### 步骤 2：重启后端服务

代码已经修复，需要重启后端服务使其生效：

```bash
# 停止当前运行的后端服务（Ctrl+C）
# 然后重新启动
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 步骤 3：清除浏览器缓存并刷新前端

1. 清除浏览器缓存（Ctrl+Shift+Delete）
2. 刷新前端页面（Ctrl+F5 强制刷新）

### 步骤 4：测试验证

#### 测试 1：查看现有设备

1. 切换到**企业工作区**
2. 进入设备列表
3. 应该能看到之前创建的企业设备

4. 切换到**个人工作区**
5. 进入设备列表
6. 应该能看到之前创建的个人设备

#### 测试 2：创建新设备

1. 在**企业工作区**创建一个新设备
2. 验证能在企业工作区的设备列表中看到
3. 切换到个人工作区，验证看不到该设备

4. 在**个人工作区**创建一个新设备
5. 验证能在个人工作区的设备列表中看到
6. 切换到企业工作区，验证看不到该设备

#### 测试 3：设备统计

1. 在企业工作区查看设备统计，应该只显示企业设备数量
2. 在个人工作区查看设备统计，应该只显示个人设备数量

## 代码修改说明

### 修改的文件

1. **backend/app/api/v1/endpoints/equipment.py**
   - `get_user_company_info()` 函数：返回值从 `"company"` 改为 `"enterprise"`

2. **backend/app/services/equipment_service.py**
   - `get_equipment_statistics()` 方法：添加工作区过滤逻辑

3. **frontend/src/services/equipment.ts**
   - `getEquipmentStatistics()` 方法：添加 `workspace_type` 参数

### 数据库字段规范

从现在开始，`equipment` 表的 `workspace_type` 字段只能有两个值：

- `'personal'` - 个人设备
- `'enterprise'` - 企业设备

**注意**：不再使用 `'company'` 作为值！

## 前后端交互规范

### 前端 → 后端

前端在调用 API 时，`workspace_type` 参数使用：
- `'personal'` - 个人工作区
- `'company'` - 企业工作区（为了保持前端代码的语义清晰）

### 后端内部

后端接收到 `workspace_type='company'` 后，会自动转换为 `'enterprise'` 保存到数据库。

### 查询逻辑

查询时，后端会：
- 接收前端的 `workspace_type='company'`
- 在查询条件中使用 `workspace_type='enterprise'`

## 验证 SQL

如果需要验证数据库中的设备状态，可以执行：

```sql
-- 查看所有设备的工作区类型分布
SELECT 
    workspace_type,
    COUNT(*) as count,
    COUNT(CASE WHEN company_id IS NOT NULL THEN 1 END) as with_company,
    COUNT(CASE WHEN company_id IS NULL THEN 1 END) as without_company
FROM equipment
GROUP BY workspace_type;

-- 查看具体设备详情
SELECT 
    id,
    equipment_code,
    equipment_name,
    workspace_type,
    user_id,
    company_id,
    is_active
FROM equipment
ORDER BY created_at DESC;

-- 检查是否有无效的 workspace_type
SELECT COUNT(*) as invalid_count
FROM equipment
WHERE workspace_type NOT IN ('personal', 'enterprise')
   OR workspace_type IS NULL;
```

## 常见问题

### Q1: 执行 SQL 后还是看不到设备？

**A**: 请确保：
1. SQL 执行成功（检查 UPDATE 语句的影响行数）
2. 后端服务已重启
3. 浏览器缓存已清除
4. 前端页面已刷新

### Q2: 新创建的设备还是看不到？

**A**: 请检查：
1. 后端服务是否已重启（代码修改需要重启才能生效）
2. 浏览器控制台是否有错误
3. 网络请求中 `workspace_type` 参数是否正确传递

### Q3: 设备统计数量不对？

**A**: 请确保：
1. 前端代码已更新（`equipment.ts` 中的 `getEquipmentStatistics` 方法）
2. 后端服务已重启
3. 前端页面已刷新

## 技术细节

### WorkspaceContext 结构

```python
@dataclass
class WorkspaceContext:
    user_id: int
    workspace_type: str  # 'personal' 或 'enterprise'
    company_id: Optional[int] = None
    factory_id: Optional[int] = None
```

### 查询过滤逻辑

```python
# 个人工作区
if workspace_context.workspace_type == "personal":
    query = query.filter(
        Equipment.workspace_type == "personal",
        Equipment.user_id == current_user.id
    )

# 企业工作区
elif workspace_context.workspace_type == "enterprise":
    query = query.filter(
        Equipment.workspace_type == "enterprise",
        Equipment.company_id == workspace_context.company_id
    )
```

## 总结

修复完成后，系统将实现严格的工作区数据隔离：

✅ 个人工作区只能看到个人设备
✅ 企业工作区只能看到企业设备
✅ 设备统计正确反映当前工作区的设备数量
✅ 新创建的设备正确归属到对应的工作区

