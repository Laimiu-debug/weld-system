# 生产管理模块 - 开发指南

## 📋 模块概述

### 功能定位
生产管理模块用于管理焊接生产任务的计划、执行、进度跟踪和资源分配，确保生产任务按时完成。

### 适用场景
- 生产任务创建和分配
- 生产进度跟踪
- 资源调度管理
- 生产数据记录
- 生产统计分析

### 开发优先级
**第二阶段** - 重要功能，优先开发

---

## 🎯 会员权限

### 访问权限
| 会员等级 | 访问权限 | 数量限制 | 功能范围 |
|---------|---------|---------|---------|
| 游客模式 | ❌ 不可访问 | 0 | - |
| 个人免费版 | ❌ 不可访问 | 0 | - |
| 个人专业版 | ❌ 不可访问 | 0 | - |
| 个人高级版 | ✅ 可访问 | 无限制 | 完整功能 |
| 个人旗舰版 | ✅ 可访问 | 无限制 | 完整功能 + 高级特性 |
| 企业版 | ✅ 可访问 | 无限制 | 完整功能 + 企业协作 |
| 企业PRO | ✅ 可访问 | 无限制 | 完整功能 + 企业协作 |
| 企业PRO MAX | ✅ 可访问 | 无限制 | 完整功能 + 企业协作 |

**重要说明**: 生产管理功能仅对**个人高级版及以上**会员开放。

---

## 📊 功能清单

### 1. 生产任务管理
- **创建任务**: 创建生产任务
- **编辑任务**: 修改任务信息
- **删除任务**: 软删除任务
- **任务详情**: 查看任务详细信息
- **任务分配**: 分配任务给焊工
- **任务状态**: 管理任务状态流转

### 2. 进度跟踪
- **进度更新**: 更新任务进度
- **进度查看**: 查看任务进度
- **里程碑管理**: 设置和跟踪里程碑
- **延期预警**: 任务延期预警
- **完成率统计**: 统计任务完成率

### 3. 资源管理
- **焊工分配**: 分配焊工到任务
- **设备分配**: 分配设备到任务
- **焊材分配**: 分配焊材到任务
- **WPS 关联**: 关联使用的 WPS
- **资源冲突检测**: 检测资源冲突

### 4. 生产数据记录
- **工时记录**: 记录实际工时
- **焊材消耗**: 记录焊材消耗量
- **设备使用**: 记录设备使用情况
- **质量记录**: 记录质量检验结果
- **问题记录**: 记录生产问题

### 5. 统计分析
- **任务统计**: 按状态、时间统计
- **效率分析**: 分析生产效率
- **成本核算**: 计算生产成本
- **资源利用率**: 分析资源利用率

---

## 🗄️ 数据模型

### 生产任务表
```sql
CREATE TABLE production_tasks (
    -- 主键和基础字段
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    factory_id UUID REFERENCES factories(id) ON DELETE SET NULL,
    
    -- 任务基本信息
    task_number VARCHAR(100) NOT NULL,             -- 任务编号
    task_name VARCHAR(255) NOT NULL,               -- 任务名称
    task_type VARCHAR(50),                         -- 任务类型
    priority VARCHAR(20) DEFAULT 'normal',         -- 优先级: low, normal, high, urgent
    status VARCHAR(50) DEFAULT 'pending',          -- 状态: pending, in_progress, completed, cancelled
    
    -- 时间信息
    planned_start_date DATE,                       -- 计划开始日期
    planned_end_date DATE,                         -- 计划结束日期
    actual_start_date DATE,                        -- 实际开始日期
    actual_end_date DATE,                          -- 实际结束日期
    
    -- 工作量
    planned_hours DECIMAL(10,2),                  -- 计划工时
    actual_hours DECIMAL(10,2) DEFAULT 0,         -- 实际工时
    progress_percentage DECIMAL(5,2) DEFAULT 0,   -- 完成百分比
    
    -- 关联信息
    wps_id UUID REFERENCES wps_records(id),        -- 使用的 WPS
    pqr_id UUID REFERENCES pqr_records(id),        -- 关联的 PQR
    
    -- 资源分配
    assigned_welders JSONB,                        -- 分配的焊工列表
    assigned_equipment JSONB,                      -- 分配的设备列表
    assigned_materials JSONB,                      -- 分配的焊材列表
    
    -- 技术要求
    technical_requirements TEXT,                   -- 技术要求
    quality_requirements TEXT,                     -- 质量要求
    safety_requirements TEXT,                      -- 安全要求
    
    -- 成本信息
    estimated_cost DECIMAL(15,2),                 -- 预估成本
    actual_cost DECIMAL(15,2) DEFAULT 0,          -- 实际成本
    
    -- 责任人
    project_manager_id UUID REFERENCES users(id),  -- 项目经理
    supervisor_id UUID REFERENCES users(id),       -- 监督人
    
    -- 附件
    drawings JSONB,                                -- 图纸
    documents JSONB,                               -- 文档
    photos JSONB,                                  -- 照片
    
    -- 备注
    notes TEXT,
    tags JSONB,
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP,
    
    -- 索引
    INDEX idx_user (user_id),
    INDEX idx_company (company_id),
    INDEX idx_factory (factory_id),
    INDEX idx_task_number (task_number),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_planned_dates (planned_start_date, planned_end_date),
    INDEX idx_wps (wps_id),
    INDEX idx_deleted (deleted_at),
    
    UNIQUE (user_id, task_number)
);
```

### 生产记录表
```sql
CREATE TABLE production_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES production_tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 记录信息
    record_date DATE NOT NULL,                     -- 记录日期
    shift VARCHAR(20),                             -- 班次
    
    -- 工作信息
    welder_id UUID REFERENCES welders(id),         -- 焊工
    work_hours DECIMAL(8,2),                      -- 工作时长
    work_description TEXT,                         -- 工作内容
    
    -- 焊材消耗
    material_consumption JSONB,                    -- 焊材消耗记录
    
    -- 设备使用
    equipment_id UUID REFERENCES equipment(id),    -- 使用的设备
    equipment_hours DECIMAL(8,2),                 -- 设备使用时长
    
    -- 质量信息
    quality_status VARCHAR(50),                    -- 质量状态: pass, fail, rework
    defects_found TEXT,                            -- 发现的缺陷
    
    -- 问题记录
    issues_encountered TEXT,                       -- 遇到的问题
    solutions_applied TEXT,                        -- 解决方案
    
    -- 备注
    notes TEXT,
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    
    -- 索引
    INDEX idx_task (task_id),
    INDEX idx_user (user_id),
    INDEX idx_record_date (record_date),
    INDEX idx_welder (welder_id),
    INDEX idx_equipment (equipment_id)
);
```

---

## 🔌 API接口

### 1. 任务列表
```http
GET /api/v1/production/tasks?page=1&page_size=20&status=in_progress
Authorization: Bearer <token>
```

### 2. 创建任务
```http
POST /api/v1/production/tasks
Authorization: Bearer <token>
Content-Type: application/json

{
  "task_number": "PT-2025-001",
  "task_name": "管道焊接任务",
  "priority": "high",
  "planned_start_date": "2025-10-20",
  "planned_end_date": "2025-10-30",
  "planned_hours": 80,
  "wps_id": "uuid",
  "assigned_welders": ["uuid1", "uuid2"]
}
```

### 3. 更新进度
```http
PUT /api/v1/production/tasks/{id}/progress
Authorization: Bearer <token>
Content-Type: application/json

{
  "progress_percentage": 50,
  "actual_hours": 40,
  "notes": "进度正常"
}
```

### 4. 添加生产记录
```http
POST /api/v1/production/tasks/{id}/records
Authorization: Bearer <token>
Content-Type: application/json

{
  "record_date": "2025-10-16",
  "welder_id": "uuid",
  "work_hours": 8,
  "work_description": "完成第一段焊接",
  "quality_status": "pass"
}
```

### 5. 任务统计
```http
GET /api/v1/production/statistics
Authorization: Bearer <token>
```

---

## 💼 业务逻辑

### 1. 任务进度更新
```python
class ProductionService:
    def update_task_progress(
        self,
        task_id: UUID,
        progress_data: TaskProgress,
        user_id: UUID,
        db: Session
    ) -> ProductionTask:
        """更新任务进度"""
        
        task = db.query(ProductionTask).filter(
            ProductionTask.id == task_id,
            ProductionTask.user_id == user_id
        ).first()
        
        if not task:
            raise HTTPException(404, "任务不存在")
        
        # 更新进度
        task.progress_percentage = progress_data.progress_percentage
        task.actual_hours = progress_data.actual_hours
        
        # 如果进度达到100%，自动完成任务
        if progress_data.progress_percentage >= 100:
            task.status = "completed"
            task.actual_end_date = date.today()
        
        task.updated_at = datetime.now()
        db.commit()
        
        return task
```

### 2. 延期检查
```python
def get_overdue_tasks(
    self,
    user_id: UUID,
    db: Session
) -> List[ProductionTask]:
    """获取延期任务"""
    
    tasks = db.query(ProductionTask).filter(
        ProductionTask.user_id == user_id,
        ProductionTask.status.in_(["pending", "in_progress"]),
        ProductionTask.planned_end_date < date.today(),
        ProductionTask.deleted_at.is_(None)
    ).all()
    
    return tasks
```

---

## 🔐 权限控制

```python
@router.get("/production/tasks")
@require_feature("production_management")  # 需要高级版及以上
async def get_task_list(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取生产任务列表"""
    service = ProductionService(db)
    return service.get_task_list(current_user.id, db)
```

---

## 🎨 前端界面

### 任务看板
```typescript
// src/pages/Production/TaskBoard.tsx

const TaskBoard: React.FC = () => {
  const { tasks, loading } = useProductionTasks();
  
  const columns = {
    pending: tasks.filter(t => t.status === 'pending'),
    in_progress: tasks.filter(t => t.status === 'in_progress'),
    completed: tasks.filter(t => t.status === 'completed')
  };
  
  return (
    <div className="task-board">
      <Column title="待开始" tasks={columns.pending} />
      <Column title="进行中" tasks={columns.in_progress} />
      <Column title="已完成" tasks={columns.completed} />
    </div>
  );
};
```

---

**文档版本**: 1.0  
**最后更新**: 2025-10-16  
**开发状态**: 已实现（需测试）

