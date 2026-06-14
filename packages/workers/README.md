# @shortsgen/workers

생성부 (FR-1~4). 비동기 큐로 4단계 파이프라인을 순차 실행한다.

| 단계 | 함수 | 스택 | 스텝 |
|---|---|---|---|
| 1 수집 | `scrape` | Playwright | P2-7 |
| 2 스크립트 | `script` | LLM → YAML | P2-4 |
| 3 음성/BGM | `voice` | ElevenLabs | P2-5 |
| 4 렌더 | `render` | @shortsgen/render(Remotion) | P2-6 |

현재 `pipeline.py` 는 인터페이스/순서 스텁(`NotImplementedError`). 큐(Celery/RQ)·실제 구현은 P2-4~7.
캐시 재사용·재시도(백오프)·dead-letter는 PRD §11 / P4-5.
