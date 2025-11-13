"""
类型定义模块
定义API客户端使用的类型
"""
from typing import Optional, Dict, Any

class ModelInfo:
    """模型信息类型"""
    def __init__(self, instance_id: str, model_name: str, device: str):
        self.instance_id = instance_id
        self.model_name = model_name
        self.device = device
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'instance_id': self.instance_id,
            'model_name': self.model_name,
            'device': self.device
        }

class TranscribeResult:
    """转录结果类型"""
    def __init__(self, text: str, language: str, duration: float, segments: list):
        self.text = text
        self.language = language
        self.duration = duration
        self.segments = segments
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'text': self.text,
            'language': self.language,
            'duration': self.duration,
            'segments': self.segments
        }
