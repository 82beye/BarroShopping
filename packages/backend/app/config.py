"""백엔드 설정 — 환경변수 기반 (PRD §11).

dev: SQLite + 인메모리 워커 / prod: PostgreSQL + Celery·Redis (DATABASE_URL·ENABLE_WORKER로 분기).
"""
from __future__ import annotations

import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./shortsgen.db")
DAILY_QUOTA = int(os.environ.get("DAILY_QUOTA", "30"))
# dev=1(인메모리 워커 가동). prod에선 0으로 두고 Celery/Redis 워커가 큐를 소비.
ENABLE_WORKER = os.environ.get("ENABLE_WORKER", "1") == "1"
