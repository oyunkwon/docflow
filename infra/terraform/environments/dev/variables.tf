variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-2"
}

variable "project_name" {
  description = "Project name used as resource name prefix"
  type        = string
  default     = "docflow"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "argocd_chart_version" {
  description = "argo-cd Helm chart version (argoproj.github.io/argo-helm)"
  type        = string
  default     = "7.7.11"
}
