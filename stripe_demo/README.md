# Stripe 购物网站演示

一个使用 Stripe 支付系统的简单购物网站，支持一次性购买和订阅功能。

## 功能特性

- ✅ 一次性购买产品
- ✅ 月度订阅功能  
- ✅ 实时价格显示（从Stripe API获取）
- ✅ 订单状态管理
- ✅ Stripe Webhook 支付回调
- ✅ 支付成功后自动跳转
- ✅ 响应式前端界面

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <your-repo-url>
cd stripe_demo

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 Stripe

1. 在 [Stripe Dashboard](https://dashboard.stripe.com/) 创建账户
2. 获取测试环境的 API 密钥
3. 创建产品和价格
4. 复制 `env_example.txt` 为 `.env` 并填入配置：

```bash
cp env_example.txt .env
```

编辑 `.env` 文件：
```
STRIPE_SECRET_KEY=sk_test_你的测试密钥
STRIPE_WEBHOOK_SECRET=whsec_你的webhook密钥
PRICE_ONE_TIME=price_一次性购买价格ID
PRICE_SUB_MONTHLY=price_订阅价格ID
DOMAIN=http://localhost:5001
DEFAULT_EMAIL=your-email@example.com
```

### 3. 启动应用

```bash
# 启动Flask应用
python app.py

# 在另一个终端启动Webhook监听（可选）
stripe listen --forward-to localhost:5001/webhook
```

访问 http://localhost:5001 查看购物网站。

## 测试支付

使用 Stripe 测试卡号：
- **成功支付**: `4242 4242 4242 4242`
- **失败支付**: `4000 0000 0000 0002`

## API 接口

- `GET /` - 购物网站首页
- `POST /api/checkout/one-time` - 创建一次性购买
- `POST /api/checkout/subscribe` - 创建订阅
- `GET /api/orders` - 获取订单列表
- `GET /api/prices` - 获取价格信息
- `POST /webhook` - Stripe Webhook 端点

## 技术栈

- **后端**: Flask + Stripe Python SDK
- **前端**: HTML + CSS + JavaScript
- **支付**: Stripe Checkout
- **部署**: 支持本地和生产环境

## 注意事项

- 本项目仅用于演示，生产环境需要添加更多安全措施
- 订单数据存储在内存中，重启服务会丢失
- 生产环境建议使用数据库存储订单信息