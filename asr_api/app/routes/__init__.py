"""
路由模块初始化
"""
from app.routes.auth import auth_bp
from app.routes.asr import asr_bp

__all__ = ['auth_bp', 'asr_bp']
