"""범용 상품 크롤러 (P2-7 재설계) — 사이트별 셀렉터/플랫폼 API 없이 구조화 데이터로 수집.

전략(간편·확장성):
  1) JSON-LD (schema.org/Product) — 대부분의 쇼핑몰이 서버렌더로 포함
  2) OpenGraph/메타 (og:title, og:image, product:price:amount ...)
  3) (선택) CSS 셀렉터 폴백 — 구조화 데이터가 없는 사이트만

핵심: 추출은 HTML '문자열'에서 수행 → WebFetch/requests/Playwright 어디서 받은 HTML이든 동작
(브라우저·API 불필요). 봇방어 사이트(쿠팡 등)는 fetch_html(headed=True, 사용자 실 크롬)로
HTML만 확보하면 동일 추출. 수집 후 누락 필드는 _needs_review로 표기 → 운영자 확정.
"""
from __future__ import annotations

import json
from html.parser import HTMLParser
from typing import Any

from .scrape import normalize

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class _Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}
        self.ldjson: list[str] = []
        self._cap = False
        self._buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        if tag == "meta":
            key = a.get("property") or a.get("name")
            if key and a.get("content"):
                self.meta.setdefault(key, a["content"])
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._cap = True
            self._buf = []

    def handle_data(self, data: str) -> None:
        if self._cap:
            self._buf.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._cap:
            self.ldjson.append("".join(self._buf))
            self._cap = False


def _iter_products(obj: Any):
    if isinstance(obj, list):
        for x in obj:
            yield from _iter_products(x)
    elif isinstance(obj, dict):
        t = obj.get("@type")
        types = t if isinstance(t, list) else [t]
        if "Product" in types:
            yield obj
        if "@graph" in obj:
            yield from _iter_products(obj["@graph"])


def _clean_rating(v: Any) -> Any:
    """평점 부동소수(4.0799…) → 보기 좋은 1자리 문자열. 그 외는 원본 유지."""
    if isinstance(v, (int, float)):
        return f"{round(float(v), 1):g}"
    return v


def _first_image(img: Any) -> str | None:
    if isinstance(img, str):
        return img
    if isinstance(img, list) and img:
        return img[0] if isinstance(img[0], str) else (img[0] or {}).get("url")
    if isinstance(img, dict):
        return img.get("url")
    return None


def extract_jsonld(html: str) -> dict[str, Any]:
    c = _Collector()
    c.feed(html)
    for block in c.ldjson:
        try:
            data = json.loads(block)
        except Exception:  # noqa: BLE001
            continue
        for prod in _iter_products(data):
            offers = prod.get("offers") or {}
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            rating = prod.get("aggregateRating") or {}
            brand = prod.get("brand")
            brand_name = brand.get("name") if isinstance(brand, dict) else brand
            return {
                "name": prod.get("name"),
                "image": _first_image(prod.get("image")),
                "category": prod.get("category"),
                "brand": brand_name,
                "now": offers.get("price"),
                "was": offers.get("highPrice") or offers.get("price"),
                "rating": _clean_rating(rating.get("ratingValue")),
                "reviews": rating.get("reviewCount") or rating.get("ratingCount"),
                "sub": prod.get("description"),
            }
    return {}


def extract_og(html: str) -> dict[str, Any]:
    c = _Collector()
    c.feed(html)
    m = c.meta
    return {
        "name": m.get("og:title"),
        "image": m.get("og:image"),
        "now": m.get("product:price:amount") or m.get("og:price:amount"),
        "sub": m.get("og:description"),
    }


def extract_product(html: str) -> dict[str, Any]:
    """HTML → render productSchema 호환 dict (+ _source, _needs_review). 브라우저/API 불필요."""
    og = {k: v for k, v in extract_og(html).items() if v}
    ld = {k: v for k, v in extract_jsonld(html).items() if v}
    merged = {**og, **ld}  # JSON-LD 우선
    source = "json-ld" if ld else ("opengraph" if og else "none")

    raw = {
        "name": merged.get("name", ""),
        "category": merged.get("category") or merged.get("brand") or "",
        "sub": merged.get("sub", ""),
        "now": merged.get("now"),
        "was": merged.get("was") or merged.get("now"),
        "rating": merged.get("rating", ""),
        "reviews": merged.get("reviews", ""),
        "image": merged.get("image"),
    }
    prod = normalize(raw)
    prod["_source"] = source
    # 수집 후 확정: 누락/저신뢰 필드 표기 → 운영자 확인
    prod["_needs_review"] = [f for f in ("name", "now", "image") if not raw.get(f)]
    if merged.get("brand"):
        prod["_brand"] = merged["brand"]
    return prod


def fetch_html(url: str, headed: bool = False, timeout_ms: int = 45000) -> str:
    """페이지 HTML 확보. 봇방어 사이트는 headed=True(사용자 실 크롬, channel=chrome)로 통과."""
    from playwright.sync_api import sync_playwright  # lazy

    launch: dict[str, Any] = {
        "headless": not headed,
        "args": ["--disable-blink-features=AutomationControlled", "--no-sandbox"],
    }
    if headed:
        launch["channel"] = "chrome"  # 사용자 로컬 실 크롬
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch)
        ctx = browser.new_context(user_agent=UA, locale="ko-KR")
        page = ctx.new_page()
        try:
            page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            return page.content()
        finally:
            browser.close()


def crawl(url: str, headed: bool = False) -> dict[str, Any]:
    """URL → 상품 dict. 봇방어 사이트는 headed=True."""
    return extract_product(fetch_html(url, headed=headed))
