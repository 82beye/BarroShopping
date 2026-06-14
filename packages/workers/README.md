# @shortsgen/workers

생성부 (FR-1~4). 4단계 파이프라인을 순차 실행한다.

| 단계 | 모듈 | 방식 | 실행 prereq | 스텝 |
|---|---|---|---|---|
| 1 수집 | `crawl.py` | **구조화 데이터 크롤(JSON-LD/OG)** — 사이트별 셀렉터·API 불필요 | (봇방어 사이트만) 실 크롬 | P2-7 |
| 2 스크립트 | `script.py` | **Claude Code 스킬(barroShopping)** | `claude` CLI — API 키 불필요 | P2-4 |
| 3 음성/BGM | `voice.py` | ElevenLabs | `ELEVENLABS_API_KEY` | P2-5 |
| 4 렌더 | (backend.render_stage) | @shortsgen/render | — | P2-6 |

## 상품 수집 (P2-7) — 구조화 데이터 크롤 (간편·확장성)
사이트별 셀렉터 튜닝이나 플랫폼 OpenAPI(가입·키·HMAC) **없이**, 대부분의 쇼핑몰이 페이지에 넣는
**구조화 데이터로 한 번에 수집**한다 → 몰이 늘어도 코드 1벌로 커버(확장성).

- `crawl.extract_product(html)` — **1) JSON-LD(schema.org/Product) → 2) OpenGraph 메타 → 3) CSS 폴백** 순. HTML '문자열'에서 추출하므로 WebFetch/requests/Playwright 어디서 받은 HTML이든 동작(브라우저·API 불필요).
- `crawl.fetch_html(url, headed=False)` — 페이지 HTML 확보. **봇방어 사이트(쿠팡 등)는 `headed=True`** (사용자 로컬 **실 크롬**, `channel=chrome`)로 통과. 헤드리스/데이터센터 IP는 차단됨.
- **수집 후 확정**: 결과의 `_needs_review`(누락/저신뢰 필드 목록)를 운영자가 확인·보정 → 파이프라인. (HITL)
- `_source`(json-ld|opengraph|none)로 신뢰도 판단.

### 폴백/선택 경로
- `scrape.py` — 구조화 데이터가 없는 사이트용 **CSS 셀렉터** 수집(사이트별).
- `coupang_partners.py` — 쿠팡 한정 **파트너스 OpenAPI**(상품검색·deeplink, 키 필요). 크롤이 막히거나 정식 deeplink가 필요할 때 선택.

## 스크립트 생성 (P2-4) — Claude Code 스킬
전역 스킬 `~/.claude/skills/barroshopping/`(`/barroShopping`) / 프로젝트 폴백 `.claude/skills/shorts-script/`.
헤드리스 `claude -p`에 스킬 본문 주입(결정적). API 키 불필요.

## 테스트
```bash
cd packages/workers
python3 -m venv .venv && ./.venv/bin/pip install -r requirements-dev.txt
./.venv/bin/pytest          # crawl(JSON-LD/OG)·compose·script·partners HMAC 등 22 케이스
```

## 런타임 설치 (실행 시)
```bash
pip install -r requirements.txt   # httpx · pyyaml · playwright
playwright install chromium       # crawl headed/scrape용
# script: Claude Code(claude CLI). partners: COUPANG_ACCESS_KEY/SECRET_KEY(선택)
```
재시도(최대 3)·백오프·dead-letter·캐시 재사용은 prod 큐(Celery/Redis) 전환 시(PRD §11 / P4-5).
