cat > AGENTS.md << 'EOF'
# DocFlow

PDF 업로드 → 비동기 메타데이터 추출 → 결과 조회.
EKS/GitOps 전주기 연습용 프로젝트.

## 레이어 경계

레포는 하나지만 책임은 완전히 분리한다.

- `apps/` 제품 코드. Docker 이미지로 빌드됨
- `infra/terraform/` AWS 기반 인프라. VPC, EKS, RDS, S3, SQS, ECR, IAM
- `gitops/` 클러스터 내부의 원하는 상태. Deployment, Service, Ingress 등

Terraform은 클러스터를 만들고, ArgoCD는 클러스터 위에서 무엇이 돌지 관리한다.
이 경계를 절대 섞지 않는다. Terraform이 Deployment를 만들지 않고,
GitOps가 AWS 리소스를 만들지 않는다.

예외: ArgoCD 자체는 Terraform이 Helm으로 부트스트랩한다 (닭과 달걀 문제).

## 스택

- API: FastAPI (Python)
- Worker: Python. SQS 소비, PDF 메타데이터 추출
- Frontend: React
- DB: RDS PostgreSQL
- 저장소: S3
- 큐: SQS + DLQ

인증 없음. 나중에 추가 시 documents에 user_id FK를 붙인다.

## 환경

dev / prod 두 개. stage 없음.

리전: ap-northeast-2 (서울)
AWS 계정: 676591241328

## 네이밍 컨벤션

AWS 리소스: `docflow-{env}-{resource}`
- docflow-dev-vpc
- docflow-dev-eks
- docflow-dev-documents (S3)
- docflow-dev-jobs (SQS)

ECR 저장소는 환경 구분 없음 (이미지는 환경 간 승격됨):
- docflow-api
- docflow-worker
- docflow-frontend

K8s 네임스페이스: `docflow`

## 브랜치 전략

trunk-based. `main` 하나 + 짧게 유지되는 feature 브랜치.
장기 develop 브랜치를 만들지 않는다.

브랜치와 환경을 일대일로 연결하지 않는다.
환경 분리는 GitOps overlay 디렉터리로 한다.

## 배포 원칙

이미지 태그는 Git commit SHA. `latest`를 쓰지 않는다.

이미지는 한 번만 빌드하고 환경 간 승격한다. 환경별 재빌드 금지.
환경별로 바뀌는 건 이미지가 아니라 GitOps의 태그다.

## Terraform

state: S3 백엔드 + S3 네이티브 잠금 (`use_lockfile = true`)
버킷: docflow-tfstate-676591241328
- dev/terraform.tfstate
- prod/terraform.tfstate

`dynamodb_table` 파라미터는 deprecated. 쓰지 않는다.

root module은 세 개:
- `infra/terraform/bootstrap/` (state 저장소 자체. 로컬 state)
- `infra/terraform/environments/dev/`
- `infra/terraform/environments/prod/`

`modules/`는 직접 apply하지 않는다. root module에서 `module` 블록으로 호출한다.

환경 진입점의 `main.tf`는 모듈 조립만 한다. 리소스를 직접 선언하지 않는다.

## GitOps

Kustomize 사용. Helm chart를 직접 만들지 않는다.

App of Apps 구조. Root Application 하나가 나머지를 불러온다.

base에 공통 설정, overlay에 환경별 차이만.
CI가 수정하는 건 overlay의 `newTag` 하나다.

## 보안

정적 AWS Access Key를 Pod에 넣지 않는다. EKS Pod Identity 사용.

Git에 커밋해도 되는 것: 버킷명, 큐 URL, 리전, 로그 레벨
Git에 커밋하면 안 되는 것: DB 비밀번호, 시크릿 키

시크릿은 Secrets Manager에 두고 앱 시작 시 SDK로 조회한다.
External Secrets Operator는 지금 단계에서 넣지 않는다.

`*.tfvars`는 gitignore 대상. `.example`만 커밋한다.

## 이번 범위에서 제외

Karpenter, Prometheus/Grafana, Service Mesh, Kafka, Redis,
Multi-cluster, External Secrets Operator, Argo Rollouts,
Canary, SSO, stage 환경.

첫 완성이 목표다. 도구를 늘리지 않는다.

## 비용

EKS 컨트롤 플레인은 시간당 과금된다. 연습 후 반드시 destroy.
NAT Gateway도 시간당 과금. 유령 리소스로 남지 않게 주의.
EOF
