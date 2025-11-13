"""
ASR实例数据模型模块
定义ASR实例数据库表结构（可选，用于持久化）
"""
from app import db
from datetime import datetime

class ASRInstance(db.Model):
    """
    ASR实例模型（可选，用于持久化模型实例信息）
    注意：实际的模型实例存储在ModelManager的内存中
    """
    __tablename__ = 'asr_instances'
    
    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    model_name = db.Column(db.String(50), nullable=False)
    device = db.Column(db.String(10), nullable=False, default='cpu')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ASRInstance {self.instance_id}>'
    
    def to_dict(self):
        """
        将ASR实例对象转换为字典格式，用于JSON序列化
        
        Returns:
            dict: 包含ASR实例信息的字典
        """
        return {
            'id': self.id,
            'instance_id': self.instance_id,
            'user_id': self.user_id,
            'model_name': self.model_name,
            'device': self.device,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
