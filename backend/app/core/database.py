"""
Database configuration and session management for the welding system backend.
"""
from typing import AsyncGenerator

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# 使用PostgreSQL数据库
database_url = str(settings.DATABASE_URL)

# PostgreSQL配置
engine = create_engine(
    database_url,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)
async_engine = create_async_engine(
    database_url.replace("postgresql://", "postgresql+asyncpg://"),
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# 会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 异步会话工厂
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 元数据
metadata = MetaData()

# 基础模型类
Base = declarative_base()


def get_db() -> sessionmaker:
    """
    获取数据库会话.

    Returns:
        数据库会话对象
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话.

    Yields:
        异步数据库会话对象
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def create_tables():
    """创建所有数据库表."""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """删除所有数据库表."""
    Base.metadata.drop_all(bind=engine)


async def init_db():
    """初始化数据库."""
    # 创建数据库表
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接."""
    await async_engine.dispose()


# Redis连接
import redis

redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True
)


def get_redis() -> redis.Redis:
    """
    获取Redis客户端.

    Returns:
        Redis客户端对象
    """
    return redis_client


# 数据库依赖函数
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI依赖函数：获取数据库会话.

    Yields:
        异步数据库会话对象
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class DatabaseManager:
    """数据库管理器."""

    def __init__(self):
        self.engine = engine
        self.async_engine = async_engine
        self.redis_client = redis_client

    async def health_check(self) -> dict:
        """
        检查数据库连接健康状态.

        Returns:
            数据库健康状态信息
        """
        health_status = {
            "database": "unknown",
            "redis": "unknown",
            "overall": "unknown"
        }

        # 检查PostgreSQL连接
        try:
            async with self.async_engine.begin() as conn:
                await conn.execute("SELECT 1")
            health_status["database"] = "healthy"
        except Exception as e:
            health_status["database"] = f"unhealthy: {str(e)}"

        # 检查Redis连接
        try:
            self.redis_client.ping()
            health_status["redis"] = "healthy"
        except Exception as e:
            health_status["redis"] = f"unhealthy: {str(e)}"

        # 整体健康状态
        if (health_status["database"] == "healthy" and
            health_status["redis"] == "healthy"):
            health_status["overall"] = "healthy"
        else:
            health_status["overall"] = "unhealthy"

        return health_status

    async def execute_raw_sql(self, sql: str, params: dict = None):
        """
        执行原始SQL查询.

        Args:
            sql: SQL语句
            params: 查询参数

        Returns:
            查询结果
        """
        async with self.async_engine.begin() as conn:
            result = await conn.execute(sql, params or {})
            return result.fetchall()

    def backup_database(self, backup_path: str):
        """
        备份数据库.

        Args:
            backup_path: 备份文件路径

        Returns:
            备份操作结果
        """
        import subprocess
        import os

        try:
            # 构建pg_dump命令
            db_config = {
                "host": settings.DATABASE_HOST,
                "port": settings.DATABASE_PORT,
                "user": settings.DATABASE_USER,
                "dbname": settings.DATABASE_NAME,
            }

            cmd = [
                "pg_dump",
                f"--host={db_config['host']}",
                f"--port={db_config['port']}",
                f"--username={db_config['user']}",
                f"--dbname={db_config['dbname']}",
                "--format=custom",
                "--verbose",
                f"--file={backup_path}"
            ]

            # 设置密码环境变量
            env = os.environ.copy()
            env["PGPASSWORD"] = settings.DATABASE_PASSWORD

            # 执行备份命令
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return {"success": True, "backup_path": backup_path}
            else:
                return {
                    "success": False,
                    "error": result.stderr
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def restore_database(self, backup_path: str):
        """
        恢复数据库.

        Args:
            backup_path: 备份文件路径

        Returns:
            恢复操作结果
        """
        try:
            # 首先删除现有表
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

            # 然后恢复备份
            import subprocess
            import os

            db_config = {
                "host": settings.DATABASE_HOST,
                "port": settings.DATABASE_PORT,
                "user": settings.DATABASE_USER,
                "dbname": settings.DATABASE_NAME,
            }

            cmd = [
                "pg_restore",
                f"--host={db_config['host']}",
                f"--port={db_config['port']}",
                f"--username={db_config['user']}",
                f"--dbname={db_config['dbname']}",
                "--verbose",
                "--clean",
                "--if-exists",
                backup_path
            ]

            env = os.environ.copy()
            env["PGPASSWORD"] = settings.DATABASE_PASSWORD

            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": result.stderr
                }

        except Exception as e:
            return {"success": False, "error": str(e)}


# 创建全局数据库管理器实例
db_manager = DatabaseManager()