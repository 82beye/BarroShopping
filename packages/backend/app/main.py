"""바로쇼핑 백엔드 (FastAPI) — FR-5.

job 수명주기(pending→generating→review→published / failed) · 일 30개 쿼터(PRD §11) ·
사람 승인 게이트(발행 전 승인 필수) · WebSocket 실시간 로그.
dev=SQLite+인메모리 워커 / prod=PostgreSQL+Redis (DATABASE_URL·ENABLE_WORKER 분기).
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models, schemas
from .config import DAILY_QUOTA, ENABLE_WORKER
from .db import get_session, init_db
from .queue import enqueue, worker
from .ws import manager


def _used_today(db: Session) -> int:
    today = date.today()
    return (
        db.scalar(
            select(func.count())
            .select_from(models.Job)
            .where(models.Job.quota_date == today)
        )
        or 0
    )


async def _emit(
    db: Session, job_id: int, stage: str, message: str, level: str = "info"
) -> None:
    """상태 전이 로그를 DB(logs)에 적재하고 WebSocket으로 브로드캐스트 (FR-5 가시성)."""
    db.add(models.Log(job_id=job_id, stage=stage, level=level, message=message))
    db.commit()
    await manager.broadcast(
        {"job_id": job_id, "stage": stage, "level": level, "message": message}
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task: asyncio.Task | None = None
    if ENABLE_WORKER:
        task = asyncio.create_task(worker())
    yield
    if task is not None:
        task.cancel()


app = FastAPI(title="ShortsGen Backend", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "service": "shortsgen-backend", "daily_quota": DAILY_QUOTA}


@app.get("/quota")
def quota(db: Session = Depends(get_session)) -> dict[str, object]:
    used = _used_today(db)
    return {
        "date": date.today().isoformat(),
        "used": used,
        "limit": DAILY_QUOTA,
        "remaining": max(0, DAILY_QUOTA - used),
    }


@app.post("/jobs", response_model=schemas.JobOut, status_code=201)
async def create_job(
    payload: schemas.JobCreate, db: Session = Depends(get_session)
) -> models.Job:
    if _used_today(db) >= DAILY_QUOTA:
        raise HTTPException(status_code=429, detail=f"일일 생성 쿼터({DAILY_QUOTA}) 초과")
    try:
        style = models.ScriptStyle(payload.style)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"알 수 없는 스타일: {payload.style}")
    job = models.Job(
        product_id=payload.product_id, style=style, input_props=payload.input_props
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    await enqueue(job.id)
    return job


@app.get("/jobs", response_model=list[schemas.JobOut])
def list_jobs(db: Session = Depends(get_session)) -> list[models.Job]:
    return list(db.scalars(select(models.Job).order_by(models.Job.id.desc())).all())


@app.get("/jobs/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: int, db: Session = Depends(get_session)) -> models.Job:
    job = db.get(models.Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없음")
    return job


@app.post("/jobs/{job_id}/approve", response_model=schemas.JobOut)
async def approve_job(
    job_id: int, approver: str = "operator", db: Session = Depends(get_session)
) -> models.Job:
    job = db.get(models.Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없음")
    # 승인 게이트: review 상태에서만 발행 가능 (FR-5)
    if job.status != models.JobStatus.review:
        raise HTTPException(
            status_code=409,
            detail=f"승인은 review 상태에서만 가능 (현재: {job.status.value})",
        )
    now = datetime.now(timezone.utc)
    job.status = models.JobStatus.published
    job.approved_by = approver
    job.approved_at = now
    job.published_at = now
    db.commit()
    db.refresh(job)
    await _emit(db, job.id, "publish", f"승인·발행 (by {approver})")
    return job


@app.post("/jobs/{job_id}/reject", response_model=schemas.JobOut)
async def reject_job(
    job_id: int, reason: str = "", db: Session = Depends(get_session)
) -> models.Job:
    job = db.get(models.Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없음")
    if job.status != models.JobStatus.review:
        raise HTTPException(
            status_code=409,
            detail=f"반려는 review 상태에서만 가능 (현재: {job.status.value})",
        )
    job.status = models.JobStatus.failed
    job.error = reason or "운영자 반려"
    db.commit()
    db.refresh(job)
    await _emit(db, job.id, "review", f"반려: {job.error}", level="warn")
    return job


@app.websocket("/ws/logs")
async def ws_logs(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
