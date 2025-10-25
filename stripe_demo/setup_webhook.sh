#!/bin/bash

echo "🔧 设置Stripe Webhook..."
echo ""

# 检查Stripe CLI是否安装
if ! command -v stripe &> /dev/null; then
    echo "❌ Stripe CLI未安装，请先安装："
    echo "   brew install stripe/stripe-cli/stripe"
    exit 1
fi

echo "1️⃣ 登录Stripe账户..."
stripe login

echo ""
echo "2️⃣ 启动Webhook监听..."
echo "   这将监听Stripe事件并转发到本地Flask应用"
echo "   请复制显示的webhook密钥到.env文件中"
echo ""

# 启动webhook监听
stripe listen --forward-to localhost:5000/webhook
