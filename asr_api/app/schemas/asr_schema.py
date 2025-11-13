"""
ASR数据验证Schema模块
使用marshmallow库进行ASR API的数据序列化、反序列化和验证
"""
from marshmallow import Schema, fields, validate

class CreateModelSchema(Schema):
    """创建模型请求Schema"""
    model_name = fields.Str(
        required=True,
        validate=validate.OneOf(['tiny', 'base', 'small', 'medium', 'large']),
        metadata={'description': 'Whisper模型名称'}
    )
    device = fields.Str(
        required=False,
        validate=validate.OneOf(['cpu', 'cuda']),
        metadata={'description': '设备类型（cpu或cuda）'}
    )

class TranscribeSchema(Schema):
    """转录请求Schema"""
    instance_id = fields.Str(
        required=True,
        metadata={'description': '模型实例ID'}
    )
    audio_base64 = fields.Str(
        required=True,
        metadata={'description': 'base64编码的音频数据'}
    )
    language = fields.Str(
        required=False,
        validate=validate.Length(min=2, max=5),
        metadata={'description': '可选的语言代码（如 "en", "zh"）'}
    )

class ModelResponseSchema(Schema):
    """模型创建响应Schema"""
    instance_id = fields.Str(required=True, metadata={'description': '模型实例ID'})
    model_name = fields.Str(required=True, metadata={'description': '模型名称'})
    device = fields.Str(required=True, metadata={'description': '设备类型'})

class TranscribeResponseSchema(Schema):
    """转录响应Schema"""
    text = fields.Str(required=True, metadata={'description': '转录文本'})
    language = fields.Str(required=True, metadata={'description': '检测到的语言'})
    duration = fields.Float(required=True, metadata={'description': '音频时长（秒）'})
    segments = fields.List(
        fields.Dict(),
        required=True,
        metadata={'description': '分段转录结果'}
    )
