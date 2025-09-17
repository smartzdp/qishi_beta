# Markdown 编辑器

一个基于 Vue 3 + Vite 的现代化在线 Markdown 编辑器，支持实时预览、导出功能和移动端适配。

## 🏗️ 项目架构

### 前端架构
```
markdown_editor/
├── src/
│   ├── views/
│   │   └── EditorView.vue      # 主编辑器页面
│   ├── router/
│   │   └── index.ts            # 路由配置
│   ├── stores/
│   │   └── editor.ts           # Pinia 状态管理
│   ├── utils/
│   │   ├── markdown.ts         # Markdown 解析工具
│   │   └── export.ts           # 文件导出工具
│   ├── App.vue                 # 根组件
│   ├── main.ts                 # 应用入口
│   └── style.css               # 全局样式
├── public/                     # 静态资源
├── package.json                # 项目配置
└── README.md                   # 项目文档
```

### 后端架构（可选）
```
markdown_editor/
├── app.py                      # Flask 后端服务
├── requirements.txt            # Python 依赖
└── venv/                       # Python 虚拟环境
```

## 🛠️ 技术栈

### 前端技术
- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 快速构建工具
- **TypeScript** - 类型安全的 JavaScript
- **Element Plus** - Vue 3 UI 组件库
- **Pinia** - Vue 3 状态管理
- **Vue Router** - 官方路由管理器

### 核心依赖
- **markdown-it** - Markdown 解析器
- **dompurify** - HTML 安全净化
- **highlight.js** - 代码高亮
- **html2pdf.js** - PDF 导出
- **file-saver** - 文件保存

### 后端技术（可选）
- **Flask** - Python Web 框架
- **Flask-CORS** - 跨域请求支持

## 🚀 快速开始

### 环境要求
- Node.js 16+ 
- npm 或 yarn
- Python 3.8+（可选，用于后端服务）

### 安装依赖
```bash
cd markdown_editor
npm install
```

### 启动开发服务器
```bash
npm run dev
```

访问：http://localhost:5173

### 启动后端服务（可选）
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py
```

## 📱 移动端测试

### 本地网络访问
```bash
npm run dev -- --host
```

### 获取本机IP
```bash
# macOS/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig | findstr "IPv4"
```

访问：http://[本机IP]:5173

## 🎯 核心功能

### 编辑模式
- **分屏模式** - 编辑器和预览同时显示
- **仅编辑模式** - 只显示编辑器
- **仅预览模式** - 只显示预览

### 编辑功能
- 实时 Markdown 预览
- 语法高亮
- 工具栏快捷操作
- 全屏编辑
- 内容清空

### 导出功能
- **HTML 导出** - 保存为 HTML 文件
- **PDF 导出** - 保存为 PDF 文件

### 响应式设计
- 桌面端优化
- 平板端适配
- 移动端友好

## 🎨 设计特色

- **粉色渐变主题** - 现代化视觉设计
- **响应式布局** - 适配各种屏幕尺寸
- **流畅动画** - 平滑的交互体验
- **直观操作** - 简洁的用户界面

## 📁 项目结构说明

### 核心文件
- `src/views/EditorView.vue` - 主编辑器组件
- `src/stores/editor.ts` - 状态管理
- `src/utils/markdown.ts` - Markdown 处理
- `src/utils/export.ts` - 导出功能

### 配置文件
- `package.json` - 项目依赖和脚本
- `vite.config.ts` - Vite 构建配置
- `tsconfig.json` - TypeScript 配置

## 🔧 开发说明

### 代码结构
- 使用 Vue 3 Composition API
- TypeScript 类型安全
- 模块化组件设计
- 响应式状态管理

### 样式系统
- CSS 变量主题
- 响应式媒体查询
- 移动端优先设计
- 统一的设计语言

### 性能优化
- 按需加载组件
- 代码分割
- 资源压缩
- 缓存策略

## 📝 使用说明

### 基本操作
1. 在左侧编辑器中输入 Markdown 文本
2. 右侧实时显示预览效果
3. 使用工具栏进行快捷操作
4. 支持全屏编辑模式

### 导出文件
1. 点击右上角下载按钮
2. 选择导出格式（HTML/PDF）
3. 文件自动下载到本地

### 移动端使用
1. 确保设备与电脑在同一网络
2. 访问 http://[本机IP]:5173
3. 支持触摸操作和手势

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 📄 许可证

MIT License

## 🆘 常见问题

### Q: 如何启用后端服务？
A: 运行 `python app.py` 启动 Flask 后端

### Q: 移动端无法访问？
A: 确保使用 `npm run dev -- --host` 启动服务

### Q: 导出功能不工作？
A: 检查浏览器是否支持文件下载功能

---

**项目已准备好分享和使用！** 🎉