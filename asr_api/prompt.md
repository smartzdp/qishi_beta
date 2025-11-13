# 🚀 Whisper ASR Service — Full Project Plan for Cursor  
### (API Spec → RESTful Service → Python SDK → PyPI Package)

This is the complete project prompt for Cursor.  
Follow this spec to generate the full codebase for the homework assignment:

> Local Whisper ASR model → RESTful API (JWT + rate limiting) → Python SDK → PyPI package.

The structure and coding style should follow the provided sample code folder (REST API规范以及封装), especially:
- The JWT authentication flow
- The rate limit decorator
- The REST API structure
- The PyPI packaging example

---

## 0. Tech Stack & Conventions

- **Backend Framework**: Flask  
- **Auth**: `flask_jwt_extended` (same pattern as sample project)  
- **Rate Limiting**: custom decorator (fixed window), modeled after sample  
- **ASR Model**: Whisper (`openai-whisper`) or `faster-whisper` locally  
- **Python Client SDK**: `requests`-based wrapper  
- **Packaging**: src layout (`pyproject.toml`, `hatchling`)  
- **Documentation Required**: API docs + sample code

---

## 1. Project Directory Layout

```
whisper_asr_service/
  run.py
  config.py
  app/
    __init__.py
    models/
      __init__.py
      user.py
      asr_instance.py
    routes/
      __init__.py
      auth.py
      asr.py
    schemas/
      __init__.py
      user_schema.py
      asr_schema.py
    utils/
      __init__.py
      model_manager.py
      audio_utils.py
      rate_limiter.py
  docs/
    api_docs.md
    usage_examples.md
  tests/
    test_auth.py
    test_asr_api.py
    test_model_manager.py
    test_rate_limit.py

client_sdk/
  pyproject.toml
  README.md
  src/whisper_asr_client/
    __init__.py
    client.py
    exceptions.py
    types.py
  tests/
    test_client_basic.py
    test_client_integration.py
```

---

## 2. Backend Implementation Plan

### 2.1 `config.py`

Define:
- SECRET_KEY
- JWT_SECRET_KEY
- JWT_ACCESS_TOKEN_EXPIRES
- DB URI (SQLite or MySQL-style per sample)
- Flask configs

---

### 2.2 `app/__init__.py`

Implement `create_app` following sample project:

- Initialize `db = SQLAlchemy()`, `jwt = JWTManager()`
- Register blueprints:
  - `/api/auth`
  - `/api/asr`

---

### 2.3 Authentication (`routes/auth.py`)

Reuse sample code pattern:

Endpoints:
- `POST /api/auth/register`
- `POST /api/auth/login`

User model + schemas required:
- `models/user.py`
- `schemas/user_schema.py`

Return JWT token using `create_access_token`.

---

## 2.4 Rate Limiting (`utils/rate_limiter.py`)

Implement a fixed-window rate limiter:

- Key by JWT user ID or IP
- Default: 60 requests/min
- Return 429 with headers:

```
X-RateLimit-Limit
X-RateLimit-Remaining
X-RateLimit-Reset
```

---

## 2.5 Model Manager (`utils/model_manager.py`)

A singleton-style Whisper model manager.

### Responsibilities:
- Create and delete model instances
- Store models in memory: `dict`
- Load Whisper or Faster-Whisper models
- Perform transcription

### Core API:
```
create_model(model_name, device="cpu")
delete_model(instance_id)
get_model(instance_id)
transcribe(instance_id, audio_bytes, language=None)
```

Each model instance:
```
instance_id
model_name
device
model (Whisper loaded)
extra_config
```

---

## 2.6 Audio Utilities (`utils/audio_utils.py`)

Implement:
- base64_to_audio_bytes
- (optional) file_to_base64

---

## 2.7 ASR Schemas (`schemas/asr_schema.py`)

### Create Model Request
```
model_name: str
device: str (optional)
```

### Transcribe Request
```
instance_id: str
audio_base64: str
language: optional
```

### Response fields:
- text
- language
- duration
- segments

---

## 2.8 ASR RESTful API (`routes/asr.py`)

### 1️⃣ `POST /api/asr/models`
Create a model instance  
Requires JWT + rate limit.

Request:
```json
{
  "model_name": "base",
  "device": "cpu"
}
```

Response:
```json
{
  "instance_id": "uuid",
  "model_name": "base",
  "device": "cpu"
}
```

---

### 2️⃣ `DELETE /api/asr/models/<instance_id>`
Deletes model instance  
Require JWT + rate limit  
Return `204 No Content`

---

### 3️⃣ `POST /api/asr/transcribe`
Transcribe audio provided as Base64.

Request:
```json
{
  "instance_id": "uuid",
  "audio_base64": "xxxxx",
  "language": "en"
}
```

Response:
```json
{
  "text": "transcribed text",
  "segments": [...],
  "language": "en",
  "duration": 12.3
}
```

---

# 3. Python Client SDK

Location: `client_sdk/src/whisper_asr_client/`

## 3.1 Features
- All REST APIs available
- Token-based login
- `file_to_base64`
- `transcribe_file`
- Exception handling

---

## 3.2 `client.py`

Methods:

```
login(username, password)
create_model(model_name, device)
delete_model(instance_id)
transcribe_base64(instance_id, audio_b64, language=None)
file_to_base64(file_path)
transcribe_file(instance_id, file_path, language=None)
```

---

## 3.3 Exceptions

```
APIError
AuthError
RateLimitError
```

Use HTTP status codes to decide which exception to throw.

---

## 3.4 Public Exports (`__init__.py`)

```
from .client import WhisperASRClient
from .exceptions import APIError, AuthError, RateLimitError
```

---

## 3.5 SDK README

Include usage example:

```python
from whisper_asr_client import WhisperASRClient

client = WhisperASRClient("http://localhost:5000")
client.login("user", "pass")

model = client.create_model("base")
text = client.transcribe_file(model["instance_id"], "audio.wav")
print(text)
```

---

# 4. Documentation (`docs/api_docs.md`)

Document:

### Authentication
- Endpoints
- Example curl
- Example Python

### ASR API
- Create model
- Delete model
- Transcribe
- JSON schemas
- Sample requests/responses

### Rate Limit
- Policy
- Sample 429 response

### Errors
Unified error format:
```json
{
  "error": "error_code",
  "message": "description"
}
```

---

# 5. Test Plan

## Backend Tests

### `test_auth.py`
- Registration
- Login
- JWT access

### `test_model_manager.py`
- Create model (mock Whisper)
- Delete model
- Transcribe mock audio

### `test_asr_api.py`
- End-to-end create → transcribe → delete (mock Whisper)

### `test_rate_limit.py`
- Force hit rate limit
- Validate 429 + headers

---

## Client SDK Tests

### `test_client_basic.py`
Use `responses` or `requests_mock`  
Test:
- login
- create model
- transcribe_base64
- error handling

### `test_client_integration.py`
Optional: full integration with real server

---

# 6. Recommended Implementation Order

1. Create project folder structure  
2. Implement `config.py`, `app/__init__.py`, `run.py`  
3. Implement authentication (copy sample repo)  
4. Implement model manager (stub → real Whisper)  
5. Implement rate limiter  
6. Implement ASR schemas  
7. Implement ASR routes  
8. Implement backend tests  
9. Implement client SDK + tests  
10. Write documentation  
11. Build & upload Python package (optional)

---

# ✔️ END OF PROMPT
