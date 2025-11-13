"""
用户数据验证Schema模块
使用marshmallow库进行数据序列化、反序列化和验证
"""
from marshmallow import Schema, fields, validate, validates_schema, ValidationError

class UserSchema(Schema):
    """用户注册数据验证Schema"""
    # id字段：只用于输出（序列化），不用于输入（反序列化）
    id = fields.Int(dump_only=True)
    
    # 用户名字段：必填，长度限制3-80字符
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    
    # 邮箱字段：必填，自动验证邮箱格式
    email = fields.Email(required=True)
    
    # 密码字段：必填，最小长度6字符，只用于输入（不输出到响应）
    password = fields.Str(required=True, validate=validate.Length(min=6), load_only=True)
    
    # 确认密码字段：必填，只用于输入
    confirm_password = fields.Str(required=True, load_only=True)
    
    # 创建时间字段：只用于输出
    created_at = fields.DateTime(dump_only=True)
    
    # 更新时间字段：只用于输出
    updated_at = fields.DateTime(dump_only=True)
    
    @validates_schema
    def validate_passwords(self, data, **kwargs):
        """自定义验证方法：验证密码和确认密码是否匹配"""
        if data.get('password') != data.get('confirm_password'):
            # 如果密码不匹配，抛出验证错误
            raise ValidationError('密码确认不匹配', 'confirm_password')

class UserLoginSchema(Schema):
    """用户登录数据验证Schema"""
    # 登录用户名：必填
    username = fields.Str(required=True)
    
    # 登录密码：必填
    password = fields.Str(required=True)
