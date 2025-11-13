"""
认证API测试
"""
import pytest
from app import create_app, db
from app.models.user import User

@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

def test_register(client):
    """测试用户注册"""
    response = client.post('/api/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert 'user' in data
    assert data['user']['username'] == 'testuser'

def test_register_duplicate_username(client):
    """测试重复用户名注册"""
    # 第一次注册
    client.post('/api/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    
    # 第二次注册（相同用户名）
    response = client.post('/api/auth/register', json={
        'username': 'testuser',
        'email': 'test2@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    assert response.status_code == 409

def test_login(client):
    """测试用户登录"""
    # 先注册
    client.post('/api/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    
    # 登录
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
    assert 'user' in data

def test_login_invalid_credentials(client):
    """测试无效凭证登录"""
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401

def test_login_nonexistent_user(client):
    """测试不存在的用户登录"""
    response = client.post('/api/auth/login', json={
        'username': 'nonexistent',
        'password': 'password123'
    })
    assert response.status_code == 401
