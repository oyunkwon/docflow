import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import aws
from .config import settings
from .db import get_db, init_db
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


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/health/ready")
def ready(db: Session = Depends(get_db)):
    """DB 연결이 되어야 ready. 큐/버킷은 지연 실패를 허용한다."""
    try:
        db.execute(select(1))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"db not ready: {exc}")
    return {"status": "ready"}


@app.post("/documents/upload-url", response_model=UploadUrlResponse)
def create_upload_url(req: UploadUrlRequest, db: Session = Depends(get_db)):
    doc_id = str(uuid.uuid4())
    s3_key = f"uploads/{doc_id}/{req.filename}"

    doc = Document(id=doc_id, filename=req.filename, s3_key=s3_key, status="PENDING")
    db.add(doc)
    db.commit()

    url = aws.presign_put(s3_key)
    return UploadUrlResponse(document_id=doc_id, upload_url=url, s3_key=s3_key)


@app.post("/documents/{doc_id}/complete", response_model=DocumentOut)
def complete_upload(doc_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")

    aws.send_job(doc_id)
    return DocumentOut.model_validate(doc)


@app.get("/documents", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    rows = db.execute(select(Document).order_by(Document.created_at.desc())).scalars()
    return [DocumentOut.model_validate(r) for r in rows]


@app.get("/documents/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")
    return DocumentOut.model_validate(doc)
