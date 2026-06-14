# db — PostgreSQL 스키마 (P2-2 / PRD §10)

## 적용
```bash
psql "$DATABASE_URL" -f db/migrations/0001_init.sql
```
> 적용에는 실행 중인 PostgreSQL이 필요합니다. 현재는 스키마 정의(DDL)만 제공 — 실제 적용·연결은 P2-3 백엔드에서.

## 테이블
- `products` — FR-1 스크래퍼 산출 (productSchema 대응)
- `jobs` — FR-5 작업 수명주기 (`status`: pending→generating→review→published / failed)
- `assets` — 산출 에셋 + 캐시 재사용 키 (PRD §11)
- `metrics` — FR-9 채널 성과 (조회/CTR/전환)
- `logs` — 단계별 로그 (WebSocket 스트림 소스)

## enum
- `job_status` = pending · generating · review · published · failed
- `script_style` = 정보형 · 감성 · 다이나믹

마이그레이션은 `migrations/NNNN_*.sql` 순차 적용 규칙.
