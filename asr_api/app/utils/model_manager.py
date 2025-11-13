"""
模型管理器模块
管理Whisper ASR模型实例的创建、删除和转录
"""
import uuid
import logging
import whisper
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Whisper模型管理器（单例模式）
    管理多个模型实例，支持创建、删除和转录
    """
    _instance = None
    _models: Dict[str, Dict[str, Any]] = {}
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance
    
    def create_model(self, model_name: str, device: str = "cpu") -> str:
        """
        创建Whisper模型实例
        
        Args:
            model_name: Whisper模型名称（如 "base", "small", "medium", "large"）
            device: 设备类型（"cpu" 或 "cuda"）
            
        Returns:
            str: 模型实例ID
            
        Raises:
            Exception: 如果模型加载失败
        """
        try:
            logger.info(f"正在加载模型: {model_name}, 设备: {device}")
            
            # 加载Whisper模型
            # 注意：首次加载会从网上下载模型，可能需要一些时间
            import ssl
            import os
            import urllib.request
            
            # SSL证书处理配置
            # 优先使用环境变量配置的SSL证书路径或验证设置
            is_production = os.environ.get('FLASK_ENV') == 'production' or \
                           os.environ.get('ENVIRONMENT') == 'production'
            
            disable_ssl_verification = os.environ.get('DISABLE_SSL_VERIFICATION', '').lower() == 'true'
            ca_cert_path = os.environ.get('SSL_CA_CERT_PATH') or os.environ.get('REQUESTS_CA_BUNDLE')
            
            # 保存原始SSL上下文
            original_context = ssl._create_default_https_context
            
            try:
                # 生产环境：优先使用正确的SSL证书
                if is_production and not disable_ssl_verification:
                    if ca_cert_path and os.path.exists(ca_cert_path):
                        # 使用自定义CA证书
                        logger.info(f"使用自定义CA证书: {ca_cert_path}")
                        ssl_context = ssl.create_default_context(cafile=ca_cert_path)
                        ssl._create_default_https_context = lambda: ssl_context
                        os.environ['REQUESTS_CA_BUNDLE'] = ca_cert_path
                        os.environ['SSL_CERT_FILE'] = ca_cert_path
                    else:
                        # 尝试使用certifi证书包
                        try:
                            import certifi
                            ca_cert_path = certifi.where()
                            logger.info(f"使用certifi CA证书: {ca_cert_path}")
                            ssl_context = ssl.create_default_context(cafile=ca_cert_path)
                            ssl._create_default_https_context = lambda: ssl_context
                            os.environ['REQUESTS_CA_BUNDLE'] = ca_cert_path
                            os.environ['SSL_CERT_FILE'] = ca_cert_path
                        except ImportError:
                            # certifi未安装，使用系统默认证书
                            logger.info("使用系统默认SSL证书")
                            ssl._create_default_https_context = original_context
                    
                    # 尝试加载模型（使用正确的SSL证书）
                    model = whisper.load_model(model_name, device=device)
                    
                elif disable_ssl_verification:
                    # 开发/测试环境：禁用SSL验证（仅在明确配置时）
                    logger.warning("SSL证书验证已禁用（仅用于开发/测试环境）")
                    ssl._create_default_https_context = ssl._create_unverified_context
                    model = whisper.load_model(model_name, device=device)
                    
                else:
                    # 默认：先尝试使用系统默认SSL证书
                    try:
                        ssl._create_default_https_context = original_context
                        model = whisper.load_model(model_name, device=device)
                    except Exception as ssl_error:
                        # 如果SSL验证失败，在非生产环境中允许禁用验证
                        error_msg = str(ssl_error)
                        if ("CERTIFICATE_VERIFY_FAILED" in error_msg or "SSL" in error_msg.upper()) and not is_production:
                            logger.warning(f"SSL证书验证失败，禁用验证（仅用于开发/测试）: {ssl_error}")
                            ssl._create_default_https_context = ssl._create_unverified_context
                            model = whisper.load_model(model_name, device=device)
                        else:
                            # 恢复原始上下文并重新抛出异常
                            ssl._create_default_https_context = original_context
                            raise
                
                # 恢复原始SSL上下文（如果已修改）
                if ssl._create_default_https_context != original_context and not disable_ssl_verification:
                    ssl._create_default_https_context = original_context
                    
            except Exception as ssl_error:
                # 恢复原始SSL上下文
                ssl._create_default_https_context = original_context
                raise
            
            # 生成唯一的实例ID
            instance_id = str(uuid.uuid4())
            
            # 存储模型实例
            self._models[instance_id] = {
                'instance_id': instance_id,
                'model_name': model_name,
                'device': device,
                'model': model,
                'extra_config': {}
            }
            
            logger.info(f"模型加载成功: {instance_id}")
            return instance_id
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            error_msg = str(e)
            # 提供更友好的错误信息
            if "SSL" in error_msg or "CERTIFICATE" in error_msg:
                error_msg = f"模型下载失败（SSL证书问题）: {error_msg}. 请检查网络连接或手动下载模型。"
            elif "Connection" in error_msg or "timeout" in error_msg.lower():
                error_msg = f"模型下载失败（网络问题）: {error_msg}. 请检查网络连接。"
            raise Exception(f"无法加载模型 {model_name}: {error_msg}")
    
    def delete_model(self, instance_id: str) -> bool:
        """
        删除模型实例
        
        Args:
            instance_id: 模型实例ID
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            KeyError: 如果模型实例不存在
        """
        if instance_id not in self._models:
            logger.warning(f"模型实例不存在: {instance_id}")
            raise KeyError(f"模型实例不存在: {instance_id}")
        
        # 删除模型实例
        del self._models[instance_id]
        logger.info(f"模型实例已删除: {instance_id}")
        return True
    
    def get_model(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        获取模型实例信息
        
        Args:
            instance_id: 模型实例ID
            
        Returns:
            dict: 模型实例信息，如果不存在则返回None
        """
        return self._models.get(instance_id)
    
    def transcribe(self, instance_id: str, audio_bytes: bytes, language: Optional[str] = None) -> Dict[str, Any]:
        """
        使用模型实例进行音频转录
        
        Args:
            instance_id: 模型实例ID
            audio_bytes: 音频字节数据
            language: 可选的语言代码（如 "en", "zh"）
            
        Returns:
            dict: 转录结果，包含text, language, segments, duration
            
        Raises:
            KeyError: 如果模型实例不存在
            Exception: 如果转录失败
        """
        if instance_id not in self._models:
            logger.warning(f"模型实例不存在: {instance_id}")
            raise KeyError(f"模型实例不存在: {instance_id}")
        
        model_info = self._models[instance_id]
        model = model_info['model']
        device = model_info.get('device', 'cpu')
        
        logger.info(f"开始转录: {instance_id}")
        
        # Save audio bytes to a temporary file
        # Whisper's transcribe method accepts file paths
        import tempfile
        import os
        
        # Create a temporary file to store audio bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name
        
        try:
            # Execute transcription using Whisper's transcribe method
            # This handles all audio format conversion automatically
            if language:
                result = model.transcribe(tmp_file_path, language=language)
            else:
                result = model.transcribe(tmp_file_path)
            
            # Extract transcription results
            text = result.get('text', '').strip()
            detected_language = result.get('language', '')
            segments = result.get('segments', [])
            
            # Calculate audio duration from segments
            duration = 0.0
            if segments:
                duration = segments[-1].get('end', 0.0)
            else:
                # Fallback: load audio to get duration
                try:
                    audio = whisper.load_audio(tmp_file_path)
                    # Whisper processes audio at 16kHz
                    duration = len(audio) / 16000.0 if hasattr(audio, '__len__') else 0.0
                except Exception:
                    duration = 0.0
            
            logger.info(f"转录完成: {instance_id}, 文本长度: {len(text)}, 语言: {detected_language}")
            
            return {
                'text': text,
                'language': detected_language,
                'segments': segments,
                'duration': duration
            }
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_file_path)
            except Exception as e:
                logger.warning(f"无法删除临时文件: {e}")
    
    def list_models(self) -> list:
        """
        列出所有模型实例
        
        Returns:
            list: 模型实例信息列表
        """
        return [
            {
                'instance_id': info['instance_id'],
                'model_name': info['model_name'],
                'device': info['device']
            }
            for info in self._models.values()
        ]
