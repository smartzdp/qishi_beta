"""
应用配置模块
包含数据库连接、JWT设置等配置信息
"""
import os
from datetime import timedelta

class Config:
    """应用配置类"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # 数据库配置 - 使用SQLite数据库（也可以改为MySQL）
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///whisper_asr.db'
    
    # 关闭SQLAlchemy修改跟踪（性能优化）
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    
    # JWT访问令牌过期时间：1小时
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # JWT刷新令牌过期时间：30天
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # JWT令牌位置：请求头
    JWT_TOKEN_LOCATION = ['headers']
    
    # JWT请求头名称
    JWT_HEADER_NAME = 'Authorization'
    
    # JWT令牌类型
    JWT_HEADER_TYPE = 'Bearer'
    
    # Rate limiting configuration
    RATE_LIMIT_WINDOW = 60  # 时间窗口：60秒（1分钟）
    RATE_LIMIT_MAX_REQUESTS = 60  # 最大请求数：60次/分钟
