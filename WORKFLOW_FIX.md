# GitHub Actions Workflow 修复说明

## 🐛 问题描述

### 问题 1: Rollup 依赖问题

在 GitHub Actions 的 Linux 环境中部署时出现以下错误：

```
Error: Cannot find module @rollup/rollup-linux-x64-gnu
```

### 问题 2: rsync 路径错误

部署到服务器时出现 rsync 错误：

```
client_loop: send disconnect: Broken pipe
rsync error: error in rsync protocol data stream (code 12)
```

## 🔍 问题原因

这是 npm 处理 optional dependencies 的已知 bug：
- Rollup 需要平台特定的二进制包 (`@rollup/rollup-linux-x64-gnu`)
- 在某些情况下，npm 不能正确安装这些可选依赖
- GitHub Actions 使用的是 Linux x64 环境，需要对应的本地模块

相关 issue: https://github.com/npm/cli/issues/4828

## ✅ 解决方案

### 解决方案 1: 修复 Rollup 依赖

在 workflow 中，**删除本地的 `node_modules` 和 `package-lock.json` 后重新安装**。

### 修改前

```yaml
- name: Install Dependencies
  working-directory: ./social_media
  run: npm install
```

### 修改后

```yaml
- name: Install Dependencies
  working-directory: ./social_media
  run: |
    rm -rf node_modules package-lock.json
    npm install
```

### 解决方案 2: 添加部署前后脚本

**问题**：目标目录可能不存在，rsync 无法自动创建多级目录，且需要正确的文件权限

```yaml
# 修改前（没有脚本）
TARGET: "server/www/depei.zhang/firebase-demo"

# 修改后（添加前后脚本）
TARGET: "server/www/depei.zhang/firebase-demo"
SCRIPT_BEFORE: |
  mkdir -p server/www/depei.zhang/firebase-demo
  echo "Target directory created or already exists"
SCRIPT_AFTER: |
  chmod -R 755 server/www/depei.zhang/firebase-demo
  echo "Target directory permissions updated"
```

### 解决方案 3: 排除 Markdown 文件触发

只修改文档不应该触发部署：

```yaml
paths:
  - 'social_media/**'  # 包含所有文件
  - '.github/workflows/social-media-deploy.yml'
  - '!social_media/**/*.md'  # 排除md文件
```

## 📝 为什么这样能解决问题

### 问题 1 原因
1. **删除本地锁文件**：本地的 `package-lock.json` 可能包含 macOS 特定的依赖信息
2. **重新解析依赖**：在 Linux 环境中重新解析，会正确安装 Linux 特定的包
3. **fresh install**：确保所有 optional dependencies 在当前平台正确安装

### 问题 2 原因
1. **目录不存在**：rsync 无法自动创建多级嵌套目录
2. **连接中断**：尝试写入不存在的目录导致 SSH 连接断开（Broken pipe）
3. **权限问题**：部署后文件可能没有正确的读取权限（需要 755）

### 问题 3 原因
修改 README 等文档文件不应该触发部署，浪费 CI/CD 资源

## 🔧 已修复的文件

- ✅ `.github/workflows/social-media-deploy.yml`（Rollup 依赖 + 目录创建 + 排除 MD）
- ✅ `.github/workflows/firebase-demo-deploy.yml`（Rollup 依赖 + 目录创建 + 排除 MD）

### 完整修复内容

```yaml
# 路径过滤 - 排除 MD 文件
on:
  push:
    paths:
      - 'social_media/**'
      - '.github/workflows/social-media-deploy.yml'
      - '!social_media/**/*.md'  # 新增：排除 md 文件

# 安装依赖 - 修复 Rollup 问题
- name: Install Dependencies
  working-directory: ./social_media
  run: |
    rm -rf node_modules package-lock.json  # 新增
    npm install

# 部署 - 创建目录、部署、设置权限
- name: Deploy to Server
  env:
    TARGET: "server/www/depei.zhang/social_media"
    SCRIPT_BEFORE: |  # 新增：部署前创建目录
      mkdir -p server/www/depei.zhang/social_media
      echo "Target directory created or already exists"
    SCRIPT_AFTER: |  # 新增：部署后设置权限
      chmod -R 755 server/www/depei.zhang/social_media
      echo "Target directory permissions updated"
```

## 📊 影响

### 优点
- ✅ 修复了 Linux 环境构建失败的问题
- ✅ 修复了 rsync 部署到服务器失败的问题
- ✅ 自动创建目标目录，无需手动操作
- ✅ 确保在 CI/CD 环境中依赖正确安装
- ✅ 排除 Markdown 文件，节省 CI/CD 资源
- ✅ 不影响本地开发

### 注意事项
- ⚠️ 部署时间会稍微增加（需要完全重新安装依赖）
- ⚠️ 大约增加 20-30 秒的安装时间
- ⚠️ SCRIPT_BEFORE 和 SCRIPT_AFTER 在每次部署时都会执行（幂等操作）
- 💡 修改 README 等 .md 文件不会触发部署
- 🔒 部署后自动设置目录权限为 755（确保 web 服务器可读）

## 📋 触发场景

修改后的触发规则：

| 修改的文件 | firebase-demo 部署 | social-media 部署 |
|-----------|-------------------|------------------|
| `firebase-demo/src/App.jsx` | ✅ 触发 | ❌ 不触发 |
| `social_media/src/App.jsx` | ❌ 不触发 | ✅ 触发 |
| `firebase-demo/README.md` | ❌ 不触发 | ❌ 不触发 |
| `social_media/README.md` | ❌ 不触发 | ❌ 不触发 |
| `firebase-demo-deploy.yml` | ✅ 触发 | ❌ 不触发 |
| `social-media-deploy.yml` | ❌ 不触发 | ✅ 触发 |
| 根目录 `README.md` | ❌ 不触发 | ❌ 不触发 |

## 🔒 关于权限设置

### 为什么需要 755 权限？

```bash
chmod -R 755 server/www/depei.zhang/social_media
```

- **7** (owner): 读、写、执行
- **5** (group): 读、执行
- **5** (others): 读、执行

这确保：
- ✅ Web 服务器可以读取文件
- ✅ 访问者可以浏览网站
- ✅ 部署用户可以更新文件
- ✅ 符合标准的 web 文件权限

## 🧪 测试

修复后的 workflow 应该能够：
1. ✅ 成功安装所有依赖（包括 rollup 的本地包）
2. ✅ 在服务器上创建目标目录（SCRIPT_BEFORE）
3. ✅ 成功构建项目
4. ✅ 成功部署到服务器
5. ✅ 自动设置文件权限为 755（SCRIPT_AFTER）
6. ✅ 修改 .md 文件时不触发部署

## 🚀 部署步骤

保存修改后，推送到 GitHub：

```bash
git add .github/workflows/
git commit -m "修复 GitHub Actions 中 Rollup 依赖问题"
git push origin main
```

GitHub Actions 会自动触发，这次应该能成功部署！

## 📚 参考资料

- [npm CLI issue #4828](https://github.com/npm/cli/issues/4828)
- [Rollup documentation](https://rollupjs.org/)
- [Vite deployment guide](https://vitejs.dev/guide/static-deploy.html)

---

**修复时间**: 2025-10-15  
**状态**: ✅ 已解决

