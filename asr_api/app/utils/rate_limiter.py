"""
速率限制工具模块
实现基于用户ID或IP的固定窗口速率限制
"""
from functools import wraps
from flask import request, jsonify, make_response, Response
from flask_jwt_extended import get_jwt_identity
from config import Config
import time
import logging

logger = logging.getLogger(__name__)

# 速率限制配置
RATE_LIMIT_WINDOW = Config.RATE_LIMIT_WINDOW  # 时间窗口：60秒（1分钟）
RATE_LIMIT_MAX_REQUESTS = Config.RATE_LIMIT_MAX_REQUESTS  # 最大请求数：60次/分钟

# 存储请求计数和最后重置时间
# 格式: {key: {'count': int, 'reset_time': float}}
rate_limit_store = {}

def get_rate_limit_key():
    """
    获取速率限制的键（优先使用JWT用户ID，否则使用IP地址）
    
    Returns:
        str: 速率限制键
    """
    try:
        # 尝试从JWT token中获取用户ID
        user_id = get_jwt_identity()
        if user_id:
            return f"user:{user_id}"
    except Exception:
        # 如果无法获取JWT identity，使用IP地址
        pass
    
    # 使用IP地址作为键
    return f"ip:{request.remote_addr or 'unknown'}"

def rate_limit(f):
    """
    速率限制装饰器
    基于固定窗口算法，按用户ID或IP进行限制
    
    Args:
        f: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        global rate_limit_store
        
        # 获取速率限制键
        key = get_rate_limit_key()
        current_time = time.time()
        
        # 获取或初始化该键的速率限制信息
        if key not in rate_limit_store:
            rate_limit_store[key] = {
                'count': 0,
                'reset_time': current_time + RATE_LIMIT_WINDOW
            }
        
        limit_info = rate_limit_store[key]
        
        # 检查是否需要重置计数
        if current_time >= limit_info['reset_time']:
            limit_info['count'] = 0
            limit_info['reset_time'] = current_time + RATE_LIMIT_WINDOW
        
        # 检查是否超过限制
        if limit_info['count'] >= RATE_LIMIT_MAX_REQUESTS:
            logger.warning(f"速率限制触发: {key}")
            
            # 计算剩余时间
            remaining_time = int(limit_info['reset_time'] - current_time)
            
            response = make_response(jsonify({
                'error': 'rate_limit_exceeded',
                'message': f'速率限制已触发，请等待 {remaining_time} 秒后重试',
                'retry_after': remaining_time
            }), 429)
            
            # 添加速率限制头信息
            response.headers['X-RateLimit-Limit'] = str(RATE_LIMIT_MAX_REQUESTS)
            response.headers['X-RateLimit-Remaining'] = '0'
            response.headers['X-RateLimit-Reset'] = str(int(limit_info['reset_time']))
            response.headers['Retry-After'] = str(remaining_time)
            
            return response
        
        # 增加请求计数
        limit_info['count'] += 1
        
        # 执行原始函数
        result = f(*args, **kwargs)
        
        # 处理响应结果
        # 如果结果已经是 Response 对象，直接使用
        if isinstance(result, Response):
            response = result
        # 如果结果是元组 (response, status_code) 或 (data, status_code)
        elif isinstance(result, tuple) and len(result) == 2:
            response_data, status_code = result
            if isinstance(response_data, Response):
                # 如果已经是Response对象，使用它，但确保状态码正确
                response = response_data
                # 如果元组中提供了状态码，使用它（优先级更高）
                if isinstance(status_code, int):
                    response.status_code = status_code
            elif isinstance(response_data, dict):
                # 如果是字典，创建JSON响应
                response = make_response(jsonify(response_data), status_code)
            elif isinstance(response_data, str):
                # 如果是字符串（如空字符串用于204），创建响应
                response = make_response(response_data, status_code)
            else:
                # 处理其他情况
                response = make_response(jsonify(response_data), status_code)
        else:
            # 如果是字典或其他可序列化对象，默认状态码200
            response = make_response(jsonify(result), 200)
        
        # 添加速率限制头信息
        remaining = max(0, RATE_LIMIT_MAX_REQUESTS - limit_info['count'])
        response.headers['X-RateLimit-Limit'] = str(RATE_LIMIT_MAX_REQUESTS)
        response.headers['X-RateLimit-Remaining'] = str(remaining)
        response.headers['X-RateLimit-Reset'] = str(int(limit_info['reset_time']))
        
        return response
    
    return decorated
