"""쿠팡 파트너스 OpenAPI 클라이언트 단위 검증 — HMAC 서명·매핑 (실키/호출 없이 결정적)."""
from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone

import pytest

from workers import coupang_partners as cp


def test_signed_date_format():
    sd = cp.signed_date(datetime(2026, 6, 14, 12, 0, 0, tzinfo=timezone.utc))
    assert sd == "260614T120000Z"


def test_generate_authorization_message_format():
    sd = "260614T120000Z"
    url = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search?keyword=a&limit=1"
    auth = cp.generate_authorization("GET", url, "AK", "SK", sdate=sd)
    # 서명을 독립 재계산하여 message 구성(=signedDate+method+path+query)을 검증
    path, _, query = url.partition("?")
    msg = sd + "GET" + path + query
    expect = hmac.new(b"SK", msg.encode(), hashlib.sha256).hexdigest()
    assert f"signature={expect}" in auth
    assert "access-key=AK" in auth
    assert f"signed-date={sd}" in auth
    assert "algorithm=HmacSHA256" in auth


def test_to_product_maps_to_schema():
    item = {
        "productName": "닥터지 브라이트닝 업 선 플러스",
        "categoryName": "뷰티",
        "productPrice": 18900,
        "productImage": "https://img.coupang/x.jpg",
        "productUrl": "https://link.coupang.com/a/ezMnwU7tQa",
    }
    p = cp.to_product(item)
    assert p["name"] == ["닥터지 브라이트닝 업 선 플러스"]
    assert p["now"] == 18900 and p["was"] == 18900  # 원가 미제공 → 0%
    assert p["image"] == "https://img.coupang/x.jpg"
    assert p["buy_url"] == "https://link.coupang.com/a/ezMnwU7tQa"


def test_search_requires_keys(monkeypatch):
    monkeypatch.delenv("COUPANG_ACCESS_KEY", raising=False)
    monkeypatch.delenv("COUPANG_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError):
        cp.search_products("선크림")


def test_deeplink_requires_keys(monkeypatch):
    monkeypatch.delenv("COUPANG_ACCESS_KEY", raising=False)
    monkeypatch.delenv("COUPANG_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError):
        cp.to_deeplink(["https://www.coupang.com/vp/products/1"])
