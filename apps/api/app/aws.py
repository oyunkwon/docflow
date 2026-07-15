import boto3
from botocore.config import Config

from .config import settings


def _endpoint(public: bool = False) -> str | None:
    """LocalStack이 없으면 None을 반환해 실제 AWS로 붙게 한다."""
    if public and settings.s3_public_endpoint:
        return settings.s3_public_endpoint
    return settings.aws_endpoint_url or None


def _s3(public: bool = False):
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        endpoint_url=_endpoint(public),
        # LocalStack에서 path-style이 필요하다.
        config=Config(s3={"addressing_style": "path"}, signature_version="s3v4"),
    )


# 서버 내부 작업용 (버킷 접근). 브라우저가 접근하지 않는다.
s3_internal = _s3(public=False)
# presigned URL 발급용. 브라우저가 접근할 host로 서명한다.
s3_presign = _s3(public=True)

sqs = boto3.client(
    "sqs",
    region_name=settings.aws_region,
    endpoint_url=_endpoint(public=False),
)


def presign_put(key: str, content_type: str = "application/pdf") -> str:
    return s3_presign.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.s3_bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=settings.presign_expiry,
    )


def send_job(document_id: str) -> None:
    sqs.send_message(
        QueueUrl=settings.sqs_queue_url,
        MessageBody=document_id,
    )
