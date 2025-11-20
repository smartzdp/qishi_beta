terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# -----------------------------------------------------------------
# 1. GitHub Actions (CI/CD) 所需的 OIDC 认证
# -----------------------------------------------------------------
# 变量：您的 GitHub 用户名/组织名
variable "github_org_or_user" {
  description = "您的 GitHub 用户名或组织名 (e.g., 'my-username')"
  type        = string
}

variable "github_repo_name" {
  description = "您的 GitHub 仓库名 (e.g., 'rag-app-demo')"
  type        = string
}

# 注册 GitHub OIDC 作为一个受信任的身份提供商
resource "aws_iam_openid_connect_provider" "github_oidc" {
  url = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d9c60c1c1107f9c7bb06a5e24dd2b17fd"] # GitHub 的标准 OIDC Thumbprint
}

# 策略：允许 GitHub Actions 推送 ECR 和 更新 App Runner
resource "aws_iam_policy" "github_actions_policy" {
  name = "github-actions-deploy-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:CompleteLayerUpload",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage",
          "ecr:UploadLayerPart"
        ],
        Resource = aws_ecr_repository.rag_app_ecr.arn
      },
      {
        Effect = "Allow",
        Action = [
          "ecr:GetAuthorizationToken"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "apprunner:StartDeployment",
          "apprunner:DescribeService",
          "apprunner:UpdateService",
          "apprunner:ListOperations",
          "apprunner:DeleteService"
         ],
        Resource = "*"
      }
      ,
      {
        Effect = "Allow",
        Action = [
          "apprunner:ListServices"
        ],
        Resource = "*"
      }
      ,
      {
        Effect = "Allow",
        Action = [
          "apprunner:CreateService"
        ],
        Resource = "*"
      }
      ,
      {
        Effect = "Allow",
        Action = [
          "iam:PassRole"
        ],
        Resource = [
          aws_iam_role.apprunner_instance_role.arn,
          aws_iam_role.apprunner_service_role.arn
        ]
      }
      ,
      {
        Effect = "Allow",
        Action = [
          "secretsmanager:DescribeSecret",
          "secretsmanager:GetSecretValue"
        ],
        Resource = aws_secretsmanager_secret.openai_key.arn
      }
    ]
  })
}

# 角色：GitHub Actions 将 "扮演" 这个角色
resource "aws_iam_role" "github_actions_role" {
  name = "github-actions-deploy-role"
  
  # 信任策略：只允许来自您特定仓库的 main 分支的请求
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_oidc.arn
        },
        Action = "sts:AssumeRoleWithWebIdentity",
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:sub" : "repo:${var.github_org_or_user}/${var.github_repo_name}:ref:refs/heads/main"
          }
        }
      }
    ]
  })
}

# 附加策略到角色
resource "aws_iam_role_policy_attachment" "github_actions" {
  role       = aws_iam_role.github_actions_role.name
  policy_arn = aws_iam_policy.github_actions_policy.arn
}

# -----------------------------------------------------------------
# 2. RAG 应用本身所需的基础设施
# -----------------------------------------------------------------

variable "openai_api_key" {
  description = "OpenAI API Key (将存入 Secrets Manager)"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.openai_api_key) > 0
    error_message = "OpenAI API Key 不能为空。"
  }
}

variable "manage_apprunner_via_terraform" {
  description = "是否由 Terraform 管理创建 App Runner 服务（默认关闭，交由 GitHub Actions 部署）"
  type        = bool
  default     = false
}

# 安全存储 API Key
resource "aws_secretsmanager_secret" "openai_key" {
  name = "rag-app-openai-key"
  recovery_window_in_days = 0
}
resource "aws_secretsmanager_secret_version" "openai_key_value" {
  count         = var.openai_api_key != "" ? 1 : 0
  secret_id     = aws_secretsmanager_secret.openai_key.id
  secret_string = var.openai_api_key
}

# ECR 镜像仓库
resource "aws_ecr_repository" "rag_app_ecr" {
  name = "rag-app"
  force_delete = true
}

# App Runner 服务角色：用于拉取 ECR 镜像
resource "aws_iam_role" "apprunner_service_role" {
  name = "rag-app-apprunner-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "build.apprunner.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# App Runner 实例角色：用于在运行时读取 Secrets Manager
resource "aws_iam_role" "apprunner_instance_role" {
  name = "rag-app-instance-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "tasks.apprunner.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "apprunner_secrets" {
  name = "rag-app-secrets-policy"
  role = aws_iam_role.apprunner_instance_role.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow",
      Action   = "secretsmanager:GetSecretValue",
      Resource = aws_secretsmanager_secret.openai_key.arn
    }]
  })
}

# App Runner 服务
resource "aws_apprunner_service" "rag_app_service" {
  count = var.manage_apprunner_via_terraform ? 1 : 0
  service_name = "rag-app"
  
  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_service_role.arn
    }
    image_repository {
      image_identifier      = "${aws_ecr_repository.rag_app_ecr.repository_url}:latest" # 使用现有 latest 镜像，避免创建失败
      image_repository_type = "ECR"
      image_configuration {
        port = "8080"
        runtime_environment_secrets = {
          OPENAI_API_KEY = aws_secretsmanager_secret.openai_key.arn
        }
      }
    }
    auto_deployments_enabled = false # 我们用 GitHub Actions 手动触发
  }
  instance_configuration {
    cpu    = "1024" # 1 vCPU
    memory = "2048" # 2 GB
    instance_role_arn = aws_iam_role.apprunner_instance_role.arn
  }
}

# 为 App Runner 服务角色授予 ECR 读取权限
resource "aws_iam_role_policy" "apprunner_ecr_access" {
  name = "rag-app-ecr-access-policy"
  role = aws_iam_role.apprunner_service_role.name
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:DescribeImages",
          "ecr:GetAuthorizationToken"
        ],
        Resource = aws_ecr_repository.rag_app_ecr.arn
      },
      {
        Effect = "Allow",
        Action = ["ecr:GetAuthorizationToken"],
        Resource = "*"
      }
    ]
  })
}

# --- 输出 ---
output "github_actions_role_arn" {
  value = aws_iam_role.github_actions_role.arn
  description = "复制到 GitHub Secret: AWS_IAM_ROLE_TO_ASSUME"
}
output "ecr_repository_name" {
  value = aws_ecr_repository.rag_app_ecr.name
  description = "复制到 GitHub Secret: ECR_REPOSITORY"
}
output "apprunner_service_arn" {
  value = can(aws_apprunner_service.rag_app_service[0].arn) ? aws_apprunner_service.rag_app_service[0].arn : null
  description = "复制到 GitHub Secret: APP_RUNNER_ARN"
}
output "apprunner_url" {
  value = can(aws_apprunner_service.rag_app_service[0].service_url) ? "https://portal.aws.amazon.com/goto/object/AppRunner?${aws_apprunner_service.rag_app_service[0].service_url}" : null
  description = "RAG 应用的公开访问 URL (需登录 AWS 查看)"
}