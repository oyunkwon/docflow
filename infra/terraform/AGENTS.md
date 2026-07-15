# infra/terraform

AWS 인프라. 커뮤니티 모듈로 조립한다. VPC/EKS를 직접 작성하지 않는다.

## 모듈 버전 (고정)

인터넷 예제는 대부분 구버전이다. 그대로 쓰면 `Unsupported argument`가 난다.

- AWS provider: `~> 6.0` (EKS 모듈 v21이 6.42+ 요구)
- `terraform-aws-modules/vpc/aws`: `~> 6.0`
- `terraform-aws-modules/eks/aws`: `~> 21.0`
- EKS 쿠버네티스 버전: `1.35`

버전을 올릴 때는 `terraform init -upgrade` 후 반드시 `validate`로 인자명을 확인한다.

## EKS 모듈 v21 인자명

v20에서 인자명이 대거 바뀌었다. 예제가 v20 이하면 아래로 치환한다.

| 옛 인자 (v20 이하)              | v21 인자                  |
|--------------------------------|---------------------------|
| `cluster_name`                 | `name`                    |
| `cluster_version`              | `kubernetes_version`      |
| `cluster_endpoint_public_access` | `endpoint_public_access` |
| `cluster_addons`               | `addons`                  |

- `vpc-cni`, `eks-pod-identity-agent` 애드온은 `before_compute = true`가 필수다.
- 노드가 붙기 전에 CNI와 Pod Identity가 준비돼야 한다.

## VPC 모듈 v6

- v6도 인자가 바뀌었을 수 있다. `validate`로 확인하고 쓴다.
- NAT: `single_nat_gateway = true` (비용).
- 서브넷 태그 필수:
  - public: `kubernetes.io/role/elb = 1`
  - private: `kubernetes.io/role/internal-elb = 1`

## Root module 구조

apply 단위는 root module이다. `modules/`는 직접 apply하지 않고 `module` 블록으로 호출한다.

- `bootstrap/` — tfstate 저장소 자체. 로컬 state.
- `environments/dev/`, `environments/prod/` — 환경별 인프라. VPC, EKS, RDS, S3, SQS.
- `shared/` — 환경 간 공유 리소스(ECR 등). 라이프사이클이 dev와 다르다. **아직 미생성.**

환경 진입점 `main.tf`는 모듈 조립만 한다. 리소스를 직접 선언하지 않는다.

## State

- 백엔드: S3 + S3 네이티브 잠금 (`use_lockfile = true`).
- 버킷: `docflow-tfstate-676591241328`
- key: `dev/terraform.tfstate`, `prod/terraform.tfstate`, `shared/terraform.tfstate`
- `dynamodb_table` 파라미터는 쓰지 않는다 (deprecated).

## 라이프사이클

- dev는 매일 destroy 대상이다. 오래 살아야 하는 리소스(ECR 이미지 등)를 dev state에 두지 않는다.
- EKS 컨트롤 플레인 + NAT은 하루 약 $6. 연습 후 반드시 destroy한다.
- apply 전에 반드시 `plan`을 검토한다.
