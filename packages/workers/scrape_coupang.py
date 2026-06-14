"""쿠팡 상품 스크래퍼 (P2-7 / D1) — Playwright 실브라우저 + 봇탐지 회피 + 쿠팡 셀렉터.

주의: 쿠팡은 강한 봇 방어(403/캡차)가 있어 헤드리스·데이터센터 IP에서 차단될 수 있다.
차단 시 raw["_blocked"]=True. 운영 권장: 쿠팡 파트너스 OpenAPI(deeplink/products) 사용
(HMAC 인증, 스크래핑보다 안정적·약관 친화적).
"""
from __future__ import annotations

from typing import Any

from .scrape import normalize

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# 쿠팡 상품페이지 셀렉터 (변동 가능 → 다중 폴백)
SEL: dict[str, list[str]] = {
    "name": [
        "h1.prod-buy-header__title",
        "h2.prod-buy-header__title",
        ".prod-buy-header__title",
    ],
    "now": [
        ".prod-sale-price .total-price strong",
        "span.total-price > strong",
        ".total-price strong",
    ],
    "was": [".prod-origin-price .origin-price", "del.origin-price", ".origin-price"],
    "rating": [
        ".prod-buy-header__rating .rds-rating__text",
        ".rating-star-num",
        ".prod-buy-header__star-rating",
    ],
    "reviews": [
        ".prod-buy-header__rating-count",
        ".count",
        ".rating-count",
    ],
}
IMG_SEL = ["img.prod-image__detail", ".prod-image__items img", ".prod-image img"]


def _first_text(page, selectors: list[str]) -> str | None:
    for s in selectors:
        el = page.query_selector(s)
        if el:
            t = (el.inner_text() or "").strip()
            if t:
                return t
    return None


def scrape_coupang(
    url: str, headless: bool = True, timeout_ms: int = 45000
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright  # lazy

    raw: dict[str, Any] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        ctx = browser.new_context(
            user_agent=UA,
            locale="ko-KR",
            viewport={"width": 1280, "height": 900},
            extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9"},
        )
        ctx.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )
        page = ctx.new_page()
        try:
            resp = page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)  # JS 가격/평점 로드 대기
            title = (page.title() or "").strip()
            status = resp.status if resp else None
            raw["_http_status"] = status
            raw["_title"] = title
            raw["_blocked"] = bool(
                (status and status >= 400)
                or not title
                or "Access Denied" in title
                or "차단" in title
                or "captcha" in title.lower()
            )
            raw["name"] = _first_text(page, SEL["name"])
            raw["now"] = _first_text(page, SEL["now"])
            raw["was"] = _first_text(page, SEL["was"])
            raw["rating"] = _first_text(page, SEL["rating"])
            raw["reviews"] = _first_text(page, SEL["reviews"])
            for s in IMG_SEL:
                el = page.query_selector(s)
                if el and el.get_attribute("src"):
                    raw["image"] = el.get_attribute("src")
                    break
        finally:
            browser.close()

    matched = sum(1 for k in ("name", "now", "was", "rating", "reviews") if raw.get(k))
    return {"raw": raw, "matched_fields": matched, "normalized": normalize(raw)}
