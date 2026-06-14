"""쿠팡 파트너스 OpenAPI 클라이언트 — 상품 검색 + 어필리에이트 deeplink 생성 (P2-7 운영 권장).

스크래핑은 쿠팡 봇방어(403/Access Denied)로 차단되므로, 쿠팡 데이터·어필리에이트 링크는
공식 OpenAPI(HMAC 인증)로 취득한다. 약관 친화적·안정적.

키: COUPANG_ACCESS_KEY / COUPANG_SECRET_KEY (env). 서명/요청구성은 결정적(단위테스트).
실제 호출 시 httpx (lazy import). 키 없으면 RuntimeError.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import urllib.parse
from datetime import datetime, timezone
from typing import Any

from .scrape import normalize

DOMAIN = "https://api-gateway.coupang.com"
DEEPLINK_PATH = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
SEARCH_PATH = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"


def signed_date(now: datetime | None = None) -> str:
    """yyMMddTHHMMSSZ (GMT) — 쿠팡 HMAC signed-date 포맷."""
    dt = now or datetime.now(timezone.utc)
    return dt.strftime("%y%m%dT%H%M%SZ")


def generate_authorization(
    method: str,
    url_path: str,
    access_key: str,
    secret_key: str,
    sdate: str | None = None,
) -> str:
    """CEA HMAC-SHA256 Authorization 헤더. message = signedDate + method + path + query."""
    sd = sdate or signed_date()
    path, _, query = url_path.partition("?")
    message = sd + method + path + query
    sig = hmac.new(
        secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return (
        f"CEA algorithm=HmacSHA256, access-key={access_key}, "
        f"signed-date={sd}, signature={sig}"
    )


def _keys() -> tuple[str, str]:
    ak = os.environ.get("COUPANG_ACCESS_KEY")
    sk = os.environ.get("COUPANG_SECRET_KEY")
    if not (ak and sk):
        raise RuntimeError(
            "COUPANG_ACCESS_KEY/COUPANG_SECRET_KEY 미설정 — 쿠팡 파트너스 OpenAPI에 필요"
        )
    return ak, sk


def to_deeplink(coupang_urls: list[str]) -> list[dict[str, Any]]:
    """일반 쿠팡 URL → 어필리에이트 deeplink(shortenUrl/landingUrl) 변환."""
    import httpx  # lazy

    ak, sk = _keys()
    auth = generate_authorization("POST", DEEPLINK_PATH, ak, sk)
    r = httpx.post(
        DOMAIN + DEEPLINK_PATH,
        headers={"Authorization": auth, "Content-Type": "application/json;charset=UTF-8"},
        json={"coupangUrls": coupang_urls},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("data", [])


def search_products(keyword: str, limit: int = 5) -> list[dict[str, Any]]:
    """키워드 상품 검색 → productData 리스트 (어필리에이트 링크 포함)."""
    import httpx  # lazy

    ak, sk = _keys()
    path = f"{SEARCH_PATH}?keyword={urllib.parse.quote(keyword)}&limit={limit}"
    auth = generate_authorization("GET", path, ak, sk)
    r = httpx.get(DOMAIN + path, headers={"Authorization": auth}, timeout=30)
    r.raise_for_status()
    return r.json().get("data", {}).get("productData", [])


def to_product(item: dict[str, Any]) -> dict[str, Any]:
    """Partners API 상품 → render productSchema 호환 dict (+ buy_url=어필리에이트 링크).

    open search API는 원가/평점/리뷰를 항상 주지 않음 → was=now(0%), rating/reviews 공란 폴백.
    """
    price = item.get("productPrice")
    prod = normalize(
        {
            "name": item.get("productName", ""),
            "category": item.get("categoryName", ""),
            "now": price,
            "was": price,  # 원가 미제공 → 0% (실딜은 별도 보정)
            "image": item.get("productImage"),
            "rating": item.get("rating", ""),
            "reviews": item.get("reviewCount", ""),
        }
    )
    prod["buy_url"] = item.get("productUrl") or item.get("shortenUrl")
    return prod
