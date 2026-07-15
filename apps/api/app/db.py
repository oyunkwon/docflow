from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings
from .models import Base

# DATABASE_URL이 없으면 엔진을 만들지 않는다. DB 없이도 프로세스가 뜬다.
engine = None
SessionLocal = None

if settings.database_url:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def db_enabled() -> bool:
    return SessionLocal is not None


def init_db() -> None:
    """테이블을 생성한다. 연습용이라 마이그레이션 도구 대신 create_all을 쓴다.

    DATABASE_URL이 없으면 아무것도 하지 않는다.
    """
    if engine is None:
        return
    Base.metadata.create_all(bind=engine)


def get_db():
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
