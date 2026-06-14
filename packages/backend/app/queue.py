"""인메모리 큐 + 워커 (dev). prod에선 Celery/Redis로 교체 (PRD §11).

워커는 작업을 pending → generating → review 로 전이시키며, 각 단계 로그를
DB(logs)에 적재하고 WebSocket으로 브로드캐스트한다. 실제 4단계 생성
(scrape/script/voice/render)은 P2-4~6의 workers 패키지에서 구현되고, 여기서는
dev 시뮬레이션(no-op)으로 수명주기만 구동한다.
"""
from __future__ import annotations

import asyncio

from .db import SessionLocal
from .models import Job, JobStatus, Log
from .ws import manager

# dev 워커가 시뮬레이션하는 파이프라인 단계 (실제 구현은 P2-4~6)
STAGES = ("scrape", "script", "voice", "render")

_queue: asyncio.Queue[int] | None = None


def get_queue() -> asyncio.Queue[int]:
    """실행 중인 이벤트 루프에서 지연 생성 (import 시점 루프 의존 회피)."""
    global _queue
    if _queue is None:
        _queue = asyncio.Queue()
    return _queue


async def enqueue(job_id: int) -> None:
    await get_queue().put(job_id)


def _set_status(job_id: int, status: JobStatus) -> None:
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is not None:
            job.status = status
            db.commit()
    finally:
        db.close()


async def _log(job_id: int, stage: str, message: str, level: str = "info") -> None:
    db = SessionLocal()
    try:
        db.add(Log(job_id=job_id, stage=stage, level=level, message=message))
        db.commit()
    finally:
        db.close()
    await manager.broadcast(
        {"job_id": job_id, "stage": stage, "level": level, "message": message}
    )


async def worker() -> None:
    q = get_queue()
    while True:
        job_id = await q.get()
        try:
            _set_status(job_id, JobStatus.generating)
            await _log(job_id, "pipeline", "생성 시작 (dev 스텁)")
            for stage in STAGES:
                await asyncio.sleep(0)  # 실제 단계 자리 (P2-4~6 workers)
                await _log(job_id, stage, f"{stage} 완료 (dev 스텁)")
            _set_status(job_id, JobStatus.review)
            await _log(job_id, "pipeline", "검토 대기 (review)")
        except Exception as exc:  # noqa: BLE001
            _set_status(job_id, JobStatus.failed)
            await _log(job_id, "pipeline", f"실패: {exc}", level="error")
        finally:
            q.task_done()
