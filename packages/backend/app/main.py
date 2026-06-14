"""바로쇼핑 백엔드 (FastAPI) — FR-5 골격.

P2-3에서 job 수명주기(pending→generating→review→published), 일 30개 쿼터(PRD §11),
사람 승인 게이트, WebSocket 실시간 로그를 구현한다. 현재는 헬스체크 + 엔드포인트 스텁.
"""
from __future__ import annotations

import os

from fastapi import FastAPI

app = FastAPI(title="ShortsGen Backend", version="0.1.0")

# 일 생성 쿼터 (PRD §11). 실제 강제는 P2-3.
DAILY_QUOTA = int(os.environ.get("DAILY_QUOTA", "30"))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "shortsgen-backend"}


@app.get("/jobs")
def list_jobs() -> dict[str, list]:
    # TODO(P2-3): DB(jobs)에서 조회
    return {"jobs": []}


@app.post("/jobs")
def create_job() -> dict[str, str]:
    # TODO(P2-3): 쿼터 체크 → 큐 적재 → pending 상태 DB 기록
    return {"status": "stub", "detail": "작업 생성은 P2-3에서 구현"}


@app.post("/jobs/{job_id}/approve")
def approve_job(job_id: int) -> dict[str, object]:
    # TODO(P2-3): 승인 게이트 → published 전이 → 발행 트리거
    return {"status": "stub", "job_id": job_id}
