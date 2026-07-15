# 결정 기록 (decisions)

AGENTS.md는 규칙만 담는다. 여기엔 그 규칙을 왜 그렇게 정했는지 남긴다.

## 왜 3레이어(apps / infra / gitops)를 분리하나

책임과 변경 주기가 다르기 때문이다.

- infra(Terraform)는 클러스터라는 "그릇"을 만든다. 자주 바뀌지 않는다.
- gitops는 그 그릇 위에서 무엇이 돌지 정한다. 배포마다 바뀐다.
- apps는 이미지로 빌드되는 제품 코드다.

한 도구가 두 역할을 겸하면 경계가 무너진다. Terraform으로 Deployment를 만들면
매 배포가 terraform apply가 되어 GitOps의 선언적 배포 이점이 사라진다.
반대로 GitOps가 AWS 리소스를 만들면 인프라 상태가 두 곳에 흩어진다.

예외는 ArgoCD 부트스트랩뿐이다. ArgoCD가 없으면 GitOps를 시작할 수 없으니
최초의 ArgoCD 설치만 Terraform이 Helm으로 한다(닭과 달걀).

## 왜 이미지를 환경 간 승격만 하고 재빌드하지 않나

dev에서 검증한 것과 prod에 뜨는 것이 "같은 바이너리"임을 보장하기 위해서다.
환경별로 재빌드하면 빌드 시점의 의존성/베이스이미지 차이로 미묘하게 다른 산출물이 나온다.
그래서 태그는 commit SHA로 고정하고, 환경 차이는 GitOps overlay로만 표현한다.
`latest`는 어떤 커밋인지 추적 불가라 금지한다.

## 왜 브랜치와 환경을 묶지 않나

trunk-based를 쓰는데 브랜치=환경으로 묶으면 장기 브랜치가 생기고 머지 지옥이 온다.
환경 분리는 코드(overlay 디렉터리)로 표현하는 게 추적 가능하고 되돌리기 쉽다.

## 왜 Pod Identity인가 (정적 키 금지)

정적 Access Key는 Pod 스펙/시크릿에 박히면 유출 위험이 크고 로테이션이 번거롭다.
EKS Pod Identity는 ServiceAccount에 IAM Role을 매핑해 단기 자격증명을 자동 발급한다.
IRSA보다 설정이 단순하다(OIDC provider 신뢰관계를 직접 안 짜도 됨).

## 왜 state에 S3 네이티브 잠금(use_lockfile)인가

Terraform 1.10+부터 S3 자체로 잠금이 가능해져 DynamoDB 잠금 테이블이 불필요해졌다.
운영할 리소스가 하나 줄어든다. bootstrap의 DynamoDB 테이블은 그래서 미사용이며 나중에 제거한다.

## 왜 ECR을 dev state에 두지 않고 shared로 빼나

dev는 매일 destroy하는데 ECR이 dev state에 있으면 destroy 때 이미지가 같이 날아간다.
또 ECR은 정의상 환경 공용(이미지를 dev→prod로 승격)이라 특정 환경 state에 속하면
논리적으로 이상하다(prod가 dev state에 의존하는 꼴). 라이프사이클이 다른 리소스는
state를 분리하는 게 정석이다. → `infra/terraform/shared/` (아직 미생성)

## 왜 커뮤니티 모듈(terraform-aws-modules)을 쓰나

VPC/EKS를 직접 작성하면 서브넷/라우팅/애드온/노드그룹 배선을 전부 손으로 맞춰야 한다.
연습의 목적은 전주기 흐름 경험이지 VPC 재발명이 아니다. 검증된 모듈로 조립한다.
단, 모듈 메이저 버전이 오르면 인자명이 바뀌므로 버전을 고정하고 validate로 확인한다.

## 왜 EKS 모듈 v21 / provider v6인가

v21에서 인자명이 대거 바뀌었고(cluster_name→name 등), v21은 AWS provider 6.42+를 요구한다.
인터넷 예제 다수가 v20 이하 기준이라 그대로 붙이면 Unsupported argument가 난다.
버전과 인자 매핑은 `infra/terraform/AGENTS.md`에 표로 고정해뒀다.

## 범위를 왜 이렇게 좁히나

Karpenter, Prometheus, Service Mesh 등은 각각이 별도 학습 곡선이다.
첫 목표는 "전주기가 끝까지 돈다"이지 도구 수집이 아니다. 완성 후에 하나씩 늘린다.

## 왜 클러스터와 그 위 리소스를 단일 root module로 두나 (트레이드오프)

정석은 클러스터(EKS)와 그 위에 얹는 리소스(Helm/ArgoCD)를 **별도 workspace로 분리**하는 것이다.
이유: helm/kubernetes provider 설정이 `module.eks`의 computed 출력(endpoint, CA)에 의존하는데,
HashiCorp도 EKS Blueprints 문서도 "provider 블록에 computed 값을 넣지 말라"고 명시한다.
클러스터가 아직 없을 때 provider 초기화가 꼬이거나, 클러스터를 destroy할 때 provider가
사라진 API를 붙잡고 apply/destroy가 실패하는 사고가 난다.

그럼에도 이번 연습은 단일 root module로 간다. 이유는 학습 목적상 "apply 한 번에 클러스터부터
ArgoCD까지 뜬다"는 전주기 경험이 우선이기 때문이다. 대신 사고를 줄이려고:
- exec 플러그인(`aws eks get-token`)으로 매 실행 시 토큰을 새로 받는다(정적 토큰 금지).
- `depends_on`으로 eks → blueprints-addons → argocd → root-app 순서를 강제한다.

실무에 들어가면 이 구조를 workspace 분리로 바꾼다. 지금은 그 트레이드오프를 알고 택한 것이다.

## 왜 root Application 적용에 kubectl_manifest(gavinbunney)를 쓰나

공식 `kubernetes_manifest`(hashicorp/kubernetes)는 **plan 시점에 클러스터 API에 접속**해
스키마 dry-run을 한다. 단일 apply 플로우에서는 plan 시점에 클러스터가 아직 없어서 plan이 실패한다.
→ "한 번에 apply" 목표가 깨진다.

`gavinbunney/kubectl`의 `kubectl_manifest`는 plan 시점에 API가 필요 없어 부트스트랩에 적합하다.
그래서 이 provider 하나를 helm/kubernetes 외에 추가로 도입했다. 용도는 root Application 적용
한 곳뿐이다. 이후의 모든 배포는 ArgoCD가 Git에서 동기화하므로 Terraform이 매니페스트를 더 다루지 않는다.

## 왜 API를 DB 없이도 뜨게 만드나 (DATABASE_URL optional)

이번 배포 범위는 "API가 health만 응답"이다. RDS/S3/SQS는 아직 붙이지 않는다.
기존 코드는 시작 시 `create_all`로 DB에 무조건 접속해서, DB가 없으면 프로세스가 죽고
readiness 이전에 CrashLoopBackOff가 난다.

ConfigMap을 optional로 두는 방식은 설정만 뺄 뿐 코드가 여전히 DB를 강제하므로 크래시가 그대로다.
그래서 코드가 **DATABASE_URL 유무로 동작을 결정**하게 고쳤다: 없으면 DB 엔진을 안 만들고
readiness는 `db: disabled`로 통과, 문서 라우트는 503으로 명확히 거부한다.
RDS를 붙이는 단계에서 overlay가 DATABASE_URL을 채우면 그때부터 readiness가 DB를 검사한다.
CI가 건드리는 건 여전히 newTag 하나뿐이라 GitOps 방침과 일관된다.

## 왜 ArgoCD를 ClusterIP + port-forward로 두나

ArgoCD 서버를 LoadBalancer로 노출하면 ALB가 하나 더 뜨고(비용) API 서버가 인터넷에 열린다.
접속은 `kubectl port-forward`로 충분하다. ALB를 아끼고 노출면을 줄인다.

