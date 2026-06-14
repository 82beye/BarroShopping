"""상품 + 스크립트 → render catalogSchema inputProps 조립 (P2-9 결합).

script.generate(상품 → hook/scenes/cta)의 카피와 상품 데이터를 합쳐 렌더 입력(catalog)을
만든다. 결정적(단위테스트 가능). 테마 기본 warm. 음성·렌더는 호출부에서 결합.
"""
from __future__ import annotations

from typing import Any

WARM_THEME = {
    "accent": "#FF4D2E",
    "ink": "#1A1714",
    "muted": "#8C8377",
    "stageFrom": "#FBF7F0",
    "stageTo": "#EFE6D7",
}


def _two(seq: Any, fallback: list[str]) -> list[str]:
    items = [s for s in (seq or []) if s]
    while len(items) < 2:
        items.append(fallback[len(items)] if len(items) < len(fallback) else "")
    return [items[0], items[1]]


def compose_catalog(
    products: list[dict[str, Any]],
    script: dict[str, Any] | None = None,
    brand: str = "바로쇼핑",
    theme: dict[str, str] | None = None,
) -> dict[str, Any]:
    """productSchema 상품들 + script(hook/cta)를 catalogSchema inputProps로 조립."""
    s = script or {}
    hook = _two(s.get("hook"), ["오늘의", "단독 특가"])
    cta = s.get("cta") or "지금 구매하기 →"
    return {
        "brandName": brand,
        "eyebrow": "TODAY ONLY · 자정 마감",
        "hookTitle": hook,
        "hookSub": f"딱 {len(products)}가지 · 한정 특가",
        "cta": cta,
        "outroTitle": ["지금", "바로 담으세요"],
        "outroSub": "수량 소진 시 조기 마감",
        "outroCta": "프로필 링크에서 구매 ↗",
        "theme": theme or dict(WARM_THEME),
        "products": products,
    }
