"""바로쇼핑 생성 파이프라인 — 4단계 오케스트레이션 (FR-1~4).

각 단계 구현은 stage 모듈에 위임. 실제 실행 prereq:
  1) scrape : Playwright + D1 대상 사이트·셀렉터        [scrape.py / P2-7]
  2) script : Claude Code 스킬(barroShopping), claude CLI [script.py / P2-4]
  3) voice  : ELEVENLABS_API_KEY                         [voice.py  / P2-5]
  4) render : @shortsgen/render (Remotion)               [P2-6]

prod 워커(Celery/Redis)가 이 순서를 큐로 구동.
"""
from __future__ import annotations

from typing import Any

from . import compose, scrape, script, voice  # noqa: F401  (단계 구현)

STAGES = ("scrape", "script", "voice", "render")


def run_from_product(
    product: dict[str, Any], style: str = "정보형", brand: str = "바로쇼핑"
) -> dict[str, Any]:
    """상품 dict → 스크립트(Claude Code) → 렌더 catalog inputProps (P2-9 결합).

    스크래퍼(P2-7) 없이 수동 상품 dict로도 동작. 음성·렌더는 호출부에서 결합.
    """
    spec = script.generate(product, style)  # Claude Code 스킬 (claude -p)
    catalog = compose.compose_catalog([product], spec, brand=brand)
    return {"script": spec, "catalog": catalog}


def run(url: str, selectors: dict[str, str], style: str = "정보형") -> dict[str, Any]:
    """대상 URL → 스크랩 → 스크립트 → catalog (스크래퍼 D1 대상 필요)."""
    product = scrape.scrape(url, selectors)
    return run_from_product(product, style)
