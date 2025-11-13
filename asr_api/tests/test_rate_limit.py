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
    
    with app.app_context():
        db.create_all()
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
    
    # 发送请求
    response = client.post('/api/asr/models', 
                          json={'model_name': 'base', 'device': 'cpu'},
                          headers=headers)
    
    # 检查响应头
    assert 'X-RateLimit-Limit' in response.headers
    assert 'X-RateLimit-Remaining' in response.headers
    assert 'X-RateLimit-Reset' in response.headers

def test_rate_limit_exceeded(client, auth_token):
    """测试速率限制触发"""
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    # 发送超过限制的请求
    for i in range(6):  # 超过5次限制
        response = client.post('/api/asr/models',
                              json={'model_name': 'base', 'device': 'cpu'},
                              headers=headers)
        if i < 5:
            assert response.status_code != 429
        else:
            # 第6次请求应该被限制
            assert response.status_code == 429
            data = response.get_json()
            assert 'error' in data
            assert 'retry_after' in data

def test_rate_limit_reset(client, auth_token):
    """测试速率限制重置"""
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    # 发送请求达到限制
    for i in range(5):
        client.post('/api/asr/models',
                   json={'model_name': 'base', 'device': 'cpu'},
                   headers=headers)
    
    # 等待窗口重置（在测试中可能需要手动重置）
    # 注意：在实际测试中，可能需要等待或手动重置rate_limit_store
    time.sleep(11)  # 等待超过10秒窗口
    
    # 再次发送请求应该成功
    response = client.post('/api/asr/models',
                          json={'model_name': 'base', 'device': 'cpu'},
                          headers=headers)
    assert response.status_code != 429
