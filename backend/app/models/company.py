"""
Company, Factory, and CompanyEmployee models for enterprise management.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Date, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Company(Base):
    """Company model for enterprise management."""
    
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 会员信息
    membership_tier = Column(String(50), nullable=False, default="enterprise")  # enterprise, enterprise_pro, enterprise_pro_max
    
    # 配额限制
    max_factories = Column(Integer, default=1)
    max_employees = Column(Integer, default=10)
    max_wps_records = Column(Integer, default=200)
    max_pqr_records = Column(Integer, default=200)
    max_ppqr_records = Column(Integer, default=200)
    
    # 企业信息
    business_license = Column(String(255))
    contact_person = Column(String(100))
    contact_phone = Column(String(20))
    contact_email = Column(String(255))
    address = Column(Text)
    website = Column(String(255))
    industry = Column(String(100))
    company_size = Column(String(50))
    description = Column(Text)
    logo_url = Column(String(500))
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # 订阅信息
    subscription_status = Column(String(50), default="active")
    subscription_start_date = Column(DateTime)
    subscription_end_date = Column(DateTime)
    trial_end_date = Column(DateTime)
    auto_renewal = Column(Boolean, default=False)
    
    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], backref="owned_companies")
    factories = relationship("Factory", back_populates="company", cascade="all, delete-orphan")
    employees = relationship("CompanyEmployee", back_populates="company", cascade="all, delete-orphan")


class Factory(Base):
    """Factory model for enterprise management."""
    
    __tablename__ = "factories"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    
    # 工厂信息
    name = Column(String(255), nullable=False)
    code = Column(String(100), unique=True)
    description = Column(Text)
    
    # 地址信息
    address = Column(Text)
    city = Column(String(100))
    province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(50), default="China")
    
    # 联系信息
    contact_person = Column(String(100))
    contact_phone = Column(String(20))
    contact_email = Column(String(255))
    
    # 其他信息
    timezone = Column(String(50), default="Asia/Shanghai")
    established_date = Column(Date)
    certification_info = Column(JSONB)
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_headquarters = Column(Boolean, default=False)
    
    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    company = relationship("Company", back_populates="factories")
    employees = relationship("CompanyEmployee", back_populates="factory")


class CompanyRole(Base):
    """Company role model for enterprise-level role management."""

    __tablename__ = "company_roles"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    # 角色信息
    name = Column(String(100), nullable=False)  # 角色名称，如"生产主管"、"质检员"等
    code = Column(String(50))  # 角色代码，如"PROD_SUPERVISOR"、"QC_INSPECTOR"
    description = Column(Text)  # 角色描述

    # 权限配置（JSONB格式存储详细权限）
    permissions = Column(JSONB, default={})  # 详细权限配置

    # 状态
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # 是否为系统预设角色（不可删除）

    # 数据访问范围
    data_access_scope = Column(String(50), default="factory")  # factory, company

    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    company = relationship("Company", backref="roles")
    employees = relationship("CompanyEmployee", back_populates="company_role")


class CompanyEmployee(Base):
    """Company employee relationship model."""

    __tablename__ = "company_employees"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 员工信息
    employee_number = Column(String(100))
    role = Column(String(50), default="employee")  # admin, manager, employee (保留用于向后兼容)
    company_role_id = Column(Integer, ForeignKey("company_roles.id", ondelete="SET NULL"))  # 新增：关联企业角色
    status = Column(String(50), default="active")  # active, inactive

    # 分配信息
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"))
    department = Column(String(100))
    position = Column(String(100))

    # 权限（保留用于向后兼容和个性化权限覆盖）
    permissions = Column(JSONB)
    data_access_scope = Column(String(50), default="factory")  # factory, company

    # 时间信息
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime)
    invited_at = Column(DateTime, default=datetime.utcnow)

    # 统计信息
    total_wps_created = Column(Integer, default=0)
    total_tasks_completed = Column(Integer, default=0)
    last_active_at = Column(DateTime)

    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    company = relationship("Company", back_populates="employees")
    user = relationship("User", foreign_keys=[user_id], backref="company_memberships")
    factory = relationship("Factory", back_populates="employees")
    company_role = relationship("CompanyRole", back_populates="employees")


class CompanyInvitation(Base):
    """Pending employee invitation sent by email."""

    __tablename__ = "company_invitations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    token = Column(String(128), unique=True, nullable=False, index=True)
    invitation_code = Column(String(32), unique=True, nullable=False, index=True)
    role = Column(String(50), default="employee")
    company_role_id = Column(Integer, ForeignKey("company_roles.id", ondelete="SET NULL"))
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"))
    department = Column(String(100))
    permissions = Column(JSONB)
    message = Column(Text)
    status = Column(String(20), default="pending", index=True)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime)
    accepted_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company")
    factory = relationship("Factory")

