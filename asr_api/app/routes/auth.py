"""
认证路由模块
处理用户注册、登录相关的API端点
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.schemas.user_schema import UserSchema, UserLoginSchema
import logging

# 创建认证蓝图，URL前缀为 /api/auth
auth_bp = Blueprint('auth', __name__)

# 初始化Schema实例用于数据验证
user_schema = UserSchema()
login_schema = UserLoginSchema()

# 配置日志
logger = logging.getLogger(__name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册接口
    POST /api/auth/register
    
    请求体示例:
    {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "confirm_password": "password123"
    }
    
    Returns:
        JSON: 注册成功信息或错误信息
    """
    logger.debug(f"注册请求: {request.get_json()}")
    
    try:
        # 验证并加载请求数据
        data = user_schema.load(request.get_json())
        logger.debug("数据验证通过")
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=data['username']).first():
            logger.warning(f"用户名已存在: {data['username']}")
            return jsonify({'error': '用户名已存在'}), 409  # 409 Conflict
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=data['email']).first():
            logger.warning(f"邮箱已存在: {data['email']}")
            return jsonify({'error': '邮箱已存在'}), 409  # 409 Conflict
        
        # 创建新用户实例
        user = User(username=data['username'], email=data['email'])
        # 设置加密后的密码
        user.set_password(data['password'])
        
        # 保存到数据库
        db.session.add(user)
        db.session.commit()
        logger.info(f"用户注册成功: {user.username}")
        
        # 返回成功响应
        return jsonify({
            'message': '用户注册成功',
            'user': user.to_dict()  # 转换为字典格式
        }), 201  # 201 Created
        
    except Exception as e:
        logger.error(f"注册失败: {e}")
        # 处理验证错误或其他异常
        if hasattr(e, 'messages'):
            return jsonify({'error': str(e.messages)}), 400
        return jsonify({'error': str(e)}), 400  # 400 Bad Request

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录接口
    POST /api/auth/login
    
    请求体示例:
    {
        "username": "testuser",
        "password": "password123"
    }
    
    Returns:
        JSON: 登录成功信息包含JWT token，或错误信息
    """
    logger.debug(f"登录请求: {request.get_json()}")
    
    try:
        # 验证并加载登录数据
        data = login_schema.load(request.get_json())
        logger.debug("登录数据验证通过")
        
        # 根据用户名查找用户
        user = User.query.filter_by(username=data['username']).first()
        
        # 验证用户是否存在和密码是否正确
        if not user or not user.check_password(data['password']):
            logger.warning(f"登录失败: 用户名或密码错误 - {data['username']}")
            return jsonify({'error': '用户名或密码错误'}), 401  # 401 Unauthorized
        
        # 创建JWT访问令牌，用户ID作为身份标识（必须转换为字符串）
        access_token = create_access_token(identity=str(user.id))
        logger.info(f"用户登录成功: {user.username}")
        
        # 返回成功响应包含JWT token
        return jsonify({
            'message': '登录成功',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200  # 200 OK
        
    except Exception as e:
        logger.error(f"登录失败: {e}")
        # 处理验证错误或其他异常
        if hasattr(e, 'messages'):
            return jsonify({'error': str(e.messages)}), 400
        return jsonify({'error': str(e)}), 400  # 400 Bad Request
