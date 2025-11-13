"""
音频工具模块
处理音频文件的base64编码和解码
"""
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def base64_to_audio_bytes(base64_string: str) -> bytes:
    """
    将base64编码的字符串转换为音频字节数据
    
    Args:
        base64_string: base64编码的音频字符串
        
    Returns:
        bytes: 音频字节数据
        
    Raises:
        ValueError: 如果base64字符串无效
    """
    try:
        # 移除可能的data URI前缀（如 "data:audio/wav;base64,"）
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # 解码base64字符串
        audio_bytes = base64.b64decode(base64_string)
        logger.debug(f"Base64解码成功，音频数据大小: {len(audio_bytes)} 字节")
        return audio_bytes
        
    except Exception as e:
        logger.error(f"Base64解码失败: {e}")
        raise ValueError(f"无效的base64字符串: {str(e)}")

def file_to_base64(file_path: str) -> str:
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
            logger.debug(f"文件编码成功: {file_path}, 大小: {len(audio_bytes)} 字节")
            return base64_string
            
    except FileNotFoundError:
        logger.error(f"文件不存在: {file_path}")
        raise FileNotFoundError(f"文件不存在: {file_path}")
    except Exception as e:
        logger.error(f"文件读取失败: {e}")
        raise IOError(f"无法读取文件: {str(e)}")
