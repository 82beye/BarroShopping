"""바로쇼핑 생성 파이프라인 — 4단계 오케스트레이션 (FR-1~4).

각 단계 구현은 stage 모듈에 위임. 실제 실행에는 자격증명/대상이 필요:
  1) scrape : Playwright + D1 대상 사이트·셀렉터        [scrape.py / P2-7]
  2) script : ANTHROPIC_API_KEY                          [script.py / P2-4]
  3) voice  : ELEVENLABS_API_KEY                         [voice.py  / P2-5]
  4) render : @shortsgen/render (Remotion) — backend.render_stage 또는 subprocess [P2-6]

prod 워커(Celery/Redis)가 이 순서를 큐로 구동. dev는 backend 인메모리 워커가
render 단계만 실제 수행(나머지는 키 없으면 스텁).
"""
from __future__ import annotations

from typing import Any

from . import scrape, script, voice  # noqa: F401  (단계 구현)

STAGES = ("scrape", "script", "voice", "render")


def run(url: str, selectors: dict[str, str], style: str = "정보형") -> dict[str, Any]:
    """상품 URL → 스크립트까지 (음성·렌더는 호출부에서 자격증명/렌더러와 결합)."""
    product = scrape.scrape(url, selectors)
    spec = script.generate(product, style)
    return {"product": product, "script": spec}
