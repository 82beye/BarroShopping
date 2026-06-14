# @shortsgen/backend (FastAPI)

제어부 (FR-5). CLI/대시보드 요청 처리, job 상태 DB 갱신, WebSocket 실시간 로그, 쿼터·승인 게이트.

## 실행 (스텁)
```bash
cd packages/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# → GET /health, GET/POST /jobs (스텁)
```
현재는 헬스체크 + 엔드포인트 스텁. job 수명주기·쿼터·승인·WebSocket은 **P2-3**에서 구현.
DB 스키마는 `db/migrations/`.
