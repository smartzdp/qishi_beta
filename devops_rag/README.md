# RAG App — GitHub Actions 部署到 AWS App Runner

本项目使用 GitHub Actions 在推送到 `main` 分支时自动构建 Docker 镜像并部署到 AWS App Runner。

## 用 Terraform 创建所需 AWS 环境

### 前提条件
- 配置 AWS CLI：`aws configure`
- 确保使用正确的 AWS 账户（当前账户：653999527472）

### 部署步骤（请在命令行依次运行如下命令，必须按照下面给出的顺序）

```bash
# 1. 初始化 Terraform
terraform init

# 2. 创建 ECR, Secrets Manager, IAM 角色（不创建 App Runner 服务）
TF_VAR_manage_apprunner_via_terraform=false \
TF_VAR_github_org_or_user=smartzdp \
TF_VAR_github_repo_name=qishi_beta \
TF_VAR_openai_api_key="<YOUR_OPENAI_KEY>" \
terraform apply -auto-approve

# 3. 本地构建 Docker 镜像并推送到 ECR（用于首次测试）
# 获取 ECR 仓库 URL（从 Terraform 输出或 AWS Console）
ECR_URL=$(aws ecr describe-repositories --repository-names bee-edu-rag-app --region us-east-1 --query 'repositories[0].repositoryUri' --output text)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URL
docker build --platform linux/amd64 -t $ECR_URL:latest .
docker push $ECR_URL:latest

# 4. （可选）使用 Terraform 创建 App Runner 服务
# 或者让 GitHub Actions 在首次部署时自动创建
TF_VAR_manage_apprunner_via_terraform=true \
TF_VAR_github_org_or_user=smartzdp \
TF_VAR_github_repo_name=qishi_beta \
TF_VAR_openai_api_key="<YOUR_OPENAI_KEY>" \
terraform apply -auto-approve
```

## 工作流概览（`.github/workflows/deploy-rag-app.yml`）

- **触发条件**：推送到 `main` 分支且 `devops_rag/**` 文件夹有变化（不包括 README.md）
- **核心步骤**：
  1. `Checkout` 代码
  2. 通过 GitHub OIDC 假设 IAM 角色（`aws-actions/configure-aws-credentials@v4`）
  3. 登录 Amazon ECR（`aws-actions/amazon-ecr-login@v2`）
  4. 构建并推送镜像到 ECR（镜像标签为提交 SHA 的前 7 位）
  5. 自动查找现有服务或使用 secrets 中的角色 ARN
  6. 使用 `awslabs/amazon-app-runner-deploy@main` 将 ECR 镜像部署到服务，并等待到稳定状态

### 部署步骤关键配置

```yaml
- name: Deploy to App Runner
  uses: awslabs/amazon-app-runner-deploy@main
  with:
    service: bee-edu-rag-service
    image: ${{ steps.ecr-login.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ env.TAG }}
    region: ${{ env.AWS_REGION }}
    access-role-arn: ${{ env.APP_RUNNER_ACCESS_ROLE_ARN }}
    instance-role-arn: ${{ env.APP_RUNNER_INSTANCE_ROLE_ARN }}
    port: 8080
    cpu: 1
    memory: 2
    wait-for-service-stability-seconds: 600
```

## 必需的仓库 Secrets

在 GitHub 仓库设置中配置以下 Secrets（Settings → Secrets and variables → Actions）：

- `AWS_REGION`：部署区域，例如 `us-east-1`
- `ECR_REPOSITORY`：ECR 仓库名，例如 `bee-edu-rag-app`
- `AWS_IAM_ROLE_TO_ASSUME`：GitHub OIDC 假设的 IAM 角色 ARN
  - 示例：`arn:aws:iam::653999527472:role/github-actions-deploy-role`
- `APP_RUNNER_ARN`：（可选）App Runner 服务 ARN，如果服务已存在
- `ACCESS_ROLE_ARN`：App Runner 访问角色 ARN（用于创建新服务时）
  - 示例：`arn:aws:iam::653999527472:role/bee-edu-apprunner-role`
- `INSTANCE_ROLE_ARN`：App Runner 实例角色 ARN（用于创建新服务时）
  - 示例：`arn:aws:iam::653999527472:role/bee-edu-apprunner-instance-role`

> 说明：日志中对 Secrets 的显示会被 GitHub 脱敏为 `***`，但运行时值有效。

## 服务配置

- **服务名称**：`bee-edu-rag-service`
- **端口**：`8080`
- **健康检查**：TCP 协议（检查端口 8080 是否开放）
- **CPU**：1 vCPU (1024)
- **内存**：2 GB (2048)
- **运行时环境变量**：
  - `OPENAI_API_KEY`：从 AWS Secrets Manager 自动注入（secret: `bee-edu-openai-key-secret`）

## 权限与最小权限建议

GitHub Actions 角色需要以下权限：
- ECR：推送和拉取镜像
- App Runner：创建、更新、描述服务
- Secrets Manager：读取 `bee-edu-openai-key-secret`
- IAM：传递角色到 App Runner（`iam:PassRole`）

需要传递的角色：
- `bee-edu-apprunner-instance-role`：用于运行时访问 Secrets Manager
- `bee-edu-apprunner-role`：用于从 ECR 拉取镜像

## 故障排除

### 服务无法启动
- 检查 CloudWatch 日志：`/aws/apprunner/bee-edu-rag-service/<service-id>/service`
- 确认 TCP 健康检查通过（应用监听在 `0.0.0.0:8080`）
- 验证 `OPENAI_API_KEY` 已正确配置在 Secrets Manager

### 部署失败
- 检查 GitHub Actions 日志
- 验证所有必需的 Secrets 已配置
- 确认 IAM 角色有足够权限

## 版本固定（可选）

为稳定性建议固定 Action 版本，例如：
- `uses: awslabs/amazon-app-runner-deploy@v2.5.2`
