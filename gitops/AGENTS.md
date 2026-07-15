# gitops

클러스터 안에서 무엇이 돌지 선언한다. AWS 리소스는 만들지 않는다(그건 infra/terraform).
ArgoCD가 이 디렉터리를 읽어 클러스터 상태를 맞춘다.

## 구조 (App of Apps)

- `bootstrap/root-application.yaml` — root Application. Terraform이 ArgoCD 설치 후 한 번 적용한다.
  root는 `environments/dev`를 가리키고, 거기 나열된 하위 Application들을 ArgoCD가 생성한다.
- `base/<app>/` — 공통 매니페스트. 환경에 무관한 부분.
- `environments/<env>/` — 그 환경의 Application 목록(App of Apps 자식).
- `environments/<env>/<app>/` — base를 참조하는 Kustomize overlay. 환경별 차이만.

두 층을 구분한다: `environments/dev/kustomization.yaml`은 **Application만** 나열하고,
`environments/dev/api/kustomization.yaml`은 **실제 워크로드**를 조립한다.

## Kustomize 규칙

- Kustomize만 쓴다. Helm chart를 직접 만들지 않는다.
- base에 공통, overlay에 차이만. base를 수정하면 모든 환경에 영향한다는 걸 기억한다.
- 이미지는 overlay의 `images:`로 확정한다. base에는 `DOCFLOW_<APP>_IMAGE` 플레이스홀더를 둔다.
- **CI가 건드리는 건 overlay `images`의 `newTag` 하나뿐이다.** 그 외 필드를 CI가 바꾸지 않는다.
- 태그는 commit SHA. `latest`/`placeholder`는 최초 배포용이며 실제 배포는 SHA로 덮는다.
- `commonLabels`(deprecated) 대신 `labels` + `includeSelectors: false`를 쓴다.
  selector에 라벨을 주입하면 기존 Deployment의 immutable selector와 충돌한다.

## 워크로드 규칙

- API/Frontend는 Service(ClusterIP) + Ingress를 가진다.
- **worker는 Service도 Ingress도 없다.** SQS를 폴링할 뿐 인바운드 트래픽을 받지 않는다.
- Ingress는 `ingressClassName: alb`. AWS Load Balancer Controller가 처리한다.
  같은 ALB를 공유하려면 `alb.ingress.kubernetes.io/group.name`을 맞춘다.
- 모든 Deployment는 readiness/liveness probe와 resources requests/limits를 가진다.
- ServiceAccount는 앱별로 둔다. 나중에 Pod Identity로 IAM Role을 매핑할 지점이다.

## 네임스페이스

- 앱은 `docflow` 네임스페이스. ArgoCD 자신은 `argocd`.
- overlay의 `namespace:`로 지정한다. 매니페스트에 하드코딩하지 않는다.

## 하지 않는 것

- Service Mesh, Argo Rollouts(카나리), External Secrets는 범위 밖.
- 시크릿을 매니페스트에 넣지 않는다. Secrets Manager + 앱 SDK 조회.
