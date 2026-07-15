#!/bin/bash
# LocalStack 준비 완료 후 자동 실행되는 초기화 훅.
# S3 버킷 + CORS, SQS 큐 + DLQ를 만든다.
set -euo pipefail

REGION="ap-northeast-2"
BUCKET="docflow-dev-documents"
QUEUE="docflow-dev-jobs"
DLQ="docflow-dev-jobs-dlq"

echo "[init] creating S3 bucket: $BUCKET"
awslocal s3api create-bucket \
  --bucket "$BUCKET" \
  --region "$REGION" \
  --create-bucket-configuration LocationConstraint="$REGION" || true

echo "[init] applying CORS to bucket (browser PUT via presigned url)"
awslocal s3api put-bucket-cors --bucket "$BUCKET" --cors-configuration '{
  "CORSRules": [
    {
      "AllowedMethods": ["PUT", "GET", "HEAD"],
      "AllowedOrigins": ["*"],
      "AllowedHeaders": ["*"],
      "ExposeHeaders": ["ETag"]
    }
  ]
}'

echo "[init] creating DLQ: $DLQ"
awslocal sqs create-queue --queue-name "$DLQ" --region "$REGION"

echo "[init] creating queue: $QUEUE"
awslocal sqs create-queue --queue-name "$QUEUE" --region "$REGION"

echo "[init] done"
