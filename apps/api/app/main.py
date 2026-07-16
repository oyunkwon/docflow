import os
import uuid
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import aws
from .db import db_enabled, get_db, init_db
from .models import Document
from .schemas import (
    DocumentOut,
    UploadUrlRequest,
    UploadUrlResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="DocFlow API", lifespan=lifespan)

# 연습용이라 전체 허용. 운영에서는 프론트 origin만 허용한다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 모든 라우트를 /api 아래에 둔다.
# ALB는 경로를 자르지 않고 그대로 전달하므로(/api/health/ready → 앱도 /api/health/ready),
# 앱이 /api prefix에서 직접 서빙해야 한다. 로컬 nginx도 prefix를 자르지 않고 넘긴다.
router = APIRouter(prefix="/api")


@router.get("/health/live")
def live():
    return {"status": "ok"}


@router.get("/health/ready")
def ready():
    """DB가 설정된 경우에만 연결을 검사한다.

    DATABASE_URL이 없으면(=아직 RDS 미연결 배포) DB 없이도 ready로 응답한다.
    큐/버킷은 지연 실패를 허용한다.
    """
    if not db_enabled():
        return {"status": "ready", "db": "disabled"}
    try:
        with next(get_db()) as db:
            db.execute(select(1))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"db not ready: {exc}") from exc
    return {"status": "ready", "db": "ok"}


def require_db():
    """문서 라우트용 의존성. DB 미설정이면 503으로 명확히 거부한다."""
    if not db_enabled():
        raise HTTPException(status_code=503, detail="database not configured")
    yield from get_db()


@router.post("/documents/upload-url", response_model=UploadUrlResponse)
def create_upload_url(req: UploadUrlRequest, db: Session = Depends(require_db)):
    doc_id = str(uuid.uuid4())
    s3_key = f"uploads/{doc_id}/{req.filename}"

    doc = Document(id=doc_id, filename=req.filename, s3_key=s3_key, status="PENDING")
    db.add(doc)
    db.commit()

    url = aws.presign_put(s3_key)
    return UploadUrlResponse(document_id=doc_id, upload_url=url, s3_key=s3_key)


@router.post("/documents/{doc_id}/complete", response_model=DocumentOut)
def complete_upload(doc_id: str, db: Session = Depends(require_db)):
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")

    aws.send_job(doc_id)
    return DocumentOut.model_validate(doc)


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(require_db)):
    rows = db.execute(select(Document).order_by(Document.created_at.desc())).scalars()
    return [DocumentOut.model_validate(r) for r in rows]


@router.get("/documents/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: str, db: Session = Depends(require_db)):
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")
    return DocumentOut.model_validate(doc)


@router.get("/version")
def version():
    return {"version": os.environ.get("APP_VERSION", "unknown")}


app.include_router(router)

# ci: trigger build to debug OIDC claims
