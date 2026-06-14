"""pytest 픽스처 — 인메모리 SQLite + TestClient (워커 비활성으로 결정적 검증)."""
from __future__ import annotations

import os

# app 모듈 import 전에 환경 고정 (모듈 로드 시점에 읽힘)
os.environ["ENABLE_WORKER"] = "0"
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  (테이블 등록)
from app.db import Base, get_session
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def _override():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_session] = _override
    with TestClient(app) as c:
        c.testing_session = TestingSession  # 테스트 헬퍼에서 직접 상태 전이용
        yield c
    app.dependency_overrides.clear()
