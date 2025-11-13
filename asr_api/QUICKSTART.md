# Quick Start Guide

快速开始指南 - 5分钟快速上手Whisper ASR Service

## 前置要求

- Python 3.8+
- pip
- 约2GB磁盘空间（用于下载Whisper模型）

## 快速开始

### 1. 安装依赖

```bash
cd qishi_beta/asr_api
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**注意**: 安装Whisper和torch可能需要几分钟时间。

### 2. 初始化数据库

```bash
source venv/bin/activate
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('✓ Database initialized')"
```

或者使用Flask命令：

```bash
export FLASK_APP=run.py
flask init-db
```

### 3. 创建测试用户

```bash
source venv/bin/activate
python -c "from app import create_app, db; from app.models.user import User; app = create_app(); app.app_context().push(); user = User(username='testuser', email='test@example.com'); user.set_password('password123'); db.session.add(user); db.session.commit(); print('✓ Test user created: username=testuser, password=password123')"
```

### 4. 启动服务器

```bash
source venv/bin/activate
python run.py
```

服务器将在 http://localhost:5001 启动

### 5. 测试API

在另一个终端中：

```bash
# 登录
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

## 使用Python客户端SDK

### 安装客户端SDK

```bash
cd qishi_beta/asr_api/client_sdk
pip install -e .
```

### 基本使用

```python
from whisper_asr_client import WhisperASRClient

# 初始化客户端
client = WhisperASRClient("http://localhost:5001")

# 登录
client.login("testuser", "password123")

# 创建模型实例（首次会下载模型，可能需要几分钟）
model = client.create_model("tiny")  # 使用tiny模型更快

# 转录音频文件
result = client.transcribe_file(model["instance_id"], "test_audio/test_audio_0.wav")
print(f"转录文本: {result['text']}")
print(f"检测到的语言: {result['language']}")
print(f"音频时长: {result['duration']} 秒")

# 删除模型实例
client.delete_model(model["instance_id"])
```

## 下载测试音频

```bash
cd qishi_beta/asr_api
source venv/bin/activate
python download_test_audio.py
```

这将下载3个测试音频文件到 `test_audio/` 目录。

## 运行测试

```bash
cd qishi_beta/asr_api
source venv/bin/activate
pytest tests/ -v
```

## 常见问题

### 1. 端口5000被占用

如果端口5000被占用（如macOS的AirPlay Receiver），服务器会自动使用端口5001。或者设置环境变量：

```bash
export PORT=5001
python run.py
```

### 2. 模型下载失败

如果Whisper模型下载失败（SSL证书问题），可以：
- 检查网络连接
- 手动下载模型并放置到 `~/.cache/whisper/` 目录
- 使用VPN或代理

### 3. 内存不足

如果内存不足，可以使用更小的模型：
- `tiny` - 最快，最省内存
- `base` - 平衡速度和准确度
- `small` - 更好的准确度
- `medium` - 高准确度
- `large` - 最高准确度，最慢

### 4. 认证失败

确保：
- 用户名和密码正确
- 服务器正在运行
- 使用正确的端口（默认5001）
- JWT token未过期

## 下一步

- 查看 [API文档](docs/api_docs.md) 了解完整的API参考
- 查看 [使用示例](docs/usage_examples.md) 了解更多用法
- 查看 [客户端SDK文档](client_sdk/README.md) 了解SDK详情

## 技术支持

如有问题，请查看：
- [README.md](README.md) - 项目概述
- [docs/api_docs.md](docs/api_docs.md) - API文档
- [docs/usage_examples.md](docs/usage_examples.md) - 使用示例

