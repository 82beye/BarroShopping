# 바로쇼핑 (ShortsGen) — Product Requirements Document

> **바로쇼핑** = 영상에 노출되는 **제품/서비스 브랜드명**
> **ShortsGen** = 이를 구동하는 **내부 시스템(코드베이스/파이프라인)명**
> 본 문서에서 두 명칭은 위 구분대로 병기한다.

---

## 0. 문서 메타

| 항목 | 값 |
|---|---|
| 문서명 | 바로쇼핑(ShortsGen) PRD |
| 버전 | v0.2 (Draft) |
| 상태 | §15 확정 결정 반영 · 리뷰 대기 |
| 작성일 | 2026-06-14 |
| 오너 | 운영 감독자(프로젝트 소유자) |
| 저장소 | https://github.com/82beye/BarroShopping |
| 적용 범위 | end-to-end (수집 → 스크립트 → 음성 → 렌더 → 백엔드/큐 → CLI → 대시보드 → 다채널 발행 → 운영/모니터링) |

### 관련 문서

| 문서 | 역할 | 본 PRD와의 관계 |
|---|---|---|
| `README.md` | 현재 렌더 레이어 사용법·기능 | 구현된 기능의 1차 출처 |
| `CLAUDE.md` | 시스템 아키텍처·코딩 규약·운영 제약 | 본 PRD의 기술/제약 근거 |
| `COWORK_SETUP.md` | 7단계 빌드 로드맵·배포·역할 분담 | 본 PRD 로드맵/운영의 근거 |
| `src/schema.ts` | inputProps 데이터 계약(Zod) | 데이터 모델(§9)의 정본 |
| `shortsgen-dashboard.jsx` | 대시보드 목업(UI·CLI 파서·상태머신) | FR-6·FR-7 사양 근거 |
| `docs/ARCHITECTURE.md`, `docs/RUNBOOK.md` | (예정) 상세 설계·운영 절차 | 본 PRD에는 개요만, 후속 분리 |

---

## 1. 배경 & 문제정의

쇼핑 쇼츠 1개를 수동 편집으로 만들면 디자이너 기준 수 시간이 든다. 상품 수가 늘면 편집은 선형으로 비싸지고, 일관성·속도·확장성이 모두 무너진다.

**바로쇼핑(ShortsGen)** 은 이 병목을 제거한다 — 상품 데이터를 구조화된 입력(`inputProps`, Zod 검증)으로 주입하면, 코드가 9:16 쇼츠를 결정적(deterministic)으로 렌더한다. 동일 상품은 항상 동일하게 나오고, 테마 색 5개만 바꾸면 100개 영상의 룩을 일괄 변경할 수 있으며, 스크립트/API로 배치 호출이 가능하다.

**현재 현실(2026-06-14 기준):** 전체 비전 중 **렌더 레이어(Remotion 합성)만 완성도 높게 구현(~15%)** 되어 있다. 나머지(상품 수집·스크립트·음성·백엔드/큐·CLI 실행기·발행·DB)는 `CLAUDE.md`/`COWORK_SETUP.md`에 **산문 설계로만** 존재하고, 대시보드(`shortsgen-dashboard.jsx`)는 인메모리 **시뮬레이션 목업**이다.

→ 흩어진 비전·설계·미구현 항목을 **단일 PRD**로 통합해 구현·운영의 기준선(single source of truth)을 만드는 것이 본 문서의 목적이다. 우선순위는 **발행까지 닿는 가장 얇은 수직 슬라이스(MVP)** 다.

---

## 2. 제품 비전 & 목표

### 비전 (1줄)
> e커머스 상품 데이터를 넣으면, 검토 한 번으로 다채널에 발행되는 쇼핑 쇼츠가 자동으로 나오는 **개인 운영용 무인 영상 공장**.

### 제품 목표
1. **편집 제로화** — 영상 편집 기술 없이 상품 데이터만으로 쇼츠를 생산한다.
2. **리드타임 단축** — "상품 → 발행"까지 사람 손이 닿는 시간을 분 단위로 줄인다.
3. **무인 운영** — 생성·검토대기·스케줄 발행·성과 수집이 24/7 자동으로 돈다(사람은 승인·전략만).
4. **비용 가시성** — 영상 1개당 비용(스크래핑/LLM/TTS/렌더/발행)을 측정·통제한다.
5. **일관 브랜딩** — 테마 토큰 5개로 바로쇼핑 룩을 전 영상에 일관 적용한다.

### Non-goals (이번 범위 아님)
- 롱폼(가로/3분 이상) 영상 — 본 시스템은 9:16 숏폼 전용.
- 실시간 라이브/스트리밍.
- 외부 고객 대상 멀티테넌시·SaaS·결제 — **내부 자동화 도구**로 한정(외부화는 검증 후 후속 검토, §15).
- 영상 내 결제·커머스 트랜잭션(딥링크/프로필 링크 유도까지만).

---

## 3. 성공 지표 (North Star + KPI)

내부 운영 도구이므로 지표는 **"비용·시간·무인운영"** 중심으로 둔다.

### North Star
> **주당 "무인 발행된 승인 쇼츠 수"** — 사람 개입을 최소화한 채 검토 게이트를 통과해 채널에 실제 발행된 쇼츠의 주간 합계.
> (단순 생성량이 아니라 "발행까지 닿은 양"을 본다 — 파이프라인 끝까지 닫혀야만 카운트.)

### 보조 KPI
| KPI | 정의 | 목표 방향 |
|---|---|---|
| 발행 리드타임 | 상품 데이터 확보 → 발행 완료까지 경과 시간 | ↓ (분 단위) |
| 영상당 비용 | 스크래핑+LLM+TTS+렌더+발행 API 합산 단가 | ↓ · 상한 내 유지 |
| 자동화율 | 사람 개입(재작업 제외 단순 승인 외) 없이 통과한 비율 | ↑ |
| 발행 성공률 | 발행 시도 대비 성공(플랫폼 거절·오류 제외) | ↑ (목표 ≥ 95%) |
| 검토 적체 | review 상태 대기 건수·평균 대기시간 | ↓ |
| 채널 성과 | 조회수·CTR·전환(프로필 링크 클릭) | ↑ (관측·학습용) |

> KPI 수집은 Phase 4에서 본격화. Phase 1~3에서는 리드타임·영상당 비용·발행 성공률을 우선 계측.

---

## 4. 사용자 & 페르소나

| 페르소나 | 정체 | 목표 | 페인 | 핵심 인터랙션 |
|---|---|---|---|---|
| **운영 감독자** | 본인(소유자) | 최소 시간으로 다수 쇼츠를 안전하게 발행 | 편집 시간·검토 누락·비용 폭주 | 대시보드 승인/반려, 일일 리포트, 전략 결정 |
| **자동화 워커/에이전트** | 파이프라인 워커·Claude/n8n | 명령·스케줄에 따라 단계 실행 | 스크래핑 실패·API 한도·싱크 오류 | 큐 소비, 단계 실행, 로그·알림 발행 |
| **임시 운영자** | 본인(애드혹 모드) | "특정 상품 즉시 N개" 빠르게 생성 | 정형 입력 작성 번거로움 | CLI 자연어 명령("1024번 정보형 3개") |

> 외부 고객 페르소나는 Non-goal(§2)에 따라 제외.

---

## 5. 핵심 사용 시나리오 (User Journeys)

### J1. 애드혹 생성 (임시 운영자)
```
CLI:  쇼츠생성 --상품ID 1024 --수량 3 --스타일 정보형
  또는 자연어:  "1024번 이어버드 정보형으로 3개 만들어줘"
→ 백엔드가 의도 파싱(상품ID/수량/스타일) → 큐 적재(pending)
→ 워커: 수집 → 스크립트 → 음성 → 렌더 (generating)
→ 완료 시 review 상태 + Telegram "검토 대기" 알림
→ 대시보드에서 승인 → published → 채널 발행
```

### J2. 정기 배치 (무인)
```
n8n cron(예: 매일 09:00) → 당일 대상 상품 N개 생성 작업 일괄 적재
→ 워커가 일 30개 쿼터 내에서 순차 처리(동시 워커 max 2)
→ review 큐 적재 → 감독자 일괄 승인 → 스케줄 발행(플랫폼 쿼터 분산)
```

### J3. 일일 성과 리포트
```
매일 정해진 시각 → 성과 API 수집 → reports/{date}.md 생성
→ 검토 적체 ≥ 임계 시 Telegram 요약 알림(외부 전송은 사전 승인)
```

---

## 6. 범위 (In / Out of Scope)

**In scope (end-to-end):**
상품 데이터 수집 · 스크립트 생성(LLM) · 음성/BGM(TTS) · 영상 렌더(Remotion) · 백엔드 API+비동기 큐 · CLI 실행기 · 대시보드(실데이터 연동) · 다채널 발행(YouTube/Instagram/TikTok) · 성과 수집/분석 · 알림/모니터링 · 배포/스케줄 운영.

**Out of scope:**
롱폼/가로 영상 · 실시간 라이브 · 외부 멀티테넌시/SaaS/결제 · 영상 내 직접 커머스 · 모바일 네이티브 앱.

---

## 7. 시스템 아키텍처 개요

### 데이터 흐름
```
[상품 소스]
   │  (URL/ID, 카탈로그)
   ▼
FR-1 스크래퍼(Playwright) ── 이미지·스펙·리뷰 → JSON
   ▼
FR-2 스크립트 생성(LLM)   ── 훅·씬·자막·스타일 → YAML
   ▼
FR-3 음성/BGM(TTS)        ── 씬별 오디오 + BGM (타이밍 동기화)
   ▼
FR-4 렌더(Remotion)       ── inputProps(Zod) → 9:16 MP4
   ▼
[검토 게이트(review)] ──(승인)──▶ FR-8 다채널 발행 ──▶ FR-9 성과 수집
   │
   └ FR-5 백엔드/큐가 전 단계 오케스트레이션 · FR-10 알림 · FR-6 CLI · FR-7 대시보드가 제어/가시화
```

### 모노레포 구성 (pnpm workspaces — `CLAUDE.md`/`COWORK_SETUP.md` 준거)
```
packages/
  cli/        Node commander — 자연어/정형 명령 → 백엔드 호출
  backend/    FastAPI + WebSocket — job 수명주기·쿼터·승인 게이트
  workers/    4단계 파이프라인(scraper·script·voice·render)
  frontend/   React 대시보드(shortsgen-dashboard.jsx 포팅)
db/           PostgreSQL 스키마(products·jobs·assets·metrics·logs)
scripts/      deploy.sh 등 운영 헬퍼
```

### 런타임 토폴로지
| 구성요소 | 위치 | 역할 |
|---|---|---|
| 개발/애드혹 | Cowork(로컬 VM) | 빌드·테스트·디버그·즉석 생성 |
| 24/7 워커·발행·WebSocket | VPS(aibitgo.com) + pm2 | 상시 큐 소비·자동 발행 |
| 오케스트레이션/cron | n8n(기존 인스턴스) | 일일 배치·리포트(BarroTube 패턴 재사용) |
| 알림 | Telegram 봇 | 생성/검토/발행/오류 알림 |
| 저장 | PostgreSQL + S3/로컬 | 상태·메타데이터 + 영상·에셋 |

> **렌더러 결정:** `COWORK_SETUP.md`는 Stage 4를 "FFmpeg/Fal.ai"로 언급하나, **실제 구현·채택 렌더러는 Remotion**(React 기반, 코드 렌더, Zod 입력). 본 PRD는 Remotion을 정본으로 한다.

---

## 8. 기능 요구사항 (FR)

> 상태 범례: **[구현]** 완료 · **[목업]** UI/시뮬만 · **[미구현]** 설계만.

### FR-1 상품 데이터 수집 · **[미구현]**
- Playwright(Python)로 상품 이미지·스펙·리뷰·가격을 추출해 JSON으로 정규화.
- **수용기준:** 상품 URL/ID 입력 → `productSchema` 호환 JSON 산출. 셀렉터 실패 시 폴백+재시도(최대 3), 요청 간 랜덤 지연. 실패는 로그+사유 명시.

### FR-2 스크립트 생성 · **[미구현]**
- LLM(GPT-4o/Claude)이 상품 JSON → YAML(제목·훅·씬 배열·자막·B-roll 키워드).
- 스타일 변형: 정보형 / 감성 / 다이나믹. 길이 15~30초로 클램프.
- **수용기준:** 동일 상품에 스타일 3종 산출 가능. 출력은 FR-4 inputProps로 매핑 가능한 필드 충족.

### FR-3 음성/BGM · **[미구현]**
- ElevenLabs TTS로 씬별 내레이션 + 무드별 BGM 매칭, 씬 타이밍과 동기화.
- **수용기준:** 스크립트 YAML → 씬별 wav + BGM 선택. 길이가 씬 duration과 정렬(±오차 허용범위 내).

### FR-4 영상 렌더 (Remotion) · **[구현 + 보강]**
- **현재 구현:** 9:16 1080×1920 @30fps. 타임라인 = `hookDuration + N×productDuration + outroDuration`(`src/Root.tsx`). Hook→Product×N→Outro 3종 씬, 테마 토큰 5색, 이미지/이모지 폴백, Google Fonts(Noto Sans KR + Archivo). CLI: `npm run render:props`, 썸네일 `npm run still`(frame 75).
- **보강 항목(미구현):**
  - `<Audio>` 트랙(내레이션+BGM) 합성 — FR-3 연동.
  - 키네틱 자막(내레이션 싱크).
  - 씬 전환 효과(슬라이드/스케일) — 현재 페이드만.
  - 긴 상품명 텍스트 오버플로 자동 축소.
  - Outro 미리보기 타일 4개 고정(`slice(0,4)`) → 상품 수 대응 동적화.
- **수용기준:** inputProps(+오디오/자막 필드) → MP4 산출, 오디오·자막이 씬과 동기화. 기존 무음 렌더 회귀 없음.

### FR-5 백엔드 API + 비동기 큐 · **[미구현]**
- FastAPI + 큐(BullMQ 또는 Celery+Redis). job 수명주기: `pending → generating → review → published`.
- **일 30개 쿼터** 강제, **사람 승인 게이트**(승인 전 발행 불가), WebSocket 실시간 로그.
- **수용기준:** 작업 적재/상태 조회/승인·반려 API. 쿼터 초과 시 거절+로그. 단계 실패 시 재시도/dead-letter.

### FR-6 CLI · **[목업→구현]**
- Node commander. 정형(`--상품ID --수량 --스타일`) + 자연어 명령 파싱 → 백엔드 호출.
- 파서 로직은 `shortsgen-dashboard.jsx`의 명령 파서 재사용.
- **수용기준:** 두 입력 형식 모두 의도(상품ID/수량/스타일)로 정확 파싱, 백엔드 작업 생성.

### FR-7 대시보드 · **[목업→구현]**
- kanban(pending/generating/review/published)·gallery·analytics·실시간 콘솔. 현재 인메모리 목업을 실 API/WebSocket으로 교체(`packages/frontend`로 포팅).
- **수용기준:** 실제 job 상태 표시, 승인/반려 동작, 실시간 로그 스트림, KPI 패널(§3) 연동.

### FR-8 다채널 발행 · **[미구현]**
- YouTube/Instagram/TikTok API(OAuth). 플랫폼별 일일 쿼터 분산, 썸네일(`npm run still`), 캡션·태그 업로드.
- **수용기준:** 승인된 job을 지정 채널에 업로드, 쿼터 초과 시 스케줄 이연, 결과 상태 기록.

### FR-9 성과 수집/분석 · **[미구현]**
- 플랫폼 Analytics API 폴링 → PostgreSQL → 대시보드 analytics.
- **수용기준:** 조회/CTR/전환 수집·저장, KPI(§3) 산출.

### FR-10 알림/모니터링 · **[미구현]**
- Telegram 봇: 생성완료·검토대기·발행성공·오류. 헬스체크·큐 적체 알림.
- **수용기준:** 이벤트별 알림 발송, 외부 전송 행위는 사전 승인 원칙 준수(§11).

---

## 9. 데이터 모델 (1) — inputProps 계약

> Zod 정본: `src/schema.ts:5-58`

**productSchema**
| 필드 | 타입/제약 | 의미 |
|---|---|---|
| `emoji` | string, default `📦` | 이미지 없을 때 폴백 |
| `image` | string, optional | URL(http/https) 또는 `public/` 파일명 |
| `category` | string | 카테고리 칩 |
| `name` | string[] (1~2) | 상품명 1~2줄 |
| `sub` | string | 스펙/설명 |
| `rating` | string | 별점(예 "4.9") |
| `reviews` | string | 리뷰 수(예 "2,841") |
| `was` | int ≥ 0 | 정가(원) |
| `now` | int ≥ 0 | 판매가(원) |
| `tint` / `tintDeep` | color(#RRGGBB) | 패널 밝은/진한 톤 |

**themeSchema:** `accent` · `ink` · `muted` · `stageFrom` · `stageTo` (모두 color)

**catalogSchema:** `brandName`("바로쇼핑") · `eyebrow` · `hookTitle[2]` · `hookSub` · `cta` · `outroTitle[2]` · `outroSub` · `outroCta` · `fps`(기본 30) · `hookDuration`(60) · `productDuration`(90) · `outroDuration`(90) · `theme` · `products[]`(≥1)

**길이 계산:** `durationInFrames = hookDuration + products.length × productDuration + outroDuration` (`src/Root.tsx:14-21`). 예: 상품 3개 → 60 + 3×90 + 90 = **420프레임(14초@30fps)**.

---

## 10. 데이터 모델 (2) — 영속 스키마 (PostgreSQL)

> 신규 DB 테이블 스케치 (FR-5 백엔드/큐가 사용).

| 테이블 | 핵심 컬럼 | 비고 |
|---|---|---|
| `products` | id, source_url, name, specs(jsonb), images(jsonb), price_was, price_now, scraped_at | FR-1 산출 |
| `jobs` | id, product_id, style, status, quota_date, created_at, approved_by, published_at | 상태 enum 아래 |
| `assets` | id, job_id, type(image/audio/video), path/url, cache_key | 캐시 재사용 키 |
| `metrics` | id, job_id, platform, views, ctr, conversion, fetched_at | FR-9 |
| `logs` | id, job_id, stage, level, message, ts | WebSocket 스트림 소스 |

**job status enum:** `pending` · `generating` · `review` · `published` · `failed`

---

## 11. 비기능 요구사항 (NFR)

| 분류 | 요구사항 |
|---|---|
| 쿼터 | 일 30개 생성 상한(CLI+백엔드 동시 강제). 초과 시 거절+로그. |
| 비용 | 스테이지별 단가(스크래핑/LLM/TTS/렌더/발행 API) 계측, 예산 상한·소진 임박 시 Telegram 경고. |
| 성능 | 큐 동시 워커 max 2. 렌더 시간 계측·기준선 설정. 캐시 재사용으로 재실행 비용 절감. |
| 안전(크롤링) | 요청 간 랜덤 지연, 지수 백오프 재시도(최대 3), 파서 실패 로그 명시. robots/약관 준수. |
| 보안 | 시크릿은 `.env`(+`.env.example`)에만, 커밋·문서·채팅 금지. Cowork 폴더 단위 권한(홈 전체 금지). |
| 신뢰성 | 단계 실패 재시도 + dead-letter, 자산 캐시(상품ID+버전 키)로 재스크래핑/재TTS 방지. |
| 관측성 | 단계별 메트릭(렌더 시간·큐 길이·오류율), 헬스체크, 일일 리포트. |
| 코드 규약(`CLAUDE.md`) | pnpm 모노레포, Biome(ESLint 아님), `any` 금지, Conventional Commits, 서버액션/명확한 엔드포인트 선호. |

---

## 12. 운영 (Operations 개요)

- **배포:** Cowork 빌드 → git push → VPS pull → `scripts/deploy.sh`(deps 설치, pm2 start/reload backend+workers). pm2 ecosystem으로 재부팅 자동 복구. `.env`는 VPS에만.
- **스케줄:** n8n cron — 일일 배치 생성·발행(플랫폼 쿼터 분산), 일일 성과 리포트.
- **승인 게이트:** 모든 발행은 대시보드 승인 후에만. 발행/메시지/삭제 등 **외부·비가역 행위는 사전 승인** 원칙.
- **장애 대응(체크리스트 개요):** 큐 적체 → 워커 상태/로그 확인 → 재시작. 발행 실패 → 플랫폼 쿼터/토큰 확인 → 이연. 스크래핑 실패 → 셀렉터 점검.
- 상세 절차·런북은 후속 `docs/RUNBOOK.md`로 분리.

---

## 13. 로드맵 / 마일스톤 (MVP 최단경로 우선)

> 척추 원칙: **발행까지 닿는 가장 얇은 수직 슬라이스를 먼저 닫는다.** 각 Phase는 이전 Phase 없이도 가치가 닫히도록 구성.

### Phase 0 — 렌더 레이어 안정화 (현 코드 기반)
- 목표: 현재 Remotion 합성을 운영 가능 상태로 다지기.
- 산출물: 텍스트 오버플로 자동 축소 + (선택)오디오 훅 골격, `out/` MP4 산출 검증 루틴.
- DoD: 임의 상품 수(1~N) JSON으로 무오류 렌더, 회귀 없음.
- 의존성: 없음(기구현).

### Phase 1 — MVP 수직 슬라이스 ← **최우선**
- 목표: **수동 상품 JSON → 렌더 → 1개 채널 수동 발행**까지 관통.
- 산출물: 상품 JSON 템플릿/작성 가이드 + `render:props` 렌더 + 1개 채널(**YouTube Shorts**, §15 D2) 수동 업로드 절차.
- DoD: "상품 1건 → 발행 1건"이 **스크래퍼·큐 없이** 닫힘.
- 의존성: Phase 0.

### Phase 2 — 생성 자동화
- 목표: 데이터·콘텐츠·음성·작업관리 자동화.
- 산출물: FR-1 스크래퍼 + FR-2 스크립트 + FR-3 음성 + FR-5 백엔드/큐 + FR-6 CLI.
- DoD: CLI 명령 → 자동 생성 → review 적재까지 무인.
- 의존성: Phase 1.

### Phase 3 — 운영 자동화
- 목표: 24/7 무인 운영.
- 산출물: n8n 스케줄(배치 생성·발행), FR-8 멀티채널 발행, FR-10 Telegram, FR-7 대시보드 실연동, VPS 배포.
- DoD: 사람은 승인만, 생성~발행이 스케줄로 자동 순환.
- 의존성: Phase 2.

### Phase 4 — 성과/최적화
- 목표: 측정·학습·비용 최적화.
- 산출물: FR-9 성과 수집, KPI 대시보드, A/B(스타일·테마), 비용 리포트.
- DoD: North Star·보조 KPI 주간 자동 산출.
- 의존성: Phase 3.

---

## 14. 위험 & 완화 (Risk Register)

| 위험 | 영향 | 완화책 |
|---|---|---|
| 플랫폼 정책/저작권(이미지·BGM·상품정보) | 높음 | 라이선스 확인, 자사/허용 자산 우선, 출처 기록 |
| 크롤링 차단·구조 변경 | 높음 | 랜덤 지연·백오프, 셀렉터 모듈화, 폴백/수동 입력 경로 유지 |
| LLM 비용·품질 편차 | 중간 | 프롬프트 템플릿화, 길이/형식 검증, 모델 등급 분기, 캐시 |
| 플랫폼 API 쿼터 소진 | 중간 | 쿼터 추적·분산 스케줄, 임박 알림 |
| 음성-자막-씬 싱크 오류 | 중간 | duration 정렬 검증, 렌더 전 QA 게이트 |
| 단일 VPS 장애 | 중간 | pm2 자동복구, 헬스체크 알림, 상태 DB로 재개 가능 |
| 비용 폭주(무인 운영) | 중간 | 일 30개 쿼터+예산 상한+소진 경고 |

---

## 15. 확정 결정 (Resolved Decisions)

> PRD v0.1의 "오픈 퀘스천"을 확정한 결과. 확정 기준 = **MVP 최단경로 + 내부 운영 도구 + Barro* 패턴 재사용**. (드래프트이므로 운영자가 언제든 변경 가능)

| # | 항목 | 확정 | 근거 |
|---|---|---|---|
| D1 | 상품 데이터 소스 | **MVP(Phase 1)는 수동 JSON 입력**. 자동 스크래핑은 Phase 2부터, **약관이 허용하는 자사/제휴 카탈로그**만 대상. | "스크래퍼 없이 발행까지 닫는" MVP 원칙과 일치, 저작권/크롤링 리스크(§14) 선제 회피 |
| D2 | 발행 채널 우선순위 | **1순위 YouTube Shorts** → 2순위 Instagram Reels → 3순위 TikTok. Phase 1 수동 발행 대상 = **YouTube Shorts**. | BarroTube가 이미 YouTube OAuth/업로드 보유 → 재사용이 최단경로 |
| D3 | 예산 통제 | **통제 프레임 확정**: 영상당 비용 = 스테이지 변동비 합(렌더는 로컬≈0원), 월 한도 = 일 30개 쿼터 기준, 소진 80%에서 Telegram 경고. 구체 금액은 실측 후 운영자 확정(잠정 가이드: 영상당 ≤ 1,000원 목표). | 렌더 로컬화로 변동비는 LLM+TTS에 집중. 수치는 §11 NFR에 확정 반영 |
| D4 | BarroTube 자산 재사용 | **재사용 확정**: 스크립트 YAML 스키마 · n8n 워크플로 패턴 · Telegram 봇 인프라. 단 **페르소나/톤은 쇼핑 도메인용으로 분리**. | CLAUDE/COWORK 기 명시, 중복 구축 회피 |
| D5 | 테마/브랜드 변형 | **MVP는 단일 바로쇼핑 테마(warm) 고정**. 캠페인별 테마 변형·A/B는 Phase 4. | 테마 토큰 5색 기구현 → 변형은 데이터 교체만, 우선순위 후순위 |
| D6 | 상품 큐레이션 주체 | **MVP는 운영자 수동 선정**. 규칙 기반 자동 선정은 Phase 3+ 옵션. | 사람 승인 게이트 철학과 일관, MVP 단순화 |

### 잔여 운영자 확정 항목 (수치·권한 — 사람만 정할 수 있음)
- **D3 예산 금액**: 영상당/월 상한 구체 수치 — 1~2주 실측 단가 확보 후 확정.
- **D1 스크래핑 대상·권한**: 자동 수집 대상 사이트와 약관/API 허용 여부 — Phase 2 착수 전 확정.

> 가정: 본 시스템은 **본인 운영용 내부 도구**이며 외부 멀티테넌시는 Non-goal(§2). 외부 상품화는 본 PRD 범위 밖 후속 검토.

---

## 16. 부록 A — 현재 구현 인벤토리 (2026-06-14)

| 영역 | 상태 | 근거 파일 |
|---|---|---|
| Remotion 합성(Hook/Product/Outro) | **구현** | `src/ShoppingCatalog.tsx`, `src/scenes/*` |
| inputProps Zod 계약 | **구현** | `src/schema.ts` |
| 동적 길이 계산 | **구현** | `src/Root.tsx:14-21` |
| 테마 5토큰 · 폰트 로드 | **구현** | `src/schema.ts`, `src/load-fonts.ts` |
| 이미지/이모지 폴백 | **구현** | `src/utils.ts`(resolveSrc), `public/README.txt` |
| 렌더/스튜디오/썸네일 스크립트 | **구현** | `package.json` |
| 오디오/자막/씬 전환/오버플로 | **미구현** | `README.md:143-148` |
| Outro 타일 동적화(현재 4개 고정) | **미구현** | `src/scenes/OutroScene.tsx`(`slice(0,4)`) |
| 대시보드(kanban/gallery/analytics/CLI바) | **목업** | `shortsgen-dashboard.jsx` |
| 스크래퍼·스크립트·음성·백엔드·큐·발행·DB | **미구현** | `CLAUDE.md`, `COWORK_SETUP.md`(설계만) |

---

## 17. 부록 B — 용어집

| 용어 | 의미 |
|---|---|
| 바로쇼핑 | 영상에 노출되는 제품/서비스 브랜드명 |
| ShortsGen | 이를 구동하는 내부 시스템(코드베이스)명 |
| inputProps | 영상 1개를 정의하는 구조화 입력(Zod 검증) |
| Hook/Product/Outro 씬 | 도입/상품카드/마무리 3종 씬 |
| review 게이트 | 발행 전 사람 승인 단계(QA) |
| 일 30개 쿼터 | 생성 일일 상한(비용·안전 통제) |
| Cowork / VPS / n8n | 개발 / 24/7 워커 / 오케스트레이션 런타임 |
| Barro* 제품군 | BarroTube(YouTube 자동화)·BarroAiTrade(자동매매)와 패턴 공유 |

---

*End of PRD v0.2 (Draft)*
