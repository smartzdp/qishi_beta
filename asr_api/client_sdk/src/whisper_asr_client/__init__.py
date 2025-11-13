"""
Whisper ASR Client SDK
Python客户端SDK for Whisper ASR Service
"""
from .client import WhisperASRClient
from .exceptions import APIError, AuthError, RateLimitError, NotFoundError

__all__ = ['WhisperASRClient', 'APIError', 'AuthError', 'RateLimitError', 'NotFoundError']
__version__ = '0.1.0'
