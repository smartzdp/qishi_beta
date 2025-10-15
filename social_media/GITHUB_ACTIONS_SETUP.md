# GitHub Actions 自动部署配置

## 📁 Workflow 文件位置

```
.github/workflows/social-media-deploy.yml
```

## 🚀 工作流程说明

### 触发条件

1. **自动触发**: 推送到 `main` 分支且 `social_media/` 目录有变化时
2. **手动触发**: 在 GitHub Actions 页面手动运行

### 部署步骤

```yaml
1. Checkout code        # 下载源代码
2. Install Dependencies # 安装 npm 依赖
3. Build               # 构建生产版本
4. Deploy to Server    # 部署到服务器
```

## 🔐 GitHub Secrets 配置

在 GitHub 仓库中配置以下 Secrets：

### 必需的 Secrets

| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| `TEST_2BRAIN_KEY` | SSH 私钥 | -----BEGIN RSA PRIVATE KEY----- |
| `TEST_2BRAIN_HOST` | 服务器地址 | your-server.com |
| `TEST_2BRAIN_USER` | SSH 用户名 | ubuntu |
| `TEST_2BRAIN_PORT` | SSH 端口 | 22 |

### 如何配置 Secrets

1. 进入 GitHub 仓库
2. 点击 `Settings` > `Secrets and variables` > `Actions`
3. 点击 `New repository secret`
4. 输入名称和值
5. 点击 `Add secret`

## 📂 部署配置

### 源文件路径
```
SOURCE: "social_media/dist/"
```

### 目标服务器路径
```
TARGET: "server/www/depei.zhang/social_media"
```

### 部署参数
```
ARGS: "-avzL"  # rsync 参数：归档、详细、压缩、跟随符号链接
```

## 🎯 使用方法

### 自动部署

推送代码到 main 分支，修改 `social_media/` 目录下的任何文件：

```bash
git add .
git commit -m "更新社交媒体平台"
git push origin main
```

GitHub Actions 会自动：
1. 检测到变化
2. 运行构建
3. 部署到服务器

### 手动部署

1. 进入 GitHub 仓库
2. 点击 `Actions` 标签
3. 选择 `social-media auto deploy to server`
4. 点击 `Run workflow`
5. 选择分支并运行

## 📊 部署流程

```mermaid
graph LR
    A[推送代码] --> B{检测变化}
    B -->|social_media/** 变化| C[触发 Workflow]
    B -->|其他变化| D[不触发]
    C --> E[下载代码]
    E --> F[安装依赖]
    F --> G[构建项目]
    G --> H[SSH 部署]
    H --> I[完成]
```

## ⏱️ 预计时间

- 安装依赖: ~20-30秒
- 构建项目: ~1-2分钟
- 部署文件: ~10-20秒
- **总计**: ~2-3分钟

## 🔍 查看部署状态

### 在 GitHub 上查看

1. 进入仓库的 `Actions` 标签
2. 查看最近的 workflow 运行
3. 点击查看详细日志

### 日志内容

- ✅ 绿色勾号：部署成功
- ❌ 红色叉号：部署失败
- 🟡 黄色圆圈：正在运行

## 🛠️ 故障排查

### 常见问题

**问题 1: SSH 连接失败**
```
Error: Permission denied (publickey)
```
解决方案：
- 检查 `TEST_2BRAIN_KEY` 是否正确
- 确认 SSH 密钥有正确的权限

**问题 2: 构建失败**
```
Error: npm install failed
```
解决方案：
- 检查 `package.json` 是否正确
- 查看是否有依赖冲突

**问题 3: 部署路径错误**
```
Error: No such file or directory
```
解决方案：
- 确认服务器上目标路径存在
- 检查用户权限

## 🔄 回滚策略

如果部署后发现问题，可以：

1. **Git 回滚**
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **手动回滚**
   - SSH 登录服务器
   - 恢复之前的备份

## 📝 最佳实践

1. ✅ 在本地测试构建成功后再推送
2. ✅ 使用有意义的 commit 信息
3. ✅ 定期检查 workflow 运行状态
4. ✅ 保持 secrets 安全，不要泄露
5. ✅ 在服务器上保留备份

## 🔒 安全建议

- 🔐 定期更新 SSH 密钥
- 🔐 限制 SSH 用户权限
- 🔐 使用防火墙保护服务器
- 🔐 监控异常的部署活动
- 🔐 启用 GitHub 二次验证

## 📞 支持

如有问题，请检查：
- GitHub Actions 日志
- 服务器日志 (`/var/log/`)
- Firebase Console 状态

---

**配置完成后，每次推送到 main 分支都会自动部署到服务器！** 🎉

