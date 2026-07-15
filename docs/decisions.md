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
