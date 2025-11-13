# Whisper ASR Client SDK

Python客户端SDK for Whisper ASR Service

## 概述

此客户端SDK通过RESTful API与Whisper ASR服务通信。**它不直接使用Whisper模型**，而是通过HTTP请求调用远程API。

### 工作原理

1. **客户端**（此SDK）：
   - 读取本地音频文件
   - 将文件转换为base64编码
   - 通过HTTP POST请求发送JSON数据到REST API
   - 接收并返回转录结果

2. **服务器端**（REST API）：
   - 接收base64编码的音频数据（JSON格式）
   - 解码音频数据
   - 使用Whisper模型进行转录
   - 返回转录结果（JSON格式）

### 依赖项

客户端SDK只需要 `requests` 库，**不需要** `whisper`、`torch` 或其他深度学习库。

## 安装

```bash
pip install whisper-asr-client
```

或者从源码安装：

```bash
cd client_sdk
pip install -e .
```

## 使用方法

### 基本使用

```python
from whisper_asr_client import WhisperASRClient

# 初始化客户端（连接到REST API服务器）
client = WhisperASRClient("http://localhost:5001")

# 登录
client.login("username", "password")

# 创建模型实例
model = client.create_model("base")
print(f"模型实例ID: {model['instance_id']}")

# 转录音频文件
result = client.transcribe_file(model["instance_id"], "audio.wav")
print(f"转录文本: {result['text']}")
print(f"检测到的语言: {result['language']}")
print(f"音频时长: {result['duration']} 秒")
```

### 高级使用

```python
from whisper_asr_client import WhisperASRClient, AuthError, RateLimitError

client = WhisperASRClient("http://localhost:5001")

try:
    # 注册新用户
    client.register("newuser", "user@example.com", "password123", "password123")
    
    # 登录
    client.login("newuser", "password123")
    
    # 创建模型实例（使用GPU）
    model = client.create_model("base", device="cuda")
    
    # 转录音频文件（指定语言）
    result = client.transcribe_file(
        model["instance_id"],
        "audio.wav",
        language="en"
    )
    
    # 列出所有模型实例
    models = client.list_models()
    print(f"共有 {models['count']} 个模型实例")
    
    # 删除模型实例
    client.delete_model(model["instance_id"])
    
except AuthError as e:
    print(f"认证失败: {e}")
except RateLimitError as e:
    print(f"速率限制: {e}, 请等待 {e.retry_after} 秒后重试")
except Exception as e:
    print(f"错误: {e}")
```

### 使用base64编码的音频

```python
# 将音频文件转换为base64（本地操作）
audio_base64 = client.file_to_base64("audio.wav")

# 使用base64编码的音频进行转录（通过REST API）
result = client.transcribe_base64(model["instance_id"], audio_base64)
```

**注意**: `transcribe_file()` 方法内部会自动执行上述两步操作（文件→base64→REST API），这是推荐的用法。

### 内部工作原理

`transcribe_file()` 方法的执行流程：

1. **读取本地文件**: 从文件系统读取音频文件
2. **转换为base64**: 将音频字节数据编码为base64字符串
3. **发送HTTP请求**: 通过POST请求发送JSON到 `/api/asr/transcribe`
   ```json
   {
     "instance_id": "uuid",
     "audio_base64": "base64_encoded_string",
     "language": "en"
   }
   ```
4. **接收响应**: 服务器返回JSON格式的转录结果
5. **返回结果**: 返回包含 `text`, `language`, `duration`, `segments` 的字典

## API参考

### WhisperASRClient

#### 方法

- `login(username, password)`: 用户登录
- `register(username, email, password, confirm_password)`: 用户注册
- `create_model(model_name, device="cpu")`: 创建模型实例
- `delete_model(instance_id)`: 删除模型实例
- `transcribe_base64(instance_id, audio_base64, language=None)`: 转录音频（base64）
- `transcribe_file(instance_id, file_path, language=None)`: 转录音频文件
- `file_to_base64(file_path)`: 将音频文件转换为base64
- `list_models()`: 列出所有模型实例

### 异常

- `APIError`: API错误基类
- `AuthError`: 认证错误（401）
- `RateLimitError`: 速率限制错误（429）
- `NotFoundError`: 资源不存在错误（404）

## 许可证

MIT License

