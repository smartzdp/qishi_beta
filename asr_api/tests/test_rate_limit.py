"""
速率限制测试
"""
import pytest
import time
from app import create_app, db
from app.models.user import User
from app.utils.rate_limiter import rate_limit_store

@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    app.config['RATE_LIMIT_WINDOW'] = 10  # 10秒窗口
    app.config['RATE_LIMIT_MAX_REQUESTS'] = 5  # 最多5次请求
    
    # 更新rate limiter配置以使用测试配置
    from app.utils import rate_limiter
    rate_limiter.RATE_LIMIT_WINDOW = 10
    rate_limiter.RATE_LIMIT_MAX_REQUESTS = 5
    
    with app.app_context():
        db.create_all()
        # 清理速率限制存储（在创建用户之前）
        rate_limit_store.clear()
        # 检查用户是否已存在，如果存在则删除
        existing_user = User.query.filter_by(username='testuser').first()
        if existing_user:
            db.session.delete(existing_user)
            db.session.commit()
        # 创建测试用户
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        yield app
        db.drop_all()
        # 清理速率限制存储
        rate_limit_store.clear()

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

@pytest.fixture
def auth_token(client):
    """获取认证token"""
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    return response.get_json()['access_token']

def test_rate_limit_headers(client, auth_token):
    """测试速率限制响应头"""
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    # 发送请求（使用一个不需要模型加载的端点，比如GET /api/asr/models）
    response = client.get('/api/asr/models', headers=headers)
    
    # 检查响应头
    assert 'X-RateLimit-Limit' in response.headers
    assert 'X-RateLimit-Remaining' in response.headers
    assert 'X-RateLimit-Reset' in response.headers
    assert response.headers['X-RateLimit-Limit'] == '5'  # 测试配置的5次限制

def test_rate_limit_exceeded(client, auth_token):
    """测试速率限制触发"""
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    # 清除速率限制存储，确保从干净状态开始
    rate_limit_store.clear()
    
    # 发送超过限制的请求（使用GET请求避免模型加载）
    for i in range(6):  # 超过5次限制
        response = client.get('/api/asr/models', headers=headers)
        if i < 5:
            # 前5次请求应该成功（200或404，但不应该是429）
            assert response.status_code != 429, f"Request {i+1} should not be rate limited"
        else:
            # 第6次请求应该被限制
            assert response.status_code == 429, f"Request {i+1} should be rate limited"
            data = response.get_json()
            assert 'error' in data
            assert 'retry_after' in data
            assert data['error'] == 'rate_limit_exceeded'

def test_rate_limit_reset(client, auth_token):
    """测试速率限制重置"""
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    # 清除速率限制存储，确保从干净状态开始
    rate_limit_store.clear()
    
    # 发送请求达到限制（使用GET请求避免模型加载）
    for i in range(5):
        response = client.get('/api/asr/models', headers=headers)
        # 前5次请求应该成功（不应该被限制）
        assert response.status_code != 429, f"Request {i+1} should not be rate limited"
        # 检查剩余请求数递减（第i+1个请求后，剩余应该是 5 - (i+1)）
        remaining = int(response.headers.get('X-RateLimit-Remaining', '0'))
        expected_remaining = 5 - (i + 1)
        assert remaining == expected_remaining, f"After request {i+1}, remaining should be {expected_remaining}, got {remaining}"
    
    # 手动重置速率限制（模拟时间窗口重置）
    # 由于我们不知道确切的key（它依赖于JWT解析），我们重置所有keys
    # 在测试环境中，通常只有一个key
    import time as time_module
    current_time = time_module.time()
    for key in rate_limit_store.keys():
        rate_limit_store[key]['count'] = 0
        rate_limit_store[key]['reset_time'] = current_time + 10
    
    # 再次发送请求应该成功（因为计数已重置）
    response = client.get('/api/asr/models', headers=headers)
    assert response.status_code != 429, "Request should succeed after reset"
    
    # 验证速率限制头显示重置后的计数
    assert 'X-RateLimit-Remaining' in response.headers
    remaining = int(response.headers['X-RateLimit-Remaining'])
    # 重置后，剩余应该是4（因为我们刚发送了1个请求，总共5个限制）
    assert remaining == 4, f"Remaining should be 4 after reset, got {remaining}"
