"""
Equipment service for managing equipment, maintenance, and usage records.
设备管理服务层
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.models.user import User
from app.models.equipment import Equipment, EquipmentMaintenance, EquipmentUsage
from app.models.company import Company, CompanyEmployee
from app.core.data_access import DataAccessMiddleware, WorkspaceContext, WorkspaceType, AccessLevel
from app.services.quota_service import QuotaService


class EquipmentService:
    """设备管理服务"""

    def __init__(self, db: Session):
        self.db = db
        self.data_access = DataAccessMiddleware(db)
        self.quota_service = QuotaService(db)

    # ==================== 设备基础管理 ====================

    def create_equipment(
        self,
        current_user: User,
        equipment_data: Dict[str, Any],
        workspace_context: WorkspaceContext
    ) -> Equipment:
        """
        创建新设备

        Args:
            current_user: 当前用户
            equipment_data: 设备数据
            workspace_context: 工作区上下文

        Returns:
            Equipment: 创建的设备对象

        Raises:
            Exception: 创建失败时抛出异常
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()

            # 企业工作区：检查创建权限
            if workspace_context.workspace_type == "enterprise":
                self._check_create_permission(current_user, workspace_context)

            # 检查配额（个人工作区会自动跳过设备配额检查）
            self.quota_service.check_quota(current_user, workspace_context, "equipment", 1)

            # 检查设备编号是否重复 - 根据工作区类型检查
            equipment_code = equipment_data.get("equipment_code")

            if workspace_context.workspace_type == "personal":
                # 个人工作区：检查该用户的个人设备中是否有重复编号
                existing_equipment = self.db.query(Equipment).filter(
                    Equipment.equipment_code == equipment_code,
                    Equipment.workspace_type == "personal",
                    Equipment.user_id == current_user.id
                ).first()
            elif workspace_context.workspace_type == "enterprise":
                # 企业工作区：检查该企业的设备中是否有重复编号
                if workspace_context.company_id:
                    existing_equipment = self.db.query(Equipment).filter(
                        Equipment.equipment_code == equipment_code,
                        Equipment.workspace_type == "enterprise",
                        Equipment.company_id == workspace_context.company_id
                    ).first()
                else:
                    existing_equipment = None
            else:
                existing_equipment = None

            if existing_equipment:
                raise Exception(f"设备编号 {equipment_code} 已存在")

            # 确定访问级别：企业工作区默认为company，个人工作区默认为private
            if workspace_context.workspace_type == "enterprise":
                default_access_level = "company"
            else:
                default_access_level = "private"

            # 创建设备
            equipment = Equipment(
                # 数据隔离字段
                user_id=current_user.id,
                workspace_type=workspace_context.workspace_type,
                company_id=workspace_context.company_id,
                factory_id=workspace_context.factory_id,
                access_level=equipment_data.get("access_level", default_access_level),

                # 基本信息
                equipment_code=equipment_data.get("equipment_code"),
                equipment_name=equipment_data.get("equipment_name"),
                equipment_type=equipment_data.get("equipment_type"),
                category=equipment_data.get("category"),

                # 制造商信息
                manufacturer=equipment_data.get("manufacturer"),
                brand=equipment_data.get("brand"),
                model=equipment_data.get("model"),
                serial_number=equipment_data.get("serial_number"),

                # 技术参数
                specifications=equipment_data.get("specifications"),
                rated_power=equipment_data.get("rated_power"),
                rated_voltage=equipment_data.get("rated_voltage"),
                rated_current=equipment_data.get("rated_current"),
                max_capacity=equipment_data.get("max_capacity"),
                working_range=equipment_data.get("working_range"),

                # 采购信息
                purchase_date=self._parse_date(equipment_data.get("purchase_date")),
                purchase_price=equipment_data.get("purchase_price"),
                currency=equipment_data.get("currency", "CNY"),
                supplier=equipment_data.get("supplier"),
                warranty_period=equipment_data.get("warranty_period"),
                warranty_expiry_date=self._parse_date(equipment_data.get("warranty_expiry_date")),

                # 位置信息
                location=equipment_data.get("location"),
                workshop=equipment_data.get("workshop"),
                area=equipment_data.get("area"),

                # 状态信息
                status=equipment_data.get("status", "operational"),
                is_active=equipment_data.get("is_active", True),
                is_critical=equipment_data.get("is_critical", False),

                # 使用信息
                installation_date=self._parse_date(equipment_data.get("installation_date")),
                commissioning_date=self._parse_date(equipment_data.get("commissioning_date")),

                # 维护信息
                maintenance_interval_days=equipment_data.get("maintenance_interval_days"),
                inspection_interval_days=equipment_data.get("inspection_interval_days"),

                # 责任人信息
                responsible_person_id=equipment_data.get("responsible_person_id"),

                # 附加信息
                description=equipment_data.get("description"),
                notes=equipment_data.get("notes"),
                manual_url=equipment_data.get("manual_url"),
                images=self._to_json(equipment_data.get("images")),
                documents=self._to_json(equipment_data.get("documents")),
                tags=equipment_data.get("tags"),

                # 审计字段
                created_by=current_user.id,
                created_at=datetime.utcnow()
            )

            self.db.add(equipment)
            self.db.commit()
            self.db.refresh(equipment)

            # 更新配额使用
            self.quota_service.update_quota_usage(
                current_user, workspace_context, "equipment", 1
            )

            return equipment

        except Exception as e:
            self.db.rollback()
            raise Exception(f"创建设备失败: {str(e)}")

    def get_equipment_list(
        self,
        current_user: User,
        workspace_context: WorkspaceContext,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        equipment_type: Optional[str] = None,
        status: Optional[str] = None,
        factory_id: Optional[int] = None
    ) -> Tuple[List[Equipment], int]:
        """
        获取设备列表

        Args:
            current_user: 当前用户
            workspace_context: 工作区上下文
            skip: 跳过记录数
            limit: 返回记录数
            search: 搜索关键词
            equipment_type: 设备类型筛选
            status: 状态筛选
            factory_id: 工厂筛选

        Returns:
            Tuple[List[Equipment], int]: 设备列表和总数
        """
        try:
            # 检查查看权限并获取访问范围
            access_info = self._check_list_permission(current_user, workspace_context)

            # 构建基础查询
            query = self.db.query(Equipment)

            # 应用工作区过滤 - 根据工作区类型严格过滤
            if workspace_context.workspace_type == "personal":
                # 个人工作区：只查询个人设备（workspace_type='personal' AND user_id=当前用户）
                query = query.filter(
                    Equipment.workspace_type == "personal",
                    Equipment.user_id == current_user.id
                )
            elif workspace_context.workspace_type == "company" or workspace_context.workspace_type == "enterprise":
                # 企业工作区：只查询企业设备（workspace_type='enterprise' AND company_id=企业ID）
                if workspace_context.company_id:
                    query = query.filter(
                        Equipment.workspace_type == "enterprise",
                        Equipment.company_id == workspace_context.company_id
                    )

                    # 根据data_access_scope过滤
                    if access_info["data_access_scope"] == "factory" and access_info["factory_id"]:
                        # 只能查看所在工厂的设备
                        query = query.filter(Equipment.factory_id == access_info["factory_id"])
                else:
                    # 如果没有company_id，返回空结果
                    query = query.filter(Equipment.id == -1)
            else:
                # 未知工作区类型，返回空结果
                query = query.filter(Equipment.id == -1)

            # 应用工厂过滤（可选，用户手动筛选）
            if factory_id:
                query = query.filter(Equipment.factory_id == factory_id)

            # 应用筛选条件
            if equipment_type:
                query = query.filter(Equipment.equipment_type == equipment_type)

            if status:
                query = query.filter(Equipment.status == status)

            if factory_id:
                query = query.filter(Equipment.factory_id == factory_id)

            # 搜索功能
            if search:
                search_filter = or_(
                    Equipment.equipment_code.ilike(f"%{search}%"),
                    Equipment.equipment_name.ilike(f"%{search}%"),
                    Equipment.manufacturer.ilike(f"%{search}%"),
                    Equipment.model.ilike(f"%{search}%"),
                    Equipment.serial_number.ilike(f"%{search}%"),
                    Equipment.location.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)

            # 只查询激活的设备
            query = query.filter(Equipment.is_active == True)

            # 获取总数
            total = query.count()

            # 分页查询
            equipments = query.order_by(desc(Equipment.created_at)).offset(skip).limit(limit).all()

            return equipments, total

        except Exception as e:
            raise Exception(f"获取设备列表失败: {str(e)}")

    def get_equipment_by_id(
        self,
        equipment_id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> Optional[Equipment]:
        """
        根据ID获取设备详情

        Args:
            equipment_id: 设备ID
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            Optional[Equipment]: 设备对象或None
        """
        try:
            # 构建查询
            query = self.db.query(Equipment).filter(Equipment.id == equipment_id)

            # 应用工作区过滤
            query = self.data_access.apply_workspace_filter(
                query, Equipment, current_user, workspace_context
            )

            equipment = query.first()

            if equipment:
                # 检查访问权限
                self.data_access.check_access(
                    current_user, equipment, "view", workspace_context
                )

            return equipment

        except Exception as e:
            raise Exception(f"获取设备详情失败: {str(e)}")

    def update_equipment(
        self,
        equipment_id: int,
        current_user: User,
        workspace_context: WorkspaceContext,
        update_data: Dict[str, Any]
    ) -> Optional[Equipment]:
        """
        更新设备信息

        Args:
            equipment_id: 设备ID
            current_user: 当前用户
            workspace_context: 工作区上下文
            update_data: 更新数据

        Returns:
            Optional[Equipment]: 更新后的设备对象或None
        """
        try:
            # 获取设备
            equipment = self.get_equipment_by_id(equipment_id, current_user, workspace_context)

            if not equipment:
                raise Exception("设备不存在或无权访问")

            # 检查编辑权限
            self.data_access.check_access(
                current_user, equipment, "edit", workspace_context
            )

            # 更新字段
            updatable_fields = [
                "equipment_name", "equipment_type", "category", "manufacturer", "brand",
                "model", "specifications", "rated_power", "rated_voltage", "rated_current",
                "max_capacity", "working_range", "purchase_price", "supplier", "location",
                "workshop", "area", "status", "is_active", "is_critical", "description",
                "notes", "manual_url", "images", "documents", "tags", "access_level"
            ]

            for field in updatable_fields:
                if field in update_data:
                    if field in ["purchase_date", "warranty_expiry_date", "installation_date",
                               "commissioning_date", "last_maintenance_date", "next_maintenance_date"]:
                        setattr(equipment, field, self._parse_date(update_data[field]))
                    elif field in ["images", "documents", "specifications"]:
                        setattr(equipment, field, self._to_json(update_data[field]))
                    else:
                        setattr(equipment, field, update_data[field])

            equipment.updated_by = current_user.id
            equipment.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(equipment)

            return equipment

        except Exception as e:
            self.db.rollback()
            raise Exception(f"更新设备失败: {str(e)}")

    def delete_equipment(
        self,
        equipment_id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> bool:
        """
        删除设备

        Args:
            equipment_id: 设备ID
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            bool: 是否删除成功
        """
        try:
            # 获取设备
            equipment = self.get_equipment_by_id(equipment_id, current_user, workspace_context)

            if not equipment:
                raise Exception("设备不存在或无权访问")

            # 检查删除权限
            self.data_access.check_access(
                current_user, equipment, "delete", workspace_context
            )

            # 软删除：标记为非激活状态
            equipment.is_active = False
            equipment.updated_by = current_user.id
            equipment.updated_at = datetime.utcnow()

            self.db.commit()

            # 更新配额使用
            self.quota_service.update_quota_usage(
                current_user, workspace_context, "equipment", -1
            )

            return True

        except Exception as e:
            self.db.rollback()
            raise Exception(f"删除设备失败: {str(e)}")

    # ==================== 设备状态管理 ====================

    def update_equipment_status(
        self,
        equipment_id: int,
        current_user: User,
        workspace_context: WorkspaceContext,
        new_status: str,
        notes: Optional[str] = None
    ) -> Optional[Equipment]:
        """
        更新设备状态

        Args:
            equipment_id: 设备ID
            current_user: 当前用户
            workspace_context: 工作区上下文
            new_status: 新状态
            notes: 状态变更备注

        Returns:
            Optional[Equipment]: 更新后的设备对象或None
        """
        try:
            # 获取设备
            equipment = self.get_equipment_by_id(equipment_id, current_user, workspace_context)

            if not equipment:
                raise Exception("设备不存在或无权访问")

            # 检查编辑权限
            self.data_access.check_access(
                current_user, equipment, "edit", workspace_context
            )

            # 记录状态变更
            old_status = equipment.status
            equipment.status = new_status
            equipment.updated_by = current_user.id
            equipment.updated_at = datetime.utcnow()

            # 如果有备注，添加到设备备注中
            if notes:
                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                status_note = f"[{timestamp}] 状态变更: {old_status} → {new_status}\n{notes}"
                if equipment.notes:
                    equipment.notes = f"{equipment.notes}\n\n{status_note}"
                else:
                    equipment.notes = status_note

            self.db.commit()
            self.db.refresh(equipment)

            return equipment

        except Exception as e:
            self.db.rollback()
            raise Exception(f"更新设备状态失败: {str(e)}")

    # ==================== 设备统计 ====================

    def get_equipment_statistics(
        self,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> Dict[str, Any]:
        """
        获取设备统计信息

        Args:
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            # 构建基础查询 - 应用工作区过滤
            query = self.db.query(Equipment).filter(Equipment.is_active == True)

            # 应用工作区过滤
            if workspace_context.workspace_type == "personal":
                query = query.filter(
                    Equipment.workspace_type == "personal",
                    Equipment.user_id == current_user.id
                )
            elif workspace_context.workspace_type == "company" or workspace_context.workspace_type == "enterprise":
                if workspace_context.company_id:
                    query = query.filter(
                        Equipment.workspace_type == "enterprise",
                        Equipment.company_id == workspace_context.company_id
                    )
                else:
                    query = query.filter(Equipment.id == -1)
            else:
                query = query.filter(Equipment.id == -1)

            # 总数统计
            total_equipment = query.count()

            # 状态统计 - 应用相同的工作区过滤
            status_query = self.db.query(
                Equipment.status,
                func.count(Equipment.id).label('count')
            ).filter(Equipment.is_active == True)

            if workspace_context.workspace_type == "personal":
                status_query = status_query.filter(
                    Equipment.workspace_type == "personal",
                    Equipment.user_id == current_user.id
                )
            elif workspace_context.workspace_type == "company" or workspace_context.workspace_type == "enterprise":
                if workspace_context.company_id:
                    status_query = status_query.filter(
                        Equipment.workspace_type == "enterprise",
                        Equipment.company_id == workspace_context.company_id
                    )

            status_stats = status_query.group_by(Equipment.status).all()
            status_counts = {stat.status: stat.count for stat in status_stats}

            # 类型统计 - 应用相同的工作区过滤
            type_query = self.db.query(
                Equipment.equipment_type,
                func.count(Equipment.id).label('count')
            ).filter(Equipment.is_active == True)

            if workspace_context.workspace_type == "personal":
                type_query = type_query.filter(
                    Equipment.workspace_type == "personal",
                    Equipment.user_id == current_user.id
                )
            elif workspace_context.workspace_type == "company" or workspace_context.workspace_type == "enterprise":
                if workspace_context.company_id:
                    type_query = type_query.filter(
                        Equipment.workspace_type == "enterprise",
                        Equipment.company_id == workspace_context.company_id
                    )

            type_stats = type_query.group_by(Equipment.equipment_type).all()
            type_counts = {stat.equipment_type: stat.count for stat in type_stats}

            # 维护提醒统计
            upcoming_maintenance = query.filter(
                Equipment.next_maintenance_date <= date.today() + timedelta(days=30)
            ).count()

            # 过期检验统计
            overdue_inspection = query.filter(
                Equipment.next_inspection_date < date.today()
            ).count()

            return {
                "total_equipment": total_equipment,
                "status_counts": status_counts,
                "type_counts": type_counts,
                "operational": status_counts.get("operational", 0),
                "idle": status_counts.get("idle", 0),
                "maintenance": status_counts.get("maintenance", 0),
                "repair": status_counts.get("repair", 0),
                "broken": status_counts.get("broken", 0),
                "upcoming_maintenance": upcoming_maintenance,
                "overdue_inspection": overdue_inspection
            }

        except Exception as e:
            raise Exception(f"获取设备统计失败: {str(e)}")

    # ==================== 工具方法 ====================

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """解析日期字符串"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    def _to_json(self, data: Any) -> Optional[str]:
        """转换为JSON字符串"""
        if not data:
            return None
        if isinstance(data, str):
            return data
        import json
        return json.dumps(data, ensure_ascii=False)

    def _get_equipment_types(self) -> List[str]:
        """获取所有设备类型"""
        return [
            "welding_machine",
            "cutting_machine",
            "grinding_machine",
            "testing_equipment",
            "auxiliary_equipment",
            "other"
        ]

    def _get_equipment_statuses(self) -> List[str]:
        """获取所有设备状态"""
        return [
            "operational",
            "idle",
            "maintenance",
            "repair",
            "broken",
            "retired"
        ]

    def _check_create_permission(self, current_user: User, workspace_context: WorkspaceContext):
        """
        检查创建设备的权限

        Args:
            current_user: 当前用户
            workspace_context: 工作区上下文

        Raises:
            HTTPException: 如果没有权限
        """
        from fastapi import HTTPException, status
        from app.models.company import Company, CompanyEmployee, CompanyRole

        # 检查用户是否是企业所有者
        company = self.db.query(Company).filter(
            Company.id == workspace_context.company_id
        ).first()

        if company and company.owner_id == current_user.id:
            # 企业所有者拥有所有权限
            return

        # 检查用户是否是企业员工
        employee = self.db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == current_user.id,
            CompanyEmployee.company_id == workspace_context.company_id,
            CompanyEmployee.status == "active"
        ).first()

        if not employee:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您不是该企业的成员"
            )

        # 企业管理员拥有所有权限
        if employee.role == "admin":
            return

        # 检查角色权限
        if employee.company_role_id:
            role = self.db.query(CompanyRole).filter(
                CompanyRole.id == employee.company_role_id,
                CompanyRole.is_active == True
            ).first()

            if role:
                permissions = role.permissions or {}
                equipment_permissions = permissions.get("equipment_management", {})

                if not equipment_permissions.get("create", False):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="权限不足：您没有创建设备的权限"
                    )
                return

        # 无角色的员工默认可以创建
        return

    def _check_list_permission(self, current_user: User, workspace_context: WorkspaceContext) -> Dict[str, Any]:
        """
        检查查看设备列表的权限，并返回访问范围

        Args:
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            Dict: 包含访问范围信息
                - can_view: 是否可以查看
                - data_access_scope: 数据访问范围 ("company" 或 "factory")
                - factory_id: 如果是factory范围，返回工厂ID

        Raises:
            HTTPException: 如果没有权限
        """
        from fastapi import HTTPException, status
        from app.models.company import Company, CompanyEmployee, CompanyRole

        # 个人工作区：可以查看自己的设备
        if workspace_context.workspace_type == "personal":
            return {
                "can_view": True,
                "data_access_scope": "personal",
                "factory_id": None
            }

        # 企业工作区：检查权限
        # 检查用户是否是企业所有者
        company = self.db.query(Company).filter(
            Company.id == workspace_context.company_id
        ).first()

        if company and company.owner_id == current_user.id:
            # 企业所有者可以查看整个企业的数据
            return {
                "can_view": True,
                "data_access_scope": "company",
                "factory_id": None
            }

        # 检查用户是否是企业员工
        employee = self.db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == current_user.id,
            CompanyEmployee.company_id == workspace_context.company_id,
            CompanyEmployee.status == "active"
        ).first()

        if not employee:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您不是该企业的成员"
            )

        # 企业管理员可以查看整个企业的数据
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
                equipment_permissions = permissions.get("equipment_management", {})

                if not equipment_permissions.get("view", False):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="权限不足：您没有查看设备的权限"
                    )

                # 根据角色的data_access_scope决定访问范围
                data_access_scope = role.data_access_scope or employee.data_access_scope or "factory"

                return {
                    "can_view": True,
                    "data_access_scope": data_access_scope,
                    "factory_id": employee.factory_id if data_access_scope == "factory" else None
                }

        # 无角色的员工默认可以查看，但只能查看所在工厂的数据
        return {
            "can_view": True,
            "data_access_scope": employee.data_access_scope or "factory",
            "factory_id": employee.factory_id if (employee.data_access_scope or "factory") == "factory" else None
        }