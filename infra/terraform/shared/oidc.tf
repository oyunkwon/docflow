# GitHub Actions OIDC — 정적 Access Key 없이 CI가 ECR에 push하도록 한다.
# 신뢰 정책은 이 레포의 main 브랜치로만 제한한다.

data "aws_caller_identity" "current" {}

# GitHub OIDC 엔드포인트의 실제 인증서에서 thumbprint를 동적으로 계산한다.
# 하드코딩하면 GitHub이 인증서를 갱신할 때 STS가 토큰을 거부한다.
data "tls_certificate" "github" {
  url = "https://token.actions.githubusercontent.com/.well-known/openid-configuration"
}

# GitHub의 OIDC IdP. 계정당 하나만 존재할 수 있다.
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github.certificates[0].sha1_fingerprint]
}

data "aws_iam_policy_document" "github_actions_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # main 브랜치의 워크플로우만 이 역할을 assume할 수 있다.
    # 이 계정/레포는 GitHub의 immutable unique ID 옵션이 켜져 있어 sub가
    # 'repo:<owner>@<ownerId>/<repo>@<repoId>:ref:...' 형식으로 온다.
    # 숫자 ID는 하드코딩하지 않고 와일드카드로 두되, owner/repo/브랜치는 고정한다.
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:oyunkwon*/docflow*:ref:refs/heads/main"]
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name               = "github-actions-docflow"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume.json
}

# ECR push에 필요한 최소 권한.
# GetAuthorizationToken은 리소스 단위 제한이 불가능해 *이지만,
# 실제 push/pull 액션은 docflow-* 저장소 3개로 제한한다.
data "aws_iam_policy_document" "ecr_push" {
  statement {
    sid       = "EcrAuth"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid    = "EcrPush"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:PutImage",
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
    ]
    resources = [for repo in aws_ecr_repository.this : repo.arn]
  }
}

resource "aws_iam_role_policy" "ecr_push" {
  name   = "ecr-push"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.ecr_push.json
}
