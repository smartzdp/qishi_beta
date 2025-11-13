"""
ASR路由模块
处理ASR模型创建、删除和转录相关的API端点
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.asr_instance import ASRInstance
from app.schemas.asr_schema import CreateModelSchema, TranscribeSchema
from app.utils.rate_limiter import rate_limit
from app.utils.model_manager import ModelManager
from app.utils.audio_utils import base64_to_audio_bytes
import logging

# 创建ASR蓝图，URL前缀为 /api/asr
asr_bp = Blueprint('asr', __name__)

# 初始化Schema实例用于数据验证
create_model_schema = CreateModelSchema()
transcribe_schema = TranscribeSchema()

# 初始化模型管理器
model_manager = ModelManager()

# 配置日志
logger = logging.getLogger(__name__)

@asr_bp.route('/models', methods=['POST'])
@jwt_required()
@rate_limit
def create_model():
    """
    创建ASR模型实例
    POST /api/asr/models
    
    请求头:
        Authorization: Bearer <jwt_token>
    
    请求体示例:
    {
        "model_name": "base",
        "device": "cpu"
    }
    
    Returns:
        JSON: 模型实例信息
    """
    logger.debug(f"创建模型请求: {request.get_json()}")
    
    try:
        # 验证并加载请求数据
        data = create_model_schema.load(request.get_json())
        logger.debug("数据验证通过")
        
        # 获取用户ID
        user_id = int(get_jwt_identity())
        
        # 获取模型名称和设备
        model_name = data.get('model_name', 'base')
        device = data.get('device', 'cpu')
        
        # 创建模型实例
        instance_id = model_manager.create_model(model_name, device)
        logger.info(f"模型实例创建成功: {instance_id}")
        
        # 可选：将实例信息保存到数据库
        try:
            asr_instance = ASRInstance(
                instance_id=instance_id,
                user_id=user_id,
                model_name=model_name,
                device=device
            )
            db.session.add(asr_instance)
            db.session.commit()
            logger.debug(f"模型实例信息已保存到数据库: {instance_id}")
        except Exception as e:
            logger.warning(f"保存模型实例信息到数据库失败: {e}")
            # 继续执行，不影响模型创建
        
        # 返回成功响应
        return jsonify({
            'instance_id': instance_id,
            'model_name': model_name,
            'device': device
        }), 201  # 201 Created
        
    except Exception as e:
        logger.error(f"创建模型失败: {e}")
        # 处理验证错误或其他异常
        if hasattr(e, 'messages'):
            return jsonify({'error': str(e.messages)}), 400
        return jsonify({'error': str(e)}), 400  # 400 Bad Request

@asr_bp.route('/models/<instance_id>', methods=['DELETE'])
@jwt_required()
@rate_limit
def delete_model(instance_id):
    """
    删除ASR模型实例
    DELETE /api/asr/models/<instance_id>
    
    请求头:
        Authorization: Bearer <jwt_token>
    
    Returns:
        204 No Content
    """
    logger.debug(f"删除模型请求: {instance_id}")
    
    try:
        # 获取用户ID
        user_id = int(get_jwt_identity())
        
        # 检查模型实例是否存在
        model_info = model_manager.get_model(instance_id)
        if not model_info:
            logger.warning(f"模型实例不存在: {instance_id}")
            return jsonify({'error': '模型实例不存在'}), 404  # 404 Not Found
        
        # 可选：检查数据库中的所有权
        try:
            asr_instance = ASRInstance.query.filter_by(instance_id=instance_id, user_id=user_id).first()
            if asr_instance:
                db.session.delete(asr_instance)
                db.session.commit()
                logger.debug(f"模型实例信息已从数据库删除: {instance_id}")
        except Exception as e:
            logger.warning(f"从数据库删除模型实例信息失败: {e}")
            # 继续执行，不影响模型删除
        
        # 删除模型实例（可能抛出KeyError）
        try:
            model_manager.delete_model(instance_id)
            logger.info(f"模型实例删除成功: {instance_id}")
        except KeyError as e:
            # 如果模型不存在（可能在检查后和删除之间被删除），返回404
            logger.warning(f"删除模型失败: {e}")
            return jsonify({'error': str(e)}), 404  # 404 Not Found
        
        # 返回204 No Content
        return '', 204  # 204 No Content
        
    except Exception as e:
        logger.error(f"删除模型失败: {e}")
        return jsonify({'error': str(e)}), 400  # 400 Bad Request

@asr_bp.route('/transcribe', methods=['POST'])
@jwt_required()
@rate_limit
def transcribe():
    """
    转录音频
    POST /api/asr/transcribe
    
    请求头:
        Authorization: Bearer <jwt_token>
    
    请求体示例:
    {
        "instance_id": "uuid",
        "audio_base64": "base64_encoded_audio",
        "language": "en"
    }
    
    Returns:
        JSON: 转录结果
    """
    logger.debug(f"转录请求: instance_id={request.get_json().get('instance_id')}")
    
    try:
        # 验证并加载请求数据
        data = transcribe_schema.load(request.get_json())
        logger.debug("数据验证通过")
        
        # 获取用户ID
        user_id = int(get_jwt_identity())
        
        # 获取参数
        instance_id = data.get('instance_id')
        audio_base64 = data.get('audio_base64')
        language = data.get('language')
        
        # 将base64字符串转换为音频字节
        audio_bytes = base64_to_audio_bytes(audio_base64)
        logger.debug(f"音频数据解码成功，大小: {len(audio_bytes)} 字节")
        
        # 执行转录（可能抛出KeyError或其他异常）
        result = model_manager.transcribe(instance_id, audio_bytes, language)
        logger.info(f"转录成功: {instance_id}, 文本长度: {len(result.get('text', ''))}")
        
        # 返回转录结果
        return jsonify({
            'text': result.get('text', ''),
            'segments': result.get('segments', []),
            'language': result.get('language', ''),
            'duration': result.get('duration', 0.0)
        }), 200  # 200 OK
        
    except KeyError as e:
        # 捕获KeyError（模型实例不存在）
        error_msg = str(e)
        if '模型实例不存在' in error_msg or '不存在' in error_msg:
            logger.error(f"转录失败: {error_msg}")
            return jsonify({'error': error_msg}), 404  # 404 Not Found
        else:
            logger.error(f"转录失败: {error_msg}")
            return jsonify({'error': error_msg}), 400  # 400 Bad Request
    except ValueError as e:
        logger.error(f"转录失败: {e}")
        return jsonify({'error': str(e)}), 400  # 400 Bad Request
    except Exception as e:
        logger.error(f"转录失败: {e}")
        # 处理验证错误或其他异常
        if hasattr(e, 'messages'):
            return jsonify({'error': str(e.messages)}), 400
        # 检查是否是模型不存在的错误
        error_msg = str(e)
        if '模型实例不存在' in error_msg or '不存在' in error_msg:
            return jsonify({'error': error_msg}), 404  # 404 Not Found
        return jsonify({'error': error_msg}), 400  # 400 Bad Request

@asr_bp.route('/models', methods=['GET'])
@jwt_required()
@rate_limit
def list_models():
    """
    列出当前用户的所有模型实例
    GET /api/asr/models
    
    请求头:
        Authorization: Bearer <jwt_token>
    
    Returns:
        JSON: 模型实例列表
    """
    logger.debug("列出模型实例请求")
    
    try:
        # 获取用户ID
        user_id = int(get_jwt_identity())
        
        # 从数据库获取用户的模型实例
        asr_instances = ASRInstance.query.filter_by(user_id=user_id).all()
        
        # 构建响应
        models = []
        for instance in asr_instances:
            # 检查模型是否仍然存在于ModelManager中
            model_info = model_manager.get_model(instance.instance_id)
            if model_info:
                models.append({
                    'instance_id': instance.instance_id,
                    'model_name': instance.model_name,
                    'device': instance.device,
                    'created_at': instance.created_at.isoformat() if instance.created_at else None
                })
        
        logger.info(f"列出模型实例成功: {len(models)} 个实例")
        
        # 返回模型实例列表
        return jsonify({
            'models': models,
            'count': len(models)
        }), 200  # 200 OK
        
    except Exception as e:
        logger.error(f"列出模型实例失败: {e}")
        return jsonify({'error': str(e)}), 400  # 400 Bad Request
