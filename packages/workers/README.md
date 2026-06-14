# @shortsgen/workers

생성부 (FR-1~4). 4단계 파이프라인을 순차 실행한다.

| 단계 | 모듈 | 스택 | 실행 prereq | 스텝 |
|---|---|---|---|---|
| 1 수집 | `scrape.py` | Playwright | **D1 대상 사이트·셀렉터** + `playwright install` | P2-7 |
| 2 스크립트 | `script.py` | **Claude Code 스킬(barroShopping)** | `claude` CLI(Claude Code) — **API 키 불필요** | P2-4 |
| 3 음성/BGM | `voice.py` | ElevenLabs | `ELEVENLABS_API_KEY` | P2-5 |
| 4 렌더 | (backend.render_stage) | @shortsgen/render | — (구현 완료) | P2-6 |

## 스크립트 생성 (P2-4) — Claude Code 스킬
Anthropic API 키가 아니라 **Claude Code 스킬**로 작성한다.
- 전역 스킬: `~/.claude/skills/barroshopping/SKILL.md` → 어느 세션에서나 `/barroShopping`
- 프로젝트 폴백: `.claude/skills/shorts-script/SKILL.md` (레포 포함)
- 헤드리스 `claude -p`는 `/명령`을 지원하지 않으므로, `script.py`가 **스킬 본문을 프롬프트에 주입**(전역 우선·프로젝트 폴백)해 결정적으로 사용 → 상품 → 훅·씬·자막·CTA JSON.
- `skill_body()`/`build_prompt()`/`parse_script()`는 결정적(단위테스트).

## 상태 (P2-4·5·7)
- **코드 구현 완료** + **결정적 로직 단위테스트**: 스킬 본문 로드·프롬프트 구성·응답 파싱(script), TTS 요청 구성(voice), 추출→productSchema 정규화(scrape).
- 실행 prereq: script=`claude` CLI / voice=`ELEVENLABS_API_KEY` / scrape=D1 대상 + Playwright. 미충족 시 명확한 `RuntimeError`.

## 테스트
```bash
cd packages/workers
python3 -m venv .venv && ./.venv/bin/pip install -r requirements-dev.txt
./.venv/bin/pytest          # 결정적 로직 검증 (외부 API/브라우저/CLI 불필요)
```

## 런타임 설치 (실행 시)
```bash
pip install -r requirements.txt   # httpx · pyyaml · playwright
playwright install chromium       # 스크래퍼용
# script: Claude Code 설치·로그인 필요 (claude CLI). 전역 스킬 barroShopping 사용.
```
재시도(최대 3)·백오프·dead-letter·캐시 재사용은 prod 큐(Celery/Redis) 전환 시(PRD §11 / P4-5).

## 쿠팡 (P2-7) — 스크래핑 대신 파트너스 OpenAPI
쿠팡은 봇 방어(403 Access Denied)로 Playwright 헤드리스 스크래핑이 차단된다(셀렉터는 `scrape_coupang.py`에 튜닝됨, 스크랩 가능한 사이트엔 동작). **운영은 `coupang_partners.py`(파트너스 OpenAPI, HMAC)** 로 상품검색·deeplink를 받는다 — 약관 친화적·안정적. 키: `COUPANG_ACCESS_KEY`/`COUPANG_SECRET_KEY`.
