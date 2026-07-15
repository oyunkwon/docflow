from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UploadUrlRequest(BaseModel):
    filename: str


class UploadUrlResponse(BaseModel):
    document_id: str
    upload_url: str
    s3_key: str


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    status: str
    page_count: int | None = None
    title: str | None = None
    author: str | None = None
    created_date: str | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
