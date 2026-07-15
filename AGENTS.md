# DocFlow

PDF 업로드 → SQS → Worker가 메타데이터 추출 → RDS 저장 → 조회.
EKS/GitOps 전주기 연습용 프로젝트.

규칙의 이유는 `docs/decisions.md`를 본다. 이 문서는 규칙만 담는다.

## 스택

- API: FastAPI (Python)
- Worker: Python. SQS 소비, PDF 메타데이터 추출
- Frontend: React
- DB: RDS PostgreSQL / 저장소: S3 / 큐: SQS + DLQ
- 인증 없음

## 레이어 경계

레포는 하나지만 책임은 완전히 분리한다. 이 경계를 절대 섞지 않는다.

- `apps/` — 제품 코드. Docker 이미지로 빌드된다. → `apps/AGENTS.md`
- `infra/terraform/` — AWS 인프라. VPC, EKS, RDS, S3, SQS, ECR, IAM. → `infra/terraform/AGENTS.md`
- `gitops/` — 클러스터 안에서 무엇이 돌지. Deployment, Service, Ingress. → `gitops/AGENTS.md`

Terraform은 클러스터를 만든다. GitOps는 클러스터 위에서 무엇이 돌지 정한다.
Terraform은 Deployment를 만들지 않는다. GitOps는 AWS 리소스를 만들지 않는다.
예외: ArgoCD 자체는 Terraform이 Helm으로 부트스트랩한다.

## 환경 / 리전 / 계정

- 환경: dev / prod 두 개. stage 없음.
- 리전: ap-northeast-2 (서울)
- AWS 계정: 676591241328

## 네이밍

- AWS 리소스: `docflow-{env}-{resource}` (예: docflow-dev-vpc, docflow-dev-documents)
- ECR: 환경 구분 없음 — `docflow-api`, `docflow-worker`, `docflow-frontend`
- K8s 네임스페이스: `docflow`

## 절대 규칙

- 이미지 태그는 Git commit SHA를 쓴다. `latest`를 쓰지 않는다.
- 이미지는 한 번만 빌드하고 환경 간 승격한다. 환경별 재빌드 금지.
- 환경 차이는 이미지가 아니라 GitOps overlay로 표현한다.
- 브랜치와 환경을 일대일로 묶지 않는다. 환경 분리는 overlay 디렉터리로 한다.
- 정적 AWS Access Key를 Pod에 넣지 않는다. EKS Pod Identity를 쓴다.
- 시크릿은 Secrets Manager에 두고 앱 시작 시 SDK로 조회한다. Git에 커밋하지 않는다.
- 커밋 가능: 버킷명, 큐 URL, 리전, 로그 레벨. 커밋 금지: DB 비밀번호, 시크릿 키.
- `*.tfvars`는 gitignore 대상. `.example`만 커밋한다.

## 브랜치 전략

trunk-based. `main` 하나 + 짧게 유지되는 feature 브랜치.
장기 develop 브랜치를 만들지 않는다.

## GitOps

Kustomize를 쓴다. Helm chart를 직접 만들지 않는다.
App of Apps 구조. Root Application 하나가 나머지를 불러온다.
base에 공통 설정, overlay에 환경별 차이만. CI가 수정하는 건 overlay의 `newTag` 하나다.

## 범위에서 제외

Karpenter, Prometheus/Grafana, Service Mesh, Kafka, Redis, Multi-cluster,
External Secrets Operator, Argo Rollouts, Canary, SSO, stage 환경.
첫 완성이 목표다. 도구를 늘리지 않는다.

## 비용

EKS 컨트롤 플레인과 NAT Gateway는 시간당 과금된다. 연습 후 반드시 destroy한다.
유령 리소스로 남지 않게 주의한다.
