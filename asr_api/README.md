# Whisper ASR Service

基于Flask的Whisper自动语音识别（ASR）RESTful API服务。

## 功能特性

- ✅ JWT身份认证
- ✅ 用户注册和登录
- ✅ 密码加密存储（bcrypt）
- ✅ 数据验证（marshmallow）
- ✅ RESTful API设计
- ✅ SQLite数据库
- ✅ 速率限制（60请求/分钟）
- ✅ Whisper ASR模型管理
- ✅ 音频转录支持
- ✅ Python客户端SDK

## 项目结构

```
qishi_beta/asr_api/
├── app/
│   ├── __init__.py          # 应用初始化
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py          # 用户模型
│   │   └── asr_instance.py  # ASR实例模型
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # 认证路由
│   │   └── asr.py           # ASR路由
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user_schema.py   # 用户数据验证
│   │   └── asr_schema.py    # ASR数据验证
│   └── utils/
│       ├── __init__.py
│       ├── model_manager.py # 模型管理器
│       ├── audio_utils.py   # 音频工具
│       └── rate_limiter.py  # 速率限制
├── client_sdk/              # Python客户端SDK
│   ├── src/
│   │   └── whisper_asr_client/
│   │       ├── __init__.py
│   │       ├── client.py
│   │       ├── exceptions.py
│   │       └── types.py
│   ├── tests/
│   ├── pyproject.toml
│   └── README.md
├── docs/                    # 文档
│   ├── api_docs.md
│   └── usage_examples.md
├── tests/                   # 测试
│   ├── test_auth.py
│   ├── test_asr_api.py
│   ├── test_model_manager.py
│   └── test_rate_limit.py
├── config.py                # 配置文件
├── run.py                   # 启动文件
├── requirements.txt         # 依赖包
└── README.md               # 说明文档
```

## 安装和运行

### 1. 安装依赖

```bash
cd qishi_beta/asr_api
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
flask init-db
```

### 3. 创建测试用户

```bash
flask create-test-user
```

### 4. 启动应用

```bash
python run.py
```

应用将在 http://localhost:5001 启动

**注意**: 如果端口5000被占用（如macOS的AirPlay Receiver），服务器会自动使用端口5001。

## API端点

### 认证相关
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录

### ASR相关
- `POST /api/asr/models` - 创建模型实例（需要JWT）
- `DELETE /api/asr/models/<instance_id>` - 删除模型实例（需要JWT）
- `GET /api/asr/models` - 列出所有模型实例（需要JWT）
- `POST /api/asr/transcribe` - 转录音频（需要JWT）

## 使用示例

### Python客户端SDK

```python
from whisper_asr_client import WhisperASRClient

# 初始化客户端
client = WhisperASRClient("http://localhost:5001")

# 登录
client.login("testuser", "password123")

# 创建模型实例
model = client.create_model("base")

# 转录音频文件
result = client.transcribe_file(model["instance_id"], "audio.wav")
print(result["text"])

# 删除模型实例
client.delete_model(model["instance_id"])
```

### curl示例

```bash
# 1. 登录
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'

# 2. 创建模型实例（使用返回的token）
curl -X POST http://localhost:5001/api/asr/models \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "base",
    "device": "cpu"
  }'

# 3. 转录音频（使用返回的instance_id）
curl -X POST http://localhost:5001/api/asr/transcribe \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "<instance_id>",
    "audio_base64": "<base64_encoded_audio>",
    "language": "en"
  }'
```

## 速率限制

所有API端点都实施了速率限制：
- **60 请求/分钟**
- 时间窗口：60秒

当触发速率限制时，返回 `429 Too Many Requests` 状态码，响应头包含：
- `X-RateLimit-Limit`: 速率限制上限
- `X-RateLimit-Remaining`: 剩余请求次数
- `X-RateLimit-Reset`: 重置时间（Unix时间戳）
- `Retry-After`: 重试等待时间（秒）

## 测试

运行测试：

```bash
pytest tests/
```

运行特定测试：

```bash
pytest tests/test_auth.py -v
pytest tests/test_asr_api.py -v
pytest tests/test_model_manager.py -v
pytest tests/test_rate_limit.py -v
```

运行客户端SDK测试：

```bash
pytest client_sdk/tests/ -v
```

运行集成测试：

```bash
python test_api.py
python test_transcription.py
python test_client_sdk.py
```

## 文档

详细文档请参考：
- [API文档](docs/api_docs.md)
- [使用示例](docs/usage_examples.md)
- [客户端SDK文档](client_sdk/README.md)
- [SSL配置文档](docs/ssl_configuration.md)
- [快速开始指南](QUICKSTART.md)
- [下一步计划](NEXT_STEPS.md)
- [修复总结](FIXES_SUMMARY.md)

## 技术栈

- Flask - Web框架
- Flask-JWT-Extended - JWT认证
- Flask-SQLAlchemy - 数据库ORM
- bcrypt - 密码加密
- marshmallow - 数据序列化和验证
- openai-whisper - Whisper ASR模型
- pytest - 测试框架

## 许可证

MIT License

