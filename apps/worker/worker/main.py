import logging
import signal
import sys
import time

import boto3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings
from .extract import extract_metadata
from .models import Document

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("worker")

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def _endpoint() -> str | None:
    return settings.aws_endpoint_url or None


s3 = boto3.client("s3", region_name=settings.aws_region, endpoint_url=_endpoint())
sqs = boto3.client("sqs", region_name=settings.aws_region, endpoint_url=_endpoint())

_running = True


def _stop(signum, frame):  # noqa: ANN001
    global _running
    log.info("received signal %s, shutting down", signum)
    _running = False


def _set_status(doc_id: str, status: str, **fields) -> bool:
    """문서 상태와 결과 필드를 갱신한다. 문서가 없으면 False."""
    with SessionLocal() as db:
        doc = db.get(Document, doc_id)
        if doc is None:
            log.warning("document %s not found in db", doc_id)
            return False
        doc.status = status
        for key, value in fields.items():
            setattr(doc, key, value)
        db.commit()
    return True


def process(doc_id: str) -> None:
    if not _set_status(doc_id, "PROCESSING"):
        return

    with SessionLocal() as db:
        doc = db.get(Document, doc_id)
        s3_key = doc.s3_key

    try:
        obj = s3.get_object(Bucket=settings.s3_bucket, Key=s3_key)
        pdf_bytes = obj["Body"].read()
        meta = extract_metadata(pdf_bytes)
    except Exception as exc:  # noqa: BLE001
        log.exception("failed to process %s", doc_id)
        _set_status(doc_id, "FAILED", error=str(exc))
        return

    _set_status(doc_id, "COMPLETED", error=None, **meta)
    log.info("completed %s: %s pages", doc_id, meta.get("page_count"))


def poll_once() -> None:
    resp = sqs.receive_message(
        QueueUrl=settings.sqs_queue_url,
        MaxNumberOfMessages=5,
        WaitTimeSeconds=settings.wait_time_seconds,
    )
    for msg in resp.get("Messages", []):
        doc_id = msg["Body"].strip()
        log.info("received job %s", doc_id)
        process(doc_id)
        # 처리 성공/실패와 무관하게 메시지를 삭제한다.
        # 실패는 FAILED로 DB에 남기므로 재시도 루프를 만들지 않는다(연습 범위).
        sqs.delete_message(
            QueueUrl=settings.sqs_queue_url,
            ReceiptHandle=msg["ReceiptHandle"],
        )


def main() -> None:
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    log.info("worker starting. queue=%s bucket=%s", settings.sqs_queue_url, settings.s3_bucket)
    if not settings.sqs_queue_url:
        log.error("SQS_QUEUE_URL is not set")
        sys.exit(1)

    while _running:
        try:
            poll_once()
        except Exception:  # noqa: BLE001
            log.exception("poll loop error; backing off 5s")
            time.sleep(5)

    log.info("worker stopped")


if __name__ == "__main__":
    main()
