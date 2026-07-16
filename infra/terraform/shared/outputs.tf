output "repository_urls" {
  description = "ECR repository URLs keyed by repo name"
  value       = { for name, repo in aws_ecr_repository.this : name => repo.repository_url }
}

output "api_repository_url" {
  description = "ECR URL for docflow-api"
  value       = aws_ecr_repository.this["docflow-api"].repository_url
}

output "worker_repository_url" {
  description = "ECR URL for docflow-worker"
  value       = aws_ecr_repository.this["docflow-worker"].repository_url
}

output "frontend_repository_url" {
  description = "ECR URL for docflow-frontend"
  value       = aws_ecr_repository.this["docflow-frontend"].repository_url
}

output "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions OIDC (ECR push)"
  value       = aws_iam_role.github_actions.arn
}
