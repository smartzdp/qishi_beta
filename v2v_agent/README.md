# GLM-4-Voice API Demo

一个基于智谱AI GLM-4-Voice API的语音对话演示应用，支持语音和文本输入，AI会同时生成文本和音频回复。

## API来源

本项目基于以下开源项目和API服务：

- **GLM-4-Voice 模型**: [https://github.com/zai-org/GLM-4-Voice](https://github.com/zai-org/GLM-4-Voice)
- **智谱AI API**: [https://open.bigmodel.cn/dev/api/rtav/GLM-4-Voice](https://open.bigmodel.cn/dev/api/rtav/GLM-4-Voice)

## 功能特性

- 🎵 **语音输入**: 支持音频文件上传和语音输入
- 📝 **文本输入**: 支持传统文本输入方式
- 🔊 **语音输出**: AI生成高质量语音回复
- 📄 **文本输出**: 同时显示文本回复内容
- 🎨 **简洁界面**: 现代化的Web界面设计

## 快速开始

### 环境要求

- Python 3.10+
- FFmpeg (用于音频处理)

### 安装依赖

```bash
# 克隆项目
git clone <your-repo-url>
cd v2v_agent

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装FFmpeg (macOS)
brew install ffmpeg
```

### 配置API密钥

**⚠️ 重要：请勿将API密钥提交到代码仓库中！**

```bash
# 方法1：环境变量
export GLM_API_KEY="your-api-key-here"
export FFMPEG_BINARY="/opt/homebrew/bin/ffmpeg"  # macOS
export FFPROBE_BINARY="/opt/homebrew/bin/ffprobe"  # macOS

# 方法2：创建.env文件（推荐）
echo "GLM_API_KEY=your-api-key-here" > .env
echo "FFMPEG_BINARY=/opt/homebrew/bin/ffmpeg" >> .env
echo "FFPROBE_BINARY=/opt/homebrew/bin/ffprobe" >> .env
```

**获取API密钥**：
1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册账号并创建API密钥
3. 将密钥设置为环境变量或保存在.env文件中

### 启动应用

```bash
python web_demo.py --port 8890
```

然后在浏览器中访问 `http://localhost:8890`

## 项目结构

```
v2v_agent/
├── api_backend.py      # API后端逻辑
├── web_demo.py         # Web界面
├── audio_process.py    # 音频处理工具
├── requirements.txt    # 依赖包
├── examples/           # API使用示例
└── README.md          # 项目说明
```

## 使用说明

1. **文本对话**: 在输入框中输入文本，点击"发送"
2. **语音对话**: 选择"音频"模式，上传音频文件或录制语音
3. **清除对话**: 点击"清除"按钮清空对话历史

## 技术栈

- **后端**: Python, FastAPI, ZhipuAI SDK
- **前端**: Gradio
- **音频处理**: FFmpeg, pydub
- **API**: 智谱AI GLM-4-Voice API

## 许可证

本项目基于 Apache 2.0 许可证开源。

## 安全注意事项

- **API密钥安全**: 请勿将API密钥提交到代码仓库中
- **环境变量**: 使用环境变量或.env文件存储敏感信息
- **权限控制**: 定期轮换API密钥，避免泄露
- **访问限制**: 在智谱AI平台设置适当的API访问限制

## 致谢

感谢智谱AI团队提供的GLM-4-Voice模型和API服务。