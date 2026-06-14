# 바로쇼핑 (ShortsGen)

e커머스 상품 데이터 → **쇼핑 쇼츠 자동 생성 → 다채널 발행 + 성과 관리** 모노레포.
(브랜드명 = 바로쇼핑 · 시스템명 = ShortsGen)

> 기획·설계 정본: [`docs/PRD.md`](docs/PRD.md) · 구현 단계: [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md)

## 모노레포 구조 (pnpm workspace)

```
packages/
  render/     Remotion 영상 합성 (Stage 4) — 구현 완료·동작 (Node)
  cli/        자연어/정형 명령 CLI (FR-6) — 스텁 (Node, commander)
  backend/    FastAPI 제어부·큐·쿼터·승인 (FR-5) — 스텁 (Python)
  workers/    파이프라인 4단계 scrape/script/voice/render (FR-1~4) — 스텁 (Python)
  frontend/   운영 대시보드 (FR-7) — 목업 (React, 포팅 대기)
db/           PostgreSQL 스키마·마이그레이션 (PRD §10)
docs/         PRD · 구현 스텝 · 발행 체크리스트
```

## 빠른 시작

```bash
pnpm install                # 워크스페이스 의존성 설치
pnpm render                 # 기본 props 렌더 → packages/render/out/video.mp4
pnpm render:props           # input-props.example.json 렌더
pnpm studio                 # Remotion Studio 프리뷰
pnpm smoke                  # 3·5·6개 상품 렌더 스모크 검증
```

상품 카탈로그 JSON 작성법: [`packages/render/INPUT_GUIDE.md`](packages/render/INPUT_GUIDE.md)

## 현재 상태 (2026-06-14)

- **P0 렌더 레이어 안정화** ✅ — 긴 상품명 자동 축소 · Outro 동적 타일(최대 6) · 선택 BGM · 스모크(3/5/6개) 렌더 검증
- **P1-1~3** ✅ — 입력 가이드/템플릿 · 렌더 래퍼 · YouTube 발행 체크리스트
- **P2-1~2** ✅ — pnpm 모노레포 스캐폴딩 · PostgreSQL 스키마
- **P2-3~** ⏳ — 백엔드/큐·스크립트(LLM)·음성(TTS)·스크래퍼 (자격증명 필요)

## 운영·규약

- 패키지: pnpm 모노레포 · 린트 Biome · Conventional Commits (CLAUDE.md §4)
- 시크릿: `.env`(+`.env.example`)에만, 커밋 금지
- 가드레일: 일 30개 쿼터 · 발행 전 사람 승인 게이트 (PRD §11~12)
