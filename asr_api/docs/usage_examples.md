# Whisper ASR Service Usage Examples

## Python客户端使用示例

### 基本使用

```python
from whisper_asr_client import WhisperASRClient

# 初始化客户端
client = WhisperASRClient("http://localhost:5001")

# 登录
client.login("testuser", "password123")

# 创建模型实例
model = client.create_model("base")
print(f"模型实例ID: {model['instance_id']}")

# 转录音频文件
result = client.transcribe_file(model["instance_id"], "audio.wav")
print(f"转录文本: {result['text']}")
print(f"检测到的语言: {result['language']}")
print(f"音频时长: {result['duration']} 秒")

# 删除模型实例
client.delete_model(model["instance_id"])
```

### 错误处理

```python
from whisper_asr_client import WhisperASRClient, AuthError, RateLimitError, APIError

client = WhisperASRClient("http://localhost:5001")

try:
    # 登录
    client.login("testuser", "password123")
    
    # 创建模型实例
    model = client.create_model("base")
    
    # 转录音频文件
    result = client.transcribe_file(model["instance_id"], "audio.wav")
    print(result["text"])
    
except AuthError as e:
    print(f"认证失败: {e}")
except RateLimitError as e:
    print(f"速率限制: {e}")
    print(f"请等待 {e.retry_after} 秒后重试")
except APIError as e:
    print(f"API错误: {e}")
    print(f"状态码: {e.status_code}")
except Exception as e:
    print(f"未知错误: {e}")
```

### 使用不同模型

```python
from whisper_asr_client import WhisperASRClient

client = WhisperASRClient("http://localhost:5001")
client.login("testuser", "password123")

# 创建不同大小的模型
tiny_model = client.create_model("tiny")
base_model = client.create_model("base")
small_model = client.create_model("small")
medium_model = client.create_model("medium")
large_model = client.create_model("large")

# 使用不同模型进行转录
result_tiny = client.transcribe_file(tiny_model["instance_id"], "audio.wav")
result_base = client.transcribe_file(base_model["instance_id"], "audio.wav")
result_small = client.transcribe_file(small_model["instance_id"], "audio.wav")

print("Tiny模型转录:", result_tiny["text"])
print("Base模型转录:", result_base["text"])
print("Small模型转录:", result_small["text"])

# 清理模型实例
client.delete_model(tiny_model["instance_id"])
client.delete_model(base_model["instance_id"])
client.delete_model(small_model["instance_id"])
```

### 使用GPU加速

```python
from whisper_asr_client import WhisperASRClient

client = WhisperASRClient("http://localhost:5001")
client.login("testuser", "password123")

# 创建GPU模型实例
gpu_model = client.create_model("base", device="cuda")

# 转录音频文件（GPU加速）
result = client.transcribe_file(gpu_model["instance_id"], "audio.wav")
print(result["text"])

# 删除模型实例
client.delete_model(gpu_model["instance_id"])
```

### 指定语言

```python
from whisper_asr_client import WhisperASRClient

client = WhisperASRClient("http://localhost:5001")
client.login("testuser", "password123")

# 创建模型实例
model = client.create_model("base")

# 转录音频文件（指定语言）
result_en = client.transcribe_file(model["instance_id"], "audio.wav", language="en")
result_zh = client.transcribe_file(model["instance_id"], "audio.wav", language="zh")

print("English:", result_en["text"])
print("Chinese:", result_zh["text"])

# 删除模型实例
client.delete_model(model["instance_id"])
```

### 使用base64编码的音频

```python
from whisper_asr_client import WhisperASRClient

client = WhisperASRClient("http://localhost:5001")
client.login("testuser", "password123")

# 创建模型实例
model = client.create_model("base")

# 将音频文件转换为base64
audio_base64 = client.file_to_base64("audio.wav")

# 使用base64编码的音频进行转录
result = client.transcribe_base64(model["instance_id"], audio_base64)
print(result["text"])

# 删除模型实例
client.delete_model(model["instance_id"])
```

### 列出所有模型实例

```python
from whisper_asr_client import WhisperASRClient

client = WhisperASRClient("http://localhost:5001")
client.login("testuser", "password123")

# 列出所有模型实例
models = client.list_models()
print(f"共有 {models['count']} 个模型实例")

for model in models["models"]:
    print(f"实例ID: {model['instance_id']}")
    print(f"模型名称: {model['model_name']}")
    print(f"设备: {model['device']}")
    print(f"创建时间: {model['created_at']}")
    print("-" * 50)
```

### 批量转录

```python
from whisper_asr_client import WhisperASRClient
import os

client = WhisperASRClient("http://localhost:5001")
client.login("testuser", "password123")

# 创建模型实例
model = client.create_model("base")

# 批量转录音频文件
audio_files = ["audio1.wav", "audio2.wav", "audio3.wav"]
results = []

for audio_file in audio_files:
    if os.path.exists(audio_file):
        try:
            result = client.transcribe_file(model["instance_id"], audio_file)
            results.append({
                "file": audio_file,
                "text": result["text"],
                "language": result["language"],
                "duration": result["duration"]
            })
        except Exception as e:
            print(f"转录失败 {audio_file}: {e}")

# 打印结果
for result in results:
    print(f"文件: {result['file']}")
    print(f"文本: {result['text']}")
    print(f"语言: {result['language']}")
    print(f"时长: {result['duration']} 秒")
    print("-" * 50)

# 删除模型实例
client.delete_model(model["instance_id"])
```

## REST API使用示例

### 使用curl

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
TOKEN=$(curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"

# 3. 创建模型实例
INSTANCE_ID=$(curl -X POST http://localhost:5001/api/asr/models \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "base",
    "device": "cpu"
  }' | jq -r '.instance_id')

echo "Instance ID: $INSTANCE_ID"

# 4. 转录音频文件
AUDIO_B64=$(base64 -i audio.wav)
curl -X POST http://localhost:5001/api/asr/transcribe \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"instance_id\": \"$INSTANCE_ID\",
    \"audio_base64\": \"$AUDIO_B64\",
    \"language\": \"en\"
  }" | jq '.'

# 5. 列出所有模型实例
curl -X GET http://localhost:5001/api/asr/models \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# 6. 删除模型实例
curl -X DELETE http://localhost:5001/api/asr/models/$INSTANCE_ID \
  -H "Authorization: Bearer $TOKEN"
```

### 使用Python requests

```python
import requests
import base64
import json

BASE_URL = "http://localhost:5001"

# 1. 注册用户
register_data = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "confirm_password": "password123"
}
response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
print("注册响应:", response.json())

# 2. 登录
login_data = {
    "username": "testuser",
    "password": "password123"
}
response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
token = response.json()["access_token"]
print("Token:", token)

# 3. 创建模型实例
headers = {"Authorization": f"Bearer {token}"}
model_data = {
    "model_name": "base",
    "device": "cpu"
}
response = requests.post(f"{BASE_URL}/api/asr/models", json=model_data, headers=headers)
instance_id = response.json()["instance_id"]
print("Instance ID:", instance_id)

# 4. 转录音频文件
with open("audio.wav", "rb") as f:
    audio_bytes = f.read()
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

transcribe_data = {
    "instance_id": instance_id,
    "audio_base64": audio_base64,
    "language": "en"
}
response = requests.post(f"{BASE_URL}/api/asr/transcribe", json=transcribe_data, headers=headers)
result = response.json()
print("转录结果:", result["text"])
print("检测到的语言:", result["language"])
print("音频时长:", result["duration"], "秒")

# 5. 列出所有模型实例
response = requests.get(f"{BASE_URL}/api/asr/models", headers=headers)
models = response.json()
print("模型实例数量:", models["count"])

# 6. 删除模型实例
response = requests.delete(f"{BASE_URL}/api/asr/models/{instance_id}", headers=headers)
print("删除状态码:", response.status_code)
```

## 最佳实践

1. **重用模型实例**: 创建模型实例后，可以多次使用它进行转录，避免频繁创建和删除模型实例。

2. **错误处理**: 始终处理可能的错误，特别是认证错误和速率限制错误。

3. **资源清理**: 使用完模型实例后，及时删除它们以释放内存。

4. **指定语言**: 如果知道音频的语言，指定语言参数可以提高转录准确性和速度。

5. **选择合适的模型**: 根据需求选择合适的模型大小，较大的模型通常更准确但速度较慢。

6. **批量处理**: 对于多个音频文件，可以使用同一个模型实例进行批量转录。

