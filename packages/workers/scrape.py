"""상품 스크래퍼 (FR-1 / P2-7) — Playwright. 대상 사이트·셀렉터는 D1 확정 필요(PRD §15).

normalize 는 결정적(추출 원본 → render productSchema 호환 dict, 단위테스트 가능).
scrape 는 Playwright로 실제 수집(대상 사이트 + `playwright install` 필요). 랜덤 지연·백오프는 §11.
"""
from __future__ import annotations

from typing import Any


def _won(v: Any) -> int:
    if v is None:
        return 0
    s = str(v).replace(",", "").replace("원", "").strip()
    digits = "".join(ch for ch in s if ch.isdigit())
    return int(digits) if digits else 0


def normalize(raw: dict[str, Any]) -> dict[str, Any]:
    """스크랩 원본 → render productSchema 호환 dict."""
    name = raw.get("name", "")
    names = name if isinstance(name, list) else [name]
    return {
        "emoji": raw.get("emoji", "📦"),
        "image": raw.get("image"),
        "category": raw.get("category", ""),
        "name": [n for n in names if n][:2] or ["상품"],
        "sub": raw.get("sub", ""),
        "rating": str(raw.get("rating", "")),
        "reviews": str(raw.get("reviews", "")),
        "was": _won(raw.get("was")),
        "now": _won(raw.get("now")),
        "tint": raw.get("tint", "#E9F0FF"),
        "tintDeep": raw.get("tintDeep", "#2E5BFF"),
    }


def scrape(url: str, selectors: dict[str, str]) -> dict[str, Any]:
    """대상 URL에서 selectors(field→CSS)로 추출 후 normalize. D1 확정 후 사용."""
    from playwright.sync_api import sync_playwright  # lazy (테스트 시 불필요)

    raw: dict[str, Any] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, timeout=30000)
            for field, sel in selectors.items():
                el = page.query_selector(sel)
                raw[field] = el.inner_text().strip() if el else None
        finally:
            browser.close()
    return normalize(raw)
