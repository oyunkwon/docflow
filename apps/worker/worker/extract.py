import io

from pypdf import PdfReader


def extract_metadata(pdf_bytes: bytes) -> dict:
    """PDF 바이트에서 페이지 수와 문서 정보를 뽑는다.

    손상되거나 정보가 없는 필드는 None으로 둔다. 예외는 호출자가 처리한다.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    meta = reader.metadata

    def _clean(value) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    return {
        "page_count": len(reader.pages),
        "title": _clean(meta.title if meta else None),
        "author": _clean(meta.author if meta else None),
        "created_date": _clean(meta.creation_date_raw if meta else None),
    }
