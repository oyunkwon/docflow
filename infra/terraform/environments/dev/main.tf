data "aws_availability_zones" "available" {
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

locals {
  name     = "${var.project_name}-${var.environment}"
  vpc_cidr = "10.0.0.0/16"
  azs      = slice(data.aws_availability_zones.available.names, 0, 2)
}

################################################################################
# VPC
################################################################################

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 6.0"

  name = "${local.name}-vpc"
  cidr = local.vpc_cidr

  azs             = local.azs
  private_subnets = [for k, v in local.azs : cidrsubnet(local.vpc_cidr, 4, k)]
  public_subnets  = [for k, v in local.azs : cidrsubnet(local.vpc_cidr, 8, k + 48)]

  enable_nat_gateway = true
  single_nat_gateway = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }

  database_subnets             = [for k, v in local.azs : cidrsubnet(local.vpc_cidr, 8, k + 52)]
  create_database_subnet_group = true
}

################################################################################
# EKS
################################################################################

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = local.name
  kubernetes_version = "1.35"

  # 로컬 kubectl 접근용. 클러스터 생성자에게 admin access entry를 자동 부여.
  endpoint_public_access                   = true
  enable_cluster_creator_admin_permissions = true

  addons = {
    coredns    = {}
    kube-proxy = {}
    vpc-cni = {
      before_compute = true
    }
    eks-pod-identity-agent = {
      before_compute = true
    }
  }

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    default = {
      ami_type       = "AL2023_x86_64_STANDARD"
      instance_types = ["t3.medium"]

      min_size     = 2
      max_size     = 3
      desired_size = 2
    }
  }
}

################################################################################
# EKS Blueprints Addons — AWS Load Balancer Controller + metrics-server
################################################################################

module "eks_blueprints_addons" {
  source  = "aws-ia/eks-blueprints-addons/aws"
  version = "~> 1.0"

  cluster_name      = module.eks.cluster_name
  cluster_endpoint  = module.eks.cluster_endpoint
  cluster_version   = module.eks.cluster_version
  oidc_provider_arn = module.eks.oidc_provider_arn

  # Ingress(alb ingressClass)를 위해 LB 컨트롤러, HPA/kubectl top을 위해 metrics-server.
  # Karpenter/Prometheus 등 나머지는 켜지 않는다(범위 밖).
  enable_aws_load_balancer_controller = true
  enable_metrics_server               = true

  # 노드가 준비된 뒤 애드온을 올린다.
  depends_on = [module.eks]
}

################################################################################
# ArgoCD 부트스트랩 (닭과 달걀: GitOps 엔진 자체는 Terraform이 설치)
################################################################################

resource "helm_release" "argocd" {
  name             = "argo-cd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  version          = var.argocd_chart_version
  namespace        = "argocd"
  create_namespace = true

  # ArgoCD 서버는 LoadBalancer로 노출하지 않는다. ClusterIP + kubectl port-forward.
  # ALB 하나를 아끼고 API 서버를 인터넷에 열지 않는다.
  set = [
    {
      name  = "server.service.type"
      value = "ClusterIP"
    },
  ]

  # 애드온(특히 LB 컨트롤러)이 준비된 뒤 ArgoCD를 올린다.
  depends_on = [module.eks_blueprints_addons]
}

# App of Apps 루트. ArgoCD 설치 후 root Application을 적용하면
# 나머지(gitops/environments/dev)는 ArgoCD가 스스로 동기화한다.
resource "kubectl_manifest" "argocd_root_app" {
  yaml_body = file("${path.module}/../../../../gitops/bootstrap/root-application.yaml")

  depends_on = [helm_release.argocd]
}
