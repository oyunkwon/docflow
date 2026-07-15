# apps

제품 코드. 각 디렉터리는 독립된 Docker 이미지로 빌드된다.

- `api/` — FastAPI. presigned URL 발급, 문서 행 생성, SQS 발행, 조회.
- `worker/` — SQS 소비. S3에서 PDF 받아 메타데이터 추출 후 RDS 갱신.
- `frontend/` — React. 업로드 폼, 목록, 상태 폴링.

## 규칙

- AWS 자격증명은 boto3 기본 자격증명 체인에 맡긴다. 코드에 키를 넣지 않는다.
  운영에서는 EKS Pod Identity가, 로컬에서는 compose의 더미 키가 채운다.
- 설정은 전부 환경변수로 받는다: `DATABASE_URL`, `S3_BUCKET`, `SQS_QUEUE_URL`, `AWS_REGION`.
  로컬 전용: `AWS_ENDPOINT_URL`(LocalStack 내부), `S3_PUBLIC_ENDPOINT`(브라우저용 presigned host).
- `AWS_ENDPOINT_URL`이 없으면 실제 AWS로 붙는다. 운영에서는 이 변수를 넣지 않는다.
- 문서 상태 흐름: `PENDING → PROCESSING → COMPLETED` / 실패 시 `FAILED`.
- api와 worker는 같은 documents 테이블을 공유하지만 코드는 공유하지 않는다.
  각자 자기 모델 정의를 가진다. 이미지 경계를 지킨다.

## 로컬 실행

레포 루트에서 `docker compose up --build`.
PostgreSQL은 컨테이너, S3/SQS는 LocalStack. 프론트는 nginx가 `/api`를 api로 프록시한다.
