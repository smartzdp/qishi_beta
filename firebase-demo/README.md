# 图书管理系统

> **注意**: 本项目复制自 https://github.com/chifn/firebase-demo.git

一个基于Firebase的现代化图书管理网站，支持用户注册、登录和图书管理功能。

## 功能特性

- 🔐 **用户认证**：支持用户注册、登录和登出
- 📚 **图书管理**：用户可以添加自己的图书名称和简介
- 👀 **公开浏览**：未登录用户可以查看所有用户的图书
- 📱 **响应式设计**：支持桌面和移动设备
- 🎨 **现代UI**：美观的用户界面和流畅的交互体验

## 技术栈

- **前端框架**：React 18
- **构建工具**：Vite
- **后端服务**：Firebase
- **认证服务**：Firebase Authentication
- **数据库**：Cloud Firestore
- **样式**：CSS3

## 项目结构

```
firebase_demo/
├── src/
│   ├── components/          # React组件
│   │   ├── Login.jsx       # 登录/注册组件
│   │   ├── BookList.jsx    # 图书列表组件
│   │   ├── AddBook.jsx     # 添加图书组件
│   │   ├── Navbar.jsx      # 导航栏组件
│   │   └── *.css          # 组件样式文件
│   ├── firebase/           # Firebase配置和服务
│   │   ├── config.js       # Firebase配置
│   │   ├── auth.js         # 认证服务
│   │   └── firestore.js    # 数据库服务
│   ├── App.jsx             # 主应用组件
│   ├── main.jsx            # 应用入口
│   └── App.css             # 全局样式
├── package.json            # 项目依赖
├── vite.config.js          # Vite配置
└── index.html              # HTML入口
```

## 安装和运行

### 1. 安装依赖

```bash
npm install
```

### 2. 配置Firebase

1. 在 [Firebase控制台](https://console.firebase.google.com/) 创建新项目
2. 启用 Authentication 和 Firestore Database
3. 在 Authentication 中启用邮箱/密码登录方式
4. 在 Firestore 中创建数据库（测试模式）
5. 复制项目配置到 `src/firebase/config.js`

```javascript
const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "your-app-id"
};
```

### 3. 运行开发服务器

```bash
npm run dev
```

应用将在 http://localhost:3000 启动

### 4. 构建生产版本

```bash
npm run build
```

## 使用说明

### 未登录用户
- 可以浏览所有用户添加的图书
- 可以看到图书标题、简介、添加者和添加时间
- 需要登录才能添加图书

### 已登录用户
- 可以添加自己的图书（标题和简介）
- 可以查看所有用户的图书
- 自己的图书会显示"我的图书"标识
- 可以登出账户

## 数据库结构

### books 集合
```javascript
{
  title: "图书标题",
  description: "图书简介",
  userId: "用户ID",
  userEmail: "用户邮箱",
  createdAt: "创建时间",
  updatedAt: "更新时间"
}
```

## 开发说明

- 所有组件都包含详细的中文注释
- 使用现代React Hooks（useState, useEffect）
- 采用函数式组件和函数式编程风格
- 响应式设计，支持移动端和桌面端
- 错误处理和加载状态完善
- 代码结构清晰，易于维护和扩展

## 许可证

MIT License

