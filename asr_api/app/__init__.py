"""
应用初始化模块
设置Flask应用和扩展，包含调试配置
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from config import Config
import logging

db = SQLAlchemy()
jwt = JWTManager()

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 输出配置信息（调试用）
    logger.debug(f"数据库连接: {app.config['SQLALCHEMY_DATABASE_URI']}")
    logger.debug(f"JWT密钥: {app.config['JWT_SECRET_KEY']}")
    
    # 初始化扩展
    try:
        db.init_app(app)
        logger.debug("SQLAlchemy初始化成功")
    except Exception as e:
        logger.error(f"SQLAlchemy初始化失败: {e}")
        raise
    
    try:
        jwt.init_app(app)
        logger.debug("JWTManager初始化成功")
    except Exception as e:
        logger.error(f"JWTManager初始化失败: {e}")
        raise
    
    # 注册蓝图
    try:
        from app.routes.auth import auth_bp
        from app.routes.asr import asr_bp
        
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(asr_bp, url_prefix='/api/asr')
        logger.debug("蓝图注册成功")
        
    except Exception as e:
        logger.error(f"蓝图注册失败: {e}")
        raise
    
    return app
