"""
应用启动文件
包含数据库初始化命令和测试用户创建
"""
from app import create_app, db
from app.models.user import User
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = create_app()

@app.cli.command('init-db')
def init_db():
    """初始化数据库"""
    try:
        with app.app_context():
            # 确保所有模型都被导入
            from app.models.user import User
            from app.models.asr_instance import ASRInstance
            
            # 创建所有表
            db.create_all()
            logger.info("数据库表创建成功")
            print('数据库初始化完成')
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        print(f'数据库初始化失败: {e}')
        raise

@app.cli.command('create-test-user')
def create_test_user():
    """创建测试用户"""
    try:
        with app.app_context():
            # 检查是否已存在测试用户
            if not User.query.filter_by(username='testuser').first():
                user = User(username='testuser', email='test@example.com')
                user.set_password('password123')
                db.session.add(user)
                db.session.commit()
                logger.info("测试用户创建成功")
                print('测试用户创建成功: username=testuser, password=password123')
            else:
                logger.warning("测试用户已存在")
                print('测试用户已存在')
    except Exception as e:
        logger.error(f"创建测试用户失败: {e}")
        print(f'创建测试用户失败: {e}')
        raise

if __name__ == '__main__':
    import os
    # 从环境变量获取端口，默认为5001
    port = int(os.environ.get('PORT', 5001))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    logger.info("启动Flask应用...")
    logger.info(f"监听地址: {host}:{port}")
    logger.info(f"调试模式: {debug}")
    try:
        app.run(host=host, port=port, debug=debug)
        logger.info("Flask应用正常启动")
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        print(f'应用启动失败: {e}')
