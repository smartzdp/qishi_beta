#!/bin/bash

# GLM-4-Voice API Demo 启动脚本

echo "🎵 启动 GLM-4-Voice API Demo..."

# 检查API密钥
if [ -z "$GLM_API_KEY" ]; then
    echo "❌ 错误: 请设置 GLM_API_KEY 环境变量"
    echo ""
    echo "方法1: 环境变量"
    echo "export GLM_API_KEY='your-api-key-here'"
    echo ""
    echo "方法2: 创建.env文件"
    echo "echo 'GLM_API_KEY=your-api-key-here' > .env"
    echo ""
    echo "获取API密钥: https://open.bigmodel.cn/"
    exit 1
fi

# 检查FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ 错误: 请安装 FFmpeg"
    echo "macOS: brew install ffmpeg"
    echo "Ubuntu: sudo apt install ffmpeg"
    exit 1
fi

# 设置环境变量
export FFMPEG_BINARY=$(which ffmpeg)
export FFPROBE_BINARY=$(which ffprobe)

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "❌ 错误: 虚拟环境不存在，请先运行: python -m venv venv"
    exit 1
fi

# 安装依赖
echo "📦 检查依赖..."
pip install -r requirements.txt

# 启动应用
echo "🚀 启动Web服务..."
python web_demo.py --port 8890

echo "✅ 应用已启动，请访问: http://localhost:8890"
