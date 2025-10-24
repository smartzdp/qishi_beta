# Excel Agent - 智能Excel分析助手

一个基于AI的Excel数据分析平台，能够理解自然语言查询并生成相应的Python代码进行数据分析。

## 功能特性

- 🤖 **AI驱动分析**: 使用GPT-4生成个性化的数据分析代码
- 📊 **智能可视化**: 自动生成交互式图表（Plotly）
- 🔍 **语义搜索**: 基于RAG技术智能匹配相关数据文件
- 📝 **伪代码生成**: 将生成的Python代码转换为易理解的伪代码
- 🎤 **语音交互**: 支持语音输入和语音输出
- 📁 **多文件支持**: 处理复杂Excel文件，支持多工作表分析
- 🔧 **数据预处理**: 自动处理合并单元格、多级表头等复杂结构

## 技术栈

### 后端
- **FastAPI**: Web框架
- **OpenAI GPT-4**: 代码生成
- **Pandas**: 数据处理
- **Plotly**: 数据可视化
- **Sentence Transformers**: 文本嵌入
- **scikit-learn**: 相似度搜索

### 前端
- **React**: UI框架
- **Vite**: 构建工具
- **WebSocket**: 实时通信

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd excel_agent

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制示例环境变量文件并配置：

```bash
cp .env.example .env
```

然后编辑 `.env` 文件，填入你的API密钥：

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

### 3. 启动服务

```bash
# 启动后端服务
python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000

# 启动前端服务（新终端）
cd frontend
npm install
npm run dev
```

### 4. 访问应用

打开浏览器访问: http://localhost:5177

## 使用说明

### 1. 上传Excel文件
- 点击"上传Excel文件"按钮
- 选择要分析的Excel文件
- 系统会自动处理文件并建立索引

### 2. 提问分析
- 在输入框中输入自然语言问题
- 例如："显示产品清仓价格排名"、"分析各地区的销售趋势"
- 点击"开始分析"按钮

### 3. 查看结果
- 系统会显示生成的Python代码
- 展示分析流程的伪代码
- 呈现交互式图表和数据表格

## 示例问题

- "显示产品清仓价格排名"
- "比较各地区的销售趋势"
- "分析学生答辩意见的关键词"
- "统计各个工作表的数据量"

## 项目结构

```
excel_agent/
├── backend/                 # 后端服务
│   ├── routers/            # API路由
│   ├── services/           # 业务逻辑
│   │   ├── codegen/        # 代码生成
│   │   ├── rag/           # 检索增强生成
│   │   ├── preprocessing/  # 数据预处理
│   │   └── ...
│   └── utils/             # 工具函数
├── frontend/              # 前端应用
│   ├── src/
│   │   ├── components/    # React组件
│   │   ├── api/          # API客户端
│   │   └── config/       # 配置文件
│   └── ...
├── data/                  # 数据存储
│   ├── samples/          # 示例文件
│   ├── processed_clean/  # 处理后的文件
│   └── knowledge_base/   # 知识库索引
└── examples/             # 示例脚本
```

## 开发说明

### 添加新的分析类型
1. 在 `backend/services/intent/parser.py` 中添加意图识别规则
2. 在 `backend/services/codegen/prompt_templates_v2.py` 中添加代码模板
3. 在 `backend/services/planner/query_rewrite.py` 中添加列名解析逻辑

### 自定义UI
- 修改 `frontend/src/styles.css` 调整样式
- 更新 `frontend/src/config/constants.js` 修改文本和配置

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！