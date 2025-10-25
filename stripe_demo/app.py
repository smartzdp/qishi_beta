import os
import uuid
from flask import Flask, request, jsonify, abort, redirect, render_template
from dotenv import load_dotenv
import stripe

load_dotenv()
app = Flask(__name__)

# 加载环境变量
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
PRICE_ONE_TIME = os.getenv("PRICE_ONE_TIME")
PRICE_SUB_MONTHLY = os.getenv("PRICE_SUB_MONTHLY")
DOMAIN = os.getenv("DOMAIN", "http://localhost:5001")
DEFAULT_EMAIL = os.getenv("DEFAULT_EMAIL", "test@2brain.cn")

# 验证Stripe配置
if not stripe.api_key:
    raise ValueError("STRIPE_SECRET_KEY 未设置")
if not PRICE_ONE_TIME:
    raise ValueError("PRICE_ONE_TIME 未设置")
if not PRICE_SUB_MONTHLY:
    raise ValueError("PRICE_SUB_MONTHLY 未设置")

# 从Stripe API获取真实价格信息
def get_price_info(price_id):
    """从Stripe API获取价格信息"""
    try:
        price = stripe.Price.retrieve(price_id)
        return {
            'id': price.id,
            'amount': price.unit_amount / 100,  # 转换为元
            'currency': price.currency.upper(),
            'type': 'one_time' if price.type == 'one_time' else 'recurring',
            'interval': price.recurring.interval if price.recurring else None
        }
    except Exception as e:
        print(f"获取价格信息失败: {e}")
        return None

# 获取价格信息
ONE_TIME_PRICE_INFO = get_price_info(PRICE_ONE_TIME)
MONTHLY_PRICE_INFO = get_price_info(PRICE_SUB_MONTHLY)

# 简单的内存数据库存储订单信息
orders = {}

# Webhook：确认事件并更新你自己的数据库
@app.post("/webhook")
def stripe_webhook():
    payload = request.data
    sig = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig, secret=WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        abort(400)

    et = event["type"]
    data = event["data"]["object"]
    print(f'event type: {et}, event object: {data}')
    
    def checkout_session_completed():
        session_id = data.get('id')
        payment_status = data.get('payment_status')
        mode = data.get('mode')
        
        print(f"Checkout session completed: {session_id}, payment_status: {payment_status}, mode: {mode}")
        
        # 更新订单状态为已支付
        for order_id, order in orders.items():
            if order.get('session_id') == session_id:
                order['status'] = 'paid'
                order['payment_status'] = payment_status
                print(f"Order {order_id} marked as paid")
                break
    
    def subscription_updated(subscription: stripe.Subscription):
        print(f"Subscription updated: {subscription.id}")
        # 处理订阅更新逻辑
    
    def subscription_deleted(subscription: stripe.Subscription):
        print(f"Subscription deleted: {subscription.id}")
        # 处理订阅删除逻辑
    
    def invoice_payment_succeeded(invoice: stripe.Invoice):
        print(f"Invoice payment succeeded: {invoice.id}")
        # 处理发票支付成功逻辑
    
    def invoice_payment_failed(invoice: stripe.Invoice):
        print(f"Invoice payment failed: {invoice.id}")
        # 处理发票支付失败逻辑

    # 结账完成，无论一次性还是订阅
    if et == "checkout.session.completed":
        checkout_session_completed()
    # 订阅更新
    elif et == 'customer.subscription.updated':
        subscription_updated(data)
    # 订阅删除
    elif et == 'customer.subscription.deleted':
        subscription_deleted(data)
    # 支付成功
    elif et == 'invoice.payment_succeeded':
        invoice_payment_succeeded(data)
    # 支付失败
    elif et == 'invoice.payment_failed':
        invoice_payment_failed(data)
        
    return "", 200

# 一次性购买：创建 Checkout Session，mode=payment
@app.post("/api/checkout/one-time")
def create_one_time_checkout():
    # user_id = get_current_user_id()
    # customer_id = ensure_customer(user_id)

    # 客户端也可以包含 quantity、coupon 等
    data = request.get_json(silent=True) or {}
    quantity = int(data.get("quantity", 1))
    price_id = data.get("price_id", PRICE_ONE_TIME)

    # 创建订单记录
    order_id = str(uuid.uuid4())
    orders[order_id] = {
        'id': order_id,
        'type': 'one_time',
        'quantity': quantity,
        'price_id': price_id,
        'status': 'pending',
        'payment_status': 'unpaid'
    }

    session = stripe.checkout.Session.create(
        customer_email=DEFAULT_EMAIL,
        mode="payment",
        line_items=[{"price": price_id, "quantity": quantity}],
        success_url=f"{DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{DOMAIN}/cancel",
        metadata={'order_id': order_id}
    )
    
    # 保存session_id到订单
    orders[order_id]['session_id'] = session.id
    
    return jsonify({"url": session.url, "order_id": order_id})
    

# 订阅：创建 Checkout Session，mode=subscription
@app.post("/api/checkout/subscribe")
def create_sub_checkout():
    # user_id = get_current_user_id()
    # customer_id = ensure_customer(user_id)

    data = request.get_json(silent=True) or {}
    price_id = data.get("price_id", PRICE_SUB_MONTHLY)
    trial_days = int(data.get("trial_days", 0))

    # 创建订阅订单记录
    order_id = str(uuid.uuid4())
    orders[order_id] = {
        'id': order_id,
        'type': 'subscription',
        'price_id': price_id,
        'trial_days': trial_days,
        'status': 'pending',
        'payment_status': 'unpaid'
    }

    session = stripe.checkout.Session.create(
        customer_email=DEFAULT_EMAIL,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{DOMAIN}/cancel",
        subscription_data={"trial_period_days": trial_days} if trial_days > 0 else {},
        metadata={'order_id': order_id}
    )
    
    # 保存session_id到订单
    orders[order_id]['session_id'] = session.id
    
    return jsonify({"url": session.url, "order_id": order_id})

# 获取订单状态
@app.get("/api/order/<order_id>")
def get_order_status(order_id):
    if order_id not in orders:
        return jsonify({"error": "Order not found"}), 404
    
    return jsonify(orders[order_id])

# 获取所有订单
@app.get("/api/orders")
def get_all_orders():
    return jsonify(list(orders.values()))

# 获取价格信息
@app.get("/api/prices")
def get_prices():
    return jsonify({
        'one_time': ONE_TIME_PRICE_INFO,
        'monthly': MONTHLY_PRICE_INFO
    })
    
# 成功和取消页
@app.get("/success")
def success():
    session_id = request.args.get('session_id')
    
    # 查找对应的订单
    order = None
    for o in orders.values():
        if o.get('session_id') == session_id:
            order = o
            break
    
    if order:
        return f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>支付成功</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 20px;
                    text-align: center;
                    background-color: #f5f5f5;
                }}
                .success-container {{
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .success-icon {{
                    font-size: 64px;
                    color: #27ae60;
                    margin-bottom: 20px;
                }}
                h1 {{
                    color: #27ae60;
                    margin-bottom: 20px;
                }}
                .order-info {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    text-align: left;
                }}
                .btn {{
                    background: #3498db;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                    margin: 10px;
                    text-decoration: none;
                    display: inline-block;
                }}
                .btn:hover {{
                    background: #2980b9;
                }}
                .auto-redirect {{
                    color: #666;
                    font-size: 14px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="success-container">
                <div class="success-icon">✅</div>
                <h1>支付成功！</h1>
                <p>感谢您的购买，您的订单已成功处理。</p>
                
                <div class="order-info">
                    <h3>订单详情</h3>
                    <p><strong>订单ID:</strong> {order['id']}</p>
                    <p><strong>订单类型:</strong> {'一次性购买' if order['type'] == 'one_time' else '订阅'}</p>
                    <p><strong>数量:</strong> {order.get('quantity', 1)}</p>
                    <p><strong>支付状态:</strong> <span style="color: #27ae60;">已支付</span></p>
                    <p><strong>Session ID:</strong> {session_id}</p>
                </div>
                
                <a href="/" class="btn">返回购物页面</a>
                <a href="/api/orders" class="btn">查看所有订单</a>
                
                <div class="auto-redirect">
                    <p>5秒后自动跳转到购物页面...</p>
                </div>
            </div>
            
            <script>
                // 5秒后自动跳转
                setTimeout(function() {{
                    window.location.href = '/';
                }}, 5000);
            </script>
        </body>
        </html>
        """
    else:
        return f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>支付成功</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 20px;
                    text-align: center;
                    background-color: #f5f5f5;
                }}
                .success-container {{
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .success-icon {{
                    font-size: 64px;
                    color: #27ae60;
                    margin-bottom: 20px;
                }}
                h1 {{
                    color: #27ae60;
                    margin-bottom: 20px;
                }}
                .btn {{
                    background: #3498db;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                    margin: 10px;
                    text-decoration: none;
                    display: inline-block;
                }}
                .btn:hover {{
                    background: #2980b9;
                }}
            </style>
        </head>
        <body>
            <div class="success-container">
                <div class="success-icon">✅</div>
                <h1>支付成功！</h1>
                <p>感谢您的购买，您的订单已成功处理。</p>
                <p>Session ID: {session_id}</p>
                
                <a href="/" class="btn">返回购物页面</a>
                <a href="/api/orders" class="btn">查看所有订单</a>
            </div>
        </body>
        </html>
        """


@app.get("/cancel")
def cancel():
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>支付取消</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                padding: 20px;
                text-align: center;
                background-color: #f5f5f5;
            }
            .cancel-container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .cancel-icon {
                font-size: 64px;
                color: #e74c3c;
                margin-bottom: 20px;
            }
            h1 {
                color: #e74c3c;
                margin-bottom: 20px;
            }
            .btn {
                background: #3498db;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin: 10px;
                text-decoration: none;
                display: inline-block;
            }
            .btn:hover {
                background: #2980b9;
            }
            .btn-primary {
                background: #27ae60;
            }
            .btn-primary:hover {
                background: #229954;
            }
        </style>
    </head>
    <body>
        <div class="cancel-container">
            <div class="cancel-icon">❌</div>
            <h1>支付已取消</h1>
            <p>您取消了支付流程，没有产生任何费用。</p>
            <p>如果您需要帮助或有任何问题，请随时联系我们。</p>
            
            <a href="/" class="btn btn-primary">重新购买</a>
            <a href="/api/orders" class="btn">查看订单</a>
        </div>
    </body>
    </html>
    """

# 主页
@app.get("/")
def index():
    return render_template('index.html')
    
if __name__ == "__main__":
    app.run(port=5001, debug=True)
