# Whisper ASR Service API Documentation

## 概述

Whisper ASR Service 是一个基于Flask的RESTful API服务，提供Whisper自动语音识别（ASR）功能。服务支持JWT认证、速率限制和模型实例管理。

## 基础URL

```
http://localhost:5001
```

**注意**: 默认端口是5001（如果端口5000被占用，如macOS的AirPlay Receiver）。可以通过环境变量或配置文件修改端口。

## 认证

所有ASR API端点都需要JWT认证。在请求头中包含：

```
Authorization: Bearer <jwt_token>
```

## 认证API

### 用户注册

**POST** `/api/auth/register`

注册新用户。

**请求体：**
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123",
  "confirm_password": "password123"
}
```

**响应：**
```json
{
  "message": "用户注册成功",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
}
```

**状态码：**
- `201 Created`: 注册成功
- `400 Bad Request`: 请求数据无效
- `409 Conflict`: 用户名或邮箱已存在

### 用户登录

**POST** `/api/auth/login`

用户登录，获取JWT token。

**请求体：**
```json
{
  "username": "testuser",
  "password": "password123"
}
```

**响应：**
```json
{
  "message": "登录成功",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
}
```

**状态码：**
- `200 OK`: 登录成功
- `401 Unauthorized`: 用户名或密码错误
- `400 Bad Request`: 请求数据无效

## ASR API

### 创建模型实例

**POST** `/api/asr/models`

创建Whisper模型实例。

**请求头：**
```
Authorization: Bearer <jwt_token>
```

**请求体：**
```json
{
  "model_name": "base",
  "device": "cpu"
}
```

**参数说明：**
- `model_name` (必填): 模型名称，可选值：`tiny`, `base`, `small`, `medium`, `large`
- `device` (可选): 设备类型，可选值：`cpu`, `cuda`，默认值为 `cpu`

**响应：**
```json
{
  "instance_id": "550e8400-e29b-41d4-a716-446655440000",
  "model_name": "base",
  "device": "cpu"
}
```

**状态码：**
- `201 Created`: 模型创建成功
- `400 Bad Request`: 请求数据无效
- `401 Unauthorized`: 未认证

**示例：**
```bash
curl -X POST http://localhost:5001/api/asr/models \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "base",
    "device": "cpu"
  }'
```

### 删除模型实例

**DELETE** `/api/asr/models/<instance_id>`

删除指定的模型实例。

**请求头：**
```
Authorization: Bearer <jwt_token>
```

**响应：**
- `204 No Content`: 删除成功
- `404 Not Found`: 模型实例不存在
- `401 Unauthorized`: 未认证

**示例：**
```bash
curl -X DELETE http://localhost:5001/api/asr/models/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <token>"
```

### 列出模型实例

**GET** `/api/asr/models`

列出当前用户的所有模型实例。

**请求头：**
```
Authorization: Bearer <jwt_token>
```

**响应：**
```json
{
  "models": [
    {
      "instance_id": "550e8400-e29b-41d4-a716-446655440000",
      "model_name": "base",
      "device": "cpu",
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "count": 1
}
```

**状态码：**
- `200 OK`: 获取成功
- `401 Unauthorized`: 未认证

### 转录音频

**POST** `/api/asr/transcribe`

使用指定的模型实例转录音频。

**请求头：**
```
Authorization: Bearer <jwt_token>
```

**请求体：**
```json
{
  "instance_id": "550e8400-e29b-41d4-a716-446655440000",
  "audio_base64": "base64_encoded_audio_data",
  "language": "en"
}
```

**参数说明：**
- `instance_id` (必填): 模型实例ID
- `audio_base64` (必填): base64编码的音频数据
- `language` (可选): 语言代码（如 `en`, `zh`），如果不指定，模型会自动检测

**响应：**
```json
{
  "text": "Hello, world!",
  "language": "en",
  "duration": 12.3,
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 12.3,
      "text": "Hello, world!"
    }
  ]
}
```

**状态码：**
- `200 OK`: 转录成功
- `400 Bad Request`: 请求数据无效
- `404 Not Found`: 模型实例不存在
- `401 Unauthorized`: 未认证

**示例：**
```bash
curl -X POST http://localhost:5001/api/asr/transcribe \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "550e8400-e29b-41d4-a716-446655440000",
    "audio_base64": "base64_encoded_audio_data",
    "language": "en"
  }'
```

## 速率限制

所有API端点都实施了速率限制。默认限制为：
- **60 请求/分钟**
- 时间窗口：60秒

### 速率限制响应头

- `X-RateLimit-Limit`: 速率限制上限
- `X-RateLimit-Remaining`: 剩余请求次数
- `X-RateLimit-Reset`: 重置时间（Unix时间戳）
- `Retry-After`: 重试等待时间（秒）

### 速率限制响应

当触发速率限制时，返回 `429 Too Many Requests` 状态码：

```json
{
  "error": "rate_limit_exceeded",
  "message": "速率限制已触发，请等待 30 秒后重试",
  "retry_after": 30
}
```

## 错误处理

所有错误响应都采用统一的格式：

```json
{
  "error": "error_code",
  "message": "错误描述"
}
```

### 常见错误码

- `400 Bad Request`: 请求数据无效
- `401 Unauthorized`: 未认证或认证失败
- `404 Not Found`: 资源不存在
- `409 Conflict`: 资源冲突（如用户名已存在）
- `429 Too Many Requests`: 速率限制已触发
- `500 Internal Server Error`: 服务器内部错误

## Python客户端示例

使用提供的Python客户端SDK：

```python
from whisper_asr_client import WhisperASRClient

# 初始化客户端
client = WhisperASRClient("http://localhost:5001")

# 登录
client.login("username", "password")

# 创建模型实例
model = client.create_model("base")

# 转录音频文件
result = client.transcribe_file(model["instance_id"], "audio.wav")
print(result["text"])
```

## curl示例

### 完整工作流

```bash
# 1. 注册用户
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "confirm_password": "password123"
  }'

# 2. 登录
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'

# 3. 创建模型实例（使用返回的token）
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
curl -X POST http://localhost:5001/api/asr/models \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "base",
    "device": "cpu"
  }'

# 4. 转录音频（使用返回的instance_id）
INSTANCE_ID="550e8400-e29b-41d4-a716-446655440000"
AUDIO_B64=$(base64 -i audio.wav)
curl -X POST http://localhost:5001/api/asr/transcribe \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"instance_id\": \"$INSTANCE_ID\",
    \"audio_base64\": \"$AUDIO_B64\",
    \"language\": \"en\"
  }"

# 5. 删除模型实例
curl -X DELETE http://localhost:5000/api/asr/models/$INSTANCE_ID \
  -H "Authorization: Bearer $TOKEN"
```

