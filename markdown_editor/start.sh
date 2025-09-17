#!/bin/bash

# Markdown 编辑器启动脚本
echo "🚀 启动 Markdown 编辑器..."

# 检查 Node.js 是否安装
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到 Node.js，请先安装 Node.js"
    exit 1
fi

# 检查 npm 是否安装
if ! command -v npm &> /dev/null; then
    echo "❌ 错误: 未找到 npm，请先安装 npm"
    exit 1
fi

# 进入项目目录
cd "$(dirname "$0")"

# 检查 node_modules 是否存在
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖包..."
    npm install
fi

# 启动开发服务器
echo "🌟 启动开发服务器..."
echo "📱 访问地址: http://localhost:5173"
echo "🛑 按 Ctrl+C 停止服务器"
echo ""

npm run dev

