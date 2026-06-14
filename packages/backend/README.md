# @shortsgen/backend (FastAPI)

제어부 (FR-5). job 수명주기 · 일 30개 쿼터 · 사람 승인 게이트 · WebSocket 실시간 로그.
dev = SQLite + 인메모리 워커 / prod = PostgreSQL + Redis(Celery) — `DATABASE_URL`·`ENABLE_WORKER`로 분기.

## 실행
```bash
cd packages/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload        # http://127.0.0.1:8000  (dev: SQLite + 워커 가동)
```

## API
| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/health` | 헬스체크 |
| GET | `/quota` | 오늘 사용량/한도/잔여 |
| POST | `/jobs` | 작업 생성(pending) → 큐 적재. 쿼터 초과 시 429 |
| GET | `/jobs` · `/jobs/{id}` | 목록·단건 |
| POST | `/jobs/{id}/approve` | **review 상태에서만** 승인 → published (승인 게이트) |
| POST | `/jobs/{id}/reject` | review 상태에서만 반려 → failed |
| WS | `/ws/logs` | 단계별 진행 로그 실시간 수신 |

수명주기: `pending → generating → review → published`(승인) / `failed`(반려·오류).
dev 워커는 4단계(scrape/script/voice/render)를 시뮬레이션만 — 실제 생성은 P2-4~6 workers.
승인·반려도 `logs` 적재 + WebSocket 브로드캐스트.

## 테스트
```bash
pip install -r requirements-dev.txt
pytest                # 쿼터·승인 게이트·수명주기 검증 (인메모리 SQLite, 8 케이스)
```

DB 스키마: `db/migrations/0001_init.sql` (모델은 `app/models.py` 와 동형).

## 강화 backlog (다각도 리뷰 검출 — prod 단계 처리)

dev MVP는 위 검증을 통과하나, 적대적 리뷰에서 확인된 아래 항목은 **운영(prod) 전환 시** 처리한다. (현재는 dev 스텁/미구현 영역이라 defer)

| # | 항목 | 처리 시점 |
|---|---|---|
| 1 | **쿼터 원자성(TOCTOU)** — 동시 POST /jobs가 카운트 검사를 동시 통과해 30 초과 가능. PG `SELECT … FOR UPDATE`/원자적 카운터 슬롯 선점 + IntegrityError 재검사 + 동시성 테스트 | P2 (prod DB) |
| 2 | **인증·인가 부재** — `/jobs/{id}/approve`·`/reject`·`/ws/logs` 무인증, `approver` 임의 문자열. 승인 게이트 우회 가능 | P3 (운영) |
| 3 | **타임존 일관성** — `quota_date`는 서버 로컬 `date.today()`, 타임스탬프는 UTC, 모델 `DateTime`에 `timezone=True` 미설정(마이그레이션 TIMESTAMPTZ와 불일치) | P2 (prod DB) |
| 4 | **재시도·dead-letter 부재** — 워커 예외 시 즉시 `failed` 종료(§11 미충족). Celery 교체 시 재시도(최대 3)·백오프·DLQ | P2-4~6 (실워커) |
| 5 | **쿼터 소진 정책** — 실패·반려 job도 그날 슬롯 영구 점유(재시도 환급 경로 없음). 정책 확정 후 카운팅 기준 일치 | P2 |
| 6 | **reject vs fail 미구분** — 둘 다 `failed`. `rejected` 상태 또는 `failure_kind` 분류(KPI·재시도 구분용) | P4 (KPI) |
| 7 | **async 핸들러 sync DB 블로킹** — `create_job` 등에서 동기 DB I/O가 이벤트 루프 블로킹. prod는 async 드라이버(asyncpg) | P2 (prod DB) |
| 8 | **input_props 무검증** — 자유형 JSON 저장. 렌더 통합 시 catalogSchema 검증 | P2-6 (렌더 통합) |
| 9 | **예외 메시지 노출** — 워커가 원시 예외를 로그/WS로 노출. 사용자 메시지/내부 로그 분리 | P2-4~6 |
