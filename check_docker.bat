@echo off
chcp 65001 >nul
echo ========================================
echo 检查 Docker 环境
echo ========================================
echo.

echo [1/3] 检查 Docker 版本...
docker --version
if %errorlevel% neq 0 (
    echo ❌ Docker 未安装或未添加到 PATH
    pause
    exit /b 1
)
echo ✅ Docker 已安装
echo.

echo [2/3] 检查 Docker 服务状态...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 服务未启动
    echo 💡 请启动 Docker Desktop 后重试
    pause
    exit /b 1
)
echo ✅ Docker 服务正在运行
echo.

echo [3/3] 检查 Docker Compose...
docker-compose --version
if %errorlevel% neq 0 (
    echo ⚠️  Docker Compose 未安装（可选）
) else (
    echo ✅ Docker Compose 已安装
)
echo.

echo ========================================
echo ✅ Docker 环境检查完成！
echo ========================================
echo.
echo 💡 现在可以运行构建测试:
echo    python test_build_local.py
echo.
pause

