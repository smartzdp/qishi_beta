"""
客户端SDK基本功能测试
"""
import pytest
import requests_mock
from whisper_asr_client import WhisperASRClient, AuthError, RateLimitError, APIError

def test_client_init():
    """测试客户端初始化"""
    client = WhisperASRClient("http://localhost:5000")
    assert client.base_url == "http://localhost:5000"
    assert client.token is None

def test_login_success():
    """测试登录成功"""
    client = WhisperASRClient("http://localhost:5000")
    
    with requests_mock.Mocker() as m:
        m.post('http://localhost:5000/api/auth/login', json={
            'message': '登录成功',
            'access_token': 'test_token',
            'user': {'id': 1, 'username': 'testuser'}
        })
        
        result = client.login('testuser', 'password123')
        assert result['access_token'] == 'test_token'
        assert client.token == 'test_token'

def test_login_failure():
    """测试登录失败"""
    client = WhisperASRClient("http://localhost:5000")
    
    with requests_mock.Mocker() as m:
        m.post('http://localhost:5000/api/auth/login', 
               status_code=401,
               json={'error': '用户名或密码错误'})
        
        with pytest.raises(AuthError):
            client.login('testuser', 'wrongpassword')

def test_register():
    """测试用户注册"""
    client = WhisperASRClient("http://localhost:5000")
    
    with requests_mock.Mocker() as m:
        m.post('http://localhost:5000/api/auth/register', json={
            'message': '用户注册成功',
            'user': {'id': 1, 'username': 'testuser'}
        })
        
        result = client.register('testuser', 'test@example.com', 
                                'password123', 'password123')
        assert 'user' in result

def test_create_model():
    """测试创建模型实例"""
    client = WhisperASRClient("http://localhost:5000")
    client.token = 'test_token'
    
    with requests_mock.Mocker() as m:
        m.post('http://localhost:5000/api/asr/models', json={
            'instance_id': 'test-instance-id',
            'model_name': 'base',
            'device': 'cpu'
        })
        
        result = client.create_model('base', device='cpu')
        assert result['instance_id'] == 'test-instance-id'
        assert result['model_name'] == 'base'

def test_create_model_unauthorized():
    """测试未认证创建模型"""
    client = WhisperASRClient("http://localhost:5000")
    
    with pytest.raises(AuthError):
        client.create_model('base')

def test_delete_model():
    """测试删除模型实例"""
    client = WhisperASRClient("http://localhost:5000")
    client.token = 'test_token'
    
    with requests_mock.Mocker() as m:
        m.delete('http://localhost:5000/api/asr/models/test-instance-id', 
                status_code=204)
        
        result = client.delete_model('test-instance-id')
        assert result is True

def test_transcribe_base64():
    """测试base64转录"""
    client = WhisperASRClient("http://localhost:5000")
    client.token = 'test_token'
    
    with requests_mock.Mocker() as m:
        m.post('http://localhost:5000/api/asr/transcribe', json={
            'text': 'Hello, world!',
            'language': 'en',
            'duration': 12.3,
            'segments': []
        })
        
        result = client.transcribe_base64('test-instance-id', 'base64_audio_data')
        assert result['text'] == 'Hello, world!'
        assert result['language'] == 'en'

def test_file_to_base64(tmp_path):
    """测试文件转base64"""
    client = WhisperASRClient("http://localhost:5000")
    
    # 创建临时文件
    test_file = tmp_path / 'test.txt'
    test_file.write_bytes(b'test content')
    
    # 转换为base64
    base64_str = client.file_to_base64(str(test_file))
    assert base64_str is not None
    assert isinstance(base64_str, str)

def test_rate_limit_error():
    """测试速率限制错误"""
    client = WhisperASRClient("http://localhost:5000")
    client.token = 'test_token'
    
    with requests_mock.Mocker() as m:
        m.post('http://localhost:5000/api/asr/models',
               status_code=429,
               json={'error': 'rate_limit_exceeded'},
               headers={'Retry-After': '30'})
        
        with pytest.raises(RateLimitError) as exc_info:
            client.create_model('base')
        assert exc_info.value.retry_after == 30

def test_not_found_error():
    """测试资源不存在错误"""
    client = WhisperASRClient("http://localhost:5000")
    client.token = 'test_token'
    
    with requests_mock.Mocker() as m:
        m.delete('http://localhost:5000/api/asr/models/nonexistent-id',
                status_code=404,
                json={'error': '模型实例不存在'})
        
        with pytest.raises(APIError) as exc_info:
            client.delete_model('nonexistent-id')
        assert exc_info.value.status_code == 404

def test_list_models():
    """测试列出模型实例"""
    client = WhisperASRClient("http://localhost:5000")
    client.token = 'test_token'
    
    with requests_mock.Mocker() as m:
        m.get('http://localhost:5000/api/asr/models', json={
            'models': [
                {
                    'instance_id': 'test-instance-id',
                    'model_name': 'base',
                    'device': 'cpu'
                }
            ],
            'count': 1
        })
        
        result = client.list_models()
        assert result['count'] == 1
        assert len(result['models']) == 1
