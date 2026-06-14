# CLAUDE.md — ShortsGen 프로젝트 컨텍스트

> 이 파일은 Cowork가 세션마다 자동으로 읽는 영구 메모리입니다.
> 프로젝트 루트(`~/projects/shortsgen/`)에 두세요. 결정 사항이 바뀌면 여기부터 갱신합니다.
> **비밀키는 절대 이 파일에 적지 않습니다.** API 키는 `.env`(gitignore)에만 둡니다.

---

## 1. 프로젝트 정체성

- **이름:** ShortsGen — AI 쇼핑쇼츠 오토메이션 플랫폼
- **목적:** e커머스 상품 데이터 → 숏폼 비디오 자동 생성 → 다채널 발행 + 성과 관리. 자연어 CLI로 운영, 통합 대시보드로 가시화.
- **핵심 철학:** "CLI의 직관성 + 웹의 가시성" 하이브리드. 무거운 작업은 비동기 큐. 배포 전 휴먼 승인(QA) 게이트 필수.

## 2. 아키텍처 (4부 구성)

```
명령부(CLI) ─▶ 제어부(Backend API) ─▶ 생성부(AI Workers, 큐) ─▶ 시각화부(Dashboard)
                       │
                  PostgreSQL(상태/메타) · S3 또는 로컬 스토리지(영상/에셋)
```

- **CLI:** Node.js + `commander`. 정형 명령(`shorts-gen --상품ID 1024 --수량 2`) + 자연어("…3개 만들어줘")를 LLM으로 파싱해 동일 인텐트로 변환.
- **Backend:** Python FastAPI. CLI/대시보드 요청 처리, 상태 DB 갱신, WebSocket으로 실시간 로그·상태 push.
- **Workers:** 비동기 큐(BullMQ 또는 Celery+Redis). 파이프라인 4단계를 순차 실행.
- **Dashboard:** React SPA. **이미 만들어진 `shortsgen-dashboard.jsx`를 `frontend/`에 이식**하고 목업 → WebSocket 실데이터로 교체.

## 3. 생성 파이프라인 4단계

| 단계 | 기능 | 스택 |
|---|---|---|
| 1 에셋 수집 | 상품 URL/ID → 이미지·스펙·리뷰 크롤링·파싱 → JSON | Playwright(Python) 헤드리스 |
| 2 스크립트 | 후킹 중심 15~30초 대본·자막 생성 | GPT-4o / Claude → **YAML 출력** |
| 3 음성·BGM | 대본 → TTS + 분위기 BGM 매칭 | ElevenLabs(또는 Minimax) + BGM API |
| 4 영상 합성 | 이미지 슬라이드쇼 + 오디오 + 자막 병합(MVP) | FFmpeg(로컬) 또는 Fal.ai FFmpeg |

- 스크립트는 **YAML 스키마**로 출력(BarroTube 파이프라인과 동일 패턴 유지 — 씬/나레이션/B-roll 키워드 블록).
- 나레이션 길이 규칙은 플랫폼별로 별도 정의(쇼츠 15~30초 기준).

## 4. 코딩 컨벤션 (기존 워크플로 유지)

- 패키지: **pnpm + 모노레포** 워크스페이스. 린트는 **Biome**(ESLint 아님). `any` 금지, 인지 복잡도 제한.
- 커밋: **Conventional Commits**. 작업 격리는 git worktree.
- 한국어 주석 허용. REST보다 가능하면 서버 액션/명확한 엔드포인트.
- 비밀키: `.env` + `.env.example`. `.env`는 절대 커밋 금지.

## 5. 제약·가드레일 (PRD 5장)

- **일일 생성 쿼터:** 기본 30건/일. CLI·백엔드 양쪽에서 강제. 초과 시 거부 + 에러 로그.
- **휴먼 승인 게이트:** 배포 전 대시보드에서 관리자 `승인` 필요(QA 옵션).
- **플랫폼 정책:** YouTube/Instagram Graph API 일일 할당량 고려한 발행 스케줄러.
- **크롤링 안전:** 요청 간 무작위 딜레이 + 실패 시 재시도(지수 백오프). UI 변경 파싱 실패 시 콘솔에 명확한 에러 로그.
- **비용 인지:** 영상 생성 API는 호출당 비용 큼 → 쿼터 + "재실행 시 캐시 재사용" 원칙.

## 6. 운영 모델 (빌드 vs 상시 런타임 분리)

- **Cowork(로컬 VM):** 빌드·테스트·리팩터·대화형 운영. 단계별 스캐폴딩과 디버깅.
- **상시 런타임 = VPS(aibitgo.com):** 워커 큐, 일일 발행 스케줄러, WebSocket 서버는 **pm2**로 상주. 오케스트레이션/스케줄은 **n8n**(기존 인스턴스 재사용).
- **알림:** Telegram 봇(BarroTube 패턴 — `@…Bot`)으로 생성 완료/검토 대기/배포/에러 push.
- **배포 흐름:** Cowork에서 빌드·테스트 → git push(GitLab/GitHub) → VPS에서 pull → pm2 reload.

## 7. 단계별 완료 정의 (Definition of Done)

- 각 단계는 **독립 실행 + 테스트 통과 + README 한 줄 사용법**이 있어야 "완료".
- 통합 전 각 모듈은 목업 입력으로 단독 검증.
- 새 기능 추가 시 이 CLAUDE.md의 관련 섹션을 함께 갱신.

## 8. 폴더 레이아웃 (목표)

```
shortsgen/
├─ CLAUDE.md            # 이 파일
├─ COWORK_SETUP.md      # 실행 가이드 + 프롬프트
├─ .env.example
├─ packages/
│  ├─ cli/              # Node commander CLI + NL 파서
│  ├─ backend/          # FastAPI + WebSocket
│  ├─ workers/          # 파이프라인 4단계 (scraper/script/voice/render)
│  └─ frontend/         # React 대시보드 (shortsgen-dashboard.jsx 이식)
├─ db/                  # PostgreSQL 스키마·마이그레이션
└─ scripts/             # 배포·스케줄 헬퍼
```
