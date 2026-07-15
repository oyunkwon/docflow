terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 3.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
    # 부트스트랩 전용. kubernetes_manifest는 plan 시점에 클러스터 API를 요구해
    # 단일 apply(클러스터가 아직 없음)에서 실패한다. kubectl_manifest는 plan 시점
    # API가 불필요해 root Application 부트스트랩에 적합하다. 이유는 docs/decisions.md.
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = "~> 1.14"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# ── kubernetes/helm provider 인증 ────────────────────────────────────────────
# 주의(트레이드오프): 아래 provider 설정은 module.eks의 "computed" 출력에 의존한다.
# HashiCorp와 EKS Blueprints 문서 모두 provider 블록에 computed 값을 넣는 것을
# 권장하지 않는다(클러스터가 아직 없을 때 provider 초기화가 꼬일 수 있음).
# 실무 정석은 클러스터(1)와 그 위 리소스(2)를 별도 workspace로 나누는 것.
# 이번 연습은 단일 root module로 가고, exec 플러그인(aws eks get-token)으로
# 매 실행 시 토큰을 새로 받고 depends_on으로 순서를 강제한다.
# 이유는 docs/decisions.md 참조.

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name, "--region", var.aws_region]
  }
}

provider "helm" {
  kubernetes = {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

    exec = {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name, "--region", var.aws_region]
    }
  }
}

provider "kubectl" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  load_config_file       = false

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name, "--region", var.aws_region]
  }
}
