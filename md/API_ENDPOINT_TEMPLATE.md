# 🔌 API端点模板

## 📋 概述

本文档提供了API端点的完整代码模板，基于设备管理模块的标准模式。

---

## 📝 API端点代码

### 文件位置
`backend/app/api/v1/endpoints/{module_name}.py`

### 完整代码

```python
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional

from app import deps
from app.models.user import User
from app.schemas.material import MaterialCreate, MaterialUpdate, MaterialResponse
from app.services.material_service import MaterialService
from app.core.workspace import WorkspaceContext
from app.services.company_service import get_user_company_info

router = APIRouter()

# ============ 辅助函数：构建工作区上下文 ============
def build_workspace_context(
    workspace_type: Optional[str],
    current_user: User,
    db: Session
) -> WorkspaceContext:
    """构建工作区上下文"""
    if workspace_type == "company" or workspace_type == "enterprise":
        # 获取用户的企业信息
        company_info = get_user_company_info(db, current_user.id)
        
        if not company_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="您还没有加入任何企业"
            )
        
        return WorkspaceContext(
            user_id=current_user.id,
            workspace_type="enterprise",
            company_id=company_info["company_id"],
            factory_id=company_info.get("factory_id")
        )
    else:
        # 个人工作区
        return WorkspaceContext(
            user_id=current_user.id,
            workspace_type="personal",
            company_id=None,
            factory_id=None
        )

# ============ 创建焊材 ============
@router.post("/", response_model=dict)
async def create_material(
    material: MaterialCreate,
    workspace_type: Optional[str] = Query(None, description="工作区类型: personal/company"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    创建焊材
    
    - **workspace_type**: 工作区类型 (personal/company)
    - **material**: 焊材信息
    """
    try:
        # 构建工作区上下文
        workspace_context = build_workspace_context(workspace_type, current_user, db)
        
        # 创建焊材
        material_service = MaterialService(db)
        new_material = material_service.create_material(
            current_user=current_user,
            material_data=material.dict(exclude_unset=True),
            workspace_context=workspace_context
        )
        
        return {
            "success": True,
            "message": "焊材创建成功",
            "data": MaterialResponse.from_orm(new_material)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建焊材失败: {str(e)}"
        )

# ============ 获取焊材列表 ============
@router.get("/", response_model=dict)
async def get_material_list(
    workspace_type: Optional[str] = Query(None, description="工作区类型: personal/company"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取焊材列表
    
    - **workspace_type**: 工作区类型 (personal/company)
    - **skip**: 跳过记录数
    - **limit**: 返回记录数
    - **search**: 搜索关键词
    """
    try:
        # 构建工作区上下文
        workspace_context = build_workspace_context(workspace_type, current_user, db)
        
        # 获取焊材列表
        material_service = MaterialService(db)
        materials = material_service.get_material_list(
            current_user=current_user,
            workspace_context=workspace_context,
            skip=skip,
            limit=limit,
            search=search
        )
        
        return {
            "success": True,
            "data": [MaterialResponse.from_orm(m) for m in materials],
            "total": len(materials)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取焊材列表失败: {str(e)}"
        )

# ============ 获取焊材详情 ============
@router.get("/{material_id}", response_model=dict)
async def get_material(
    material_id: int,
    workspace_type: Optional[str] = Query(None, description="工作区类型: personal/company"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取焊材详情
    
    - **material_id**: 焊材ID
    - **workspace_type**: 工作区类型 (personal/company)
    """
    try:
        # 构建工作区上下文
        workspace_context = build_workspace_context(workspace_type, current_user, db)
        
        # 获取焊材
        material_service = MaterialService(db)
        material = material_service.get_material_by_id(
            material_id=material_id,
            current_user=current_user,
            workspace_context=workspace_context
        )
        
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="焊材不存在或无权访问"
            )
        
        return {
            "success": True,
            "data": MaterialResponse.from_orm(material)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取焊材失败: {str(e)}"
        )

# ============ 更新焊材 ============
@router.put("/{material_id}", response_model=dict)
async def update_material(
    material_id: int,
    material: MaterialUpdate,
    workspace_type: Optional[str] = Query(None, description="工作区类型: personal/company"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    更新焊材
    
    - **material_id**: 焊材ID
    - **workspace_type**: 工作区类型 (personal/company)
    - **material**: 更新的焊材信息
    """
    try:
        # 构建工作区上下文
        workspace_context = build_workspace_context(workspace_type, current_user, db)
        
        # 更新焊材
        material_service = MaterialService(db)
        updated_material = material_service.update_material(
            material_id=material_id,
            current_user=current_user,
            update_data=material.dict(exclude_unset=True),
            workspace_context=workspace_context
        )
        
        return {
            "success": True,
            "message": "焊材更新成功",
            "data": MaterialResponse.from_orm(updated_material)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新焊材失败: {str(e)}"
        )

# ============ 删除焊材 ============
@router.delete("/{material_id}", response_model=dict)
async def delete_material(
    material_id: int,
    workspace_type: Optional[str] = Query(None, description="工作区类型: personal/company"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    删除焊材
    
    - **material_id**: 焊材ID
    - **workspace_type**: 工作区类型 (personal/company)
    """
    try:
        # 构建工作区上下文
        workspace_context = build_workspace_context(workspace_type, current_user, db)
        
        # 删除焊材
        material_service = MaterialService(db)
        success = material_service.delete_material(
            material_id=material_id,
            current_user=current_user,
            workspace_context=workspace_context
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="焊材不存在或无权访问"
            )
        
        return {
            "success": True,
            "message": "焊材删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除焊材失败: {str(e)}"
        )

# ============ 批量删除焊材 ============
@router.post("/batch-delete", response_model=dict)
async def batch_delete_materials(
    material_ids: List[int],
    workspace_type: Optional[str] = Query(None, description="工作区类型: personal/company"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    批量删除焊材
    
    - **material_ids**: 焊材ID列表
    - **workspace_type**: 工作区类型 (personal/company)
    """
    try:
        # 构建工作区上下文
        workspace_context = build_workspace_context(workspace_type, current_user, db)
        
        # 批量删除
        material_service = MaterialService(db)
        success_count = 0
        failed_count = 0
        
        for material_id in material_ids:
            try:
                material_service.delete_material(
                    material_id=material_id,
                    current_user=current_user,
                    workspace_context=workspace_context
                )
                success_count += 1
            except:
                failed_count += 1
        
        return {
            "success": True,
            "message": f"成功删除 {success_count} 个焊材，失败 {failed_count} 个",
            "data": {
                "success_count": success_count,
                "failed_count": failed_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量删除焊材失败: {str(e)}"
        )
```

---

## 📝 注册路由

### 文件位置
`backend/app/api/v1/api.py`

### 添加路由

```python
from app.api.v1.endpoints import material  # 添加导入

api_router.APIRouter()

# ... 其他路由 ...

api_router.include_router(
    material.router,
    prefix="/materials",
    tags=["materials"]
)
```

---

## 🔑 关键点说明

### 1. 工作区上下文构建

```python
def build_workspace_context(workspace_type, current_user, db):
    """
    统一的工作区上下文构建逻辑
    - 企业工作区：获取用户的企业信息
    - 个人工作区：只需要用户ID
    """
```

### 2. 错误处理

```python
try:
    # 业务逻辑
except HTTPException:
    raise  # 直接抛出HTTP异常
except Exception as e:
    # 捕获其他异常，包装成HTTP 500错误
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"操作失败: {str(e)}"
    )
```

### 3. 响应格式

```python
# 成功响应
{
    "success": True,
    "message": "操作成功",
    "data": {...}
}

# 列表响应
{
    "success": True,
    "data": [...],
    "total": 100
}
```

---

## ✅ 实施检查清单

- [ ] 修改所有类名和变量名（Material → 你的模块名）
- [ ] 修改所有描述文本（焊材 → 你的模块名称）
- [ ] 修改Schema导入（MaterialCreate, MaterialUpdate, MaterialResponse）
- [ ] 修改Service导入（MaterialService）
- [ ] 修改路由前缀和标签（/materials, materials）
- [ ] 在api.py中注册路由
- [ ] 测试所有端点（创建、查询、更新、删除）

---

## 🧪 测试建议

### 1. 个人工作区测试

```bash
# 创建
POST /api/v1/materials?workspace_type=personal

# 查询列表
GET /api/v1/materials?workspace_type=personal

# 查询详情
GET /api/v1/materials/1?workspace_type=personal

# 更新
PUT /api/v1/materials/1?workspace_type=personal

# 删除
DELETE /api/v1/materials/1?workspace_type=personal
```

### 2. 企业工作区测试

```bash
# 创建（需要CREATE权限）
POST /api/v1/materials?workspace_type=company

# 查询列表（需要VIEW权限）
GET /api/v1/materials?workspace_type=company

# 更新（需要EDIT权限）
PUT /api/v1/materials/1?workspace_type=company

# 删除（需要DELETE权限）
DELETE /api/v1/materials/1?workspace_type=company
```

### 3. 权限测试

- [ ] 企业所有者：所有操作都应该成功
- [ ] 企业管理员：所有操作都应该成功
- [ ] 有完整权限的员工：所有操作都应该成功
- [ ] 只有VIEW权限的员工：只能查询，不能创建/编辑/删除
- [ ] 无权限的员工：所有操作都应该失败（403错误）
- [ ] 非企业成员：所有操作都应该失败（403错误）

---

## 📚 下一步

1. 创建数据库迁移脚本
2. 实现前端页面
3. 编写单元测试
4. 更新API文档

查看 `FRONTEND_TEMPLATE.md` 获取前端实现模板。

