#!/bin/bash

echo "🚀 设置 Stripe 购物网站演示项目..."

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装 Python3"
    exit 1
fi

# 创建虚拟环境
echo "📦 创建虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装依赖包..."
pip install -r requirements.txt

# 创建 .env 文件（如果不存在）
if [ ! -f .env ]; then
    echo "📝 创建 .env 配置文件..."
    cp env_example.txt .env
    echo "⚠️  请编辑 .env 文件，填入你的 Stripe 配置信息"
fi

echo "✅ 设置完成！"
echo ""
echo "下一步："
echo "1. 编辑 .env 文件，填入 Stripe 配置"
echo "2. 运行: source venv/bin/activate"
echo "3. 运行: python app.py"
echo "4. 访问: http://localhost:5000"
