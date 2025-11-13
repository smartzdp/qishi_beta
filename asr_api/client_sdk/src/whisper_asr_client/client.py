"""
Whisper ASR Client
Python客户端SDK for Whisper ASR Service
"""
import requests
import base64
from typing import Optional, Dict, Any
from .exceptions import APIError, AuthError, RateLimitError, NotFoundError

class WhisperASRClient:
    """
    Whisper ASR Service客户端
    
    此客户端SDK通过RESTful API与Whisper ASR服务通信。
    它不直接使用Whisper模型，而是通过HTTP请求调用远程API。
    
    使用方法:
        client = WhisperASRClient("http://localhost:5001")
        client.login("username", "password")
        model = client.create_model("base")
        result = client.transcribe_file(model["instance_id"], "audio.wav")
    
    注意:
        - transcribe_file()方法会将本地文件转换为base64编码，然后通过REST API发送
        - 所有操作都通过HTTP请求完成，不直接使用Whisper模型
        - 客户端只需要requests库，不需要whisper或torch
    """
    
    def __init__(self, base_url: str):
        """
        初始化客户端
        
        Args:
            base_url: API服务的基础URL（如 "http://localhost:5000"）
        """
        self.base_url = base_url.rstrip('/')
        self.token: Optional[str] = None
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """
        获取请求头（包含JWT token）
        
        Returns:
            dict: 请求头字典
        """
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        处理HTTP响应
        
        Args:
            response: requests响应对象
            
        Returns:
            dict: 响应数据
            
        Raises:
            AuthError: 如果状态码为401
            RateLimitError: 如果状态码为429
            NotFoundError: 如果状态码为404
            APIError: 如果其他错误
        """
        if response.status_code == 204:
            return {}
        
        try:
            data = response.json()
        except ValueError:
            data = {'error': response.text}
        
        if response.status_code == 401:
            raise AuthError(data.get('error', '认证失败'), response.status_code, response)
        elif response.status_code == 429:
            retry_after = response.headers.get('Retry-After')
            raise RateLimitError(
                data.get('error', '速率限制已触发'),
                response.status_code,
                response,
                retry_after=int(retry_after) if retry_after else None
            )
        elif response.status_code == 404:
            raise NotFoundError(data.get('error', '资源不存在'), response.status_code, response)
        elif response.status_code >= 400:
            raise APIError(data.get('error', 'API错误'), response.status_code, response)
        
        return data
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            dict: 登录响应，包含access_token和user信息
            
        Raises:
            AuthError: 如果登录失败
        """
        url = f'{self.base_url}/api/auth/login'
        data = {
            'username': username,
            'password': password
        }
        
        response = self.session.post(url, json=data, headers=self._get_headers())
        result = self._handle_response(response)
        
        # 保存token
        if 'access_token' in result:
            self.token = result['access_token']
        
        return result
    
    def register(self, username: str, email: str, password: str, confirm_password: str) -> Dict[str, Any]:
        """
        用户注册
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            confirm_password: 确认密码
            
        Returns:
            dict: 注册响应
            
        Raises:
            APIError: 如果注册失败
        """
        url = f'{self.base_url}/api/auth/register'
        data = {
            'username': username,
            'email': email,
            'password': password,
            'confirm_password': confirm_password
        }
        
        response = self.session.post(url, json=data, headers=self._get_headers())
        return self._handle_response(response)
    
    def create_model(self, model_name: str, device: str = "cpu") -> Dict[str, Any]:
        """
        创建模型实例
        
        Args:
            model_name: 模型名称（如 "base", "small", "medium", "large"）
            device: 设备类型（"cpu" 或 "cuda"）
            
        Returns:
            dict: 模型实例信息，包含instance_id
            
        Raises:
            APIError: 如果创建失败
        """
        if not self.token:
            raise AuthError("请先登录")
        
        url = f'{self.base_url}/api/asr/models'
        data = {
            'model_name': model_name,
            'device': device
        }
        
        response = self.session.post(url, json=data, headers=self._get_headers())
        return self._handle_response(response)
    
    def delete_model(self, instance_id: str) -> bool:
        """
        删除模型实例
        
        Args:
            instance_id: 模型实例ID
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            APIError: 如果删除失败
        """
        if not self.token:
            raise AuthError("请先登录")
        
        url = f'{self.base_url}/api/asr/models/{instance_id}'
        response = self.session.delete(url, headers=self._get_headers())
        self._handle_response(response)
        return True
    
    def transcribe_base64(self, instance_id: str, audio_base64: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        转录音频（使用base64编码的音频数据）
        
        Args:
            instance_id: 模型实例ID
            audio_base64: base64编码的音频数据
            language: 可选的语言代码（如 "en", "zh"）
            
        Returns:
            dict: 转录结果，包含text, language, duration, segments
            
        Raises:
            APIError: 如果转录失败
        """
        if not self.token:
            raise AuthError("请先登录")
        
        url = f'{self.base_url}/api/asr/transcribe'
        data = {
            'instance_id': instance_id,
            'audio_base64': audio_base64
        }
        if language:
            data['language'] = language
        
        response = self.session.post(url, json=data, headers=self._get_headers())
        return self._handle_response(response)
    
    def file_to_base64(self, file_path: str) -> str:
        """
        将音频文件转换为base64编码的字符串
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            str: base64编码的音频字符串
            
        Raises:
            FileNotFoundError: 如果文件不存在
            IOError: 如果文件读取失败
        """
        try:
            with open(file_path, 'rb') as f:
                audio_bytes = f.read()
                base64_string = base64.b64encode(audio_bytes).decode('utf-8')
                return base64_string
        except FileNotFoundError:
            raise FileNotFoundError(f"文件不存在: {file_path}")
        except Exception as e:
            raise IOError(f"无法读取文件: {str(e)}")
    
    def transcribe_file(self, instance_id: str, file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        转录音频文件
        
        此方法将本地音频文件转换为base64编码，然后通过REST API发送到服务器进行转录。
        服务器端的Whisper模型会处理音频并返回转录结果。
        
        Args:
            instance_id: 模型实例ID
            file_path: 音频文件路径（本地文件系统路径）
            language: 可选的语言代码（如 "en", "zh"）
            
        Returns:
            dict: 转录结果，包含text, language, duration, segments
            
        Raises:
            APIError: 如果转录失败
            FileNotFoundError: 如果文件不存在
            IOError: 如果文件读取失败
        """
        # 将文件转换为base64（本地操作）
        audio_base64 = self.file_to_base64(file_path)
        
        # 通过REST API执行转录（发送HTTP请求）
        return self.transcribe_base64(instance_id, audio_base64, language)
    
    def list_models(self) -> Dict[str, Any]:
        """
        列出当前用户的所有模型实例
        
        Returns:
            dict: 模型实例列表
            
        Raises:
            APIError: 如果获取失败
        """
        if not self.token:
            raise AuthError("请先登录")
        
        url = f'{self.base_url}/api/asr/models'
        response = self.session.get(url, headers=self._get_headers())
        return self._handle_response(response)
