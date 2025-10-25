#!/bin/bash

echo "🚀 启动 Stripe 购物网站演示..."

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 ./setup.sh"
    exit 1
fi

# 检查 .env 文件是否存在
if [ ! -f ".env" ]; then
    echo "❌ .env 文件不存在，请先运行 ./setup.sh"
    exit 1
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 检查依赖是否安装
echo "📦 检查依赖..."
pip list | grep -q "Flask\|stripe\|python-dotenv"
if [ $? -ne 0 ]; then
    echo "📥 安装依赖..."
    pip install -r requirements.txt
fi

# 启动应用
echo "🌟 启动 Flask 应用..."
echo "   访问地址: http://localhost:5000"
echo "   按 Ctrl+C 停止服务"
echo ""

python app.py
