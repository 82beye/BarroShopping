# COWORK_SETUP.md — Cowork로 ShortsGen 빌드부터 운영까지

이 문서는 Claude Cowork에서 ShortsGen을 단계별로 구현하고 운영하기 위한 실전 런북입니다.
프롬프트는 **그대로 복사해 Cowork 작업창에 붙여넣으면** 됩니다.

---

## Part 0. 무엇을 Cowork로, 무엇을 VPS로?

| 일 | 어디서 | 이유 |
|---|---|---|
| 코드 빌드·테스트·디버그 | **Cowork (로컬 VM)** | 스크립트를 즉시 실행·반복. 결과 파일을 폴더에 직접 생성 |
| 대화형 운영 (특정 상품 쇼츠 생성/검토) | **Cowork** | "1024번 감성 VLOG 2개" 같은 즉석 작업 |
| 정기 감독 작업 (매일 성과 리포트 등) | **Cowork 스케줄 작업** | cadence 한 번 정의 → 반복 |
| 워커 큐 · 일일 자동발행 · WebSocket 서버 | **VPS(aibitgo.com) + pm2** | 24/7 상주 필요. Cowork VM은 상시 서버가 아님 |
| 오케스트레이션 · 크론 | **n8n (기존 인스턴스)** | BarroTube 운영 방식 그대로 |

> 핵심: Cowork는 **만들고 굴려보는 곳**, VPS는 **계속 돌아가는 곳**.

---

## Part 1. 사전 준비 (5분)

1. **폴더 생성 후 권한만 부여** — Cowork는 폴더 단위 권한 모델입니다.
   - `~/projects/shortsgen/` 를 만들고, Cowork에서 **이 폴더에만** 읽기/쓰기 권한 부여.
   - ⚠️ 상위 폴더(예: 홈 전체)는 절대 열지 마세요. (대용량 폴더를 통째로 읽다 사고나는 사례 있음 — 범위를 좁게.)
2. **시드 파일 배치** — 이 폴더에 `CLAUDE.md`, `COWORK_SETUP.md`, `shortsgen-dashboard.jsx`를 넣어둡니다.
3. **비밀키는 `.env`로만** — Cowork에 키를 채팅으로 주지 말고, 직접 `.env`에 적습니다. 프롬프트에는 "`.env`에서 읽어라"라고만.
4. **연결(connectors)** — 필요 시 GitHub/GitLab, Google Drive, Slack 등 연결. (Telegram 알림은 봇 토큰을 `.env`로.)

---

## Part 2. Day-1 킥오프 프롬프트 (스캐폴딩)

> Cowork 새 작업창에 그대로 붙여넣기:

```
~/projects/shortsgen/ 폴더에서 작업해. 먼저 CLAUDE.md를 읽고 그 결정사항을 그대로 따라.

오늘 목표는 모노레포 스캐폴딩이야. 다음을 순서대로 해줘:
1. CLAUDE.md의 폴더 레이아웃대로 pnpm 워크스페이스 모노레포를 만들어
   (packages/cli, backend, workers, frontend, db, scripts).
2. 루트에 Biome 설정, .gitignore, .env.example, pnpm-workspace.yaml을 만들어.
   .env.example에는 키 이름만 두고 값은 비워둬 (OPENAI_API_KEY, ANTHROPIC_API_KEY,
   ELEVENLABS_API_KEY, TELEGRAM_BOT_TOKEN, DATABASE_URL 등).
3. db/에 PostgreSQL 스키마 초안을 만들어:
   products, jobs(상태: pending/generating/review/published), assets, metrics, logs.
4. README.md에 전체 구조와 각 패키지 1줄 설명, 로컬 실행 순서를 적어.
5. git 초기화 후 conventional commit으로 첫 커밋.

각 단계 끝나면 무엇을 만들었는지 1~2줄로 보고하고, 다음 단계로 넘어가기 전에 확인받아.
설치가 막히면(Zscaler 등) 에러를 그대로 보여줘 — 임의로 우회하지 마.
```

---

## Part 3. 단계별 빌드 프롬프트

각 단계는 **독립 실행 + 테스트 + 사용법 1줄**까지 끝내고 다음으로. 한 단계씩 붙여넣으세요.

### ① Scraper (에셋 수집) — Playwright Python
```
packages/workers/scraper 를 만들어. Playwright(Python) 헤드리스로 상품 URL을 받아
이미지 src, 상품명, 가격/프로모션, 상세 스펙 텍스트, 베스트 리뷰를 추출해 JSON으로 저장해.
필수: 요청 간 무작위 딜레이(1~3초), 실패 시 지수 백오프 재시도(최대 3회),
셀렉터 파싱 실패 시 폴백 셀렉터 + 명확한 에러 로그(stderr).
실제 사이트 대신 먼저 로컬 샘플 HTML로 단위 테스트를 만들어 검증해.
(참고: Naver 카페 크롤러와 동일한 안전 패턴 — 그 구조를 재사용해도 좋아.)
```

### ② 스크립트 생성 — LLM → YAML
```
packages/workers/script 를 만들어. scraper의 JSON을 입력으로,
.env의 OPENAI_API_KEY/ANTHROPIC_API_KEY를 읽어 15~30초 쇼츠 대본을 생성해.
출력은 YAML 스키마로: title, hook, scenes[](narration, duration, broll_keywords), captions[].
스타일 인자(감성 VLOG/정보형/리뷰형/다이나믹)에 따라 톤을 바꿔.
샘플 JSON으로 실행해서 YAML이 스키마대로 나오는지 검증해.
```

### ③ 음성·BGM
```
packages/workers/voice 를 만들어. script의 YAML 나레이션을 ElevenLabs TTS로 음성 생성,
씬별 오디오 파일로 저장. BGM은 분위기 태그로 매칭(초기엔 로컬 BGM 폴더에서 선택).
키는 .env에서 읽고, 호출 실패/빈 프롬프트 같은 엣지 케이스 에러 처리 포함.
```

### ④ 영상 합성 — FFmpeg
```
packages/workers/render 를 만들어. scraper 이미지 + voice 오디오 + 자막을 FFmpeg로 병합해
9:16 세로 쇼츠 mp4를 출력해. 이미지 슬라이드쇼 + 자막 번인(MVP).
FFmpeg 설치 여부를 먼저 확인하고, 샘플 에셋으로 1개 영상을 끝까지 뽑아 검증해.
```

### ⑤ Backend + 큐
```
packages/backend 를 FastAPI로 만들어. 엔드포인트: 작업 생성/조회/상태변경/승인.
워커 큐(Celery+Redis 또는 BullMQ 중 선택)로 ①~④를 순차 비동기 실행하고
단계 전환마다 상태 DB 갱신 + WebSocket으로 로그/상태 push.
일일 생성 쿼터(기본 30) 강제, 초과 시 거부. 휴먼 승인 전엔 published로 못 넘어가게.
```

### ⑥ CLI — 자연어 + 정형
```
packages/cli 를 Node commander로 만들어. shorts-gen/publish/status/analytics 명령.
입력이 자연어면 LLM으로 파싱해 정형 인텐트(상품ID/수량/스타일)로 변환 후 backend 호출.
명령 히스토리, --help, 쿼터 표시 포함. 예제 명령으로 e2e 동작 확인.
```

### ⑦ 대시보드 이식 + 실데이터
```
shortsgen-dashboard.jsx 를 packages/frontend 에 React 앱으로 이식해.
지금은 목업/시뮬레이션인데, 이걸 backend WebSocket 실데이터로 교체해:
- 칸반/갤러리/분석을 API에서 받은 jobs·metrics로 렌더
- 하단 콘솔은 WebSocket 로그 스트림 구독
- 상단 명령바는 backend의 CLI 인텐트 엔드포인트로 전송
디자인 토큰·레이아웃은 유지해.
```

---

## Part 4. 운영 (상시 가동)

### A. VPS 배포 (워커·발행·WebSocket 상주)
```
scripts/deploy.sh 를 만들어: VPS(aibitgo.com)로 코드 배포 → 의존성 설치 →
backend/workers를 pm2로 기동(ecosystem.config.js). pm2 startup으로 재부팅 시 자동 복구.
민감정보는 VPS의 .env에 두고 커밋하지 않아. 배포 후 헬스체크까지 확인.
```

### B. 일일 발행 스케줄러
- n8n(기존 인스턴스)에 크론 워크플로 추가: 정해진 시각에 `review` 통과분 중 승인된 것만 발행.
- 플랫폼별 API 일일 할당량을 고려해 시차 발행. 발행 결과를 Telegram으로 알림.

### C. Cowork 스케줄 작업 (감독용)
> Cowork에 cadence를 등록:
```
매일 오전 9시, ShortsGen backend의 analytics API에서 전일 성과(조회수/CTR/전환율)를 가져와
요약 리포트를 만들고 ~/projects/shortsgen/reports/ 에 날짜별 마크다운으로 저장해.
검토 대기(review)가 3건 이상이면 Telegram으로 알림 메시지를 보내(텍스트 초안을 먼저 보여주고 승인받아).
```
> (메시지 전송 같은 외부 행동은 Cowork가 실행 전 확인을 받습니다 — 승인 후 발송.)

---

## Part 5. Cowork 실전 팁

- **CLAUDE.md를 메모리로 활용:** 새 결정·선호가 생기면 "이걸 CLAUDE.md에 기록해줘"라고 시켜 영구 저장. 다음 세션이 그대로 이어집니다.
- **서브에이전트 병렬화:** "scraper와 script를 병렬로 스캐폴딩해"처럼 독립 작업은 병렬 지시 가능. 단, 통합·테스트는 순차로.
- **한 번에 한 단계:** 파이프라인 전체를 한 프롬프트에 몰지 말고 위 ①~⑦처럼 끊어서. 검증 가능 + 컨텍스트 안정.
- **외부 행동 = 확인:** 발행·메시지 전송·삭제 같은 비가역 동작은 항상 초안/계획을 먼저 받고 승인. 키 입력·결제·권한변경은 Cowork에 시키지 말고 직접.
- **폴더 권한은 좁게:** 프로젝트 폴더만. 권한 부여 전 백업.
- **막히면 그대로 보고:** Zscaler/오프라인 번들 이슈는 우회 대신 에러를 보여주게 해서 기존 방식(NODE_EXTRA_CA_CERTS 등)으로 직접 처리.

---

### 빠른 시작 3줄 요약
1. `~/projects/shortsgen/` 만들고 폴더 권한 부여 → 시드 3파일 넣기.
2. **Part 2 킥오프 프롬프트** 붙여넣어 스캐폴딩.
3. **Part 3 ①~⑦** 한 단계씩 진행 → 상시 부분은 **Part 4**로 VPS에 올리기.
