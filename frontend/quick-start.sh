#!/bin/bash

echo "正在启动焊接工艺管理系统用户门户前端..."
echo

# 检查Node.js和npm是否已安装
if ! command -v node &> /dev/null; then
    echo "错误: Node.js未安装，请先安装Node.js 16.0或更高版本"
    echo "下载地址: https://nodejs.org/"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "错误: npm未安装，请先安装npm"
    exit 1
fi

echo "Node.js和npm已安装"
echo "Node.js版本: $(node --version)"
echo "npm版本: $(npm --version)"
echo

# 安装项目依赖
echo "安装项目依赖..."
npm install

if [ $? -ne 0 ]; then
    echo "依赖安装失败，请检查网络连接"
    echo "可以尝试使用以下命令:"
    echo "npm cache clean --force"
    echo "npm install --legacy-peer-deps"
    exit 1
fi

echo "依赖安装成功"
echo

# 启动开发服务器
echo "启动开发服务器..."
echo "浏览器将自动打开 http://localhost:3000"
echo
echo "按 Ctrl+C 停止服务器"
echo

npm run dev