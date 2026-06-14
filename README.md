# 바로쇼핑 (ShortsGen)

e커머스 상품 데이터 → **쇼핑 쇼츠 자동 생성 → 다채널 발행 + 성과 관리** 모노레포.
(브랜드명 = 바로쇼핑 · 시스템명 = ShortsGen)

> 기획·설계 정본: [`docs/PRD.md`](docs/PRD.md) · 구현 단계: [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md)

## 모노레포 구조 (pnpm workspace)

```
packages/
  render/     Remotion 영상 합성 (Stage 4·FR-4) — 구현·동작 (Node)
  cli/        자연어/정형 명령 CLI (FR-6) — 백엔드 연결 (Node, commander)
  backend/    FastAPI 제어부·큐·쿼터·승인·WebSocket (FR-5) — 구현 (Python)
  workers/    파이프라인 scrape/script/voice (FR-1~3) — 코드+단위테스트 (Python, 실행 시 키 필요)
  frontend/   운영 대시보드 (FR-7) — 백엔드 실연동 (Vite+React)
db/           PostgreSQL 스키마·마이그레이션 (PRD §10)
docs/         PRD · 구현 스텝 · 발행 체크리스트
```

## 빠른 시작

```bash
pnpm install
pnpm render                 # 기본 props 렌더 → packages/render/out/video.mp4
pnpm smoke                  # 3·5·6개 상품 렌더 스모크

# 백엔드 + 대시보드 (dev)
cd packages/backend && python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
DATABASE_URL="sqlite:///./dev.db" ./.venv/bin/uvicorn app.main:app   # :8000
pnpm --filter @shortsgen/frontend dev                                 # :5173 (8000 프록시)

# CLI로 작업 생성 → 워커 렌더 → 승인
node packages/cli/dist/index.js generate -p 1024 --props packages/render/input-props.example.json
node packages/cli/dist/index.js approve <id>
```

## 현재 상태 (2026-06-14)

| 단계 | 상태 |
|---|---|
| P0 렌더 안정화 (오버플로·동적 타일·BGM·스모크) | ✅ |
| P1-1~3 입력 가이드·렌더 래퍼·발행 체크리스트 | ✅ |
| P2-1·2 모노레포·PostgreSQL 스키마 | ✅ |
| P2-3 백엔드(수명주기·쿼터·승인 게이트·WebSocket) | ✅ pytest 11 |
| P2-6·8·9 워커 렌더 통합·CLI 연결·e2e(명령→영상→승인) | ✅ 라이브 검증 |
| P3-1 대시보드 백엔드 실연동 | ✅ build |
| **P2-4·5·7 스크립트(LLM)·음성(TTS)·스크래퍼** | 🔑 코드+단위테스트 완료, **실행에 키/대상 필요** |
| P3-2~5 발행·VPS 배포·n8n 스케줄·Telegram | ⏳ OAuth/인프라 필요 |

실행에 필요한 자격증명: `ANTHROPIC_API_KEY`(스크립트) · `ELEVENLABS_API_KEY`(음성) · 스크래핑 대상 사이트/셀렉터(PRD §15 D1) · YouTube OAuth(발행). → `.env`(커밋 금지, `.env.example` 참고).

## 운영·규약

- 패키지: pnpm 모노레포 · 린트 Biome · Conventional Commits (CLAUDE.md §4)
- 시크릿: `.env`(+`.env.example`)에만, 커밋 금지
- 가드레일: 일 30개 쿼터 · 발행 전 사람 승인 게이트 (PRD §11~12)
- 운영 전 강화 항목: `packages/backend/README.md` 강화 backlog(인증·쿼터 원자성·타임존 등)
