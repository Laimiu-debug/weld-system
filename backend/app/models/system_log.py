"""
System log model for the welding system backend.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class SystemLog(Base):
    """系统日志模型"""

    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)

    # 日志信息
    log_level = Column(String(20), nullable=True)               # 级别: debug, info, warning, error, critical
    log_type = Column(String(50), nullable=True)                # 类型: api, database, security, system
    message = Column(Text, nullable=True)                       # 消息
    details = Column(JSONB, nullable=True)                      # 详细信息（JSON格式）

    # 来源信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 用户ID
    ip_address = Column(String(50), nullable=True)              # IP 地址
    user_agent = Column(Text, nullable=True)                    # 浏览器信息

    # 请求信息
    request_method = Column(String(10), nullable=True)          # 请求方法
    request_path = Column(String(500), nullable=True)           # 请求路径
    request_params = Column(JSONB, nullable=True)               # 请求参数
    response_status = Column(Integer, nullable=True)            # 响应状态码
    response_time = Column(DECIMAL(10, 3), nullable=True)       # 响应时间（毫秒）

    # 错误信息
    error_message = Column(Text, nullable=True)                 # 错误消息
    stack_trace = Column(Text, nullable=True)                   # 堆栈跟踪

    # 时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关系
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<SystemLog(id={self.id}, level={self.log_level}, type={self.log_type})>"