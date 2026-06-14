# @shortsgen/workers

생성부 (FR-1~4). 4단계 파이프라인을 순차 실행한다.

| 단계 | 모듈 | 스택 | 실행 prereq | 스텝 |
|---|---|---|---|---|
| 1 수집 | `scrape.py` | Playwright | **D1 대상 사이트·셀렉터** + `playwright install` | P2-7 |
| 2 스크립트 | `script.py` | LLM(Anthropic) | `ANTHROPIC_API_KEY` | P2-4 |
| 3 음성/BGM | `voice.py` | ElevenLabs | `ELEVENLABS_API_KEY` | P2-5 |
| 4 렌더 | (backend.render_stage) | @shortsgen/render | — (구현 완료) | P2-6 |

## 상태 (P2-4·5·7)
- **코드 구현 완료** + **결정적 로직 단위테스트**(`pyproject` + `tests/`): 프롬프트 구성·응답 파싱(script), TTS 요청 구성(voice), 추출→productSchema 정규화(scrape).
- **실제 실행은 위 prereq 충족 시 동작** — 키/대상이 없으면 명확한 `RuntimeError`. dev 백엔드 워커는 키 없을 때 해당 단계를 스텁 로그로 우회(render만 실제 수행).

## 테스트
```bash
cd packages/workers
python3 -m venv .venv && ./.venv/bin/pip install -r requirements-dev.txt
./.venv/bin/pytest          # 결정적 로직 검증 (외부 API/브라우저 불필요)
```

## 런타임 설치 (실행 시)
```bash
pip install -r requirements.txt   # httpx · pyyaml · playwright
playwright install chromium       # 스크래퍼용
```
재시도(최대 3)·백오프·dead-letter·캐시 재사용은 prod 큐(Celery/Redis) 전환 시(PRD §11 / P4-5).
