# Runbook — dev 전체 apply (아침 한 방)

목표: `terraform apply` 몇 번으로 클러스터 + ArgoCD + api Pod까지 띄우고,
`kubectl get nodes`가 Ready, api `/health/ready`가 200이 되는 것.

전제: 어제 dev는 destroy됨(state 0개, NAT/EIP 잔존 없음). shared/ECR은 아직 apply 안 함.
계정 676591241328, 리전 ap-northeast-2.

> 순서가 중요하다. shared(ECR) → dev(클러스터+ArgoCD) → 이미지 빌드/푸시 → 태그 갱신.
> ArgoCD가 Git을 보고 배포하므로, 태그 갱신 커밋은 **push**까지 해야 반영된다.

---

## 0. 사전 확인

```bash
aws sts get-caller-identity            # 676591241328 인지
kubectl version --client               # 1.36
terraform version                      # 1.15+
```

---

## 1. shared — ECR 3개 (한 번만. 매일 destroy 대상 아님)

```bash
cd infra/terraform/shared
terraform init          # 최초엔 backend S3 연결. -upgrade 불필요
terraform plan          # ECR 3개 + lifecycle policy 확인
terraform apply         # yes

terraform output repository_urls
```

기대 출력(예):
```
docflow-api      = 676591241328.dkr.ecr.ap-northeast-2.amazonaws.com/docflow-api
docflow-worker   = ...docflow-worker
docflow-frontend = ...docflow-frontend
```

---

## 2. dev — VPC + EKS + Blueprints Addons + ArgoCD + root App

```bash
cd ../environments/dev
terraform init          # helm/kubernetes/kubectl provider가 이미 lock에 있음
terraform plan          # 클러스터 + 애드온 + argocd + root-app. 60+ 리소스
terraform apply         # yes. 15~20분 (컨트롤플레인 ~8분 + 애드온/노드/argocd)
```

주의(컨트롤 플레인 대기 중 네트워크 끊김 → taint 사고):
- apply 중 로컬 WiFi/VPN이 끊기면 `aws_eks_cluster`가 tainted 되어 재실행 시
  409(already exists)가 날 수 있다. 그때:
  ```bash
  aws eks describe-cluster --region ap-northeast-2 --name docflow-dev --query cluster.status
  # ACTIVE 확인되면:
  terraform untaint 'module.eks.aws_eks_cluster.this[0]'
  terraform apply
  ```

apply 끝나면:
```bash
aws eks update-kubeconfig --region ap-northeast-2 --name docflow-dev
kubectl get nodes                      # 노드 2대 Ready  ← 1차 목표
kubectl get pods -n argocd             # argocd 컴포넌트 Running
kubectl get applications -n argocd     # root, api Application 보임
```

이 시점에 api Pod는 `docflow-api:placeholder` 이미지를 당기려다 **ImagePullBackOff**가
정상이다(아직 이미지를 안 올림). 3번에서 실제 이미지를 올리고 태그를 갱신하면 해소된다.

---

## 3. 이미지 빌드 & 푸시 (반드시 --platform linux/amd64)

맥은 arm64다. 그냥 빌드하면 arm64 이미지가 나오고, 노드(AL2023 x86_64)에서
`exec format error`로 CrashLoopBackOff 난다. **--platform linux/amd64 필수.**

```bash
cd ../../../..            # 레포 루트
ACCOUNT=676591241328
REGION=ap-northeast-2
REGISTRY=$ACCOUNT.dkr.ecr.$REGION.amazonaws.com
SHA=$(git rev-parse --short HEAD)      # 이미지 태그 = commit SHA

# ECR 로그인
aws ecr get-login-password --region $REGION \
  | docker login --username AWS --password-stdin $REGISTRY

# api 이미지 (오늘 배포 대상). buildx로 플랫폼 명시.
docker buildx build --platform linux/amd64 \
  -t $REGISTRY/docflow-api:$SHA \
  --push \
  ./apps/api

echo "pushed: $REGISTRY/docflow-api:$SHA"
```

> `--push`가 buildx에서 바로 레지스트리로 올린다. `docker build`(레거시)를 쓸 거면
> `docker build --platform linux/amd64 ...` 후 `docker push`.
> worker/frontend는 오늘 배포 안 하지만 올려두려면 같은 방식으로.

---

## 4. 이미지 태그 갱신 → 커밋 → push (ArgoCD가 이걸 본다)

CI가 하는 일을 손으로 한다. overlay의 newTag만 바꾼다.

```bash
# gitops/environments/dev/api/kustomization.yaml 의 newTag를 SHA로.
# (standalone kustomize 없으면 파일을 직접 편집)
cd gitops/environments/dev/api
kubectl kustomize . | grep image:      # 현재 placeholder 확인

# newTag: placeholder → newTag: <SHA> 로 편집 후:
git add gitops/environments/dev/api/kustomization.yaml
git commit -m "deploy(api): $SHA"
git push origin main                   # ★ push해야 ArgoCD가 본다
```

> 지금 브랜치는 feat/platform이다. root-application.yaml은 targetRevision: main을 본다.
> 오늘 실제 배포까지 하려면 이 브랜치를 main에 머지(push)해야 ArgoCD가 동기화한다.
> 머지 없이 테스트만 하려면 root-application.yaml의 targetRevision을 현재 브랜치로
> 잠깐 바꿔도 되지만, trunk-based 방침상 머지가 정석이다.

---

## 5. 배포 확인

```bash
# ArgoCD가 자동 동기화(automated). 강제로 보고 싶으면 UI/CLI에서 sync.
kubectl get applications -n argocd            # api: Synced / Healthy
kubectl get pods -n docflow                   # api Pod Running, READY 1/1
kubectl logs -n docflow deploy/api            # uvicorn startup complete

# ALB 주소 확인 (LB 컨트롤러가 Ingress로 ALB 생성. 2~3분 걸림)
kubectl get ingress -n docflow
ADDR=$(kubectl get ingress api -n docflow -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl -s http://$ADDR/api/health/ready         # {"status":"ready","db":"disabled"}
curl -s http://$ADDR/api/health/live          # {"status":"ok"}
```

ArgoCD UI:
```bash
kubectl port-forward -n argocd svc/argo-cd-argocd-server 8080:80
# 초기 admin 비밀번호:
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d; echo
# http://localhost:8080  (user: admin)
```

---

## 6. 하루 끝 — 반드시 destroy (dev만. shared는 남긴다)

```bash
cd infra/terraform/environments/dev
terraform destroy        # yes

# 잔존 확인 (NAT/EIP가 제일 자주 유령으로 남는다)
aws ec2 describe-nat-gateways --region ap-northeast-2 \
  --query 'NatGateways[?State!=`deleted`].[NatGatewayId,State]' --output text
aws ec2 describe-addresses --region ap-northeast-2 --query 'Addresses[].PublicIp' --output text
```

- 둘 다 비면 과금 끊긴 것.
- **shared(ECR)는 destroy하지 않는다.** 이미지를 보존하려고 dev와 state를 분리한 것.
- destroy 시 helm/kubectl provider가 사라진 클러스터 API를 붙잡아 에러가 나면,
  해당 리소스만 state에서 제거 후 재시도:
  ```bash
  terraform state rm kubectl_manifest.argocd_root_app helm_release.argocd 2>/dev/null
  terraform destroy
  ```

---

## 비용 메모

EKS 컨트롤플레인 + NAT + t3.medium×2 + ALB ≈ 하루 $6~7. 끝나면 6번 반드시 실행.

## 오늘 apply 안 하는 것

RDS, S3, SQS, worker, frontend. API는 health만. DB 없이 뜨도록 코드가 처리한다
(DATABASE_URL 없으면 readiness가 db:disabled로 통과).
