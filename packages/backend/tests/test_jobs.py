"""FR-5 백엔드 검증 — 수명주기 · 일일 쿼터 · 사람 승인 게이트."""
from __future__ import annotations

from app import models


def _force_status(client, job_id: int, status: models.JobStatus) -> None:
    """워커 비활성 환경에서 테스트가 직접 상태를 전이 (review 준비용)."""
    db = client.testing_session()
    try:
        job = db.get(models.Job, job_id)
        job.status = status
        db.commit()
    finally:
        db.close()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_job_starts_pending(client):
    r = client.post("/jobs", json={"product_id": 1024, "style": "정보형"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "pending"  # 워커 비활성 → pending 유지
    assert body["style"] == "정보형"
    assert body["product_id"] == 1024


def test_unknown_style_rejected(client):
    r = client.post("/jobs", json={"product_id": 1, "style": "없는스타일"})
    assert r.status_code == 422


def test_quota_blocks_over_limit(client, monkeypatch):
    import app.main as m

    monkeypatch.setattr(m, "DAILY_QUOTA", 2)
    assert client.post("/jobs", json={"product_id": 1}).status_code == 201
    assert client.post("/jobs", json={"product_id": 2}).status_code == 201
    r = client.post("/jobs", json={"product_id": 3})
    assert r.status_code == 429  # 쿼터 초과
    # /quota 도 동일 반영
    q = client.get("/quota").json()
    assert q["used"] == 2 and q["remaining"] == 0


def test_approval_gate_blocks_non_review(client):
    jid = client.post("/jobs", json={"product_id": 1}).json()["id"]
    # pending 상태 직접 승인 시도 → 게이트가 차단
    r = client.post(f"/jobs/{jid}/approve")
    assert r.status_code == 409


def test_approve_publishes_from_review(client):
    jid = client.post("/jobs", json={"product_id": 1}).json()["id"]
    _force_status(client, jid, models.JobStatus.review)
    r = client.post(f"/jobs/{jid}/approve", params={"approver": "beye"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "published"
    assert body["approved_by"] == "beye"
    assert body["published_at"] is not None


def test_reject_from_review(client):
    jid = client.post("/jobs", json={"product_id": 1}).json()["id"]
    _force_status(client, jid, models.JobStatus.review)
    r = client.post(f"/jobs/{jid}/reject", params={"reason": "가격 오류"})
    assert r.status_code == 200
    assert r.json()["status"] == "failed"


def test_get_missing_job_404(client):
    assert client.get("/jobs/99999").status_code == 404
