"""
Main application entry point for the welding system backend.
"""
import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import engine, Base

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# 添加一个调试端点来测试CORS
@app.get("/api/v1/debug/cors-test")
async def cors_test():
    """CORS测试端点"""
    return {
        "message": "CORS test successful",
        "timestamp": "2025-10-22T13:59:00Z",
        "development": settings.DEVELOPMENT
    }


# 请求处理时间中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加请求处理时间头."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# 设置可信主机中间件（生产环境）
if not settings.DEVELOPMENT:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "sdhaohan.cn",
            "*.sdhaohan.cn",
            "api.sdhaohan.cn",
            "laimiu.sdhaohan.cn",
            "localhost",
            "127.0.0.1"
        ]
    )


# 设置CORS中间件 - 必须最后添加，这样它会最先执行
# 在开发环境下使用更宽松的CORS配置
if settings.DEVELOPMENT:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 开发环境允许所有来源
        allow_credentials=True,
        allow_methods=["*"],  # 允许所有方法
        allow_headers=["*"],  # 允许所有头部
        expose_headers=["*"],
    )
    logger.info("CORS middleware configured for DEVELOPMENT (allow all origins)")
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=settings.ALLOWED_CREDENTIALS,
        allow_methods=settings.ALLOWED_METHODS,
        allow_headers=settings.ALLOWED_HEADERS,
    )
    logger.info(f"CORS middleware configured for PRODUCTION (allowed origins: {settings.ALLOWED_ORIGINS})")


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器."""
    import traceback

    logger.error(f"=== 全局异常处理器被触发 ===")
    logger.error(f"请求路径: {request.url}")
    logger.error(f"请求方法: {request.method}")
    logger.error(f"异常类型: {type(exc).__name__}")
    logger.error(f"异常信息: {str(exc)}")
    logger.error(f"异常堆栈: {traceback.format_exc()}")

    # 如果有认证头，也记录下来
    auth_header = request.headers.get("authorization")
    if auth_header:
        logger.error(f"认证头: {auth_header[:20]}...")  # 只记录前20个字符

    # 记录请求体（如果有的话）
    try:
        body = await request.body()
        if body:
            logger.error(f"请求体: {body[:500]}...")  # 只记录前500个字符
    except Exception as body_error:
        logger.error(f"读取请求体失败: {body_error}")

    if settings.DEVELOPMENT:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "error": str(exc),
                "type": type(exc).__name__,
                "path": str(request.url),
                "traceback": traceback.format_exc()
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )

# 添加请求体异常处理
@app.exception_handler(Exception)
async def request_body_exception_handler(request: Request, exc: Exception):
    """请求体异常处理器."""
    logger.error(f"Request body exception: {exc}", exc_info=True)

    if "JSON" in str(exc) or "body" in str(exc):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": f"Invalid request body format: {str(exc)}",
                "error": "JSON parsing error",
                "type": type(exc).__name__,
            }
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化操作."""
    logger.info("Starting Welding System Backend with verification code support...")

    # 创建数据库表
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")

    # 创建上传目录
    import os
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"Upload directory created: {settings.UPLOAD_DIR}")

    logger.info("Welding System Backend started successfully")


# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理操作."""
    logger.info("Shutting down Welding System Backend...")
    # 这里可以添加清理逻辑
    logger.info("Welding System Backend shutdown completed")


# 健康检查端点
@app.get("/health")
@app.get("/api/v1/health")
async def health_check():
    """健康检查端点."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": "development" if settings.DEVELOPMENT else "production"
    }


# 根路径
@app.get("/")
async def root():
    """根路径端点."""
    return {
        "message": "Welcome to Welding System Backend API",
        "version": settings.APP_VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs",
        "api_url": settings.API_V1_STR
    }


# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 静态文件服务（如果需要）
# app.mount("/static", StaticFiles(directory="static"), name="static")
# app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEVELOPMENT,
        log_level=settings.LOG_LEVEL.lower(),
    )