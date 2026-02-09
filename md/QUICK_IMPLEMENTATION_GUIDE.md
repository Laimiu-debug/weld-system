# 🚀 快速实施指南：新模块开发

## 📋 概述

本指南提供了基于设备管理模块的标准模式，快速实现新模块（焊材、焊工、生产、质量）的步骤。

---

## 🎯 实施步骤

### 步骤1：创建数据模型（5分钟）

#### 文件位置
`backend/app/models/{module_name}.py`

#### 模板代码

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class Material(Base):  # 修改类名
    """焊材管理"""  # 修改描述
    __tablename__ = "materials"  # 修改表名
    
    # ============ 主键 ============
    id = Column(Integer, primary_key=True, index=True)
    
    # ============ 数据隔离字段（必需，不要修改）============
    workspace_type = Column(String(20), nullable=False, index=True, comment="工作区类型")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="创建者ID")
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True, comment="企业ID")
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=True, index=True, comment="工厂ID")
    access_level = Column(String(20), default="private", nullable=False, comment="访问级别")
    
    # ============ 业务字段（根据需求修改）============
    material_name = Column(String(200), nullable=False, comment="焊材名称")
    material_code = Column(String(100), unique=True, comment="焊材编号")
    material_type = Column(String(50), comment="焊材类型")
    specification = Column(String(200), comment="规格型号")
    manufacturer = Column(String(200), comment="生产厂家")
    
    # ============ 审计字段（必需，不要修改）============
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")
    updated_by = Column(Integer, ForeignKey("users.id"), comment="更新人")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # ============ 关系（可选）============
    creator = relationship("User", foreign_keys=[created_by])
    company = relationship("Company", foreign_keys=[company_id])
    factory = relationship("Factory", foreign_keys=[factory_id])
```

#### 注册模型

在 `backend/app/db/base.py` 中导入：

```python
from app.models.material import Material  # 添加这行
```

---

### 步骤2：创建Pydantic Schema（5分钟）

#### 文件位置
`backend/app/schemas/{module_name}.py`

#### 模板代码

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ============ 创建Schema ============
class MaterialCreate(BaseModel):
    material_name: str = Field(..., description="焊材名称")
    material_code: Optional[str] = Field(None, description="焊材编号")
    material_type: Optional[str] = Field(None, description="焊材类型")
    specification: Optional[str] = Field(None, description="规格型号")
    manufacturer: Optional[str] = Field(None, description="生产厂家")

# ============ 更新Schema ============
class MaterialUpdate(BaseModel):
    material_name: Optional[str] = Field(None, description="焊材名称")
    material_code: Optional[str] = Field(None, description="焊材编号")
    material_type: Optional[str] = Field(None, description="焊材类型")
    specification: Optional[str] = Field(None, description="规格型号")
    manufacturer: Optional[str] = Field(None, description="生产厂家")

# ============ 响应Schema ============
class MaterialResponse(BaseModel):
    id: int
    material_name: str
    material_code: Optional[str]
    material_type: Optional[str]
    specification: Optional[str]
    manufacturer: Optional[str]
    
    workspace_type: str
    user_id: int
    company_id: Optional[int]
    factory_id: Optional[int]
    access_level: str
    
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True
```

---

### 步骤3：创建服务层（15分钟）

#### 文件位置
`backend/app/services/{module_name}_service.py`

#### 模板代码

```python
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict
from datetime import datetime
from fastapi import HTTPException, status

from app.models.material import Material  # 修改导入
from app.models.user import User
from app.models.company import Company, CompanyEmployee, CompanyRole
from app.core.data_access import DataAccessMiddleware
from app.core.workspace import WorkspaceContext
from app.services.quota_service import QuotaService

class MaterialService:  # 修改类名
    def __init__(self, db: Session):
        self.db = db
        self.data_access = DataAccessMiddleware(db)
        self.quota_service = QuotaService(db)
    
    # ============ 创建 ============
    def create_material(
        self,
        current_user: User,
        material_data: Dict,
        workspace_context: WorkspaceContext
    ):
        """创建焊材"""
        try:
            # 1. 企业工作区：检查创建权限
            if workspace_context.workspace_type == "enterprise":
                self._check_create_permission(current_user, workspace_context)

            # 2. 检查配额
            # 注意：物理资产模块（materials）会自动跳过配额检查
            # 但仍然需要调用此方法以保持代码一致性
            self.quota_service.check_quota(
                current_user, workspace_context, "materials", 1
            )

            # 3. 创建焊材
            material = Material(**material_data)
            material.workspace_type = workspace_context.workspace_type
            material.user_id = current_user.id
            material.company_id = workspace_context.company_id
            material.factory_id = workspace_context.factory_id
            material.created_by = current_user.id

            # 4. 设置访问级别
            if workspace_context.workspace_type == "enterprise":
                material.access_level = "company"  # 企业工作区默认company
            else:
                material.access_level = "private"  # 个人工作区默认private

            self.db.add(material)
            self.db.commit()
            self.db.refresh(material)

            # 5. 更新配额使用
            # 注意：物理资产模块（materials）会自动跳过配额更新
            # 但仍然需要调用此方法以保持代码一致性
            self.quota_service.update_quota_usage(
                current_user, workspace_context, "materials", 1
            )

            return material

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise Exception(f"创建焊材失败: {str(e)}")
    
    # ============ 查询列表 ============
    def get_material_list(
        self,
        current_user: User,
        workspace_context: WorkspaceContext,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[Material]:
        """获取焊材列表"""
        try:
            # 检查查看权限并获取访问范围
            access_info = self._check_list_permission(current_user, workspace_context)
            
            query = self.db.query(Material).filter(Material.is_active == True)
            
            # 个人工作区：只查询自己的数据
            if workspace_context.workspace_type == "personal":
                query = query.filter(
                    Material.workspace_type == "personal",
                    Material.user_id == current_user.id
                )
            
            # 企业工作区：根据data_access_scope过滤
            elif workspace_context.workspace_type == "enterprise":
                query = query.filter(
                    Material.workspace_type == "enterprise",
                    Material.company_id == workspace_context.company_id
                )
                
                # 工厂级别访问：只能看到所在工厂的数据
                if access_info["data_access_scope"] == "factory":
                    query = query.filter(
                        Material.factory_id == access_info["factory_id"]
                    )
            
            # 搜索过滤
            if search:
                query = query.filter(
                    or_(
                        Material.material_name.ilike(f"%{search}%"),
                        Material.material_code.ilike(f"%{search}%")
                    )
                )
            
            # 分页
            query = query.offset(skip).limit(limit)
            
            return query.all()
            
        except HTTPException:
            raise
        except Exception as e:
            raise Exception(f"获取焊材列表失败: {str(e)}")
    
    # ============ 查询单个 ============
    def get_material_by_id(
        self,
        material_id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> Optional[Material]:
        """根据ID获取焊材"""
        try:
            query = self.db.query(Material).filter(
                Material.id == material_id,
                Material.is_active == True
            )
            
            # 应用工作区过滤
            query = self.data_access.apply_workspace_filter(
                query, Material, current_user, workspace_context
            )
            
            material = query.first()
            
            if material:
                # 检查访问权限
                self.data_access.check_access(
                    current_user, material, "view", workspace_context
                )
            
            return material
            
        except HTTPException:
            raise
        except Exception as e:
            raise Exception(f"获取焊材失败: {str(e)}")
    
    # ============ 更新 ============
    def update_material(
        self,
        material_id: int,
        current_user: User,
        update_data: Dict,
        workspace_context: WorkspaceContext
    ):
        """更新焊材"""
        try:
            # 获取焊材
            material = self.get_material_by_id(
                material_id, current_user, workspace_context
            )
            
            if not material:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="焊材不存在或无权访问"
                )
            
            # 检查编辑权限
            self.data_access.check_access(
                current_user, material, "edit", workspace_context
            )
            
            # 更新焊材
            for key, value in update_data.items():
                if value is not None:
                    setattr(material, key, value)
            
            material.updated_by = current_user.id
            material.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(material)
            
            return material
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise Exception(f"更新焊材失败: {str(e)}")
    
    # ============ 删除 ============
    def delete_material(
        self,
        material_id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> bool:
        """删除焊材"""
        try:
            # 1. 获取焊材（含数据隔离过滤）
            material = self.get_material_by_id(
                material_id, current_user, workspace_context
            )

            if not material:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="焊材不存在或无权访问"
                )

            # 2. 检查删除权限
            self.data_access.check_access(
                current_user, material, "delete", workspace_context
            )

            # 3. 软删除
            material.is_active = False
            material.updated_by = current_user.id
            material.updated_at = datetime.utcnow()

            self.db.commit()

            # 4. 更新配额使用（减少）
            # 注意：物理资产模块（materials）会自动跳过配额更新
            # 但仍然需要调用此方法以保持代码一致性
            self.quota_service.update_quota_usage(
                current_user, workspace_context, "materials", -1
            )

            return True

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise Exception(f"删除焊材失败: {str(e)}")
    
    # ============ 权限检查辅助方法 ============
    def _check_create_permission(
        self,
        current_user: User,
        workspace_context: WorkspaceContext
    ):
        """检查创建权限"""
        # 获取企业信息
        company = self.db.query(Company).filter(
            Company.id == workspace_context.company_id
        ).first()
        
        # 企业所有者：可以创建
        if company and company.owner_id == current_user.id:
            return True
        
        # 获取员工信息
        employee = self.db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == current_user.id,
            CompanyEmployee.company_id == workspace_context.company_id,
            CompanyEmployee.status == "active"
        ).first()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：您不是该企业的成员"
            )
        
        # 企业管理员：可以创建
        if employee.role == "admin":
            return True
        
        # 检查角色权限
        if employee.company_role_id:
            role = self.db.query(CompanyRole).filter(
                CompanyRole.id == employee.company_role_id,
                CompanyRole.is_active == True
            ).first()
            
            if role:
                permissions = role.permissions or {}
                material_permissions = permissions.get("material_management", {})
                
                if not material_permissions.get("create", False):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="权限不足：您没有创建焊材的权限"
                    )
                return True
        
        # 无角色：默认可以创建
        return True
    
    def _check_list_permission(
        self,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> Dict:
        """检查查看权限并返回访问范围"""
        # 个人工作区：可以查看自己的数据
        if workspace_context.workspace_type == "personal":
            return {
                "can_view": True,
                "data_access_scope": "personal",
                "factory_id": None
            }
        
        # 企业工作区：检查权限
        company = self.db.query(Company).filter(
            Company.id == workspace_context.company_id
        ).first()
        
        # 企业所有者：可以查看所有数据
        if company and company.owner_id == current_user.id:
            return {
                "can_view": True,
                "data_access_scope": "company",
                "factory_id": None
            }
        
        # 获取员工信息
        employee = self.db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == current_user.id,
            CompanyEmployee.company_id == workspace_context.company_id,
            CompanyEmployee.status == "active"
        ).first()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：您不是该企业的成员"
            )
        
        # 企业管理员：可以查看所有数据
        if employee.role == "admin":
            return {
                "can_view": True,
                "data_access_scope": "company",
                "factory_id": None
            }
        
        # 检查角色权限
        if employee.company_role_id:
            role = self.db.query(CompanyRole).filter(
                CompanyRole.id == employee.company_role_id,
                CompanyRole.is_active == True
            ).first()
            
            if role:
                permissions = role.permissions or {}
                material_permissions = permissions.get("material_management", {})
                
                if not material_permissions.get("view", False):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="权限不足：您没有查看焊材的权限"
                    )
                
                # 返回访问范围
                data_access_scope = role.data_access_scope or employee.data_access_scope or "factory"
                return {
                    "can_view": True,
                    "data_access_scope": data_access_scope,
                    "factory_id": employee.factory_id if data_access_scope == "factory" else None
                }
        
        # 无角色：默认可以查看，但只能查看所在工厂的数据
        return {
            "can_view": True,
            "data_access_scope": employee.data_access_scope or "factory",
            "factory_id": employee.factory_id
        }
```

---

### 步骤4：创建API端点（10分钟）

#### 文件位置
`backend/app/api/v1/endpoints/{module_name}.py`

#### 模板代码（见下一个文件）

由于字数限制，API端点代码将在下一个文件中提供。

---

## 📝 修改清单

### 需要修改的地方

1. **类名和表名**：`Material` → 你的模块名
2. **业务字段**：根据实际需求修改
3. **权限键名**：`material_management` → 你的模块权限键
4. **配额类型**：`materials` → 你的模块配额类型
5. **错误提示**：`焊材` → 你的模块名称

### 不要修改的地方

1. **数据隔离字段**：workspace_type, user_id, company_id, factory_id, access_level
2. **审计字段**：created_by, updated_by, created_at, updated_at, is_active
3. **权限检查逻辑**：企业所有者 > 管理员 > 角色权限 > 默认权限
4. **数据过滤逻辑**：个人工作区、企业工作区、工厂级别访问

---

---

## 💎 会员体系集成

### 模块分类

#### 物理资产类模块（焊材、焊工、设备、生产、质量）

**特点**：
- ✅ **不受配额限制**：所有会员等级都可以无限创建
- ✅ **仍需调用配额方法**：保持代码一致性，QuotaService会自动跳过
- ✅ **不需要usage字段**：User和Company表不需要添加usage字段

**代码示例**：
```python
# 创建时
self.quota_service.check_quota(
    current_user, workspace_context, "materials", 1
)  # 会自动跳过检查

# 删除时
self.quota_service.update_quota_usage(
    current_user, workspace_context, "materials", -1
)  # 会自动跳过更新
```

#### 文档类模块（WPS、PQR、pPQR）

**特点**：
- ✅ **受配额限制**：根据会员等级限制创建数量
- ✅ **需要usage字段**：User和Company表需要添加`{module}_usage`字段
- ✅ **需要配置配额**：在PERSONAL_TIERS和ENTERPRISE_TIERS中配置

**代码示例**：
```python
# 创建时
self.quota_service.check_quota(
    current_user, workspace_context, "wps", 1
)  # 会检查配额是否充足

# 创建成功后
self.quota_service.update_quota_usage(
    current_user, workspace_context, "wps", 1
)  # 增加使用量

# 删除时
self.quota_service.update_quota_usage(
    current_user, workspace_context, "wps", -1
)  # 减少使用量
```

### 配额配置位置

**后端配置**：`backend/app/core/config.py`
```python
PERSONAL_TIERS = {
    "free": {"wps_quota": 10, "pqr_quota": 10, "ppqr_quota": 10},
    "pro": {"wps_quota": 200, "pqr_quota": 200, "ppqr_quota": 200},
    # ...
}

ENTERPRISE_TIERS = {
    "enterprise_pro": {"wps_quota": 400, "pqr_quota": 400, "ppqr_quota": 400},
    "enterprise_pro_max": {"wps_quota": 500, "pqr_quota": 500, "ppqr_quota": 500},
    # ...
}
```

**前端配置**：`frontend/src/config/membership.ts`

### 关键点

1. ⚠️ **所有模块都需要调用配额方法**（保持一致性）
2. ⚠️ **QuotaService会自动判断**模块类型并决定是否检查
3. ⚠️ **物理资产模块不需要添加usage字段**
4. ⚠️ **配额类型名称必须与模块名称一致**

---

## ✅ 下一步

继续查看以下文档：
- `API_ENDPOINT_TEMPLATE.md` - API端点的完整代码模板
- `MEMBERSHIP_AND_QUOTA_SYSTEM.md` - 会员体系和配额管理详细文档

