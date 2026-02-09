"""
Welding Material Service for the welding system backend.
焊材管理服务层
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status

from app.models.material import WeldingMaterial
from app.models.user import User
from app.models.company import Company, CompanyEmployee, CompanyRole
from app.schemas.material import MaterialCreate, MaterialUpdate
from app.core.data_access import DataAccessMiddleware, WorkspaceContext
from app.services.quota_service import QuotaService


class MaterialService:
    """焊材管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.data_access = DataAccessMiddleware(db)
        self.quota_service = QuotaService(db)
    
    # ==================== 焊材基础管理 ====================
    
    def create_material(
        self,
        current_user: User,
        material_data: Dict[str, Any],
        workspace_context: WorkspaceContext
    ) -> WeldingMaterial:
        """
        创建新焊材
        
        Args:
            current_user: 当前用户
            material_data: 焊材数据
            workspace_context: 工作区上下文
            
        Returns:
            WeldingMaterial: 创建的焊材对象
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()
            
            # 企业工作区：检查创建权限
            if workspace_context.workspace_type == "enterprise":
                self._check_create_permission(current_user, workspace_context)
            
            # 检查配额（物理资产模块会自动跳过）
            self.quota_service.check_quota(current_user, workspace_context, "materials", 1)
            
            # 检查焊材编号是否重复
            material_code = material_data.get("material_code")
            if material_code:
                existing = self._check_material_code_exists(
                    material_code, workspace_context
                )
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"焊材编号 {material_code} 已存在"
                    )
            
            # 创建焊材对象
            material = WeldingMaterial(**material_data)
            
            # 设置数据隔离字段
            material.workspace_type = workspace_context.workspace_type
            material.user_id = current_user.id
            material.company_id = workspace_context.company_id
            material.factory_id = workspace_context.factory_id
            material.created_by = current_user.id
            
            # 设置访问级别
            if workspace_context.workspace_type == "enterprise":
                material.access_level = "company"  # 企业工作区默认company
            else:
                material.access_level = "private"  # 个人工作区默认private
            
            # 保存到数据库
            self.db.add(material)
            self.db.commit()
            self.db.refresh(material)
            
            # 更新配额使用（物理资产模块会自动跳过）
            self.quota_service.update_quota_usage(current_user, workspace_context, "materials", 1)
            
            return material
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建焊材失败: {str(e)}"
            )
    
    def get_material_list(
        self,
        current_user: User,
        workspace_context: WorkspaceContext,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        material_type: Optional[str] = None,
        low_stock: Optional[bool] = None
    ) -> tuple[List[WeldingMaterial], int]:
        """
        获取焊材列表
        
        Args:
            current_user: 当前用户
            workspace_context: 工作区上下文
            skip: 跳过记录数
            limit: 返回记录数
            search: 搜索关键词
            material_type: 焊材类型筛选
            low_stock: 低库存筛选
            
        Returns:
            tuple: (焊材列表, 总数)
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()
            
            # 检查查看权限并获取访问范围
            permission_result = self._check_list_permission(current_user, workspace_context)
            
            # 构建基础查询
            query = self.db.query(WeldingMaterial).filter(
                WeldingMaterial.is_active == True
            )
            
            # 应用数据隔离过滤
            query = self.data_access.apply_workspace_filter(
                query,
                WeldingMaterial,
                current_user,
                workspace_context
            )
            
            # 搜索过滤
            if search:
                search_filter = or_(
                    WeldingMaterial.material_code.ilike(f"%{search}%"),
                    WeldingMaterial.material_name.ilike(f"%{search}%"),
                    WeldingMaterial.manufacturer.ilike(f"%{search}%"),
                    WeldingMaterial.brand.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)
            
            # 焊材类型筛选
            if material_type:
                query = query.filter(WeldingMaterial.material_type == material_type)
            
            # 低库存筛选
            if low_stock:
                query = query.filter(
                    WeldingMaterial.current_stock <= WeldingMaterial.min_stock_level
                )
            
            # 获取总数
            total = query.count()
            
            # 分页和排序
            materials = query.order_by(WeldingMaterial.created_at.desc()).offset(skip).limit(limit).all()
            
            return materials, total
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取焊材列表失败: {str(e)}"
            )
    
    def get_material_by_id(
        self,
        material_id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> WeldingMaterial:
        """
        获取焊材详情
        
        Args:
            material_id: 焊材ID
            current_user: 当前用户
            workspace_context: 工作区上下文
            
        Returns:
            WeldingMaterial: 焊材对象
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()
            
            # 查询焊材
            material = self.db.query(WeldingMaterial).filter(
                WeldingMaterial.id == material_id,
                WeldingMaterial.is_active == True
            ).first()
            
            if not material:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="焊材不存在"
                )
            
            # 检查查看权限
            self.data_access.check_access(
                current_user,
                material,
                "VIEW",
                workspace_context
            )
            
            return material
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取焊材详情失败: {str(e)}"
            )
    
    def update_material(
        self,
        material_id: int,
        current_user: User,
        material_data: Dict[str, Any],
        workspace_context: WorkspaceContext
    ) -> WeldingMaterial:
        """
        更新焊材
        
        Args:
            material_id: 焊材ID
            current_user: 当前用户
            material_data: 更新数据
            workspace_context: 工作区上下文
            
        Returns:
            WeldingMaterial: 更新后的焊材对象
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()
            
            # 查询焊材
            material = self.db.query(WeldingMaterial).filter(
                WeldingMaterial.id == material_id,
                WeldingMaterial.is_active == True
            ).first()
            
            if not material:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="焊材不存在"
                )
            
            # 检查编辑权限
            self.data_access.check_access(
                current_user,
                material,
                "EDIT",
                workspace_context
            )
            
            # 更新字段
            for key, value in material_data.items():
                if hasattr(material, key) and value is not None:
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新焊材失败: {str(e)}"
            )
    
    def delete_material(
        self,
        material_id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> bool:
        """
        删除焊材（软删除）
        
        Args:
            material_id: 焊材ID
            current_user: 当前用户
            workspace_context: 工作区上下文
            
        Returns:
            bool: 是否成功
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()
            
            # 查询焊材
            material = self.db.query(WeldingMaterial).filter(
                WeldingMaterial.id == material_id,
                WeldingMaterial.is_active == True
            ).first()
            
            if not material:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="焊材不存在"
                )
            
            # 检查删除权限
            self.data_access.check_access(
                current_user,
                material,
                "DELETE",
                workspace_context
            )
            
            # 软删除
            material.is_active = False
            material.updated_by = current_user.id
            material.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # 更新配额使用（物理资产模块会自动跳过）
            self.quota_service.update_quota_usage(current_user, workspace_context, "materials", -1)
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除焊材失败: {str(e)}"
            )
    
    # ==================== 权限检查辅助方法 ====================
    
    def _check_create_permission(self, current_user: User, workspace_context: WorkspaceContext):
        """检查创建权限"""
        # 获取企业信息
        company = self.db.query(Company).filter(
            Company.id == workspace_context.company_id
        ).first()
        
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="企业不存在"
            )
        
        # 企业所有者：有创建权限
        if company.owner_id == current_user.id:
            return
        
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
        
        # 企业管理员：有创建权限
        if employee.role == "admin":
            return

        # 检查角色权限
        if employee.company_role_id:
            role = self.db.query(CompanyRole).filter(
                CompanyRole.id == employee.company_role_id
            ).first()

            if role and role.permissions:
                permissions = role.permissions
                if permissions.get("materials", {}).get("create", False):
                    return
        
        # 默认权限：允许创建
        return
    
    def _check_list_permission(self, current_user: User, workspace_context: WorkspaceContext) -> Dict:
        """检查查看权限"""
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
        
        # 检查角色权限和数据访问范围
        if employee.company_role_id:
            role = self.db.query(CompanyRole).filter(
                CompanyRole.id == employee.company_role_id
            ).first()

            if role:
                # 检查查看权限
                if role.permissions and role.permissions.get("materials", {}).get("view", False):
                    # 根据数据访问范围返回
                    if role.data_access_scope == "company":
                        return {
                            "can_view": True,
                            "data_access_scope": "company",
                            "factory_id": None
                        }
                    elif role.data_access_scope == "factory":
                        return {
                            "can_view": True,
                            "data_access_scope": "factory",
                            "factory_id": employee.factory_id
                        }
        
        # 默认权限：可以查看，但只能看到自己创建的
        return {
            "can_view": True,
            "data_access_scope": "personal",
            "factory_id": None
        }
    
    def _check_material_code_exists(
        self,
        material_code: str,
        workspace_context: WorkspaceContext
    ) -> bool:
        """检查焊材编号是否存在"""
        query = self.db.query(WeldingMaterial).filter(
            WeldingMaterial.material_code == material_code,
            WeldingMaterial.is_active == True
        )
        
        # 根据工作区类型检查
        if workspace_context.workspace_type == "personal":
            query = query.filter(
                WeldingMaterial.workspace_type == "personal",
                WeldingMaterial.user_id == workspace_context.user_id
            )
        else:
            query = query.filter(
                WeldingMaterial.workspace_type == "enterprise",
                WeldingMaterial.company_id == workspace_context.company_id
            )
        
        return query.first() is not None

    # ==================== 出入库管理 ====================

    def _generate_transaction_number(self, transaction_type: str) -> str:
        """生成交易单号"""
        from datetime import datetime
        prefix_map = {
            "in": "IN",
            "out": "OUT",
            "adjust": "ADJ",
            "return": "RET",
            "transfer": "TRF",
            "consume": "CON"
        }
        prefix = prefix_map.get(transaction_type, "TXN")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        import random
        random_suffix = random.randint(1000, 9999)
        return f"{prefix}{timestamp}{random_suffix}"

    def stock_in(
        self,
        current_user: User,
        material_id: int,
        quantity: float,
        workspace_context: WorkspaceContext,
        **kwargs
    ) -> Dict[str, Any]:
        """
        焊材入库

        Args:
            current_user: 当前用户
            material_id: 焊材ID
            quantity: 入库数量
            workspace_context: 工作区上下文
            **kwargs: 其他参数（unit_price, source, batch_number等）

        Returns:
            Dict: 包含交易记录和更新后的焊材信息
        """
        from app.models.material import MaterialTransaction

        try:
            # 验证工作区上下文
            workspace_context.validate()

            # 查询焊材（应用工作区过滤）
            query = self.db.query(WeldingMaterial).filter(
                WeldingMaterial.id == material_id,
                WeldingMaterial.is_active == True
            )

            # 应用工作区过滤
            query = self.data_access.apply_workspace_filter(
                query, WeldingMaterial, current_user, workspace_context
            )

            material = query.first()

            if not material:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="焊材不存在"
                )

            # 检查权限（需要编辑权限）
            self.data_access.check_access(
                current_user,
                material,
                "edit",  # 使用小写
                workspace_context
            )

            # 记录交易前库存
            stock_before = material.current_stock
            stock_after = stock_before + quantity

            # 创建交易记录
            transaction = MaterialTransaction(
                user_id=current_user.id,
                workspace_type=workspace_context.workspace_type,
                company_id=workspace_context.company_id,
                factory_id=workspace_context.factory_id,
                material_id=material_id,
                transaction_type="in",
                transaction_number=self._generate_transaction_number("in"),
                transaction_date=datetime.utcnow(),
                quantity=quantity,
                unit=material.unit,
                stock_before=stock_before,
                stock_after=stock_after,
                unit_price=kwargs.get("unit_price"),
                total_price=kwargs.get("unit_price") * quantity if kwargs.get("unit_price") else None,
                currency=kwargs.get("currency", "CNY"),
                source=kwargs.get("source"),
                batch_number=kwargs.get("batch_number"),
                production_date=kwargs.get("production_date"),
                expiry_date=kwargs.get("expiry_date"),
                warehouse=kwargs.get("warehouse"),
                storage_location=kwargs.get("storage_location"),
                operator=current_user.username,
                notes=kwargs.get("notes"),
                created_by=current_user.id,
                updated_by=current_user.id
            )

            # 更新焊材库存
            material.current_stock = stock_after
            material.updated_by = current_user.id
            material.updated_at = datetime.utcnow()

            # 更新最后采购信息
            if kwargs.get("unit_price"):
                material.last_purchase_price = kwargs.get("unit_price")
                material.last_purchase_date = datetime.utcnow()

            # 保存到数据库
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(material)
            self.db.refresh(transaction)

            return {
                "transaction": transaction,
                "material": material,
                "message": f"入库成功，当前库存：{stock_after} {material.unit}"
            }

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"入库失败：{str(e)}"
            )

    def stock_out(
        self,
        current_user: User,
        material_id: int,
        quantity: float,
        workspace_context: WorkspaceContext,
        **kwargs
    ) -> Dict[str, Any]:
        """
        焊材出库

        Args:
            current_user: 当前用户
            material_id: 焊材ID
            quantity: 出库数量
            workspace_context: 工作区上下文
            **kwargs: 其他参数（destination, reference_type等）

        Returns:
            Dict: 包含交易记录和更新后的焊材信息
        """
        from app.models.material import MaterialTransaction

        try:
            # 验证工作区上下文
            workspace_context.validate()

            # 查询焊材（应用工作区过滤）
            query = self.db.query(WeldingMaterial).filter(
                WeldingMaterial.id == material_id,
                WeldingMaterial.is_active == True
            )

            # 应用工作区过滤
            query = self.data_access.apply_workspace_filter(
                query, WeldingMaterial, current_user, workspace_context
            )

            material = query.first()

            if not material:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="焊材不存在"
                )

            # 检查权限（需要编辑权限）
            self.data_access.check_access(
                current_user,
                material,
                "edit",  # 使用小写
                workspace_context
            )

            # 检查库存是否充足
            if material.current_stock < quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"库存不足，当前库存：{material.current_stock} {material.unit}，需要：{quantity} {material.unit}"
                )

            # 记录交易前库存
            stock_before = material.current_stock
            stock_after = stock_before - quantity

            # 创建交易记录
            transaction = MaterialTransaction(
                user_id=current_user.id,
                workspace_type=workspace_context.workspace_type,
                company_id=workspace_context.company_id,
                factory_id=workspace_context.factory_id,
                material_id=material_id,
                transaction_type="out",
                transaction_number=self._generate_transaction_number("out"),
                transaction_date=datetime.utcnow(),
                quantity=-quantity,  # 负数表示减少
                unit=material.unit,
                stock_before=stock_before,
                stock_after=stock_after,
                destination=kwargs.get("destination"),
                reference_type=kwargs.get("reference_type"),
                reference_id=kwargs.get("reference_id"),
                reference_number=kwargs.get("reference_number"),
                operator=current_user.username,
                notes=kwargs.get("notes"),
                created_by=current_user.id,
                updated_by=current_user.id
            )

            # 更新焊材库存
            material.current_stock = stock_after
            material.updated_by = current_user.id
            material.updated_at = datetime.utcnow()

            # 更新使用统计
            material.usage_count = (material.usage_count or 0) + 1
            material.total_consumed = (material.total_consumed or 0) + quantity
            material.last_used_date = datetime.utcnow()

            # 保存到数据库
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(material)
            self.db.refresh(transaction)

            return {
                "transaction": transaction,
                "material": material,
                "message": f"出库成功，当前库存：{stock_after} {material.unit}"
            }

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"出库失败：{str(e)}"
            )

    def get_transaction_list(
        self,
        current_user: User,
        workspace_context: WorkspaceContext,
        material_id: Optional[int] = None,
        transaction_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        获取出入库记录列表

        Args:
            current_user: 当前用户
            workspace_context: 工作区上下文
            material_id: 焊材ID（可选，用于筛选特定焊材的记录）
            transaction_type: 交易类型（可选）
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            Dict: 包含记录列表和总数
        """
        from app.models.material import MaterialTransaction

        try:
            # 验证工作区上下文
            workspace_context.validate()

            # 构建基础查询
            query = self.db.query(MaterialTransaction).filter(
                MaterialTransaction.is_active == True
            )

            # 应用工作区过滤
            query = self.data_access.apply_workspace_filter(
                query,
                MaterialTransaction,
                current_user,
                workspace_context
            )

            # 筛选条件
            if material_id:
                query = query.filter(MaterialTransaction.material_id == material_id)

            if transaction_type:
                query = query.filter(MaterialTransaction.transaction_type == transaction_type)

            # 获取总数
            total = query.count()

            # 分页查询
            items = query.order_by(MaterialTransaction.transaction_date.desc()).offset(skip).limit(limit).all()

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取出入库记录失败：{str(e)}"
            )

