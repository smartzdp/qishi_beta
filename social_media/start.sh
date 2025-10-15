#!/bin/bash
# 社交媒体平台启动脚本

echo "🚀 启动社交媒体平台..."
echo ""

# 检查node_modules是否存在
if [ ! -d "node_modules" ]; then
    echo "📦 首次运行，正在安装依赖..."
    npm install
    echo ""
fi

echo "🌐 启动开发服务器..."
echo "📱 应用将在 http://localhost:5173 启动"
echo ""
echo "⚠️  请确保已在 src/firebase/config.js 中配置了 Firebase"
echo ""

npm run dev

