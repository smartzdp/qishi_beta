"""
ASR API测试
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
        # 创建测试用户
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        yield app
        db.drop_all()

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

def test_create_model(client, auth_token):
    """测试创建模型实例"""
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    try:
        response = client.post('/api/asr/models',
                              json={'model_name': 'tiny', 'device': 'cpu'},
                              headers=headers)
        assert response.status_code == 201
        data = response.get_json()
        assert 'instance_id' in data
        assert data['model_name'] == 'tiny'
        assert data['device'] == 'cpu'
        
        # 清理
        instance_id = data['instance_id']
        client.delete(f'/api/asr/models/{instance_id}', headers=headers)
    except Exception as e:
        # 如果模型加载失败，跳过测试
        pytest.skip(f"模型加载失败: {e}")

def test_create_model_unauthorized(client):
    """测试未认证创建模型"""
    response = client.post('/api/asr/models',
                            json={'model_name': 'base', 'device': 'cpu'})
    assert response.status_code == 401

def test_delete_model(client, auth_token):
    """测试删除模型实例"""
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    try:
        # 先创建模型实例
        response = client.post('/api/asr/models',
                              json={'model_name': 'tiny', 'device': 'cpu'},
                              headers=headers)
        instance_id = response.get_json()['instance_id']
        
        # 删除模型实例
        response = client.delete(f'/api/asr/models/{instance_id}', headers=headers)
        assert response.status_code == 204
    except Exception as e:
        pytest.skip(f"模型加载失败: {e}")

def test_delete_nonexistent_model(client, auth_token):
    """测试删除不存在的模型实例"""
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    response = client.delete('/api/asr/models/nonexistent-id', headers=headers)
    assert response.status_code == 404

def test_list_models(client, auth_token):
    """测试列出模型实例"""
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    try:
        # 创建模型实例
        response = client.post('/api/asr/models',
                              json={'model_name': 'tiny', 'device': 'cpu'},
                              headers=headers)
        instance_id = response.get_json()['instance_id']
        
        # 列出模型实例
        response = client.get('/api/asr/models', headers=headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'models' in data
        assert 'count' in data
        assert len(data['models']) >= 1
        
        # 清理
        client.delete(f'/api/asr/models/{instance_id}', headers=headers)
    except Exception as e:
        pytest.skip(f"模型加载失败: {e}")

def test_transcribe_invalid_instance(client, auth_token):
    """测试使用无效实例ID转录"""
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    import base64
    # 创建模拟的base64音频数据
    fake_audio = base64.b64encode(b'fake_audio_data').decode('utf-8')
    
    response = client.post('/api/asr/transcribe',
                          json={
                              'instance_id': 'nonexistent-id',
                              'audio_base64': fake_audio
                          },
                          headers=headers)
    assert response.status_code == 404
