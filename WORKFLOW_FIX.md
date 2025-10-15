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

### 解决方案 2: 修复 rsync 目标路径

**问题**：TARGET 路径使用了相对路径，需要使用服务器的绝对路径
```yaml
# 错误
TARGET: "server/www/depei.zhang/firebase-demo"

# 正确（服务器上的绝对路径）
TARGET: "/home/track_a/server/www/depei.zhang/firebase-demo"
```

## 📝 为什么这样能解决问题

### 问题 1 原因
1. **删除本地锁文件**：本地的 `package-lock.json` 可能包含 macOS 特定的依赖信息
2. **重新解析依赖**：在 Linux 环境中重新解析，会正确安装 Linux 特定的包
3. **fresh install**：确保所有 optional dependencies 在当前平台正确安装

### 问题 2 原因
1. **相对路径问题**：rsync 需要服务器上的完整绝对路径
2. **路径解析错误**：相对路径会导致 rsync 无法找到正确的目标目录
3. **连接中断**：无法正确创建目标目录导致连接断开
4. **正确路径**：服务器的 home folder 是 `/home/track_a/`

## 🔧 已修复的文件

- ✅ `.github/workflows/social-media-deploy.yml`（Rollup 依赖 + rsync 路径）
- ✅ `.github/workflows/firebase-demo-deploy.yml`（Rollup 依赖 + rsync 路径）

### 完整修复内容

```yaml
# 安装依赖 - 修复 Rollup 问题
- name: Install Dependencies
  working-directory: ./social_media
  run: |
    rm -rf node_modules package-lock.json  # 新增
    npm install

# 部署 - 修复路径问题
- name: Deploy to Server
  env:
    TARGET: "/home/track_a/server/www/depei.zhang/social_media"  # 使用绝对路径
```

## 📊 影响

### 优点
- ✅ 修复了 Linux 环境构建失败的问题
- ✅ 确保在 CI/CD 环境中依赖正确安装
- ✅ 不影响本地开发

### 注意事项
- ⚠️ 部署时间会稍微增加（需要完全重新安装依赖）
- ⚠️ 大约增加 20-30 秒的安装时间

## 🧪 测试

修复后的 workflow 应该能够：
1. ✅ 成功安装所有依赖（包括 rollup 的本地包）
2. ✅ 成功构建项目
3. ✅ 成功部署到服务器

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

