# 社交媒体平台

一个基于Firebase的现代化社交媒体网站，支持用户注册、登录和消息发布功能。

## 功能特性

- 🔐 **用户认证**：支持用户注册、登录和登出
- 💬 **消息系统**：用户可以发布、编辑、删除自己的消息
- ❤️ **点赞功能**：所有用户都可以对消息点赞/取消点赞
- 💭 **回帖功能**：用户可以在消息下进行回复讨论
- 📊 **排序功能**：支持按时间、点赞数、回帖数三种方式排序
- 👀 **公开浏览**：未登录用户可以查看所有用户的消息
- 📱 **响应式设计**：支持桌面和移动设备
- 🎨 **淡粉色主题**：美观的用户界面和流畅的交互体验

## 技术栈

- **前端框架**：React 18
- **构建工具**：Vite
- **后端服务**：Firebase
- **认证服务**：Firebase Authentication
- **数据库**：Cloud Firestore
- **样式**：CSS3

## 项目结构

```
social_media/
├── src/
│   ├── components/          # React组件
│   │   ├── Login.jsx       # 登录/注册组件
│   │   ├── PostList.jsx    # 消息列表组件
│   │   ├── AddPost.jsx     # 发布消息组件
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

## 快速开始

使用启动脚本一键运行：

```bash
./start.sh
```

或手动安装：

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
- 可以浏览所有用户发布的消息
- 可以看到消息标题、内容、发布者、发布时间、点赞数和回帖
- 可以使用排序功能（按时间/按点赞数/按回帖数）
- 需要登录才能发布消息、点赞和回帖

### 已登录用户
- 可以发布新消息（标题和内容）
- 可以编辑和删除自己的消息
- 可以对任何消息点赞/取消点赞
- 可以在任何消息下回帖
- 可以删除自己的回帖
- 可以使用排序功能查看消息（按时间/按点赞数/按回帖数）
- 自己的消息会显示"我的消息"标识

## 数据库结构

### posts 集合
```javascript
{
  title: "消息标题",
  content: "消息内容",
  userId: "用户ID",
  userEmail: "用户邮箱",
  likes: ["userId1", "userId2"],  // 点赞用户ID数组
  likesCount: 10,                  // 点赞数
  comments: [                      // 回帖列表
    {
      id: "commentId",
      userId: "用户ID",
      userEmail: "用户邮箱",
      content: "回帖内容",
      createdAt: "创建时间"
    }
  ],
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

## 部署

查看详细部署说明：
- [部署检查清单](./DEPLOYMENT_CHECKLIST.md)
- [部署前总结](./PRE_DEPLOYMENT_SUMMARY.md)

快速部署到服务器：

```bash
# 构建生产版本
npm run build

# dist 目录包含所有静态文件，可直接部署
```

## 功能演示

### 核心功能
- ✅ 用户注册和登录（邮箱验证）
- ✅ 发布消息（标题 + 内容，最多500字）
- ✅ 点赞系统（实时更新）
- ✅ 回帖讨论（支持删除）
- ✅ 智能排序（最新/最热/热议）
- ✅ 权限控制（只能操作自己的内容）

### 界面特色
- 🎨 淡粉色主题（#fff5f7 - #ffe4e9）
- 📱 单列卡片布局，清晰易读
- ⚡ 实时数据同步
- 🎯 流畅的用户体验

## 常见问题

**Q: 为什么点赞/回帖按钮是灰色的？**  
A: 需要先登录才能使用互动功能。

**Q: 如何切换排序方式？**  
A: 点击页面顶部的"最新"、"最热"或"热议"按钮。

**Q: 可以删除别人的回帖吗？**  
A: 不可以，只能删除自己发布的回帖。

**Q: Firebase配置在哪里？**  
A: 在 `src/firebase/config.js` 文件中。

## 许可证

MIT License
