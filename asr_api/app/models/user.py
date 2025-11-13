"""
用户数据模型模块
定义用户数据库表结构和相关操作方法
"""
from app import db
import bcrypt
from datetime import datetime

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """
        设置用户密码并进行bcrypt加密
        
        Args:
            password (str): 明文密码
        """
        # 生成随机的salt
        salt = bcrypt.gensalt()
        # 使用bcrypt加密密码，并存储哈希值
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        """
        验证用户输入的密码是否正确
        
        Args:
            password (str): 待验证的明文密码
            
        Returns:
            bool: 密码是否正确
        """
        # 使用bcrypt验证密码
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self):
        """
        将用户对象转换为字典格式，用于JSON序列化
        
        Returns:
            dict: 包含用户信息的字典
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
