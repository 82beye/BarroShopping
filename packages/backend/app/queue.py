"""인메모리 큐 + 워커 (dev). prod에선 Celery/Redis로 교체 (PRD §11).

워커는 작업을 pending → generating → review 로 전이시키며, 각 단계 로그를
DB(logs)에 적재하고 WebSocket으로 브로드캐스트한다.

- scrape/script/voice : 자격증명 필요 → 아직 스텁(P2-4·5·7)
- render              : input_props가 있으면 @shortsgen/render로 실제 MP4 산출 (P2-6)
"""
from __future__ import annotations

import asyncio

from .db import SessionLocal
from .models import Job, JobStatus, Log
from .render_stage import output_path, render_command, render_dir, write_props
from .ws import manager

# 자격증명이 필요해 아직 스텁인 단계 (P2-4 스크립트 / P2-5 음성 / P2-7 스크래퍼)
STUB_STAGES = ("scrape", "script", "voice")

_queue: asyncio.Queue[int] | None = None


def get_queue() -> asyncio.Queue[int]:
    global _queue
    if _queue is None:
        _queue = asyncio.Queue()
    return _queue


async def enqueue(job_id: int) -> None:
    await get_queue().put(job_id)


def _get_input_props(job_id: int) -> dict | None:
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        return job.input_props if job else None
    finally:
        db.close()


def _set_status(job_id: int, status: JobStatus) -> None:
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is not None:
            job.status = status
            db.commit()
    finally:
        db.close()


def _set_video_path(job_id: int, path: str) -> None:
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is not None:
            job.video_path = path
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


async def _render(job_id: int, input_props: dict | None) -> str | None:
    """input_props가 있으면 Remotion으로 실제 렌더, 없으면 스킵 (P2-6)."""
    if not input_props:
        await _log(job_id, "render", "input_props 없음 → 렌더 스킵 (dev)")
        return None
    props = write_props(job_id, input_props)
    cmd = render_command(job_id, props)
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(render_dir()),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    if proc.returncode != 0:
        tail = (out or b"").decode(errors="replace")[-600:]
        raise RuntimeError(f"렌더 실패 rc={proc.returncode}: {tail}")
    return str(output_path(job_id))


async def worker() -> None:
    q = get_queue()
    while True:
        job_id = await q.get()
        try:
            input_props = _get_input_props(job_id)
            _set_status(job_id, JobStatus.generating)
            await _log(job_id, "pipeline", "생성 시작")
            for stage in STUB_STAGES:
                await asyncio.sleep(0)  # 실제 단계 자리 (P2-4·5·7, 자격증명 필요)
                await _log(job_id, stage, f"{stage} 스텁 (자격증명 필요)")
            video = await _render(job_id, input_props)
            if video:
                _set_video_path(job_id, video)
                await _log(job_id, "render", f"렌더 완료: {video}")
            _set_status(job_id, JobStatus.review)
            await _log(job_id, "pipeline", "검토 대기 (review)")
        except Exception as exc:  # noqa: BLE001
            _set_status(job_id, JobStatus.failed)
            await _log(job_id, "pipeline", f"실패: {exc}", level="error")
        finally:
            q.task_done()
