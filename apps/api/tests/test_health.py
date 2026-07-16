"""API 스모크 테스트. DB 없이(DATABASE_URL 미설정) health 경로가 뜨는지 확인한다."""

import os

os.environ.setdefault("DATABASE_URL", "")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_live():
    resp = client.get("/api/health/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_ready_without_db():
    resp = client.get("/api/health/ready")
    assert resp.status_code == 200
    assert resp.json()["db"] == "disabled"


def test_documents_requires_db():
    # DB 미설정이면 문서 라우트는 503으로 명확히 거부한다.
    resp = client.get("/api/documents")
    assert resp.status_code == 503


def test_routes_are_under_api_prefix():
    # ALB가 경로를 자르지 않으므로 앱은 /api 아래에서만 서빙해야 한다.
    assert client.get("/health/live").status_code == 404
