@echo off
echo 正在启动焊序用户门户前端...
echo.

echo 检查Node.js和npm是否已安装...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Node.js未安装，请先安装Node.js 16.0或更高版本
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)

npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: npm未安装，请先安装npm
    pause
    exit /b 1
)

echo Node.js和npm已安装
echo.

echo 安装项目依赖...
call npm install
if %errorlevel% neq 0 (
    echo 依赖安装失败，请检查网络连接
    echo 可以尝试使用以下命令:
    echo npm cache clean --force
    echo npm install --legacy-peer-deps
    pause
    exit /b 1
)

echo 依赖安装成功
echo.

echo 启动开发服务器...
echo 浏览器将自动打开 http://localhost:3000
echo.
echo 按 Ctrl+C 停止服务器
echo.

call npm run dev

pause